# Module: 對話研究管線 S0-S9 逐階段 how-to（Mode A 主線）

> 屬 [`gemini-conversation-research`](../SKILL.md) §S0..§S9。各階段的完整步驟、checkpoint、硬數據 schema、子代理 dispatch 模板。
> Mode B 入口（S-1 + S0-ALT）→ [mode-b-contextqa.md](mode-b-contextqa.md)；追問構造 → [first-principles-probe.md](first-principles-probe.md)；閉環全景/gate → [loop-panorama-ssot.md](loop-panorama-ssot.md)；retarget 帳本 → [retarget-map.md](retarget-map.md)。
> **活基座**：DR 引擎 = 外部 `automate.js`（`runDrOnce`/`runGeminiDeepResearch*`/`extractReportHtmlInBrowser`/`htmlToMarkdown`）；DR 抽取 = 外部 `gemini-deep-research-extract`（skill-bettor 未安裝時標 `external_engine_required`）；反幻覺 = [external-verify](../../external-verify/SKILL.md)。

---

## AUP 內容隔離（跨 S0/S1/S3/S7/S9 共用，P0）

**根因**: 21K+ 外部對話原文一次進入主 agent context = 資料外洩面（northstar 稱 Data Exfiltration）。
**antigravity 設計**: **架構性 file-based 天生安全**——瀏覽器抽取直接寫檔、任何 LLM 分析走子代理。**不需要 northstar 的 `gemini-aup-guard.sh` hook + marker**（本 repo 無此 hook；為何「自主只因無 guard、架構決定 autonomy 非權限」→ [retarget-map §4](retarget-map.md)）。

```
主會話 context（安全）：              子代理 context（隔離）：
  S0：瀏覽器抽取 → 寫 .md              S1-Agent：Read 對話檔 → 回 conversation_analysis YAML (~3K)
  S2：DR prompt (≤1200字) → /tmp 檔     S7-Agent：Read DR + S1 → 回 gap_list (~1K)
  S3：bounded adapter/CDP engine → 寫 .md  S9-Agent：Read all → 回結構化落地 YAML (~2K)
  S4/S6：outcome/harvest (小)          ← 只回 YAML ≤5K
```

**三條隔離規則（P0）**:
1. **瀏覽器抽取 → 檔案**：S0/S3 用 `extractReportHtmlInBrowser`+`htmlToMarkdown` 寫 `.md`，原文不經主 context。
2. **子代理分治**：S1/S7/S9 委派 `Agent` tool，讀完整檔、做分析、只回結構化 YAML（≤5K）。
3. **Browser carrier 禁正文回傳**：Gemini 分頁禁 `domSnapshot`、conversation `textContent/innerText`、screenshot/OCR、回正文的 `evaluate`；完整抽取與 button projection 都必須在 browser runtime 內寫檔，只回 ≤4096 chars receipt。唯一 recipe 見 [browser-content-isolation.md](browser-content-isolation.md)。
4. **主會話禁讀原文**：禁 `Read` 對話檔/DR 報告全文；只允許 ≤50 行片段做 spot-check。

**子代理 prompt 模板**（S1/S7/S9 共用骨架）:
```
你是 gemini-conversation-research 管線的 S{N} 分析子代理。
任務：讀取 {file_path}，按 {stage-specific framework} 產出結構化 YAML。
輸出：只回 YAML block（conversation_analysis / gap_list / 落地 edges）。
      不回原文引用、不回長段摘要。嚴格 ≤5000 chars。
分析完成後將 YAML 寫入 {output_path} 作 checkpoint。
```

---

## S0: EXTRACT — Gemini/AI Studio 對話抽取

**輸入**: Gemini URL（`https://gemini.google.com/app/<id>` 或 `https://aistudio.google.com/prompts/<id>`）。

**平台判定（URL prefix）**:
- `gemini.google.com/app/` → **Gemini Web**（連續滾動載入）。
- `aistudio.google.com/prompts/` → **AI Studio**（虛擬滾動：turn 離開 viewport 即卸載，`scrollIntoView` 不觸發載入，只有 `.prompt-scrollbar-dot` click 有效 → 須逐段 dot 導航、等 ~3s、抽當前可見 turns、再移下一段）。

**執行**:

- **primary / Codex Chrome extension**：claim 使用者已開啟且 URL 精確匹配 conv-id 的 tab，從目前 checkout 的絕對路徑 import repo-root `scripts/extract-gemini-conversation-browser-runtime.mjs`。先用 `inspectGeminiConversationMetadataFromBrowserTab`，再用 `extractGeminiConversationFromBrowserTab` 寫檔；外部只輸出 metadata receipt。禁止 snapshot fallback。完整 recipe 見 [browser-content-isolation.md](browser-content-isolation.md)。
- **legacy CDP fallback**：外部 antigravity repo 根目錄 `/Users/neon/antigravity/scripts/extract-gemini-conversation.mjs <convId> [--port 9333] [--out <path>]`（⚠ 非本 skill 目錄下同名檔；skill-bettor packet 必標 `external_engine_required`）。

兩條路徑都沿用 turn-structured HTML→Markdown、DR report panel、citation/bibliography 與 metadata-only receipt。手動細節：
1. 取得已登入瀏覽器頁面：
   - **primary**：使用者既有、已登入、由 Chrome extension 暴露的 tab；不得另開測試 profile。
   - **CDP fallback**（`auth_required` 且使用者拒新登入）：`puppeteer-core.connect({browserURL:'http://127.0.0.1:9333'})`（用 antigravity 已裝的 `node_modules/puppeteer-core`）。目標對話已是該瀏覽器一個開啟分頁 → `(await b.pages()).find(p=>p.url().includes(id))` 零導航直讀。**必須 `page.bringToFront()`**：多個 gemini.google.com 分頁同開時，非前景分頁的 timer 被 Chrome 節流，scroll-wait 迴圈會撞 puppeteer 180s `protocolTimeout`（cc-20260712 實測連續兩次重現，加回 bringToFront 即解）。
2. 等 SPA 渲染（~10s，不靠 networkidle）；Gemini Web 連續 `scrollBy` 到底載入全對話；AI Studio 逐 `.prompt-scrollbar-dot` 導航（cc-20260712 只驗證過 Gemini Web 路徑，AI Studio 虛擬滾動分支未動）。
3. **抽取 → 保真 md 寫檔**：一般 turn（`user-query`/`model-response`）走純 turndown；若偵測到 `deep-research-immersive-panel`（DR 報告面板，可能是 turn 序列裡任一輪觸發、渲染在 sibling 位置而非巢狀在該輪內）則額外走 `extractReportHtmlInBrowser`+`htmlToMarkdown`（citation marker `[cite:N]` + bibliography 保真，逐字元複製自 `data.js:17,24`）附加在 QA 之後。**turn 選擇器陷阱**：`model-response` 常有巢狀子元素 `.response-container`，若把兩者塞進同一個 `querySelectorAll` OR-list 會導致每輪被抓兩次（cc-20260712 實測 87 turns 應為 58，逐位元組重複）——每個角色只用命中的那一個 selector。**turndown ESM 陷阱**：`import` 走 `.../lib/turndown.cjs.js` build（`.es.js` 內部 `require()` 會炸 ES module scope）。
4. 加 1 行 metadata header（URL + date）→ 寫 `gemini_research/<source>/<slug>-conversation.md`（產物目錄 gitignore，SSOT 在索引，同 dr-research-loop 慣例）。

**對話存檔 SSOT 規則（P0）**:
- 對話檔必須是抽取內容的**逐字元完整副本**。
- **禁任何形式的簡化、重組、摘要、結構化改寫**——結構化分析是 **S1 產物**，不是 S0 存檔。
- 只允許檔頂 1 行 metadata comment（URL + date），正文零修改。
- Checkpoint：存檔 chars ≈ 原始內容 chars（±5%，僅 header 差異）。

**AI Studio DOM 結構速查**:
| 元素 | Selector | 備註 |
|------|----------|------|
| 全部 turns | `.chat-turn-container` | 虛擬渲染 |
| 導航 dots | `.prompt-scrollbar-dot` | ~6 dots ≈ ~19 turns |
| Turn 內容 | `.turn-content` | 可能空（`<!---->`），需 dot click |

> ⚠ **selector 漂移**：Gemini/AI Studio UI 持續改，current working selectors 的權威分散在 `ui.js`（`model-response`/`.markdown-main-panel` 系列，如 `countTurns`/DR 面板抓取）與 `data.js`（`extractReportHtmlInBrowser` 的候選 selector）；`automate.js` 本身只 290 行純調度層，不含 selector（cc-20260712 核實，舊稱「權威是 automate.js」不精確）。`user-query` 是本 S0 腳本專用、非 automate.js/ui.js/data.js 既有 selector。（AUP 擋 live-probe，用 source-contrast）。抽取反覆失敗 → 走 [dr-research-loop](../../dr-research-loop/SKILL.md) live 唯讀診斷。

**Checkpoint**: 抽取文字 > 1000 chars。
**硬數據**: `s0_extract: {gemini_url, conversation_id, platform: gemini_web|ai_studio, session_source: research_profile|cdp_9333, content_chars, content_lines, local_path}`

---

## S1: ANALYZE — 對話脈絡結構化分析（子代理隔離）

**輸入**: S0 存檔對話**檔路徑**（不是對話全文）。
**⚠ Context Isolation（P0）**: 主會話禁讀對話全文 → 委派子代理。

**子代理 6 步分析框架**:
1. **主題維度識別**：掃描對話，識別 N 個討論維度（每個 = 獨立主題區塊）。
2. **認知遞進模式**：使用者提問序列的認知層級（L1 探索 → L2 質疑 → L3 建構）。
3. **Q&A 邏輯設計解構**：AI 回應結構範式（維度拆解、映射錨定、鈎子問題）。
4. **結構性缺口識別**：每個維度標記資訊密度（`sufficient` / `partial` / `shallow`）。
5. **高價值 DR 方向排序**：按 impact × gap_depth。
6. **Q&A 效能模式抽取**：每個 Q-A 對分類 effective（→ sufficient）/ ineffective（→ shallow），記問題類型與回應結構相關性。

**分析框架模板**（子代理輸出）:
```yaml
conversation_analysis:
  title / total_turns
  dimensions:
    - { name, density: "sufficient|partial|shallow", gap_type: "knowledge|research|cross_domain",
        key_conclusions: [], gaps: [] }
  user_question_pattern: { progression, levels: ["L1 探索","L2 質疑","L3 建構"] }
  ai_response_structure: { pattern, design_intents: [] }
  qa_effectiveness:
    effective_patterns:   [ { question_type, density_yield: "sufficient", example, response_structure } ]
    ineffective_patterns: [ { question_type, density_yield: "shallow", example, response_structure } ]
    density_correlation:  { highest_density_question_type, lowest_density_question_type }
    optimization_insights: ["<下次 S2 prompt 構造的具體改進>"]
  horizontal_challenge:
    echo_back_detected: <bool>            # 使用者是否重複 Gemini 末尾引導問題
    missing_lateral_dimensions: []
    challenge_candidates: [ { topic, reason, new_conversation_required: true } ]   # P0：橫向挑戰須新開對話
  vision_to_roadmap:
    full_vision_concepts: []
    best_landing_entities: []             # 可含尚未存在的模組
    landable_subset: []
    deferred_vision: []
  dr_candidates: [ { topic, priority: "S|A|B", reason, gap_type: "shallow|partial" } ]
```

**橫向挑戰規則**: echo-back（重複 Gemini 末尾引導問題）本身不是錯，但須識別**缺失的橫向維度**（成本合理性 / 替代方案比較 / 落地可行性）——這些**必須在新開 Gemini 對話討論**（同對話上下文窗口已被原方向佔滿）。
**願景→路線圖**: 概念消費端是 long-term roadmap，不僅現有系統直接落地；`landable_subset` 聚焦當前可執行，`deferred_vision` 記需要未來基礎設施的部分。

**Checkpoint**: `dimensions >= 3` AND `dr_candidates >= 1`。
**硬數據**: `s1_analyze: {dimensions_identified, density_sufficient/partial/shallow, dr_candidates, user_question_levels, qa_effective/ineffective_patterns, knowledge_gaps, research_gaps}`

---

## S1.5: PROBE — 同一對話追問（knowledge_gap 填補）

**前置**: S1 識別 `gap_type=knowledge` 的 partial 維度。**`knowledge_gap == 0` → 跳過 S1.5，直接 S2**。
**核心**: 追問比 DR 便宜兩個數量級（~45s vs ~15min）。部分 partial 維度只需 Gemini 展開已有知識即升級 sufficient，不需外部研究。
> **追問怎麼構造才鑽到底（抗放水）**：引用-鑽入 + 反向自陳 + first-principles 約分 → [first-principles-probe.md](first-principles-probe.md)（取代泛泛「要數據/案例/細節」）。

**步驟**:
1. 構造追問 prompt——**批量合併**所有 knowledge_gap 維度（一段內逐一列，避免多輪零散撞上限）。
2. 回到 S0 記錄的 `conversation_url`，同一對話追問（快捷模式 ~10s），只抽最後一條回應。
3. Claude 整合判斷每個維度：**升級 sufficient**（含具體數據/框架/可操作結論 → 跳 DR 直接落地）/ **確認 research_gap**（泛化/重述/明說「沒數據」→ gap_type 改 research 送 S2）/ **發現新維度**（新增 dimension）。
4. 更新 S1 dimension density 與 gap_type；記 probe 的 Q&A effectiveness 回饋。

**追問上限**: max 2 輪。R1 後不足的維度直接標 research_gap；R2 只對「有進展但還差一點」的維度。
**Checkpoint**: `probe_response_chars > 200`（per probed dimension）。
**硬數據**: `s1_5_probe: {knowledge_gap_count, probe_rounds(1-2), response_chars, upgraded_to_sufficient, confirmed_research_gap, new_dimensions_discovered, probe_success_rate}`

---

## S2: TRIAGE — DR 路由決策

**輸入**: S1 conversation_analysis（經 S1.5 更新後的 density 與 gap_type）。

**步驟**:
1. 對每個 `gap_type=research` 的 dr_candidate 評估：值得 15-20 分鐘 DR？
2. 合併相關 candidates 為**最少的 DR 查詢**（目標 1-2 個合併 prompt）。
3. 構造 DR prompt（背景 + 具體方向 + 輸出要求，建議英文，產出更多）。
4. 計算 `dr_savings_rate = areas_skipped / areas_total`；不得用 `sufficient + partial` 代替，因為 partial 仍可能被送進 DR，會高估實際節省率。

**DR prompt 構造規範**:
```
Research Topic: <主題>
背景：<從對話脈絡萃取的 1-2 句上下文>
請深入研究以下 N 個方向：
1. <方向 1> — <具體子問題>
2. <方向 2> — <具體子問題>
輸出要求：每個方向提供具體數據、論文引用、技術規格，而非概念性描述。
```

**🔴 反幻覺硬化（過 [external-verify](../../external-verify/SKILL.md) 紀律）**: 當目標是 repo/framework 且「是否純本地 / 依賴雲端 / 預設供應商」是 load-bearing 結論時，DR prompt 必須：
- **G3 源碼 = 100% SSOT**（可讀 repo 用源碼讀，DR 只補外部缺口）——**砍它 = DR 幻覺入庫**。
- **G5 事後查證**：逐條查一份 DR 的 claim 真假時，**錨定 source 自己的 bibliography + 拉 primary source**，**禁盲搜 WebSearch**（post-cutoff 會 confabulate「某名字指哪篇」→ 把真論文判杜撰）。external-verify **誠實分級**（VERIFIED / UNVERIFIED / FETCH-FAILED）——報告結論為真 ≠ 被引 URL 撐得住。

**DR prompt file-only（P0，內容隔離）**: 構造完成的 DR prompt **必須寫檔** `/tmp/dr-prompts/<slug>-<YYYYMMDD-HHMMSS>.txt`，**禁** stdout / heredoc / 主會話 chat / argv（避免 process list 暴露）。S3 透過 `--prompt-file` 引用。

**Checkpoint**: dr_prompt 字數 ≤~1200（單一聚焦段落；長/多問拆 S8）。
**硬數據**: `s2_triage: {areas_total, areas_to_dr, areas_skipped, dr_savings_rate, dr_prompt_chars, prompt_file_path, prompt_via_file: true}`

---

## S3: DEEP — Gemini Deep Research 執行（**複用狀態機；carrier 分流**）

> **命門**：狀態機 SSOT 仍是 antigravity `automate.js`/`ui.js` 的 hardened sequence；Codex Chrome extension 不能接 `:9333`，所以以 repo-root bounded adapter 移植同一組 read-back gates，而非另造較弱 monitor。詳 [browser-content-isolation](browser-content-isolation.md)。

**步驟**:
1. **投遞** → extension Chrome 優先呼叫 `launchGeminiDeepResearchFromPromptFile`；只有 extension 不可用才以 `automate.js runDrOnce` 接既有 `:9333`。兩者的 DR prompt 都只從 S2 `/tmp/dr-prompts/*.txt` 讀。
2. **完成偵測**（**非** `verifyStarted` 假陽性）→ 字數 ≥3000 ∧ 0 計劃殘留（`开始研究`/`修改方案`/`只需要几分钟`；**認簡繁**）∧ `deep-research-source-lists` 出現。extension 走 `inspectGeminiConversationMetadataFromBrowserTab`；CDP 才用 puppeteer probe。兩者都只回 metadata。
3. **抽取 → 保真 md** → extension 走 `extractGeminiConversationFromBrowserTab` 直接寫檔；CDP 委派 `gemini-deep-research-extract`。兩者均保留 `[cite:N]` 與 used bibliography。

**帳號序列約束**: 一 Gemini 帳號 DR 槽只在 init ~2-3min 被佔，研究脫鉤（~210s）後釋放 → **等脫鉤才投下一個**（太早投搶槽餓死前者）。**不可與 dr-research-loop 影片管線同跑同一 :9333 帳號**（跑前 `pgrep -fl automate.js` 確認無）。長 DR（安全/市場綜述）真會 >25min，runner timeout ≥ 引擎報告 poll（1800s）+ extract buffer（≥2100s），否則砍掉健康長 DR。

**Checkpoint**: DR 報告 > 5000 chars。
**硬數據**: `s3_deep: {gemini_dr_url, dr_prompt_chars, engine: "automate.js runDrOnce", extraction_method: "html_markdown|innertext_fallback", report_chars, report_lines, bibliography_refs_count}`

---

## S4: HARVEST — 本地雙文件存檔

**核心**: DR 報告保留**完整原始內容**（含 bibliography）。雙文件 SSOT。
**步驟**:
1. 完整 DR 報告 → `gemini_research/<slug>.md`（**SSOT，含 bibliography，引用標號 + URL 全保留，不改格式**）。
2. 結構化版 → `gemini_research/<slug>.structured.txt`（頭部 metadata：DR URL / Source Conversation / date；正文 `##`；含 bibliography section）。
3. 原始對話 → 同目錄 `<slug>-conversation.md`。
4. 寫 `outcome`（見 S6）。

**SSOT 驗證**: `.md` refs 數量 ≥ `.txt` refs 數量；`.txt`=0 而 `.md`>0 → 標 `bibliography_sync: false`。
> **回應契約（P0）**: S0/S3/S4 對使用者的最終回應**必須逐字給檔案絕對路徑**——AUP 隔離下主會話不讀全文，路徑是使用者唯一能自行讀取的線索。多候選檔案用比較表列出，明確標哪份是使用者實際要的。

**Checkpoint**: 雙文件存在 + `.md` chars > 5000 + `bibliography_refs_count > 0`（warn if 0）。
**硬數據**: `s4_harvest: {dr_ssot_path, dr_ssot_chars, dr_ssot_refs_count, dr_structured_path, bibliography_sync, conversation_local_path}`

---

## S6: FEEDBACK — 反饋閉環（**輕量版；治理路由拿掉**）

> northstar 的 transcript-harvest / isolation-validator / 下游 concept-landing·dr-governance-router **拿掉**（antigravity 無基座，見 [retarget-map §2](retarget-map.md)）。保留的是 **feedback 三角紀律**。

**步驟**:
1. 寫 `outcome`（聚合 S0-S4 硬數據；記進 harvest 檔或 `AGENTS.md` Resolved）。
2. 反饋指標：`extraction_success_rate = 1/extraction_attempts`；`dr_savings_rate = areas_skipped/areas_total`；`dr_report_density = report_chars/dr_prompt_directions`。
3. Q&A 學習：從 S1 qa_effectiveness + S1.5 probe 抽取跨 session 可用 pattern（哪些 question_type density_yield 最高）。

**feedback_triangle**: `initial_prompt`（S2 prompt 設計）× `conversation_content`（S0 抽取品質）× `dr_outcome`（DR 報告品質 + coverage）。三頂點別少一個。
**硬數據（outcome）**:
```yaml
cycle_id: "gcr-<date>-<topic>"
skill: "gemini-conversation-research"
stages_completed: [0,1,2,3,4,6]        # + [7,8,9] if 全覆蓋管線
s0_extract / s1_analyze / s2_triage / s3_deep / s4_harvest: { ... }
feedback_loop:
  conversation_url / dr_url
  metrics: { extraction_success_rate, analysis_coverage, dr_savings_rate, dr_report_density }
  qa_learning: { effective_question_types: [], ineffective_question_types: [], probe_success_rate }
provenance: { source_type: "gemini_conversation", source_url, conversation_title }
ssot_verification: { dr_ssot_is_complete_copy, bibliography_sync, conversation_file_is_complete_copy }
```

---

## S7: GAP-ANALYZE — 知識點覆蓋率比對（子代理隔離）

**前置**: S6 完成（至少 1 個 DR 已採收）。
**⚠ Context Isolation（P0）**: S7 需讀 S1 YAML + DR 報告做交叉比對 → 委派子代理。

**子代理步驟**: (1) 列 S1 全部 dimensions；(2) 列 DR 已覆蓋概念；(3) 逐一比對每個 dimension × knowledge_point → `covered_by_dr` / `covered_by_conversation` / `uncovered`；(4) 對 uncovered 評對齊度（CRITICAL/HIGH/MEDIUM/LOW）；(5) 過濾 CRITICAL+HIGH → `gap_list`。

**覆蓋率判定規則**:
- `sufficient` density + 無 DR = `covered_by_conversation`（直接落地，不需 DR）。
- `partial/shallow` + 已 DR = `covered_by_dr`。
- `partial/shallow` + 未 DR + CRITICAL/HIGH = `uncovered` → 進 S8。

> ⚠ **比對前必驗 DR 載體格式**：Gemini DR `.md` 常把公式/數字/不等式渲染成 reference-style base64 PNG（文中 `![][imageN]`、定義集中檔尾）→ 純文本 coverage 比對**看不到任何數學知識點** → **假 covered / 假 100%**。比對前先解碼 image → 視覺讀取補回語義（走外部 `gemini-deep-research-extract` 的 `[data-math]` 保真路徑可從源頭避免此問題）。

**Checkpoint**: gap_list 產出（可為空 = 100% 覆蓋）。
**硬數據**: `s7_gap: {total_knowledge_points, covered_by_dr, covered_by_conversation, uncovered_critical, uncovered_high, coverage_rate, gap_list:[{name, alignment:"CRITICAL|HIGH", reason}]}`

---

## S8: MULTI-DR — 迭代生成額外 DR

**前置**: S7 gap_list 非空。
**步驟**:
1. gap_list 按主題相似度合併（最少 DR 查詢數）。
2. 對每組 gaps 構造 DR prompt（**複用 S2 模板**）。
3. 執行 DR（**複用 S3 carrier 分流與同一組 read-back gates**）。
4. 存檔 `gemini_research/<slug>.gap-NN.md`。
5. 記各新 DR 之間的 COMPLEMENTS 跨 DR 關係（記檔，非 KG）。

**迭代收斂**: S8 完成後回 S7 重算 coverage_rate；仍有 uncovered CRITICAL → 再次 S8。**收斂上限 3 輪**（防無限循環）。
**Checkpoint**: 新 DR 報告 > 5000 chars + `coverage_rate > 0.9`。
**硬數據**: `s8_multi_dr: {iteration(1-3), new_dr_count, new_dr_reports:[{gemini_url, report_chars}], coverage_after, converged}`

---

## S9: INGEST — 全知識點結構化落地（子代理隔離；**入 antigravity KG**）

> northstar S9 是「純 Node.js kg-ingest.ts → rag-local KG 邊」。**antigravity 無 rag-local**——但**有自己的 KG**（`indexing/` GraphStore + `.cache/kg/graph.json`）。**KG 等價層已補**（cc-20260703）：新增 `Conversation` 源節點型別（`conv:gemini:<id>`，三重映射登記 models.py + CONTEXT.md + 設計 §1）+ `indexing/ingest_conversation.py`——**鏡像 `concepts.ingest_concepts_for_video`**，把對話概念走**同一個 `extract_concepts` 引擎** → `Conversation ─DISCUSSES→ Concept`。概念與既有 Video/RepoDoc 概念**跨源 join**（同 canonical concept id 自動合流）。詳 [retarget-map §KG-sink](retarget-map.md)。

**前置**: S8 收斂（或 S7 gap_list 為空）。
**⚠ Context Isolation（P0）**: S9 讀全部 DR 報告 / 對話提取概念 → 委派子代理（子代理回**扁平概念名清單** `<slug>-concepts.txt` + 結構化 `<slug>-analysis.yaml`，不回原文）。
**入庫**:
```bash
# CLI（extra_concepts 走 --concepts-yaml；Ollama 走 --md）：
python3 -m indexing.ingest_conversation --id <convId> --title <t> --url <u> \
    [--md <conversation.md>] [--concepts-yaml <analysis.yaml>]
# 或程式化 ingest_conversation(conv_id, title, url, text=..., extra_concepts=[...])
```
**🔴 grounding 紀律（順序：verify-before-exclude，非 suspect-then-exclude）**: DR/對話盤點的疑點 named 實體 → **先 SURFACE + external-verify（web-grounded primary source），只永久排除 CONFIRMED-fake**。**別在『疑』就排除**——⚠ **cutoff-bound 子代理（如 S1 Anthropic subagent）對 post-cutoff 真實體會 false-positive**：本對話 6 個「疑 post-cutoff 杜撰」的實體（ATIF/Harbor/AgentHER/AgentWorkforce/ASSERT-KTH/reproducible-trajectories）external-verify 後 **6/6 全查實為真**（見 `<slug>-hallucination-audit.yaml`）。訓練 cutoff 判不了 cutoff 後事實——這對「疑真」與「疑假」同時成立（PG-163 雙向）。**存在性 VERIFIED ≠ 細節/perf/framing 也對**（PG-GCR-004：如 AgentHER 論文 perf 數字未證、AgentWorkforce 是平台非 dataset）——存在與細節分開判。
**Checkpoint**: `conv 節點寫入` + `DISCUSSES 邊數 = grounded 概念數`。
**Library 升格（真實 repo）**: 對話提及且 external-verify 過的**真 repo** → `Library` 節點 + `Conversation ─MENTIONS→ Library`（`ingest_conversation(..., libraries=[{raw_name, repo_url, license}])`；raw_name 傳 `org/repo` 消歧 → JOINS 既有 lib）。spec/format/研究組非單一 repo 者留 Concept。見 [retarget-map §KG-sink](retarget-map.md)。
**硬數據**: `s9_ingest: {conv_node_id, concepts_grounded, concepts_excluded_hallucination, concepts_reused_existing(跨源join), libraries_mentioned, kg_nodes_delta, kg_edges_delta}`
> **LIVE ✓（cc-20260703, RIP）**: `conv:gemini:2f75cc431e794606`（「LLM 吞噬 Harness」對話）全流程真跑：S0 抽取（turns_html 9 turns）→ S1 子代理分析（7 維度/50 概念/5 DR 候選）→ S9 ingest（初 45 grounded，5 疑幻覺暫排除）→ **S 級 hallucination-audit（external-verify 6 實體，6/6 VERIFIED，`<slug>-hallucination-audit.yaml`）→ 撤銷排除補回 50 概念全入庫 → 4 真 repo 升格 Library + MENTIONS**（lib:harbor JOINS 既有影片 lib、enrich repo_url）。跨源 join：10 concept + Harbor lib（影片軸↔對話軸）。KG 最終 10645 nodes / 16665 edges。29 unit tests + schema_ssot + isolation 綠。

**下游評估（S9 後，SURFACE 給人，不 auto-chain）**: 概念密度足 + 有外部 repo 參考 → SURFACE「是否要對該 repo 做深度理解 / specs-as-code」給人裁；有 DR 指向外部 GitHub repo → SURFACE「是否要框架決策橋接」。**人 admit 才續**（非機器自選 demand）。完整下游落地驗證四段程序（D1 DR 落地驗證→D2 架構設計→D3 gap 收斂→D4 prototype）→ [downstream-landing.md](downstream-landing.md)。
