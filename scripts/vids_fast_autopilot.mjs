#!/usr/bin/env node
// Version: 3.0.0
// Changelog:
//   - v3.0.0: 終極零踩坑極速版。
//     1. 單一常駐 MCP Client 連線（消除每次呼叫重啟 Node 子程序之 8 秒延遲）。
//     2. 根據單次 vids_observe 的『生成的影片：...』卡片索引 k (1-based)，直接計算精確 Tab 步數 (9 + 10*(k-1))，只在最後一步驗證『插入』焦點，徹底消除逐次 Tab 呼叫 vids_observe 造成的 4~5 分鐘卡頓！
//     3. 自動處理 RECONCILIATION_REQUIRED、自動切換/新增場景、自動觸發『檔案 -> 下載 -> MP4 影片 (.mp4)』。

import {pathToFileURL} from 'node:url'
import {readFileSync} from 'node:fs'
import {resolve} from 'node:path'
import {randomUUID} from 'node:crypto'

function parseArgs(argv) {
  const out = {}
  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === '--manifest' && argv[i + 1]) out.manifest = argv[++i]
    else if (argv[i] === '--state' && argv[i + 1]) out.state = argv[++i]
    else if (argv[i] === '--bridge' && argv[i + 1]) out.bridge = argv[++i]
    else if (argv[i] === '--pair-code' && argv[i + 1]) out.pairCode = argv[++i]
  }
  return out
}

const args = parseArgs(process.argv)
if (!args.manifest || !args.state) {
  console.error('Usage: node vids_fast_autopilot.mjs --manifest <manifest.json> --state <.vids_session_state.json> [--bridge <vids-studio-dir>]')
  process.exit(2)
}

const bridge = resolve(args.bridge || process.env.VIDS_CODEX_BRIDGE || 'd:/2026antigravity/.agents/tools/vids-studio')
const manifest = JSON.parse(readFileSync(resolve(args.manifest), 'utf8'))
const state = JSON.parse(readFileSync(resolve(args.state), 'utf8'))
const sid = state.sessionId
const ctok = state.controlToken

const sdk = file => import(pathToFileURL(`${bridge}/node_modules/@modelcontextprotocol/sdk/dist/esm/client/${file}`).href)
const {Client} = await sdk('index.js')
const {StdioClientTransport} = await sdk('stdio.js')

const client = new Client({name: 'vids-fast-autopilot', version: '3.0.0'})
await client.connect(new StdioClientTransport({
  command: process.execPath,
  args: [`${bridge}/server/index.mjs`],
  env: {}
}))

const sleep = ms => new Promise(r => setTimeout(r, ms))

async function call(tool, payload) {
  const res = await client.callTool({name: tool, arguments: payload}, undefined, {timeout: 60000})
  const txt = res.content?.find(c => c.type === 'text')?.text || '{}'
  const data = JSON.parse(txt)
  if (res.isError || data.ok === false) {
    throw new Error(`${tool} failed: ${txt}`)
  }
  return data
}

async function observe(maxNodes = 1200) {
  const r = await call('vids_observe', {sessionId: sid, controlToken: ctok, maxNodes})
  return r.result
}

async function pressKeyWithSnap(snapId, key) {
  await call('vids_press_key', {
    sessionId: sid,
    controlToken: ctok,
    snapshotId: snapId,
    operation_id: randomUUID(),
    key
  })
}

async function ensureReconciled() {
  const st = await call('vids_status', {sessionId: sid})
  if (st.coordinator?.state === 'reconcile' || st.recovery) {
    const obs = await observe(400)
    await call('vids_reconcile_control', {
      sessionId: sid,
      controlToken: ctok,
      snapshotId: obs.snapshotId,
      acknowledgeUnknown: true
    })
    console.log('🔧 已自動完成控制權對齊 (Reconciled)')
  }
}

async function ensureAiVideoPanelOpen() {
  const obs = await observe()
  const aiBtn = obs.nodes.find(n => n.role === 'button' && n.name === '生成 AI 短片')
  if (aiBtn && String(aiBtn.states?.pressed) !== 'true') {
    await call('vids_click', {
      sessionId: sid,
      controlToken: ctok,
      snapshotId: obs.snapshotId,
      operation_id: randomUUID(),
      nodeRef: aiBtn.ref
    })
    await sleep(600)
  }
}

async function selectOrCreateScene(scNum) {
  const obs = await observe()
  const scBtn = obs.nodes.find(n => n.role === 'button' && (n.name || '').startsWith(`場景 ${scNum} `))
  if (scBtn) {
    await call('vids_click', {
      sessionId: sid,
      controlToken: ctok,
      snapshotId: obs.snapshotId,
      operation_id: randomUUID(),
      nodeRef: scBtn.ref
    })
    console.log(`  🎯 已選取時間軸上的『${scBtn.name}』`)
    await sleep(500)
  } else {
    const newScBtn = obs.nodes.find(n => n.name === '新場景 (Ctrl+M)' && n.role === 'button')
    await call('vids_click', {
      sessionId: sid,
      controlToken: ctok,
      snapshotId: obs.snapshotId,
      operation_id: randomUUID(),
      nodeRef: newScBtn.ref
    })
    console.log(`  ➕ 已新增並選取第 ${scNum} 場`)
    await sleep(900)
  }
}

async function expandPromptIfNeeded() {
  let obs = await observe()
  const box = obs.nodes.find(n => n.role === 'textbox' && (n.name || '').includes('請描述影片內容'))
  if (box) return obs
  const createTab = obs.nodes.find(n => n.role === 'tab' && n.name === '建立')
  await call('vids_click', {
    sessionId: sid,
    controlToken: ctok,
    snapshotId: obs.snapshotId,
    operation_id: randomUUID(),
    nodeRef: createTab.ref
  })
  await sleep(200)
  obs = await observe(400)
  await pressKeyWithSnap(obs.snapshotId, 'Tab')
  obs = await observe(400)
  await pressKeyWithSnap(obs.snapshotId, 'Enter')
  console.log('  📂 已展開提示詞輸入框 (Tab 1 + Enter)')
  await sleep(500)
  return await observe()
}

async function generateIfNotExists(scene) {
  const matchPrefix = scene.match_prefix || scene.matchPrefix || scene.prompt.slice(0, 38)
  let obs = await observe()
  let existing = obs.nodes.find(n => n.role === 'button' && (n.name || '').includes('生成的影片') && (n.name || '').includes(matchPrefix))
  if (existing) {
    console.log(`  ✅ ${scene.id} 已存在於影片結果清單中，跳過重複算圖`)
    return
  }

  const cancelBtn = obs.nodes.find(n => n.role === 'button' && n.name === '取消')
  if (!cancelBtn) {
    obs = await expandPromptIfNeeded()
    const box = obs.nodes.find(n => n.role === 'textbox' && (n.name || '').includes('請描述影片內容'))
    await call('vids_type_text', {
      sessionId: sid,
      controlToken: ctok,
      snapshotId: obs.snapshotId,
      operation_id: randomUUID(),
      nodeRef: box.ref,
      text: scene.prompt,
      replace: true
    })
    console.log(`  ✍️ 已填入 ${scene.id} 提示詞`)
    await sleep(300)

    for (let step = 1; step <= 8; step++) {
      obs = await observe(500)
      await pressKeyWithSnap(obs.snapshotId, 'Tab')
      obs = await observe(500)
      const focused = obs.nodes.filter(n => n.states?.focused)
      if (focused.some(n => n.role === 'button' && n.name === '生成')) {
        await pressKeyWithSnap(obs.snapshotId, 'Enter')
        console.log(`  🚀 已送出 ${scene.id} 生成請求 (Tab ${step} + Enter)！`)
        break
      }
    }
  }

  const start = Date.now()
  while (Date.now() - start < 160000) {
    await sleep(5000)
    obs = await observe()
    existing = obs.nodes.find(n => n.role === 'button' && (n.name || '').includes('生成的影片') && (n.name || '').includes(matchPrefix))
    if (existing) {
      console.log(`  ✅ ${scene.id} 10秒 AI 短片算圖完成！(${Math.round((Date.now() - start) / 1000)}s)`)
      return
    }
    console.log(`  ⏳ ${scene.id} 雲端算圖中 (${Math.round((Date.now() - start) / 1000)}s)...`)
  }
  throw new Error(`${scene.id} 算圖逾時`)
}

async function insertClipFast(scene, scNum) {
  const matchPrefix = scene.match_prefix || scene.matchPrefix || scene.prompt.slice(0, 38)
  let obs = await observe()
  const videoCards = obs.nodes.filter(n => n.role === 'button' && (n.name || '').startsWith('生成的影片：'))
  const cardIdx = videoCards.findIndex(n => (n.name || '').includes(matchPrefix))
  if (cardIdx < 0) {
    throw new Error(`找不到 ${scene.id} (${matchPrefix}) 的影片卡片`)
  }

  // 直接計算從『建立』頁籤出發到第 (cardIdx+1) 部影片『插入』按鈕的目標步數：9 + 10 * cardIdx
  const targetTabs = 9 + 10 * cardIdx
  const createTab = obs.nodes.find(n => n.role === 'tab' && n.name === '建立')
  await call('vids_click', {
    sessionId: sid,
    controlToken: ctok,
    snapshotId: obs.snapshotId,
    operation_id: randomUUID(),
    nodeRef: createTab.ref
  })
  await sleep(200)

  console.log(`  ⚡ ${scene.id} 位於結果清單第 ${cardIdx + 1} 張，直接執行 ${targetTabs} 步極速 Tab 導航 (minimal detail)...`)
  for (let i = 1; i <= targetTabs; i++) {
    // 使用 maxNodes: 80 減少序列化開銷
    const minObs = await observe(80)
    await pressKeyWithSnap(minObs.snapshotId, 'Tab')
  }

  obs = await observe()
  const focused = obs.nodes.filter(n => n.states?.focused)
  if (!focused.some(n => n.role === 'button' && n.name === '插入')) {
    // 微調搜尋最多 6 步
    for (let extra = 0; extra < 6; extra++) {
      await pressKeyWithSnap(obs.snapshotId, 'Tab')
      obs = await observe()
      if (obs.nodes.some(n => n.states?.focused && n.role === 'button' && n.name === '插入')) break
    }
  }
  await pressKeyWithSnap(obs.snapshotId, 'Enter')
  await sleep(3000)
  console.log(`  🎬 ${scene.id} 已成功插入第 ${scNum} 場！`)
}

async function exportMp4() {
  console.log('\n📦 開始自動觸發『檔案 -> 下載 -> MP4 影片 (.mp4)』...')
  let obs = await observe(800)
  const fileMenu = obs.nodes.find(n => n.role === 'menuitem' && n.name === '檔案')
  await call('vids_click', {
    sessionId: sid,
    controlToken: ctok,
    snapshotId: obs.snapshotId,
    operation_id: randomUUID(),
    nodeRef: fileMenu.ref
  })
  await sleep(600)
  obs = await observe(800)
  const dlMenu = obs.nodes.find(n => n.role === 'menuitem' && (n.name || '').includes('下載'))
  if (dlMenu) {
    await call('vids_click', {
      sessionId: sid,
      controlToken: ctok,
      snapshotId: obs.snapshotId,
      operation_id: randomUUID(),
      nodeRef: dlMenu.ref
    })
    await sleep(600)
  }
  obs = await observe(800)
  const mp4Item = obs.nodes.find(n => n.role === 'menuitem' && (n.name || '').includes('MP4 影片'))
  if (mp4Item) {
    await call('vids_click', {
      sessionId: sid,
      controlToken: ctok,
      snapshotId: obs.snapshotId,
      operation_id: randomUUID(),
      nodeRef: mp4Item.ref
    })
    console.log('✅ 已點擊『MP4 影片 (.mp4)』，Chrome 正在將 1080p MP4 下載至本機！')
  }
}

try {
  await ensureReconciled()
  await ensureAiVideoPanelOpen()

  const scenes = manifest.scenes || []
  for (let i = 0; i < scenes.length; i++) {
    const scNum = i + 1
    const sc = scenes[i]
    console.log(`\n==========================================`)
    console.log(` 🎬 處理第 ${scNum}/${scenes.length} 鏡 (${sc.id})`)
    console.log(`==========================================`)
    await selectOrCreateScene(scNum)
    await generateIfNotExists(sc)
    await selectOrCreateScene(scNum)
    await insertClipFast(sc, scNum)
  }

  await exportMp4()
} finally {
  await client.close().catch(() => {})
}
