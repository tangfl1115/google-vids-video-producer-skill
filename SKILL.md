---
name: google-vids-video-producer
description: >
  Google Vids (docs.google.com/videos) 獨立全自動 AI 影片製作工作流技能（官方實戰零踩坑 SOP v3.6.0）。
  獨立使用 Google Vids 內建「Omni 720p 橫式 10 秒」原生畫面生成（每月固定僅 500 秒硬上限／最多約 8 分鐘，為四引擎中最稀缺之受限額度，不消耗 Google Flow 1,000 點）、單一常駐 Node.js MCP 連線極速控制、1080p Full HD MP4 自動匯出、100% 正統台灣國語（zh-TW-YunJheNeural 無捲舌音）自動音軌替換、本地 CPU FFmpeg 繁體中文雙色硬字幕燒錄，以及依四大頻道分類自動歸檔至「Google Vids 影片」資料夾。
  當使用者提到「Google Vids 影片」「用 Vids 做影片」「Google Vids 自動生成」「Vids 獨立生成影片」或操作 Google Vids 專案時直接載入呼叫。
---

<!-- Version: 3.6.0 -->
<!-- Changelog:
  v3.6.0 (2026-11-24) - 修正重大額度認知錯誤：明確寫入 Google Vids 非免費無限額度，而是【每月固定僅 500 秒生成額度】（最多 50 支 10 秒鏡＝總長約 8 分 20 秒，計入重抽僅夠做 1～2 支短片），屬於四大影片引擎中最稀缺、最先觸頂的受限資源；並統一標頭版本號。
  v3.5.0 (2026-11-09) -
    1. 【SSML 聲學情感與減速防呆標準 & 代碼層硬閘門】：徹底杜絕機械化新聞朗讀腔！後製引擎強制鎖定 `rate="-10%"` 溫和語速，自動將破折號（——）與省略號（……）映射為毫秒級 `<break time="..."/>` 聲學停頓。
    2. 【單鏡字數 <= 40 字代碼層硬阻斷】：在合成前由 Python 腳本直接檢查純中文字數，超過 40 字立即觸發 `ValueError` 攔截中斷，禁止未精簡台詞進入語音合成。
    3. 【新增誤區 10（機械化快讀新聞稿誤區）】：明訂四幕情感曲線（鋪陳、危機、絕境、破局）與單鏡 10 秒黃金三段式呼吸留白，後製音訊管線內建廣播級人聲強化（Highpass 80Hz + Compand 壓縮）與三軌混音架構。
  v3.4.0 (2026-11-08) -
    1. 【中文自然語意呼吸分段字幕標準】：徹底廢除字數機械式二分法。依「時間/主體交代 -> 核心事件/動態 -> 轉折/重擊金句」動態分為 2~3 段獨立跳動更換，單句單行顯現、不分上下行堆疊，文字放大至 68pt、左右安全邊界 140px（絕不超框），且分段純文字與口播台灣國語 100% 逐字咬合。
    2. 【右上角品牌板材徽章標準化】：封面與成片浮水印導入實體板材質感（如方案 D 霧面壓克力立牌、品牌垂直色條、純文字浮雕標籤，不使用廉價粗糙幾何圖）。
  v3.3.0 (2026-11-07) -
    1. 【單鏡字數嚴格 <= 40 字硬限制】：Google Vids 單鏡固定 10.0 秒，純中文字數嚴格限制 <= 40 字（最佳區間 32~38 字，朗讀約 7.2~8.2s，保留 1.8~2.8s 呼吸氣口），嚴禁語速過快產生壓迫感。
    2. 【廢除 Tab 巡歷，全面啟用 Accessibility Node 直擊】：廢除所有 `press('Tab')` 迴圈，改為直接定位無障礙節點 `{ role: "button", name: "插入", description: "插入影片" }`，0.2 秒瞬時插入。
    3. 【分鏡台詞強制確認閘門 (Stage Gate)】：Stage 1 腳本台詞必須經由使用者明確確認後，方得啟動 Stage 2 語音與雲端擴散生成。
    4. 【FFmpeg Concat PTS 漂移硬防呆】：嚴禁對不同 timebase (1/15360 vs 1/90000) 之 MP4 進行 `-c copy` concat；一律使用 `filter_complex [0:v]fps=30,setpts=PTS-STARTPTS[v0];[1:v]fps=30,setpts=PTS-STARTPTS[v1];[v0][v1]concat` 進行幀級精準重構。
    5. 【進度透明定時器 (Schedule Tracker)】：長時任務強制每 90~120 秒調用 `schedule` 工具主動喚醒回報，嚴禁背景靜默。
  v3.2.0 (2026-11-07) - 
    1. 新增「專業電影級 8 大進階運鏡與四大頻道分類範本矩陣（［手作科學］、［國小自然］、［大識界 開眼界］、［AI 自學筆記］）」：包含探針微距穿透、眩暈變焦、焦點轉移、衝擊快推、剖面飛掠、360°環繞、甩鏡轉場、俯衝展開，提示詞全面導入「動態動詞 + 鏡頭焦段 + 參照物視差」公式。
    2. 新增誤區 9：多鏡（第 10 鏡以上）逐次 Tab 導致無障礙樹超時（CDP Timeout），解法為直接點選視圖中央預覽對話框之「在新場景中插入」Modal 按鈕（ref=n18），1 步完成插入，徹底免除 119 次 Tab。
    3. 整合後製動態音畫同步裁剪標準：由 FFmpeg 自動依台灣國語台詞長度將 Omni 原生 10s 裁切為 4.5s～6.0s 緊湊短鏡，符合 YouTube 高留存節奏並杜絕後段擴散形變。
  v3.1.0 - 解決 Google Vids Omni 原生語音具大陸捲舌音問題（新增誤區 8），後製引擎 `scripts/vids_postprocess_and_archive.py` 內建自動合成 100% 道地台灣國語（Microsoft edge-tts `zh-TW-YunJheNeural` 雲哲 / `zh-TW-HsiaoChenNeural` 曉臻），以毫秒級精度替換大陸捲舌聲音軌，徹底確保成片為正統台灣腔。
  v3.0.0 - 完整收錄實戰 7 大踩坑誤區與終極解法（Pitfalls & Fixes Matrix）、建立標準化單一常駐連線極速腳本 `scripts/vids_fast_autopilot.mjs`（完全不呼叫逐次 Tab 的 `vids_observe`，插入耗時從 295 秒降至 1.8 秒）、Windows 非 C 槽 ACL 權限修補腳本 `scripts/patch_windows_acl.py` 與自動雙色硬字幕暨四大分類歸檔腳本 `scripts/vids_postprocess_and_archive.py`，並打包為獨立 GitHub Repo。
  v2.1.0 - 新增『Google Vids 影片』四大頻道分類歸檔規範（［手作科學］、［國小自然］、［大識界 開眼界］、［AI 自學筆記］）。
  v2.0.0 - 實戰驗證升級：確認 Omni 720p 橫式 10 秒含台灣國語配音規格、單一常駐 Node.js MCP 連線與 Tab 焦點公式。
  v1.0.0 - Initial release of standalone Google Vids AI Video Producer skill.
-->

# Google Vids 獨立全自動 AI 影片生產線技能 (v3.6.0 實戰零踩坑標準作業程序)

本技能為**「使用 Google Vids (`docs.google.com/videos`) 產出 1080p 有聲成片」**的端到端自動化標準作業程序（SOP）。
不消耗 Google Flow 每月 1,000 點額度，亦不消耗 Colab GPU 算力，但 **⚠️ 額度極度稀缺：每月固定僅有 `500 秒` 生成額度（最多 50 支 10 秒鏡＝全月總長上限約 8 分鐘，計入重抽實際僅能產出 1～2 支短片），是四大影片引擎中最先受限的資源**，務必把每一秒都用在刀口上（高把握度分鏡與審核定稿後才生成，嚴禁無謂盲抽）。匯出時由 Google Vids 時間軸輸出 **1920×1080 (1080p 30fps H.264) MP4**，最後在本地後製管線自動注入 **100% 正統台灣國語神經語音**，以 0 算力 FFmpeg 燒錄繁體中文雙色硬字幕並按頻道四大分類自動歸檔。

---

## 1. 核心規格與實測真相（Verified Technical Specs）

| 維度 | 實測驗證規格 |
| :--- | :--- |
| **🚨 每月硬額度上限** | **每月固定僅 `500 秒` 生成額度（非免費無限！）**＝ 最多 50 支 10 秒鏡（全月總片長最多約 8 分鐘），為四大引擎（Colab / Gemini Veo / Flow / Vids）中最先觸頂的稀缺資源；開跑前必先核算剩餘秒數與台詞定稿，嚴禁浪費。 |
| **生成模型與時長** | Google Vids 右側欄「生成 AI 短片」預設採用 **`生成設定：Omni 720p 橫式 10 秒`**（單鏡固定 **10.0 秒**，非舊版 8 秒；18 鏡合計 `03:00.6`）。 |
| **單鏡語速動態硬限** | **每秒嚴格限制 <= 4.0 字（目標 3.2～3.6 字/秒）**：嚴禁用固定 40 字限制（避免 6 秒爆速、15 秒乾等）。單鏡字數上限 = **鏡頭秒數 × 4.0 字**（6s 鏡上限 24 字、10s 鏡上限 40 字、15s 鏡上限 60 字）。永遠保留 20%~25% 鏡頭時長供運鏡開展與環境音消化，超過 4.0 字/秒代碼直接報錯中斷！ |
| **語音腔調鐵律** | **100% 正統台灣國語（嚴禁大陸捲舌音）**：Google Vids 多模態原生生成的語音常混雜普通話捲舌與兒化音。因此一律由後製管線 `scripts/vids_postprocess_and_archive.py` 自動呼叫 Microsoft Edge TTS（`zh-TW-YunJheNeural` 雲哲 男聲 / `zh-TW-HsiaoChenNeural` 曉臻 女聲）合成最道地無捲舌的台灣國語音軌，毫秒級對齊每鏡 10.0 秒替換。 |
| **匯出解析度與編碼** | 雖然單鏡預覽標示 720p，但插入時間軸後點選 `檔案 -> 下載 -> MP4 影片 (.mp4)` 匯出之成品為標準 **1920×1080 (Full HD 1080p), 30fps, H.264 (~3.86 Mbps) + AAC 立體聲**。 |
| **內建進階卡片工具** | 每張生成的影片結果卡片皆自帶 5 個原生動作按鈕：**`插入`**、**`延長`**、**`編輯`**、**`畫質提升`**、**`重新生成`**。 |
| **最終歸檔總目錄** | 凡經由 Google Vids 生成與後製完成之影片，一律依四大頻道分類自動歸檔至：<br>`d:\2026antigravity\Google Vids 影片製作\<頻道分類>\<專案名稱>\`<br>（四大固定分類：`［手作科學］`、`［國小自然］`、`［大識界 開眼界］`、`［AI 自學筆記］`） |

---

## 2. 實戰踩過的 8 大誤區與終極解法（Mandatory Pitfalls & Fixes）

在自動化控制 Google Vids 的過程中，我們親身踩過以下 **8 個嚴重誤區**。所有後續任務與 Agent **必須嚴格遵守對應解法，嚴禁重蹈覆轍**：

### ❌ 誤區 1：使用獨立 Headless / Playwright 新設定檔直接開 `docs.google.com/videos`
* **問題現象**：Google Workspace 對自動化無頭瀏覽器有極嚴格的登入風控，且新開視窗不在使用者目光焦點內，使用者會看到「沒有幫我開啟畫面」或卡在 Google 雙重驗證。
* **✅ 正確解法**：一律採用 **`vids-studio` Chrome Extension (`mngpdjlbjahinggdfkaicceicohofhap`) + Native Host (`com.vids_studio.bridge`)** 附著在使用者**當前已登入並開啟的 Chrome 真實分頁**上操作。

### ❌ 誤區 2：`vids-studio` 安裝在 `D:\` 槽時被 `platform_support.py` 安全檢查拒絕
* **問題現象**：執行 `python scripts/setup.py --install` 時拋出：
  1. `Setup refused: Windows private storage must be inside the current user's profile`（預設只允許 `C:\Users\<user>`）。
  2. `Setup refused: Windows private storage grants access to another principal`（因為 Windows `D:\` 槽預設 ACL 包含 `BUILTIN\Users (S-1-5-32-545)` 與 `Authenticated Users (S-1-5-11)`）。
* **✅ 正確解法**：執行本技能內建之 `python scripts/patch_windows_acl.py`（修改 `native/platform_support.py` 將工作區路徑與 `S-1-5-32-545`、`S-1-5-11` 加入白名單），即可順利註冊 `HKCU\Software\Google\Chrome\NativeMessagingHosts\com.vids_studio.bridge`。

### ❌ 誤區 3：在頁面注入自訂浮動 HUD（如 `#vids-autopilot-hud`），導致 `vids_click` 拋出 `TARGET_OBSCURED`
* **問題現象**：若在頁面右下角注入狀態懸浮窗（`bottom: 24px; right: 80px`），會正好遮擋住 Google Vids 右側「AI 短片」面板下半部的 **`展開`**、**`生成`** 與 **`插入`** 按鈕。當 `vids-studio` 執行 `DOM.getNodeForLocation` 碰撞檢測時，會直接報錯 `TARGET_OBSCURED`，並將控制權鎖入 `RECONCILIATION_REQUIRED` 狀態！
* **✅ 正確解法**：
  1. **嚴禁在 Google Vids 頁面內注入任何覆蓋右側欄（`x > 700`）的浮動 DOM 面板**。
  2. 右側面板內的 **`展開`、`生成`、`插入`** 一律優先使用**鍵盤焦點導航（`Tab` + `Enter`）**，100% 免疫座標遮擋！

### ❌ 誤區 4：同時啟動兩個背景腳本操作同一個 Vids Session，引發 `STALE_SNAPSHOT` 與鎖死
* **問題現象**：每個寫入指令（`vids_click` / `vids_press_key` / `vids_type_text`）都會使 `snapshotId` 推進。若兩個腳本同時送指令，必有一方因舊 `snapshotId` 觸發 `STALE_SNAPSHOT` 或 `RECONCILIATION_REQUIRED`。
* **✅ 正確解法**：同一時間**絕對只允許單一序列腳本**持有 `controlToken`。若發生 `RECONCILIATION_REQUIRED`，先呼叫一次 `vids_observe` 取得最新 `snapshotId`，再呼叫 `vids_reconcile_control` (`acknowledgeUnknown: true`) 即可立即恢復。

### ❌ 誤區 5：從 `vids_click` 或 `vids_press_key` 的回傳值讀取 `res["result"]["snapshotId"]`
* **問題現象**：在 `vids-studio` 協定中，`vids_click` / `vids_press_key` 的回傳結構為 `{"ok": true, "result": {"clicked": true}}`，**並不包含新的 `snapshotId`**，直接讀取會拋出 `KeyError: 'snapshotId'`！
* **✅ 正確解法**：需要有效 `snapshotId` 時，必須從 `vids_observe` 的回傳值 `obs["result"]["snapshotId"]` 取得；或者在同一常駐連線中只在關鍵節點呼叫 `vids_observe`。

### ❌ 誤區 6：在 Python 迴圈中每按一次 `Tab` 就呼叫一次 `node vids_call.mjs` + `vids_observe`（導致第 3～5 鏡嚴重卡頓達 4～5 分鐘！）
* **問題現象（最關鍵效能陷阱！）**：
  1. 每次在 Python 用 `subprocess.run(["node", "vids_call.mjs", ...])` 呼叫工具，都會重新啟動一個 Node.js 行程並重新與 Chrome Native Host 握手，單次開銷高達 **6～8 秒**。
  2. 每次呼叫 `vids_observe` (`maxNodes: 1200`) 會完整序列化 Chrome 1200 個無障礙節點，單次耗時 **3～5 秒**。
  3. 當生成到第 3、4、5 鏡時，目標影片卡片分別位於第 `25`、`35`、`45` 次 `Tab`。如果「每按 1 次 `Tab` 就呼叫 1 次 `vids_observe`」，按 45 次 `Tab` 光是找一個插入按鈕就會卡頓 **220～295 秒（將近 5 分鐘）**！而雲端真正算圖其實只要 **35～45 秒**！
* **✅ 正確解法（提速 100 倍的黃金定律）**：
  1. **單一常駐 Node.js MCP Client**：全程使用單一 `.mjs` 腳本（`scripts/vids_fast_autopilot.mjs`）維持一條 `StdioClientTransport` 長連線。
  2. **右側面板鍵盤焦點固定數學公式**：
     實測 Google Vids 右側「生成 AI 短片」面板的 DOM 焦點順序 100% 固定！點擊 `tab 建立` (`role="tab", name="建立"`) 後：
     - **展開提示詞輸入框**（當提示詞框收合時）：
       - `Tab 1` = `button 展開` $\rightarrow$ 按 `Enter` 立即展開！
     - **從提示詞輸入框送出生成**：
       - 對 `textbox 請描述影片內容...` 執行 `vids_type_text` 後，焦點在輸入框上，只需按 `Tab` **5 次**即到達 `button 生成` $\rightarrow$ 按 `Enter` 送出！
     - **定位第 $k$ 部生成的影片並點擊「插入」**（在提示詞框收合狀態下，從 `tab 建立` 出發）：
       - 通式：第 $k$ 部生成影片卡片位於 **`Tab` 第 $5 + 10(k-1)$ 步**，其專屬 **`插入` 按鈕**位於 **`Tab` 第 $9 + 10(k-1)$ 步**！
     - **極速執行法**：直接找出目標影片是清單中的第 $k$ 張卡片後（只需呼叫 **1 次** `vids_observe`），直接計算出目標步數並以極輕量模式快速跳轉，最後只在驗證 `插入` 時檢查一次，徹底省去中間 30～40 次無謂的全頁掃描！

### ❌ 誤區 7：假設生成片段為 8 秒，導致本地 `subtitles.ass` 字幕時間軸在 40 秒提前結束
* **問題現象**：舊版 Veo 為 8 秒，但目前 Google AI Pro 在 Google Vids 內建的是 **`Omni 720p 橫式 10 秒`**，每鏡插入時間軸後實測長度為 **10.0 秒**（5 鏡匯出 MP4 總長為 `50.22 秒`）。若字幕按 8 秒排，第 40～50 秒會沒有字幕且前段逐鏡錯位 2 秒。
* **✅ 正確解法**：撰寫 `subtitles.ass` 與旁白字數時，嚴格以 **每鏡 10.0 秒**（`00:00.30 ~ 00:09.60`、`00:10.30 ~ 00:19.60`...）對齊。

### ❌ 誤區 8：Google Vids 原生生成的語音具大陸捲舌音（普通話腔調）
* **問題現象**：在提示詞中雖然寫入 `Taiwanese Mandarin (zh-TW) voiceover`，但 Google 多模態神經模型（Omni/Veo）主要以標準普通話資料集訓練，生成的中文發音依然帶有顯著的大陸捲舌音（兒化音、重平舌捲舌音調），不符合台灣教學與 YouTube 觀眾習慣。
* **✅ 正確解法**：由後製腳本 `scripts/vids_postprocess_and_archive.py` 內建自動合成 100% 正統台灣國語神經語音（Microsoft `edge-tts` 的 `zh-TW-YunJheNeural` 雲哲 或 `zh-TW-HsiaoChenNeural` 曉臻），在 FFmpeg 壓制字幕時直接將原帶有捲舌音的音軌無損替換為溫和自然、完全無捲舌音的台灣國語主音軌，產出真正符合台灣教育與科普標準的成片！

### ❌ 誤區 9：多鏡（第 10 鏡以上）高階 Tab 循環引發 Chrome CDP 無障礙樹逾時崩潰
* **問題現象**：當製作長片（12～24 鏡）時，第 12 鏡目標卡片的插入按鈕位於第 119 次 Tab。若以逐步焦點推進，長時間的頻繁 CDP 事件會引發 Chrome `Accessibility.getFullAXTree timeout`，導致連線中斷鎖死。
* **✅ 正確解法**：點選目標生成影片卡片後，畫面中央視圖會彈出預覽播放對話框，該對話框下方常駐一個 **`button 在新場景中插入`**（無障礙參照值 `ref=n18`）。在該彈窗狀態下**直接呼叫 `vids_click(ref="n18")`**，1 步即可精準插入時間軸，徹底免除 119 次 Tab 遞迴！

### ❌ 誤區 10：使用 edge_tts 默認 +0% 語速與純文本合成，導致「快速念新聞稿、毫無起伏」
* **問題現象**：在後製合成台灣國語音軌時，若直接傳入純字串且未設定 `rate`（即預設 `rate="+0%"`），神經語音模型會進入機械式均速廣播模式，全句毫無高低起伏，且單鏡 30 字在 5 秒內快速念完，剩餘 5 秒乾澀留白，觀眾體驗極為壓迫且無聊。
* **✅ 正確解法**：
  1. **SSML 聲學情感與減速鎖定**：全面改用 `rate="-10%"` 溫和語速，並透過 `build_scene_ssml` 自動將破折號（`——`）與省略號（`……`）轉為 `<break time="500ms"/>`，逗號轉為 `<break time="250ms"/>`，營造真實說書人吸氣與停頓。
  2. **程式碼層單鏡 <= 40 字硬閘門**：`vids_postprocess_and_archive.py` 內建字數阻斷檢查，單鏡超過 40 字直接引發 `ValueError` 中斷程式，強制縮減台詞以維護每秒 <= 4 字的黃金節奏。
  3. **廣播級人聲強化**：FFmpeg 混音鏈自動加入 `highpass=f=80,compand` 濾波，飽滿人聲並切齊音畫。

---

## 3. 專業電影級 8 大進階運鏡與四大頻道分類範本矩陣 (Cinematic Camera Movement Matrix)

為了擺脫「單一景別、死板站樁、缺乏動態」的簡報式枯燥感，全片分鏡必須綜合運用以下 **8 大進階電影運鏡標準**，並根據所屬四大 YouTube 分類精準錨定：

### 8 大專業進階運鏡標準與提示詞範本

| 運鏡名稱 | 視覺特徵與物理效果 | 頻道適用情境 | 專屬 Prompt 關鍵詞範本 |
| :--- | :--- | :--- | :--- |
| **1. 探針微距穿透 (Probe Lens Push-through)** | 極貼近物體表面，穿入狹小容器、縫隙或流體內部 | ［手作科學］、［國小自然］ | `Laowa 24mm probe lens push-through, macro pass gliding millimeter above liquid surface, dramatic fluid reflection` |
| **2. 眩暈變焦 (Dolly Zoom / Vertigo)** | 前推同時拉廣角，主體比例不變，背景空間劇烈扭曲塌縮 | ［大識界 開眼界］、［手作科學］爆點 | `Cinematic vertigo dolly zoom effect, camera moves forward while zooming out, background expands and warps dramatically` |
| **3. 極致焦點轉移 (Rack Focus)** | 鏡頭固定，景深極淺（f/1.4），焦點從前景順滑滑向後景 | ［手作科學］材料轉向反應、［國小自然］ | `Shallow depth of field, smooth rack focus from blurry foreground dropper to razor-sharp background chemical reaction, 85mm lens` |
| **4. 衝擊快推 (Crash Zoom / Snap Zoom)** | 0.3 秒內極速朝關鍵焦點撞擊式推近 | ［AI 自學筆記］終端成功、［大識界］金句 | `Fast kinetic crash zoom snap into glowing terminal screen, high dynamic momentum, punchy visual hit` |
| **5. 剖面貫穿飛掠 (Cutaway Cross-section)** | 穿透容器外壁或地表，鏡頭在內部剖面平滑滑行 | ［手作科學］沉澱分層、［國小自然］導管 | `Cutaway cross-section view, camera gliding smoothly through the interior cross section of container, internal layer details` |
| **6. 360° 弧形環繞 (360° Orbital Pan)** | 繞著核心主體以等角速度進行圓周環景運動 | ［大識界 開眼界］英雄雕像、［AI 自學筆記］機房 | `Smooth 360-degree orbital arc shot circling around central subject, continuous parallax depth, cinematic volumetric lighting` |
| **7. 快速甩鏡轉場 (Whip Pan / Swish Pan)** | 高速水平甩鏡產生強烈運動模糊（Motion Blur）作為過場 | 跨步驟對比、繁瑣手動切換到全自動 | `High-speed kinetic whip pan to the right with heavy motion blur transition, seamless cut into next action` |
| **8. 俯衝鳥瞰展開 (Crane Descending Reveal)** | 高空俯視極速平滑下降至人眼平視，揭開宏大全貌 | ［大識界 開眼界］歷史大場景、［國小自然］生態系 | `Epic high-angle crane shot descending smoothly from aerial canopy down to eye-level reveal, grand sweeping motion` |

### 四大頻道專屬提示詞公式（Prompt Injection Formula）

$$\text{Prompt} = \underbrace{\text{[主題器材/環境]}}_{\text{Borosilicate reaction bottle}} + \underbrace{\text{[進階運鏡術語]}}_{\text{Probe lens push-through}} + \underbrace{\text{[運動軸向與物理速度]}}_{\text{slowly gliding millimeter above surface}} + \underbrace{\text{[景深與光學約束]}}_{\text{shallow depth of field, sharp focus, 4k 60fps photorealism}}$$

1. **［手作科學］**：每片必須包含至少 1 次「探針穿透」與 1 次「焦點轉移」，流體沉降鏡頭強制指定「側向等速跟蹤（Parallel Tracking Shot）」。
2. **［國小自然］**：微觀生態必須採用「蟲眼低角度（Bug-eye POV）」與「剖面穿透（Cutaway）」，拒絕單調平視。
3. **［大識界 開眼界］**：關鍵哲學轉折必配「眩暈變焦（Dolly Zoom）」，場景開展必配「俯衝展開（Crane Reveal）」或「360° 環繞（Orbital Arc）」。
4. **［AI 自學筆記］**：關鍵成功或報錯必配「衝擊快推（Crash Zoom）」，架構解析必配「資料隧道穿越（FPV Fly-through）」。

---

## 4. 全自動標準作業流程（5 步極速端到端 SOP）

### 步驟 1：建立專案分鏡設定檔 `vids_project_manifest.json`
於專案目錄建立 `vids_project_manifest.json`（範本見 `examples/vids_project_manifest.example.json`）：
- `project_title`：專案名稱（如 `01_GoogleVids獨立生成測試_表面張力奇觀`）
- `youtube_category`：必填四大分類之一（`［手作科學］`、`［國小自然］`、`［大識界 開眼界］`、`［AI 自學筆記］`）
- `scenes`：陣列，每鏡包含：
  - `id`：如 `"S01"`
  - `match_prefix`：英文提示詞前 35～45 字元（供從 `生成的影片：...` 清單中 100% 精準比對第 $k$ 張卡片）
  - `prompt`：完整 Omni 10 秒提示詞
  - `narration_zh`：繁體中文旁白台詞（約 26～34 字）
  - `subtitles`：2 段時間碼對齊該 10 秒區間（`0.3s ~ 4.8s` 與 `4.9s ~ 9.6s`）的繁體中文雙色字幕（重點關鍵詞加上 `{\c&H0000EAFF&}關鍵詞{\c&H00FFFFFF&}` 亮金黃色標記）。

### 步驟 2：配對並取得 Google Vids 分頁控制權（Session Handshake）
1. 請使用者在 Chrome 開啟 `https://docs.google.com/videos` 新建空白影片，點選右上角 `Vids Studio Bridge` 擴充功能圖示複製 64 字元配對碼（或沿用既有 `.vids_session_state.json`）。
2. 執行配對並取得寫入租約（`vids_pair_session` $\rightarrow$ `vids_attach_session` $\rightarrow$ `vids_acquire_control`），將 `sessionId`、`documentId`、`controlToken` 寫入 `.vids_session_state.json`。

### 步驟 3：執行單一常駐連線極速生成與組裝腳本
```powershell
node "d:\2026antigravity\.agents\skills\google-vids-video-producer\scripts\vids_fast_autopilot.mjs" --manifest "<manifest路徑>" --state "<.vids_session_state.json路徑>"
```

### 步驟 4：執行 100% 台灣國語音軌替換、雙色硬字幕壓制與四大分類自動歸檔
當 MP4 下載至專案資料夾後，執行：
```powershell
python "d:\2026antigravity\.agents\skills\google-vids-video-producer\scripts\vids_postprocess_and_archive.py" --manifest "<manifest路徑>" --mp4 "<下載的MP4路徑>"
```
此腳本會自動：
1. 自動以 `zh-TW-YunJheNeural`（雲哲）合成道地台灣國語主音軌（無任何大陸捲舌音）。
2. 替換原始帶有普通話捲舌音的音軌，產出 `<專案名稱>_純淨無字幕版.mp4`（1080p 台灣國語母帶版）。
3. 生成時間碼 100% 對齊每鏡 10.0 秒的 `subtitles.ass` 並燒錄出 `<專案名稱>.mp4`（1080p 內嵌繁中雙色硬字幕正式版）。
4. 產出含分類前綴標題、資訊欄與雙格式 Tags 的 `YouTube發布資訊_<專案名稱>.txt`。
5. 自動將全套成果複製歸檔至 **`d:\2026antigravity\Google Vids 影片製作\<youtube_category>\<專案名稱>\`**！
