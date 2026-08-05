# Module: gemini-conversation-research — northstar → antigravity retarget 映射 + 誠實拿掉了什麼

> 屬 [`gemini-conversation-research`](../SKILL.md)。本檔 = port 的**命門與誠實帳本**：哪些機制一對一映到 antigravity、哪些**沒有基座被拿掉、為何拿掉不是簡化**。
> 命門：northstar gcr 的核心是**對話研究 11 階段紀律**（S0 抽取 → 分析 → 缺口 → DR → 覆蓋 → 落地）。這條**乾淨映得過來**。**掛在它旁邊的整套 northstar 治理/KG/hook 基座在 antigravity 不存在**——原樣搬 = 引用一堆跑不動的東西 = 死 husk（antigravity [`fold-in.md`](../../fold-in/SKILL.md) 反模式明文禁）。
> **skill-bettor port addendum (2026-07-23)**: 本檔保留 antigravity retarget 的歷史帳本，不是 skill-bettor 本地 runnable map。本地/外部/歷史來源分級的 SSOT 改看 [skill-bettor-port-map.md](skill-bettor-port-map.md)。

---

## 1. 為何這個 port 的「拿掉」比 fold-in/judge-loop-chooser 更多

northstar gcr 是**四層疊加**：
- **層 1（對話研究管線 S0-S9）**：Gemini 對話 → 分析 → 追問 → 分診 → DR → 覆蓋 → 落地。→ **這層 retarget 得乾淨**（antigravity 本就做 DR，只是上游從 YouTube 換成 Gemini 對話 URL）。
- **層 2（DR 執行機器）**：northstar 的 `stealth-browser/src/tools/submit-dr-prompt.ts` + `extract-dr-report.ts`。→ **antigravity 已有更硬的等價物**（`automate.js`）→ **接過去、不搬**（見 §3 DR-reuse）。
- **層 3（治理閉環）**：`dr-governance-router` / `concept-landing` / `research-to-subproject-pipeline` / Bug Scar·DDR·Slop·PG registry / `skill-conformance` / `evals.json`。→ **antigravity 無任何基座** → **全部拿掉**。
- **層 4（AUP 物理強制）**：`gemini-aup-guard.sh` hook + `/tmp/.gcr-skill-active.<session>` marker + `execution/scripts/*.sh` wrapper + `validate-isolation-compliance.py`。→ **antigravity 是結構性 file-based 天生安全，不需要 hook** → **拿掉 hook，保留隔離紀律散文**（見 §4）。

antigravity 是**瀏覽器自動化執行器**（`automate.js`）。它的產物是**檔案**（`ai_studio/`、`gemini_research/`、`gemini_refine_pathb/`，SSOT 在索引），不是 KG registry 或治理 ledger。所以層 3/層 4 的基座在 antigravity 不存在——保留它們 = 讓 skill 引用不存在的 `execution/`、不存在的 hook、不存在的 rag-local MCP。

---

## 2. 逐機制 retarget 映射表

| northstar 機制 | antigravity 對應物 | 為何這樣映 / 拿掉了什麼 |
|---|---|---|
| Claude 斜線命令 `.claude/commands/`（本 skill northstar 無 command，只有 Skill tool） | 保留為**薄轉發層** `.claude/commands/gemini-conversation-research.md`（指向 `.agents/skills/` SSOT）+ antigravity 原生 skill `.agents/skills/gemini-conversation-research/SKILL.md` | 本 repo 雙平台：Claude Code 走 command 轉發、Google Antigravity 走 `activate_skill`，同一 SSOT。**這是本任務「做 .claude/commands 轉發層」的落點**。 |
| **S0** 對話抽取（`gemini-extract-pipeline.sh` + stealth-browser MCP + base64 分段） | 保留紀律，執行換成**瀏覽器 CDP → 檔案**（`extractReportHtmlInBrowser`+`htmlToMarkdown`；CDP fallback 連既有 `:9333`） | 「逐字元完整、禁摘要、原文不進 context」的**紀律**乾淨映；`base64 分段` 是 northstar 繞 MCP evaluate 上限的手法，antigravity file-based 抽取天生不經 context，**不需要 base64 管道**。 |
| **S1/S7/S9** 子代理隔離（`gemini-analyze-pipeline.sh` / `gemini-gap-analyze-pipeline.sh` / `gemini-kg-ingest-pipeline.sh` wrapper） | 保留**子代理隔離紀律**（Agent tool，回結構化 YAML ≤5K）；**拿掉 `execution/scripts/*.sh` wrapper** | wrapper 是 northstar 的 AUP exit-code 封裝（exit 9 = AUP）+ transcript harvest，antigravity 無此 hook 基座。子代理分治**本身**是可移植紀律。 |
| **S2** DR prompt 反幻覺四守則（`dr-anti-hallucination-guards.md` G1-G4）+ **§G5** 事後 bibliography 查證 | 保留，retarget → [`external-verify`](../../external-verify/SKILL.md)（6 步確定性程序，訓練=幻覺源、拉 primary source） | antigravity 已有 external-verify skill = 同紀律的執行化。**G3「源碼=100% SSOT」/ G5「禁盲搜 WebSearch、錨 source bibliography」不可砍**（砍 = DR 幻覺入庫；post-cutoff confabulate 把真論文判杜撰）。 |
| **S3** DR 投遞+抽取（`submit-dr-prompt.ts` + `extract-dr-report.ts`，northstar 版） | **拿掉 northstar 版** → extension Chrome 接 repo-root bounded adapter（沿用 antigravity read-back gates）；CDP 接 `automate.js runDrOnce` + [`gemini-deep-research-extract`](../../gemini-deep-research-extract/SKILL.md) | 見 §3 **DR-reuse 命門**：不可移植成較弱的 click-only/verifyStarted 複製。 |
| **S5 / S9** KG 入庫（`kg_fast_write` rag-local MCP + `kg-ingest.ts` + snake_case node/edge） | **retarget 到 antigravity 自己的 KG**（`indexing/` GraphStore + `.cache/kg/graph.json`）：新 `Conversation` 型別 + `indexing/ingest_conversation.py`，鏡像 `concepts.py` 概念軸 | 見 §KG-sink。antigravity 無 rag-local，但**有自己的 KG**——所以不是「拿掉」而是「換活基座」。cc-20260703 補完並 live 驗（見 §KG-sink）。 |
| **S6** FEEDBACK 治理閉環（`outcome.yaml` + `parse-isolation-from-transcript.py` + `validate-isolation-compliance.py` + 下游路由 concept-landing/dr-governance-router） | **降級**為輕量 `outcome`（feedback_triangle：initial_prompt × conversation × dr_outcome/coverage 記檔）；**拿掉** transcript-harvest / isolation-validator / 下游路由 | antigravity 無 transcript hook、無 concept-landing/dr-governance-router skill。feedback 三角**紀律**保留（記進 harvest 檔或 `AGENTS.md` Resolved），治理路由**拿掉**。 |
| `gemini-aup-guard.sh` hook + `/tmp/.gcr-skill-active.<session>` marker + `gcr-authorize.sh` | **拿掉 hook + marker 全套** | antigravity **file-based 天生安全**（內容不進 agent context），不需要 hook 補救。marker session_id 三源不一致 bug（northstar PG-GCR-005）在 antigravity **不存在**（無 marker 就無此 bug）。見 §4。 |
| 5 個 `pg/PG-GCR-*` 檔（UI drift / pipeline-discipline / DR 幻覺 / capability-drift / marker bug） | **拿掉 pg/ 目錄**，know-why 折進 modules 散文 + `AGENTS.md` Resolved | antigravity **不用 `pg/` 慣例**（同 jlc「拿掉編號、保留紀律散文」）。UI drift 真相在 `automate.js`；DR 幻覺紀律在 external-verify；capability-drift 紀律在 [`judge-loop-chooser`](../../judge-loop-chooser/SKILL.md) grounding 三態。 |
| `evals.json`（17KB northstar eval harness）+ `tests/test_gcr_runtime.py` + `test_panorama_anchors.py` | **拿掉／換** → `node --check automate.js`（引擎）+ 人審 + panorama 錨點人工對照 | antigravity 無 pytest skill-eval-runner、無 `.northstar/run-all-tests.sh`。驗證錨換成 syntax check + live run + 引用基座存在性檢查（§5 鐵錨）。 |
| 上游 `signal-scanner.sh`（openclaw dispatch `gemini_conversation` signal）+ `bookmark-research-orchestrator` | **拿掉** | antigravity 無 openclaw / signal / 書籤管線。Mode B 觸發源改成「使用者直接給主題 + 上下文」。 |
| `sovereignty_check()` BLOCKED_PATTERNS（DDR-NNN / Bug Scar / local_stack / openclaw / zeroclaw / ixsecurity 等內部名 regex 替換） | 保留**資料主權紀律**，retarget → 泛化為「Q&A prompt 只含公開術語，不洩漏私有專案脈絡」；**拿掉 northstar 內部名 regex 表** | northstar 的 BLOCKED_PATTERNS 全是 northstar 內部專有名詞；在 antigravity 那些名字不存在。紀律（不把私有脈絡洩漏給外部 Gemini）保留，具體字典改由使用者當下脈絡定。 |
| `repo-fullstack-debugger` rfd-takeover（`browser-l2-quadrants.md` Bot/Timing/Selector/Auth 四象限） | **拿掉** → 瀏覽器失敗診斷改走 [`dr-research-loop`](../../dr-research-loop/SKILL.md) 的 live 唯讀診斷方法論 + `execution-playbook.md §8` 失敗模式表 | antigravity 無 repo-fullstack-debugger skill；它的瀏覽器診斷紀律已在 dr-research-loop。 |
| `autoresearch-integration.md`（northstar autoresearch optimizer 可變異面） | **拿掉** | antigravity 無 northstar 版 autoresearch skill-optimizer 掛接。 |
| `activation-prompts.md` GCR-0..5（含「已授權 stealth surface / autoMode.environment / INV-HUMAN-GATE」等 northstar RUN-CONTRACT 術語） | 保留 **Mode A 啟動意圖**，retarget 進 [mode-b-contextqa.md](mode-b-contextqa.md) + 命令 `$ARGUMENTS`；**拿掉 INV-HUMAN-GATE / autoMode.environment 等 northstar engine-locus 術語** | 那些不變量是 northstar 治理框架詞；antigravity 的閘就是「人跑瀏覽器 / 人開 CDP」，紀律用平白話說。 |

---

## 3. DR-reuse 命門 — 為何**接** `automate.js` 而非搬 northstar 的 stealth-browser DR 工具

northstar `loop-panorama-ssot.md §5`（實證 cc-20260629/0630）自證了這一點：

> 🔴 **reliability 命門 = 復用 `automate.js --dr-once`，不在 gcr 重造**。gcr `submit-dr-prompt.ts` 是 automate.js DR flow 的**滯後複製**（缺 monitor-to-complete + `MAX_DR_ATTEMPTS` retry）→ 間歇卡 plan/submit 失敗（實證 0/N）。同 prompt 經 `automate.js --dr-once`（硬化引擎）**一次跑完 22.8K 字**。

即 northstar 那條 DR 工具鏈**本來就在追 antigravity `automate.js` 的尾巴**。在 antigravity 原地，直接接**原版硬化引擎**：
- **S3 投遞** → extension 用 `launchGeminiDeepResearchFromPromptFile`；CDP 用 `automate.js runDrOnce`/`runGeminiDeepResearch*`。批次序列都走「脫鉤才投下一個」。
- **S3 抽取** → extension 用 `extractGeminiConversationFromBrowserTab`；CDP 用 [`gemini-deep-research-extract`](../../gemini-deep-research-extract/SKILL.md)。兩者都保留 `[cite:N]` 與 used bibliography。
- **完成判據**（非 `verifyStarted` 假陽性）→ 字數 ≥3000 ∧ 0 計劃殘留 ∧ `deep-research-source-lists`；~8min 後 metadata-only 探針看 `hasPanel`。

**把 northstar 版 `submit-dr-prompt.ts` 搬進 antigravity = 把滯後複製搬回來，撞回它自己的間歇卡 bug。** 擋下。

---

## 4. AUP 隔離 — antigravity「自主只因無 guard」是**架構**非權限

northstar `context-isolation-aup.md` 自己記了（line 62）：

> **antigravity 對比**：它自主**只因無 guard**（結構性 file-based，content 從不進 agent context）——**架構決定 autonomy，非權限**；不可靠「拆 northstar guard」製造。

所以在 antigravity：
- **拿掉** `gemini-aup-guard.sh` hook、`/tmp/.gcr-skill-active.<session>` marker、marker session_id 三源 bug（PG-GCR-005）——這些**在 antigravity 不存在也不需要**。
- **保留**的隔離紀律（可移植、且 antigravity 天生符合）：①瀏覽器抽取 → 檔案，原文不進主 context；②S1/S7/S9 分析走子代理回 YAML；③主會話禁 Read 對話原文全文。
- ⚠ **不可拿掉的硬約束**：外部原文跨界進主 context 是**不可約的資料外洩面**（northstar 稱 Data Exfiltration hard_deny）——這與「平台權限」無關，file-based 架構 **mandatory**。這條**不是 hook 給的**，是架構本身給的。

---

## 5. 拿掉的東西不是「簡化」，是「不引入不存在的基座」

northstar gcr 的 KG 入庫、治理路由、aup-guard hook、pg/ 編號、execution 腳本、evals harness 在 northstar 是**活的**（有對應基座）。在 antigravity 它們**沒有基座**——保留 = 讓 skill 引用一堆跑不動的東西 = 正是 antigravity `fold-in.md` 反模式禁的「原檔搬進本 repo 引用不存在基座 = 死 husk」，也是 northstar 自己反的 supply-push husk（RIP：不被調用的能力不是能力）。

retarget 的正確姿勢：
- **能一對一映的映**：轉發層、S0-S9 對話研究紀律、子代理隔離、feedback 三角、追問協議、覆蓋比對。
- **活基座換掉**：DR 引擎 `submit-dr-prompt.ts` → `automate.js runDrOnce`；反幻覺 `dr-anti-hallucination-guards` → external-verify；Path B → path-b-reduction；瀏覽器診斷 → dr-research-loop。
- **沒對應物的誠實拿掉並記錄**（本表）：KG 入庫、治理路由、aup-guard hook + marker、pg/ 編號、execution wrapper、evals harness、signal/openclaw 上游、autoresearch 掛接。

**判別「retarget 成立」的鐵錨**：本 skill 引用的每個 antigravity 基座都真存在——
- `automate.js`：`extractReportHtmlInBrowser`(43) / `runGeminiDeepResearch`(1364) / `runGeminiDeepResearchAttempt`(1383) / `runDrOnce`(2287) / `htmlToMarkdown` ✅
- 四個 sibling skill 真在 `.agents/skills/`：`gemini-deep-research-extract` / `external-verify` / `path-b-reduction` / `dr-research-loop` ✅

若哪天有人往 SKILL.md / modules 塞回 `kg_fast_write` / `execution/scripts/*.sh` / `gemini-aup-guard.sh` / `PG-GCR-NNN` / rag-local MCP / `submit-dr-prompt.ts`，那就是把死 husk 搬回來——擋下。

---

## §KG-sink — KG 等價層（cc-20260703 補完，live 驗）

northstar S9 走 `kg_fast_write`（rag-local MCP）。antigravity **無 rag-local**，但**有自己的 KG**（`indexing/` package 的 `GraphStore` + `.cache/kg/graph.json`，現 10K+ 節點）。所以「補 KG 等價層」= **接 antigravity 自己的 KG 引擎，非重造、非用 rag-local**：

- **新 node 型別 `Conversation`**（`conv:gemini:<id>`），經**三重映射**登記（`indexing/models.py BASE_NODE_TYPES` + `docs/plans/.../CONTEXT.md node_id 範式` + `docs/…-design.md §1`；`test_schema_ssot.py` 精確比對，漏登記即紅）。
- **`indexing/ingest_conversation.py`** = **鏡像 `concepts.ingest_concepts_for_video`**：對話文本走**同一個 `extract_concepts`（Ollama qwen3:4b）+ `canonical_concept_id`** 引擎 → `Conversation ─DISCUSSES→ Concept`。邊全複用既有 `DISCUSSES`（無新 edge 型別）。
- **跨源 join 是白賺的價值**：concept 用 canonical id → Gemini 對話的概念與既有 Video/RepoDoc 概念**自動合流**（`Concept` 成為「對話 ↔ 講座 ↔ repo」的跨軸 join）。
- **Library 軸升格（cc-20260703）**：對話提及的**真實 repo**（external-verify 過）可升格為 `Library` 節點 + 新 `MENTIONS` 邊（`Conversation ─MENTIONS→ Library`，三重映射登記；`ingest_conversation(..., libraries=[{raw_name(org/repo), repo_url, license}])`）。raw_name 傳 `org/repo` 形經 `canonical_lib_name` 消歧 → **JOINS 既有 Library**（實證：對話的 Harbor = 影片 Equivalent 的 `lib:harbor` 同節點，enrich 了影片缺的 repo_url；license 傳 None 保留既有 = 保守 fill-gap）。⚠ 同名碰撞先 external-verify 既有節點身分（`lib:harbor` 的 name prop 確認是 `harbor-framework/harbor` 才 join，否則另立 id）。非 repo 的（spec/format/研究組）留 Concept 不升 Library。
- **隔離不變量守住**：每節點 `props.source="antigravity"`，生成器版本放 `props.generator="gcr-v1"`（勿借 source）。validation gate（`_ALLOWED_NODE_TYPES={Conversation,Concept}` / `_ALLOWED_EDGE_TYPES={DISCUSSES}`）⊆ BASE_*。
- **grounding 紀律**：S 級 hallucination-audit 未過前，疑 post-cutoff 杜撰的 named 實體**排除、勿 ingest**（否則 hallucination propagation）。
- **測試**：`indexing/tests/test_ingest_conversation.py`（8）+ `test_schema_ssot`（三重映射）+ `test_isolation` 綠；全套 316 passed（1 pre-existing 失敗 `test_export_e2e` 硬編碼已移除的 `/Users/neon/antigravity-kb/` 路徑，與本 port 無關）。
- **LIVE ✓ RIP**：`conv:gemini:2f75cc431e794606`（「LLM 吞噬 Harness」對話，S0 真抽 → S1 子代理分析 → S9 ingest）：45 grounded 概念、5 疑幻覺排除、**9 複用既有 concept（跨源 join）**、KG 10601→10638 nodes / 16611→16656 edges。

> ⚠ 仍禁 rag-local：本層接的是 **antigravity 自己的 `indexing/` KG**，不是 northstar rag-local MCP。往 SKILL/modules 塞 `kg_fast_write` / rag-local 仍是搬 husk——擋下。

## Sources / Lineage
- northstar 源：`/Users/neon/northstar/.claude/skills/gemini-conversation-research/`（skill.md v3.7.0 + 12 modules + 5 `pg/PG-GCR-*` + `playbook/gemini-browser-playbook.md` + `evals.json` + `tests/`）。
- skill-bettor 慣例：[skill-authoring](../../skill-authoring/SKILL.md)、[`judge-loop-chooser/modules/retarget-map.md`](../../judge-loop-chooser/modules/retarget-map.md)（同型 port 先例）、[`AGENTS.md`](../../../../AGENTS.md)。
- 活基座：`/Users/neon/antigravity/automate.js`（DR 引擎）+ `.agents/skills/{gemini-deep-research-extract,external-verify,path-b-reduction,dr-research-loop}`。
