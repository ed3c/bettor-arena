---
name: gemini-conversation-research
description: |
  研究 Gemini 對話（不是 YouTube 影片）時使用 — 給定一個 Gemini/AI Studio 對話 URL 或一個研究主題，
  把對話的隱性知識結構化、只把真缺口送 Deep Research、迭代到知識點全覆蓋。11 階段 rigid pipeline
  （S0 抽取 → S1 脈絡分析 → S1.5 同對話追問 → S2 分診 → S3 DR → S4 存檔 → S7 覆蓋比對 → S8 multi-DR → S9 落地）
  ＋ 雙模式（Mode A URL 抽取 / Mode B 主動 Context-QA）。DR 投遞與抽取複用 antigravity 既有引擎，不重造。
  觸發詞：研究這個 Gemini 對話、分析 Gemini 對話脈絡、用 Gemini 研究某主題、Gemini DR、對話知識全覆蓋、
  exhaustive extraction、對話知識萃取。
---

# Skill: Gemini 對話研究管線（skill-bettor 版；port 自 antigravity `gemini-conversation-research`）

> **skill-bettor port note (2026-07-23)**: 本 skill 複製自 `/Users/neon/antigravity/.agents/skills/gemini-conversation-research`。在 skill-bettor 內，`/Users/neon/antigravity` 是來源證據與外部執行經驗，不是隱含本地基座。能在 skill-bettor 內 production 化的部分必須落到 `.claude/skills/`、`loop_wiki/evolve-unknown-discovery-plan-truth/templates/gemini-conversation-research/`、golden cases、validator、plan-package gates。任何仍依賴 antigravity browser/KG/DR engine 的步驟都必須標 `external_engine_required`，禁止宣稱本 repo 已可直接執行。

> **Role**: 把一個 Gemini 對話（高密度認知結晶：主題脈絡 / 認知遞進 / Q&A 邏輯 / 結論框架 / 知識缺口）結構化，
>   **只把缺口送 DR**、其餘直接存檔，迭代到知識點全覆蓋。與 [dr-research-loop](../dr-research-loop/SKILL.md) **正交**——
>   那條是 YouTube 影片 → 卡片盒 → DR，本條是**既有 Gemini 對話 URL / 主動 Q&A** → 分析 → 缺口 → DR。
> **結構**: SKILL.md = 11 階段架構 + 每階段編排 know-how（1-2 行 + 指針）；逐階段 how-to / checkpoint / 子代理模板在 `modules/`。
> **SSOT / 活基座分級（本地可跑 vs 外部引擎，這是本 port「非 husk」的鐵錨）**:
>   - DR 投遞 + 抽取引擎 = `automate.js` 的 `runDrOnce`(256) + `ui.js` 的 `runGeminiDeepResearch`(906) / `runGeminiDeepResearchAttempt`(924) + `data.js` 的 `extractReportHtmlInBrowser`(24) / `htmlToMarkdown`(17)（cc-20260712 核實：舊引註「automate.js:1364/1383/2287/43」是 state.js／data.js／ui.js 拆分前的殘留行號，automate.js 現僅 290 行、純調度層——已修正）。**gcr 不重造 DR monitor+retry**（northstar 曾重造 = 滯後複製，實證間歇卡；見 [retarget-map §DR-reuse](modules/retarget-map.md)）。
>   - DR 報告 → 保真 Markdown：extension Chrome 用 repo-root browser adapter；獨立 CDP extractor 仍是 `gemini-deep-research-extract`（skill-bettor 未隨本次複製，CDP 路徑缺它時標 `external_engine_required`）。
>   - 反幻覺 / 外部查證 = [external-verify](../external-verify/SKILL.md)（S2 DR prompt 硬化 + 事後逐 claim 查證）。
>   - Path B 精煉 = [path-b-reduction](../path-b-reduction/SKILL.md)。
>   - skill-bettor 本地新增可跑 seed = [guided-conversation-observation](modules/guided-conversation-observation.md) + [production-guidance-hardening](modules/production-guidance-hardening.md) + file-only `scripts/run_guided_conversation.py`/Bun technical equivalent + `loop_wiki/evolve-unknown-discovery-plan-truth/templates/gemini-conversation-research/` golden cases/evals/ROUTES contract。
>   漂移時以本地 port map 的分級為準；外部 DR/browser/KG 行為以 antigravity 原始引擎程式碼為權威。
> **retarget 誠實帳本**（northstar → antigravity 拿掉了什麼、為何不是簡化）→ [modules/retarget-map.md](modules/retarget-map.md)。
>   ⚠ **別把 northstar 原檔的 KG 入庫（`kg_fast_write`）/ `dr-governance-router` / Bug Scar #NNN 編號 / `gemini-aup-guard.sh` hook / `execution/scripts/*.sh` wrapper 搬回來**——antigravity 無此基座 = 死 husk（見 [fold-in](../fold-in/SKILL.md) 反模式）。

## When to Use
- 有一個 **Gemini 對話 URL**（`gemini.google.com/app/<id>` 或 `aistudio.google.com/prompts/<id>`）要萃取知識 + 補缺口研究。
- 有一個**研究主題 + 上下文**，要**主動開新 Gemini 對話**做多輪 Q&A 再萃取（Mode B）。
- 要對一個對話做「知識點覆蓋率」比對，迭代 DR 到全覆蓋。

## Not For
- ❌ YouTube 影片 → 卡片盒 → DR 全量管線 → [dr-research-loop](../dr-research-loop/SKILL.md)（不同上游、不同閉環）。
- ❌ 只要把一份**已生成**的 DR 報告經 CDP 抽成保真 md → `gemini-deep-research-extract`；extension Chrome 則使用 repo-root bounded adapter，不需要該外部 skill。
- ❌ 可讀 repo 的 codebase 掌握用 DR 當主幹（漏斗倒置）——源碼 = SSOT，DR 只補外部缺口。
- ❌ 造新 skill / 改 skill 規範 → [skill-authoring](../skill-authoring/SKILL.md)。

## 核心原理 + 雙模式
Gemini 對話是高密度認知結晶。本 skill 把隱性知識結構化，**只把缺口送 DR**，其餘直接存檔。
- **Mode A（URL 抽取）**: 對話 URL → S0 抽取已有對話 → S1-S9。
- **Mode B（Context-QA）**: 研究主題 + 上下文 → S-1 載入 → S0-ALT 主動開新 Gemini 對話逐輪 Q&A → 併回 S1。

```
Mode A:  URL → [S0 抽取] → [S1 分析] → [S1.5 追問] → [S2 分診] → [S3 DR] → [S4 存檔]
                                                                  ↘ [S7 覆蓋比對] → [S8 multi-DR]⟲S2/S3 → [S9 落地]
Mode B:  主題+上下文 → [S-1 載入] → [S0-ALT Q&A] → (併入 S1…)
```

## 🛡 改任一階段 / prompt 前先讀全景（防誤改 SSOT）
改任一 S-stage 或任一 prompt 前，先在 [modules/loop-panorama-ssot.md](modules/loop-panorama-ssot.md) 對照：①該物歸屬哪段（別改錯地方）②會不會斷閉環 gate/loop-back ③prompt 改 canonical 原檔、禁散補 / 禁簡化。**sibling 全景**（不同管線同紀律的 worked-example）= [dr-research-loop/modules/loop-panorama-ssot.md](../dr-research-loop/modules/loop-panorama-ssot.md)——改 gcr 別去改它，反之亦然。

## AUP 內容隔離（antigravity 是**架構性天生安全**，非靠 hook）
外部對話原文（21K+）**永不進主會話 context**。antigravity 的隔離是**架構決定的**（file-based：瀏覽器抽取直接寫檔、任何 LLM 分析走子代理），**不是** northstar 的 `gemini-aup-guard.sh` marker hook——**本 repo 無此 hook，也不需要**（northstar 靠 hook 補救；antigravity 天生 file-based 就無此暴露面）。三條規則：
1. **S0/S3 抽取走瀏覽器 → 檔案**（`extractReportHtmlInBrowser` + `htmlToMarkdown` 寫 `.md`），原文不經 agent context。
2. **S1/S7/S9 分析走子代理**，只回結構化 YAML（≤5K）；主會話禁 `Read` 對話原文全文（≤50 行 spot-check 例外）。
3. **Chrome carrier 也要隔離**：Gemini 分頁的 snapshot、conversation `textContent/innerText`、screenshot/OCR 或正文 `evaluate` **不得回傳主會話**；locator grounding snapshot 只可留在 repo-root adapter runtime，正文/projection 直接寫檔並回 bounded receipt。
4. ⚠ 這層是硬約束：**即使平台權限放開，外部原文跨界進主 context 仍不可約（Data Exfiltration）**——file-based 架構 mandatory。
> 完整隔離設計 + 為何 antigravity「自主只因無 guard、架構決定 autonomy 非權限」→ [modules/conversation-pipeline.md §AUP 內容隔離](modules/conversation-pipeline.md)；Chrome 擴充功能的唯一安全 recipe → [modules/browser-content-isolation.md](modules/browser-content-isolation.md)。

## S0-S9 階段編排（逐階段 how-to → [modules/conversation-pipeline.md](modules/conversation-pipeline.md)）
| 階段 | 一句話 | 委派 / 複用 |
|------|--------|-------------|
| **S0 EXTRACT** | 抽取 Gemini/AI Studio 對話原文 → 寫檔（逐字元完整，**禁摘要/重組**，摘要是 S1 產物）；若對話內含已完成的 Deep Research 報告（`deep-research-immersive-panel`），citation/bibliography 一併保真抽出附加在 QA 之後 | Codex/ChatGPT Chrome 擴充功能：先 claim 使用者已開啟的對話分頁，再 import **repo 根目錄** `scripts/extract-gemini-conversation-browser-runtime.mjs` 並呼叫 `extractGeminiConversationFromBrowserTab`（正文直接寫檔、回傳 ≤4096-char metadata receipt）；legacy `:9333` CDP 仍複用 antigravity 根腳本。LIVE ✓ |
| **S1 ANALYZE** | 子代理讀對話檔，6 步框架 → `conversation_analysis` YAML（維度 / 認知遞進 / Q&A 邏輯 / 密度 / echo-back 橫向挑戰 / vision→roadmap） | **子代理隔離** |
| **S1.5 PROBE** | knowledge_gap 維度先**同對話追問**（≤2 輪，比 DR 便宜兩數量級）；`knowledge_gap=0` 跳過 | 追問構造 → [first-principles-probe.md](modules/first-principles-probe.md) |
| **S2 TRIAGE** | 只把 research-gap 送 DR、合併最少查詢；DR prompt 過 **external-verify** 硬化，寫 `/tmp/dr-prompts/<slug>-<ts>.txt` file-only | [external-verify](../external-verify/SKILL.md) |
| **S3 DEEP** | DR 投遞 + 抽取 | extension Chrome：repo-root adapter `launchGeminiDeepResearchFromPromptFile` → metadata probe → `extractGeminiConversationFromBrowserTab`；CDP fallback 才複用外部 `automate.js runDrOnce` + `gemini-deep-research-extract` |
| **S4 HARVEST** | 雙文件存檔（`.md` 完整含 bibliography / `.txt` 結構化）；回應**必給絕對路徑**（AUP 下主會話不讀全文，路徑是使用者唯一線索） | — |
| **S7 GAP** | 子代理交叉比對 S1 維度 × DR 覆蓋 → 過濾 CRITICAL/HIGH uncovered → `gap_list` | **子代理隔離** |
| **S8 MULTI-DR** | `gap_list` 合併 → 複用 S2/S3 跑額外 DR → 回 S7 重算覆蓋（**≤3 輪收斂**） | 複用 S3 引擎 |
| **S9 INGEST** | 全知識點**入 antigravity KG**：`Conversation` 節點 + `DISCUSSES→Concept`（複用 `concepts.py` 引擎）+ 真 repo `MENTIONS→Library`（帶 repo_url，JOINS 既有 lib）；跨源 join 既有 Video/RepoDoc | `indexing/ingest_conversation.py`（子代理隔離 + KG ingest）；LIVE ✓ |

> **S9 後下游落地驗證（SURFACE-gated，人 admit，非 auto-chain）**：DR 存檔 ≠ 可信 ≠ 可落地。四段定序＝**D1 DR 落地驗證**（多模型分工 + external-verify + 🔴 HTTP 確定性錨打實體存在性，別信 LLM grounding）→ **D2 架構設計合成**（真實度計分卡 + 等價物矩陣）→ **D3 可行度 gap 收斂**（unknown-discovery-composer 四象限 → repo-wiki-converge/repo-agent-native；真實作常**反證** DR 論點）→ **D4 prototype 端到端**（`kb-ingest/setup-prototype.sh`，推導→實測）。完整 how-to/血淚 → [modules/downstream-landing.md](modules/downstream-landing.md)。

## Guided Conversation Buttons（Gemini 額外探討按鈕）
Gemini 回應後可能出現非固定複製/分享 UI 的 contextual suggestion buttons，例如「是」、方向選項、比較選項、追問選項。這些按鈕是對話語義事件，必須按照上下文順序觀察、分類、觸發、抽取 auto prompt/auto answer，並把被簡化資訊、遺失資訊、遺失 Domain 專有名詞寫成 state。Codex Chrome 路徑必須用 repo-root `run-gemini-guided-conversation-browser-runtime.mjs`：只承認最新 model response 內有明確 suggestion ownership 的候選，generic source/chip 是負例；click/submit 均預設 dry-run。emergent prompt 只從 decision file 送出，回答須經 turn advancement + 非 streaming + 兩次 metadata 穩定後才抽檔。一次只執行一條 edge；禁止用歷史按鈕、全頁 ordinal 或半截回答推進。程序與 schema 見 [modules/guided-conversation-observation.md](modules/guided-conversation-observation.md)；小迴圈模板與 golden behavior eval 見 `loop_wiki/evolve-unknown-discovery-plan-truth/templates/gemini-conversation-research/`。

歷史對話序列不得回灌 live button runner。若只有隔離分析的 carrier
provenance、branch outcome 與 semantic-loss metadata，使用 Bun
`gcr:historical-normalize`；它驗 hash、count identity、三 prompt slots 與
branch reason，只輸出 `candidate_not_promoted` 和 metadata receipt。歷史
DOM ownership 不可由文字序列補推，下一條合法邊固定為獨立的
`G7.execution_replay_and_claim_verification`。

歷史 declarative repair 通過 fixture polarity 後，不得把本輪安裝的工具
倒灌成歷史 runtime。使用 Bun `gcr:historical-tool-runtime-bind` 只接受
hash-bound DOM package manifest、lockfile 或 install receipt 的 exact semver；
flattened Markdown 只做 metadata audit，當前 migration 的 package/bin/lock
必須列為 ineligible exclusion。找不到直接證據時輸出
`historical_runtime_unavailable` 並路由 `G7.grade_repaired_historical_claim`，
禁止用時間相容版本補猜。

`G7.grade_repaired_historical_claim` 必須用 Bun
`gcr:repaired-historical-claim-grade` 組合 exact claim、prior verdict、artifact
binding、original replay、repair comparison 與 runtime-binding receipt。歷史
runtime unavailable 時，candidate-runtime schema rejection 只能標
counterevidence，不能升格為 historical contradiction；repair 通過只能標
counterfactual，且 `repair_substitution_allowed=false`。

若下一個歷史 claim 橫跨 partial branch 的多個 TypeScript artifact，不得把
單一 declarative config binder 名稱類推為等價。先真跑既有 binder，再用
`gcr:historical-typescript-claim-bind` 同時綁定兩個 exact code blocks 與各自
same-response JSON path carrier。輸出必須分開
`source_lineage_status=exact_multi_artifact_pair_bound` 與
`semantic_contract_status`；相關 anchor、可解析或函式簽名都不等於歷史執行
證明，`historical_execution_verified=false` 且不得 promotion。

selected pair 不滿足 claim 仍不可直接判 historical contradiction。使用
`gcr:bound-eslint-refactoring-claim-grade` 從完整 capture manifest 列舉所有
與 exact target-path carrier 同 response、且具相應 anchor 的 TypeScript pair；
只要 parser 或 input-contract selection 非 exhaustive，就保持
`historical_contradiction_proven=false`，並路由替代 candidate binding。

替代 parser candidates 必須用 `gcr:alternative-eslint-parser-bind` 全數
hash-bind。`JSON.parse` 不是 ESLint parser 的充分證據；若同時只有
dependency-cruiser `--output-type json`、沒有 ESLint invocation/format 與
`ruleId`/`severity` shape，必標 `dependency_cruiser_json_parser_only=true`。
本節只完成 source exhaustiveness，不在 binder 內判歷史 contradiction。

全數 parser candidates 與唯一 agent candidate 都 exact-bound 後，使用
`gcr:exhaustive-eslint-refactoring-claim-grade` 分命題裁決。captured-artifact
scope 的 implementation 可判 contradicted；缺 execution receipt 只容許
`implementation_executed_and_verified=unverified_no_execution_receipt`，禁止把
absence-of-evidence 改寫成歷史 nonexecution proof。

每個 terminal proposition grade 完成後，使用
`gcr:next-unverified-claim-select` 以原始五-claim result 與 terminal grade
hashes 重建 remaining queue；禁止靠記憶跳 claim。選擇順序先處理 bounded
historical evidence availability，再處理 broad aggregate，最後才是 external
human-gated effect。selector 接受 2–5 個 unique、屬於原五 claims 且
`promotion_allowed=false` 的 hash-bound terminal grades，並要求
dependency-cruiser 與 ESLint 兩個先決 grade 永遠存在：2 個選 DOM、3 個選
generated surfaces、4 個選 threshold human gate、5 個路由 completion audit。
selector 只排程，禁止執行被選 claim。

選到 `G7-GENERATED-SURFACES-001` 後，先跑
`gcr:historical-generated-surfaces-coverage-audit`：必須 hash/byte-count
驗證全部 capture records，將 path candidates 依 settings、scripts、tests、
workflows、documentation 分類，並把 generated presence、parseability、
bounded runnable semantics、historical execution、target-repository correctness
分層。path carrier 只證明命名候選，不等於 exact artifact binding；缺 execution
receipt 仍不是歷史 nonexecution proof。auditor 禁止輸出 raw bytes 或執行 artifact。

coverage audit 完成後用 `gcr:historical-generated-surfaces-claim-grade`
分別判級 required-surface generation、artifact parseability、bounded runnable
semantics、historical execution、target-repository correctness。exact-bound parse
或 semantic counterexample 可反駁全稱的 correct-execution proposition；但不得
順勢把 execution receipt 缺失改寫成「歷史上沒執行」。

`G7-THRESHOLD-EFFECT-001` 用
`gcr:threshold-effect-human-gate-grade` 終止：source 若仍是
`hash_verified_insufficient` 且 external execution 需人類授權，輸出
`human_required_unexecuted`、effect/threshold 值保持 null、external calls=0。
這個 human gate 阻擋該 claim 的效果驗證，不得誤升格成整體 migration blocker。

五個 terminal grades 完成後，用
`gcr:historical-claim-completion-audit` 驗證 original claim set 等於 terminal
grade set、selector terminal hash order 一致、每份 grade
`promotion_allowed=false`。輸出 classification complete 不等於 all claims
PASS，也不等於 migration complete；後者必須另走 G8 audit。

G8 completion pre-audit 若發現 registered receipt hash pointer 與目前檔案 bytes
不一致，必須先走 `G8.repair_stale_registry_packet_hash`：以 canonical exchange
validator 區分真 identity drift 與 legacy packet 格式差異，只允許修正已存在
artifact 的單一 SHA-256 pointer。不得把 draft/human gate 改成 admitted、不得把
`normalized_output` 強制改成 registry ingress，也不得把 `N/A-*` identity
誤判為缺檔。修復登錄後才可重跑 G8 migration completion audit。

`gcr:migration-completion-audit` 只能吃 hash-bound metadata：plan manifest、input
registry、materialization ratchet、prototype stats、final compat、historical claim
completion result 與本輪真跑 gate snapshot。它要逐筆重驗 registry order、ingress、
packet 基礎契約與現存 64-hex artifact identity；同時保留 `N/A-*` 與合法 draft
boundary。`requested_migration_complete` 必須和 `all_repository_gates_green` 分開；
既有 red 可保留，但 snapshot 必須列明且 `baseline_updated=false`。
Terminal completion receipt 的登錄是預先聲明的 bookkeeping closure；登錄後只需
重跑 materialization/serial/full gates 並封 receipt hash，不得因 receipt 自身成為
新 registry input 而製造無限自我審計，也不得藉此 promotion 或更新 baseline。

歷史 DOM ownership 必須用 `gcr:historical-dom-ownership-grade` 組合
historical trace、code-block capture 與 latest-response receipts。若 trace 明示
time-indexed receipt unavailable，輸出 unverifiable；禁止用 current DOM、code
blocks 或 missing receipt 推出 historical control ownership 或 manual-text
ownership。

## Production Guidance / ROUTES
凡是要把 GCR 對話導入小迴圈、計畫包、prototype、或 `repo/agent-skills-repo`，必須同時讀 [modules/production-guidance-hardening.md](modules/production-guidance-hardening.md) 與 `loop_wiki/evolve-unknown-discovery-plan-truth/ROUTES.md` 的 `GCR Production Guidance Route`。agy 只能作為 `Gemini 3.6 Flash` + `High` 的獨立 context replay actor；stdout 可能只是摘要，必須解析檔案 artifact 後再與末端 repo code/data 比對。任何未落到 `golden/production-guidance-routes.json`、`schemas/production-guidance-contract.schema.json`、plan-package packet、prototype mirror、final repo runtime surface、terminal validators 的輸出，只能是 candidate，不能 promote。

## Gotchas（跑前必知）
- **DR reliability 命門 = 復用 `automate.js --dr-once`，別在本 skill 重造 monitor+retry**：northstar 實證滯後複製間歇卡 plan/submit（0/N）；同 prompt 經 `automate.js` 硬化引擎一次跑完 22.8K 字（RIP）。批次 DR 走序列 → bridge → 引擎，別加 monitor+retry（= 重造）。
- **一帳號 DR 序列、脫鉤才投下一個**：DR 槽只在 ~2-3min init 期被佔，研究脫鉤（~210s）後釋放；太早投搶槽餓死前者。**不可與 dr-research-loop 影片管線同跑同一 :9333 帳號**（跑前 `pgrep -fl automate.js` 確認無）。
- **`verifyStarted` 是假陽性**（秒級 Start 鈕消失 ≠ 會跑完）：真完成 = 字數 ≥3000 ∧ 0 計劃殘留（`开始研究`/`修改方案`/`只需要几分钟`）∧ `deep-research-source-lists`。投 DR 後 ~8min 跑 metadata-only 探針看 `hasPanel` 判「卡 plan」vs「健康」。
- **簡繁陷阱**：開始研究鈕含**簡體「开始研究」**（开≠開），matcher 須認簡繁，否則卡計劃階段。
- **DR prompt ≤~1200 字單段**：長 / 多問 → soft-decline 或 `start_button_not_found`；多問拆 **S8 multi-DR**，勿塞一個長 prompt。
- **CDP fallback**：research profile `auth_required` 且使用者拒新登入 → 連使用者既有已登入 `:9333`（`puppeteer-core.connect({browserURL:'http://127.0.0.1:9333'})`，用 antigravity 已裝的 `node_modules/puppeteer-core`）；目標對話已開分頁則零導航直讀。**turndown ESM 陷阱**：`import` 走 `.../lib/turndown.cjs.js` build（`.es.js` 內部 `require()` 會炸 ES module scope）。
- **Codex Chrome 擴充功能優先路徑**：若 browser runtime 列出 `type: extension` 的 Chrome，必須使用同一已登入 profile，不得另開測試 profile。既有對話用 `browser.user.openTabs()` 精確 conv-id + `claimTab()`；新 DR 可用 `browser.tabs.new()` 開同 profile tab，再呼叫 repo-root bounded adapter。adapter 可在 runtime 內用 snapshot 建 locator ground truth，但**不得輸出 snapshot/evaluate 正文**；外部只收 metadata receipt。完整 recipe 見 `modules/browser-content-isolation.md`。只有擴充功能未連線時才退回 `:9333` CDP。
- **S0 腳本同名異義陷阱（cc-20260712 實測）**：repo 根目錄 `scripts/extract-gemini-conversation.mjs`（turn-structured 多輪 QA，S0 真正使用的版本）與 `.agents/skills/gemini-conversation-research/scripts/extract-gemini-conversation.mjs`（單一最大面板抓法，only 給「已完成 DR 報告」單獨抽取用，**非**多輪對話）同名並存——相對路徑 `scripts/extract-gemini-conversation.mjs` 在 skill 目錄脈絡下會誤解析到後者。**一律用根目錄絕對路徑**；後者已加棄用註記指回根目錄版。
- **turn 選擇器重複抓取（已修，cc-20260712）**：根目錄腳本原把 `model-response` 與其巢狀子元素 `.response-container` 塞進同一個 `querySelectorAll('qSel, rSel')` OR-list，導致每個 Model 回合被抓兩次（實測：87 turns 應為 29 user+29 model=58，逐位元組重複）。已修成每個角色只用「命中的那一個」selector（`pickSel` 回傳 selector 字串而非 NodeList），非把整個 OR-list 塞進同一個 query。**禁回退**：合併多個候選 selector 到同一個 `querySelectorAll` 呼叫（巢狀元素會被 OR-list 的不同分支各命中一次）。
- **背景分頁 timer 節流 → CDP timeout（已修，cc-20260712）**：根目錄腳本原缺 `page.bringToFront()`，多個 gemini.google.com 分頁同開時，非前景分頁的 `sleep()` 被 Chrome 節流，scroll-wait 迴圈實測連續兩次撞 puppeteer `Runtime.callFunctionOn timed out`（180s protocolTimeout）。加回 `bringToFront()` 後同一對話即時成功（14 turns / 24658 chars）。**禁回退**：拿掉 `bringToFront()` 呼叫。
- **agy `-p` 對 question/辯論型 prompt silent-no-op（0 bytes）**：命令式 trivial prompt（如 `PONG`）可跑,但問句/架構辯論型 prompt 靜默產 0 bytes（根因未診斷）。**cc-20260711 擴充**：從 Claude Code **非互動 session** 內 agy 更是 5 模式全敗（accept-edits 需 TTY／PTY 包裹不完成寫檔／`--print` no-op 且**無視 `--model`**，指 Pro3.1 仍跑 Flash）→ D1 獨立第二意見同樣別靠 agy，改 GitHub API 等確定性錨。**Mode B（E 軸架構辯論）禁回退用 `agy -p` 起 Gemini,走瀏覽器 CDP `:9333`**（`scripts/extract-gemini-conversation.mjs` 同引擎）。多分頁**必用確切對話 conv-id 鎖定**,別選「最後一個匹配 gemini 分頁」——會打到使用者其他對話（實測污染風險,turn count 是查污染的鐵錨）。**cc-20260712 擴充（根因補上,非單純 0 bytes）**：`--model` 無視的實際成因是呼叫語法錯——`agy --help` 確認 `--print`/`--prompt` 是互為別名的**吃值旗標**（`Run a single prompt non-interactively and print the response`），prompt 須緊跟 `--print` 之後；`dr-research-loop` 側 `runAgyFallback` 原本寫成 `--print --model <值> <prompt>`，讓 `--model` 卡位吃掉本該給 `--print` 的值，agy 收不到提示詞、回自我介紹交差。修正語法（`--print <prompt> --model <值>`）後，簡單問句能正確回應，但**對複雜生成任務（如完整卡片盒知識架構）agy 是當 agent 執行**：真內容寫進它自己的 `~/.gemini/antigravity-cli/brain/<session-id>/*.md` scratch 檔，`--print` 的 stdout 只回一份摘要 + `file://` 連結 + 反問後續動作，並非把生成內容整份吐回來（live 實測：5413 chars 完整卡片盒 prompt → stdout 摘要僅 1253 chars，解析摘要中的 `file://` 路徑讀真檔驗證為 16533 chars 合格全文）。**這解釋了為何「命令式 trivial prompt 可跑,問句/辯論型靜默 0 bytes」的舊觀察不完整**：agy 對複雜任務不是單純靜默失敗，而是把真輸出藏進 stdout 看不到的地方——若下游程式碼直接把 `output.trim()` 當正文，會誤判為「內容過短失敗」或更糟、悄悄存下摘要當正文。**若真要用 `agy -p` 起 Gemini 處理複雜生成任務，禁回退成只看 stdout 長度判斷成敗——須解析 stdout 內 `file://` 路徑讀真檔**；但本 skill 既有結論（走瀏覽器 CDP）對 Mode B 架構辯論這類即時互動場景仍優先，agy 檔案輸出模式較適合單次批次生成（如 dr-research-loop 的卡片盒 fallback）。

## Modules
- [modules/conversation-pipeline.md](modules/conversation-pipeline.md) — S0-S9 逐階段 how-to / checkpoint / 子代理 dispatch / AUP 隔離規則（Mode A 主線）
- [modules/browser-content-isolation.md](modules/browser-content-isolation.md) — Chrome 擴充功能 carrier 的 bounded metadata/file-sink recipe、guided button projection 與 canary regression gate
- [modules/mode-b-contextqa.md](modules/mode-b-contextqa.md) — Mode B（S-1 CONTEXT-LOAD + S0-ALT CONTEXT-QA + 資料主權過濾 + Mode B 啟動提示）
- [modules/first-principles-probe.md](modules/first-principles-probe.md) — 追問怎麼鑽到底（引用-鑽入 + 反向自陳 + first-principles 約分，抗放水；S1.5 + Mode B R2-4）
- [modules/guided-conversation-observation.md](modules/guided-conversation-observation.md) — Gemini contextual suggestion buttons / 自動提示問答 / 缺失資訊與 Domain term 修復的 state graph 程序
- [modules/production-guidance-hardening.md](modules/production-guidance-hardening.md) — GCR 對話進入小迴圈/計畫包/prototype/final repo 的 ROUTES contract、agy Gemini 3.6 Flash High replay 規則、末端神經感知與 promotion gate
- [modules/skill-bettor-port-map.md](modules/skill-bettor-port-map.md) — 本次從 antigravity 複製後的本地/外部/歷史來源路徑分級，防止目錄引用假本地化
- [modules/loop-panorama-ssot.md](modules/loop-panorama-ssot.md) — 閉環全景 + 迴圈判斷邏輯 + prompt 錨點（**改階段/prompt 前先讀**）
- [modules/retarget-map.md](modules/retarget-map.md) — northstar → antigravity retarget 映射 + 誠實拿掉了什麼
- [modules/downstream-landing.md](modules/downstream-landing.md) — **S9 後**下游落地驗證方法論（D1 DR 落地驗證→D2 架構設計→D3 gap 收斂→D4 prototype；多模型分工 + 確定性錨 + recipe-not-engine）

---
*port 自 northstar `.claude/skills/gemini-conversation-research/` v3.7.0（skill.md + 12 modules + 5 PG + playbook + evals，~2168 行）。**retarget 非原樣搬**：DR 引擎接 `automate.js`、反幻覺接 `external-verify`、Path B 接 `path-b-reduction`；KG 入庫 / dr-governance / Bug Scar 編號 / aup-guard hook / execution 腳本 **拿掉（無基座）**。完整帳本 → [modules/retarget-map.md](modules/retarget-map.md)。*
