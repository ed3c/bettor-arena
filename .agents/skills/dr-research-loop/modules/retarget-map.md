# retarget-map — antigravity dr-research-loop → skill-bettor DR proposal 迴圈(誠實帳本)

> 方向:antigravity `.agents/skills/dr-research-loop/`(+`automate.js/state.js/data.js/ui.js`
> 平坦四模組)→ 本 repo `.claude/skills/dr-research-loop/`+`loop_wiki/_template_dr/`。
> 上游是「影片→知識體系」媒體研究管線(driver=puppeteer 驅動 Gemini 網頁);本地是
> 「研究題目→skill 變現情報 proposal」批次(driver=agy/claude -p/subagent,走八大基座驗證骨架)。
> 帳本原則同 loop-harness-standard/modules/retarget-map.md:只搬可轉移方法論,
> 上游自己的歷史證成紀錄與瀏覽器自動化實作不搬。

## 1. 搬了什麼(方法論,已 retarget 落地)

| 上游機制 | 上游落點 | 本地落點 | retarget 內容 |
|---|---|---|---|
| 研究漏斗拓撲(主研→覆蓋稽核→gap fan-out) | 主迴圈決策樹 Step A→D(loop-panorama-ssot §2) | run.sh 祈使任務+PROMPT.md gap fan-out 紀律+engine 迭代 | 漏斗折進 iterate-until-pass:缺口維度=下一輪 gap 題 |
| 14 維完整性量規 COMPLETENESS_RUBRIC | `data.js:97`(P1-P9+V1-V5,生產環境/技術觀點) | `_template_dr/scripts/rubric.json`(M1-M14,變現維度) | 維度對象換為市場/ROI/授權雙軌/巨頭/創作者/規範/評估/迭代/通路/商模/等價物/競品/風險 |
| 「技術實現等價物必做」prompt 慣例 | 逐題 gap query(開源可商用庫+repo+授權;無則 [推論]) | rubric M12+每維度「等價物」欄+check_licenses | 加零 copyleft allowlist 機械化(上游只靠 prompt 約束) |
| [推論] 誠實降級 | Path B 覆蓋矩陣「來源[推論]」 | schema 狀態=推論+check_anchors R2 | 由散文慣例升級為機械閘 |
| DR 完成偵測(≥3000 字+sources 訊號+0 計劃殘留) | `ui.js` DOM 偵測 | check_schema MIN_BODY_CHARS=3000+check_anchors R5(≥3 URL) | DOM 訊號換成檔案級機械判 |
| 佇列誠實收尾(completed ⇔ 真有報告) | `progress.json`+`history.json` | `proposals/QUEUE.md` status 欄 | JSON 帳換 markdown 帳(人工挑題 MVP,人可直接編) |
| 階段重試量級 MAX_*_ATTEMPTS=3 | `automate.js` 重試 wrapper | PROMPT.md stop-loss pin(max-iters=4/no-progress=2,engine 執行) | wrapper 換 engine 兩型 stop-loss |
| MAX_GAP_TOPICS=6 截斷 | `automate.js` Step D | CLAUDE.md 紀律 7+PLAN.md gap fan-out 帳 | 同值保留;截斷記帳從 log 換 PLAN.md |

## 2. 換掉什麼(架構前提不同,非優化)

- **driver**:puppeteer 驅動 Gemini/AI Studio 網頁 UI → `agy --model gemini-3.1-pro`(主)/
  `claude -p --allowedTools WebSearch,WebFetch`(備援)/對話內 subagent(輕量)。
  依據=ARCHITECTURE §5 tier-dispatch(DR=agy Pro 3.1)+§5 硬約束④雙指揮路徑。
- **研究對象**:YouTube 影片(@aiDotEngineer 單頻道)→ skill 變現情報題目(QUEUE.md 場景佇列:
  claude-code/codex/grok/agy/pinescript-quant/cross-market)。
- **產物**:四種 gitignored 報告(卡片盒/DR/Path B/gap)→ 單一 schema 化 proposal
  (`proposals/YYYY-MM-DD-<topic>.md`,入 git,走知識單向流)。
- **卡片盒 Step A**(影片→結構化文章)→ PROMPT.md Op 節 scenario 卡(題目+場景+domain 指針);
  影片轉寫需求不存在,結構化由 schema 承。
- **Path B 四階段精煉**(另開對話量規稽核)→ 覆蓋矩陣內建於 proposal schema(每輪 verify 機械
  勾稽覆蓋率),semantic 稽核外移給 judge-loop-chooser D3(findings-only)+人 admit。
- **人閘**:manualLoginGate(登入態)+watchdog pkill(人決定何時停)→ engine exit 10
  awaiting-human-admit+D3+7 天 TTL(本 repo 人閘清單 §8)。

## 3. 拿掉什麼(為何不是簡化)

- **瀏覽器自動化整層**(Chrome :9333/`.chrome-profile`/TrustedHTML bypass/DR 計劃偵測 DOM 輪詢/
  `automation.log` 簽名/watchdog pkill):上游為繞 Gemini Deep Research 無 API 而生;本地 driver
  是 CLI/subagent,無此前提。拿掉=不引入不存在的架構前提。
- **`automate.js/state.js/data.js/ui.js` 平坦四模組**:職責由 engine.sh(迭代/stop-loss)+
  run.sh(dispatch)+scripts/checkers(驗證)+QUEUE.md(狀態)分承——沿用本 repo 既有八大基座,
  不平行再造一套 Node 執行體。
- **卡片盒 v6.6 系統指令全文/Path B 精煉模板全文**:上游 prompt SSOT 綁影片知識體系場景,
  逐字搬=husk;只搬其中可轉移的兩條慣例(等價物必做+[推論]),已入 rubric 與 schema。

## 4. 判「retarget 成立」的鐵錨
- 本地活基座真跑:`loop_wiki/_template_dr/selftest.sh` 2026-07-11 綠(4 checkers good/hollow
  正控+rubric↔PROMPT 勾稽+scripts↔tests 計數勾稽)。
- verify.sh engine 契約實測:good fixture exit 0;hollow exit 2+`PROGRESS:` 行。
- 上游指針(只讀參照,非本地依賴):`/Users/neon/antigravity/.agents/skills/dr-research-loop/`
  `modules/loop-panorama-ssot.md`(決策樹§2/prompt§3)。已知上游漂移:judge-loop-chooser
  retarget-map 指 `automate.js:199`,實際在 `data.js:97`。
