<!-- Version: 3.1.0 -->
<!-- Changelog: v3.1.0 - Added Pitfall #8 and auto-Taiwanese Mandarin (zh-TW-YunJheNeural) neural voice replacement to eliminate mainland retroflex -->

# 🎬 Google Vids 獨立全自動 AI 影片製作技能 (`google-vids-video-producer` v3.1.0)

專為 **Antigravity / Claude Code / Codex** 打造的 **Google Vids (`docs.google.com/videos`) 100% 獨立全自動 AI 影片生產線技能**。

無需消耗 Google Flow 每月 1,000 點額度，也不需要 Colab GPU 算力——直接運用 **Google AI Pro (Gemini Pro)** 帳號在 Google Vids 內建的 **`Omni 720p 橫式 10 秒` 生成引擎**，自動完成多鏡算圖、時間軸組裝、**1080p Full HD (1920×1080 30fps) MP4 匯出**、**100% 正統台灣國語（無大陸捲舌音）自動音軌替換**、本地 **FFmpeg 繁體中文雙色硬字幕燒錄**，並依四大頻道分類自動歸檔至 `Google Vids 影片` 總目錄。

---

## ✨ 核心亮點

1. **0 點 Google Flow 額度消耗**：100% 走 Google Vids 獨立每日配額池。
2. **100% 正統台灣國語旁白（無大陸捲舌音）**：後製引擎自動呼叫 Microsoft Edge TTS（`zh-TW-YunJheNeural` 雲哲 男聲 / `zh-TW-HsiaoChenNeural` 曉臻 女聲）毫秒級對齊每鏡 10.0 秒無損替換，徹底消除 Google Omni 原生語音的大陸普通話兒化與捲舌音。
3. **匯出即升頻 1080p Full HD**：透過 `檔案 -> 下載 -> MP4 影片 (.mp4)` 匯出時，時間軸自動輸出 **1920×1080 @ 30fps (H.264 + AAC)**。
4. **單一常駐 Node.js MCP 連線 + 固定鍵盤公式（提速 100 倍）**：
   - 徹底解決逐次啟動 `node vids_call.mjs` 與逐次 `vids_observe` 造成的 5 分鐘卡頓。
   - 內建右側面板無死角鍵盤導航公式（第 $k$ 部生成影片卡片位於 `Tab` 第 $5 + 10(k-1)$ 步，其專屬 `插入` 按鈕位於第 **$9 + 10(k-1)$** 步），100% 免疫浮動視窗遮擋（`TARGET_OBSCURED`）。
5. **雙版本輸出 + 四大分類自動歸檔**：
   - 自動產出 `<專案名稱>.mp4`（內嵌繁中雙色硬字幕 + 台灣國語正式版）與 `<專案名稱>_純淨無字幕版.mp4`（台灣國語母帶版）。
   - 自動歸檔至 `Google Vids 影片\［手作科學］|［國小自然］|［大識界 開眼界］|［AI 自學筆記］\`。

---

## ⚠️ 實戰踩過的 8 大誤區與終極解法一覽

| # | 實戰誤區 (Pitfall) | 發生原因 | 終極解法 (Built-in Fix) |
| :- | :--- | :--- | :--- |
| **1** | 用獨立 Headless / Playwright 新開視窗登入失敗或背景隱形 | Google Workspace 阻擋無頭瀏覽器，且使用者看不到前台畫面 | 改用 [`Shugar86/vids-studio`](https://github.com/Shugar86/vids-studio) Chrome 擴充功能直接附著於使用者已開啟之真實 Chrome 分頁 |
| **2** | Windows 非 `C:\Users` 路徑（如 `D:\` 槽）安裝 Native Host 被拒絕 | `platform_support.py` 預設只允許 `Path.home()` 且拒絕 `BUILTIN\Users (S-1-5-32-545)` ACL | 執行 [`scripts/patch_windows_acl.py`](scripts/patch_windows_acl.py) 一鍵修補白名單 |
| **3** | 在頁面右下角注入自訂浮動 HUD 導致 `TARGET_OBSCURED` | 浮動 DOM 遮擋右側面板下半部的 `展開`、`生成`、`插入` 按鈕，觸發碰撞攔截 | 禁止注入遮擋右側欄之浮動面板；右側面板按鈕全面改用 `Tab + Enter` 鍵盤導航 |
| **4** | 同時跑兩個背景腳本導致 `STALE_SNAPSHOT` 與 `RECONCILIATION_REQUIRED` | 雙行程搶占同一個 `snapshotId` | 嚴守單一常駐連線序列執行；內建 `ensureReconciled()` 自動修復租約 |
| **5** | 從 `vids_click` / `vids_press_key` 回傳值讀取 `snapshotId` 拋出 `KeyError` | 寫入動作回傳值僅含 `{clicked: true}`，不含新 `snapshotId` | 統一透過 `vids_observe` 取得有效 `snapshotId` |
| **6** | **第 3～5 鏡插入時嚴重卡頓 4～5 分鐘** | Python 迴圈每按 1 次 `Tab` 就重開 `node vids_call.mjs` (8s) + 掃描 1200 節點 (4s)，按 45 次耗時 295 秒 | [`scripts/vids_fast_autopilot.mjs`](scripts/vids_fast_autopilot.mjs) 採用單一常駐 MCP 連線 + 固定步數公式 $9 + 10(k-1)$ + 輕量快照 |
| **7** | 字幕在 40 秒提前結束、每鏡錯位 2 秒 | 誤以為單鏡 8 秒，實測 Google Vids Omni 模型每鏡為 **10.0 秒**（5 鏡共 50.2 秒） | [`scripts/vids_postprocess_and_archive.py`](scripts/vids_postprocess_and_archive.py) 強制以 `10.0s / 鏡` 動態生成雙色 ASS 字幕 |
| **8** | **語音帶有大陸普通話捲舌音與兒化音** | Google Vids Omni 模型主要以簡體普通話語料訓練，即使 prompt 寫 zh-TW 仍帶有北京捲舌腔調 | [`scripts/vids_postprocess_and_archive.py`](scripts/vids_postprocess_and_archive.py) 自動以 `zh-TW-YunJheNeural` 合成 100% 正統台灣國語無捲舌音軌替換 |

---

## 📂 專案結構

```text
google-vids-video-producer/
├── SKILL.md                                    # 完整技能規範與 8 大誤區 SOP (v3.1.0)
├── README.md                                   # 專案說明文件
├── scripts/
│   ├── vids_fast_autopilot.mjs                 # 單一常駐 MCP 連線極速生成、插入與匯出腳本
│   ├── patch_windows_acl.py                    # Windows 非 C 槽 Native Host 權限白名單修補工具
│   └── vids_postprocess_and_archive.py         # 100% 台灣國語音軌替換 + 1080p 雙色硬字幕壓制 + 四大分類自動歸檔引擎
└── examples/
    └── vids_project_manifest.example.json      # 5 鏡 × 10 秒「表面張力奇觀」實戰範例設定檔
```

---

## 🚀 快速開始

### 1. 安裝技能
將本儲存庫放入您的專案 `.agents/skills/google-vids-video-producer` 或全域技能目錄：
```bash
git clone https://github.com/tangfl1115/google-vids-video-producer-skill.git .agents/skills/google-vids-video-producer
```

### 2. 修補 Windows 路徑權限並註冊 `vids-studio` Native Bridge（首次安裝）
```powershell
python .agents/skills/google-vids-video-producer/scripts/patch_windows_acl.py "d:\2026antigravity\.agents\tools\vids-studio"
```

### 3. 一鍵極速生成、組裝時間軸與匯出 1080p MP4
```powershell
node .agents/skills/google-vids-video-producer/scripts/vids_fast_autopilot.mjs `
  --manifest "examples/vids_project_manifest.example.json" `
  --state ".vids_session_state.json"
```

### 4. 一鍵注入 100% 台灣國語、燒錄繁體中文雙色硬字幕並按頻道分類歸檔
```powershell
python .agents/skills/google-vids-video-producer/scripts/vids_postprocess_and_archive.py `
  --manifest "examples/vids_project_manifest.example.json"
```
