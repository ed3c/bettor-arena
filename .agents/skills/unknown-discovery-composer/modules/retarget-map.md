# Module: unknown-discovery-composer — antigravity → skill-bettor retarget 映射 + 誠實帳本

> 屬 [`unknown-discovery-composer`](../SKILL.md)。本檔 = 這次移植的命門與誠實帳本：哪些機制一對一映到
> skill-bettor、哪些因為架構前提不同被拿掉/降級、為何不是簡化。
> **不是**在複述 antigravity 版自己的 `modules/retarget-map.md`（那份記的是 northstar → antigravity
> 那一環，講的是「northstar 專屬下游被拿掉/antigravity 本地 fork 頂上」）——本檔是 lineage 鏈的**下一環**：
> antigravity → skill-bettor，起點是 antigravity 版已經 retarget 過一次的產物,不是 northstar 原版。

---

## 1. 為何不能逐字複製——antigravity 版的路由表繫在它自己一整組本地 fork 上

antigravity 版 `unknown-discovery-composer` 的 U1/U3 路由表，有 4 格指向 antigravity **自己的本地
fork**（`repo-agent-native`／`gemini-conversation-research`／`judge-loop-chooser`／`sdlc-plan-composer`），
其中 `judge-loop-chooser` 的可判物範例（DR 報告／Path-B 精煉／COMPLETENESS 覆蓋矩陣）本身又綁死
antigravity 的卡片盒 v6.6／`automate.js` 產物形態；另有 2 格指向 antigravity 專屬的量測/理解迴圈
（`truth-verify-loop`／`repo-wiki-converge`）。這些 fork 與迴圈 skill-bettor **完全沒有**——逐字複製
這張路由表，搬過來的會是一張指向不存在系統的死路由表。

真正可搬的是**這份 skill 的路由紀律本身**：四象限盤點 + 三時段路由 + recipe-not-engine + 人 admit
出口 gate。這套紀律與「路由到誰」正交，可以完整保留；需要換的只是「路由到誰」這一側的具體目標。

## 2. 逐機制 retarget 映射表

| antigravity 機制 | skill-bettor 對應物 | 為何這樣映 / 拿掉了什麼 |
|---|---|---|
| U1 出口 `sdlc-plan-composer`（antigravity 本地 fork，`.agents/skills/sdlc-plan-composer/`） | **retarget 為 skill-bettor 本地同批移植 sibling** `.claude/skills/sdlc-plan-composer/` | 本次批次移植的 7 個 composer skill 之一，同批落地；本檔只做「該不該交棒」的判斷，不預判其內容（其自己的 retarget-map 才是那份帳本），比 antigravity 版當時「northstar 專屬、無基座」的起點更乾淨——skill-bettor 一開始就有本地 sibling 可指。 |
| U1 KU 列 `repo-agent-native`（antigravity 本地 fork：源碼=SSOT，evidence-tagged 業務不變量抽取進 KB） | **（2026-07-11 更新，已補上）** 本地 `.claude/skills/repo-agent-native/`——9 階段抽取，輸出落 `docs/plans/<date>-<topic>/invariants/`，無 KG 入庫。本行原記錄「拿掉退化為人工讀源碼」已過期，見 SKILL.md 對應行與 repo-agent-native 自己的 retarget-map。 | 原判斷（無此基座、真實能力差距）在移植當下成立，同批稍後移植了它，此表僅補記更新，不删除歷史記錄。 |
| U1 KU 列 `repo-wiki-converge`（antigravity 專屬：Opus 判官 × Gemini 作者 judge-loop 產 repo wiki） | **拿掉，無替代** | skill-bettor 單 host（Claude Code），無跨模型 judge-loop 產 wiki 的既有機制；與 `repo-agent-native` 同一格被拿掉，兩者皆真實能力差距。 |
| U1 KU/UU 列「研究一個 Gemini 對話」`gemini-conversation-research`（antigravity 本地 fork，綁 `automate.js` DR 引擎 + AI Studio 對話管線） | **拿掉，無替代**；一般背景研究仍走 `research`（mattpocock 全局，未變） | skill-bettor 無 `automate.js`、無 YouTube/AI Studio 對話抽取管線。DR 研究批次改走 `agy` 直發（`ARCHITECTURE.md` §9「06:30 research」步驟），是大迴圈編排的一部分，不是透過 composer skill 路由——換了機制而非簡化同一機制。 |
| U1 KU/UU 列「post-cutoff 框架/能力 claim」（antigravity 原表把此半掛在 `gemini-conversation-research` 底下） | **retarget 為 skill-bettor 本地同批移植 sibling** `.claude/skills/external-verify/` | 讀過 antigravity `external-verify/SKILL.md` 後判斷：post-cutoff claim 查證是它的核心職能（官方 primary source 六步程序），跟「研究一個 Gemini 對話」的 DR 管線是兩件事、antigravity 原表把它們並列在同一格只是路由表的簡寫。skill-bettor 這次拆開兩者：DR 對話管線真無基座拿掉；claim 查證有本地同批 sibling 可直接指，比原表的並列更精確，不是新增能力。 |
| U1 KU 列「真相驗證/token-efficiency 量測」`truth-verify-loop`（antigravity 專屬量測迴圈：t0 工具鏈+合約+播錯集） | **claim 級真相驗證半拆給 `external-verify`（同上）；量測迴圈本體無替代** | skill-bettor 沒有對應的 token-efficiency 量測迴圈，也沒有播錯集方法論的既有實作。若真需要，得先用 `loop-harness-standard` 的 skill→小迴圈 recipe 從頭建一條，不是「重新發明」而是「本來就沒有」。 |
| U2「顯式棄跑（Path B）」引註 antigravity `truth-verify` 三個具體案例（BS1/3-majority/H4） | **拿掉具體案例引用，retarget 為本地既有紀律** [loop-harness-standard 八基座卡 #7](../../loop-harness-standard/SKILL.md)「判定式先於 run 落檔，不事後改」 | `path-b-reduction`/`truth-verify-loop` 兩個 skill 與其案例史都是 antigravity 自己的軌跡，skill-bettor 沒有；但「棄跑要顯式標記、不能事後改判定式遷就」這條紀律本身，skill-bettor 已經在 `loop-harness-standard` 的八基座卡第 7 條原生擁有——這格不是拿掉，是換一個本地真實存在的錨。 |
| U2「context 滿了要跨 session 交棒」→ 裸 `handoff`/`claude-handoff`（antigravity 已無 `fidelity-handoff` 形態決策+lint 閘） | **原樣承接同一降級狀態，非本次新降級** | antigravity 自己早就退化到裸 handoff（無覆蓋閘防漏 load-bearing negative）；本次移植只是把「已經降級過一次」的狀態原樣搬過來，不重新論證。 |
| U3「產物判準」`judge-loop-chooser`（antigravity 本地 fork，可判物 = DR 報告／Path-B 精煉／COMPLETENESS 覆蓋矩陣） | **retarget 為 skill-bettor 本地同批移植 sibling** `.claude/skills/judge-loop-chooser/`；antigravity 的三類可判物範例**不預先假設 skill-bettor 有對應** | 同批移植、我不控制其內容或最終落地時間。已讀過 antigravity 源版 `judge-loop-chooser/SKILL.md`：其可判物完全綁死 antigravity 卡片盒/`automate.js` 產物形態，skill-bettor 沒有這些產物；skill-bettor 自己夠格的可判物候選是 family eval 報告／holdout 畢業判／`llm_judge` checks（`ARCHITECTURE.md` §4），但這是 `judge-loop-chooser` sibling 自己要處理的映射，本檔只指路由指針、不越權替它預判內容。 |
| U3「代碼產物 → `code-review`」+ STOP 表「judge-loop-chooser 明言無 code-branch」 | **原樣映**，措辭改為「skill-bettor 同批移植 sibling 承此現況」 | 讀過 antigravity `judge-loop-chooser` 的不變量 #5「無 code-branch」是其自身明文條款；同批移植大概率原樣帶過去（除非該 sibling 的 retarget-map 另有決定，那不是本檔能預判的）,措辭上只標「承現況」不斷言「保證如此」。 |
| `superpowers:brainstorming` / `superpowers:writing-plans`（Claude Code plugin 級 skill） | **2026-07-17 retarget：拿掉理論性 fallback，改指 mattpocock 真實技術等價物** `grilling`（brainstorming 等價，一次一問+推薦答案技術一致）／`to-prd`+`implement`（writing-plans 等價，無需訪談直接 synthesis PRD→執行） | 2026-07-11 移植當下已查證 `~/.claude/settings.json` 的 `enabledPlugins` 無 `superpowers-marketplace` 鍵，`~/.claude/plugins/marketplaces/superpowers-marketplace/` 也只是市集索引非啟用證據——確認未啟用（見下方 §4）。antigravity 同日（2026-07-17）已完成同一步 retarget（見其 `unknown-discovery-composer/modules/retarget-map.md`），本檔比照結論、不重新查證。原始 superpowers 版文字封存於 `~/.claude/plugins/cache/superpowers-marketplace/superpowers/6.1.1/skills/{brainstorming,writing-plans}/`（唯讀參考，非路由目標）。 |
| 其餘 mattpocock 全局路由（`zoom-out`／`teach`／`research`／`wayfinder`／`grilling`／`grill-me`／`grill-with-docs`／`loop-me`／`prototype`／`design-an-interface`／`improve-codebase-architecture`／`diagnose`／`diagnosing-bugs`／`to-prd`／`writing-shape`／`edit-article`／`qa`／`ask-matt`／`code-review`） | **原樣映，無需 retarget** | 全部經 `~/.claude/skills/<name>` 符號連結，與 project 無關；本次移植逐一 `ls` 驗證 18 個名稱全存在於 disk（見 §4）。 |
| `grill-with-docs`「沉澱 ADR/glossary」的無編號決策記錄降級 | **原樣映**（skill-bettor 同樣無編號 ADR/DDR 系統） | `ARCHITECTURE.md`/`CLAUDE.md` 全篇無編號決策系統，只有 `families/<family>/changelog/`（日期式紀錄）；antigravity 早已做過的「拿掉編號、留散文紀律」對 skill-bettor 同樣成立，且補上本地對應落點指針。 |
| YAML frontmatter（無 skill-conformance-hub `liveness`/`grounding` 治理欄位） | **原樣映（不變）** | antigravity 版本身就沒有這套治理欄位（northstar → antigravity 那一環已拿掉）；skill-bettor 同樣沒有 skill-conformance-hub，這格是「兩邊都沒有」的無操作，不算本次移植新降級的內容，僅為完整性記錄於此。 |
| SSOT 路徑 `.agents/skills/`（antigravity：Google Antigravity CLI skill 目錄規範） | **retarget 路徑寫法為 `.claude/skills/`** | skill-bettor 是 Claude-Code-only，skill 目錄本來就是 `.claude/skills/`，不是 antigravity 的 `.agents/skills/`——純粹是平台規範差異（同任務書提到的 antigravity-skill-authoring vs write-a-skill 那類差異的姊妹版本，只是這裡是路徑而非 skill-authoring skill 本身；本 skill 未引用 `antigravity-skill-authoring`，故無需替換為 `write-a-skill`）。 |

## 3. 拿掉的東西不是「簡化」，而是「不存在對應本地 fork/迴圈」

- **能一對一映的映**：U0-U3 路由紀律骨架（四象限盤點、起跑點披露、pivot 迴路、quiz 人理解閘、
  出口 gate 的「人 admit」結構）、全部 mattpocock 全局路由、`grilling`/`grill-with-docs` 系列的既有
  降級措辭、frontmatter 精簡風格。
- **有本地同批 sibling 可換的換**（4 格）：`sdlc-plan-composer`／`judge-loop-chooser`／`external-verify`
  三個下游交棒點換成本地 `.claude/skills/` sibling；U2「棄跑不改判定式」換成本地
  `loop-harness-standard` 八基座卡 #7 的既有紀律。
- **無本地基座、真實能力差距、誠實拿掉並記錄**（原 4 格，2026-07-11 起剩 3 格——`repo-agent-native`
  已於同批稍後補上本地移植，見上表更新行）：`repo-wiki-converge`（Opus 判官 × Gemini 作者 wiki）、
  `gemini-conversation-research`（DR 對話管線）、`truth-verify-loop`（token-efficiency 量測迴圈本體）。
  這三項不是「skill-bettor 選擇不做」，是
  「skill-bettor 現階段（單家族、單 host、無跨模型量測迴圈）根本沒有對應的機器」。
- **antigravity 自己已經做過的降級、原樣承接**：`fidelity-handoff` → 裸 `handoff`/`claude-handoff`
  （這是 northstar → antigravity 那一環的降級，本次只是不重新論證地帶過來）。

## 4. 判別「retarget 成立」的鐵錨

驗證於 2026-07-11，本次移植現場執行：

- **mattpocock 全局符號連結全存在**（`ls -la ~/.claude/skills/` 逐一核對，18 個路由目標
  `zoom-out`/`teach`/`research`/`wayfinder`/`grilling`/`grill-me`/`grill-with-docs`/`loop-me`/
  `prototype`/`design-an-interface`/`improve-codebase-architecture`/`diagnose`/`diagnosing-bugs`/
  `to-prd`/`writing-shape`/`edit-article`/`qa`/`ask-matt`/`code-review`/`handoff`/`claude-handoff`
  均為有效符號連結）。
- **（2026-07-11 補驗，確認為「未啟用」而非僅「未驗證」）`superpowers:brainstorming`/
  `superpowers:writing-plans`**：`~/.claude/settings.json` 的 `enabledPlugins` 字典**逐一列出**所有
  已註冊 plugin 的啟用狀態（`rust-analyzer-lsp`/`swift-lsp`/`skill-creator`/`claude-md-management`/
  `code-simplifier`/`claude-code-setup`/`agent-skills`/`understand-anything`），**完全沒有
  `superpowers-marketplace` 或任何 `superpowers` 鍵**——即使 `~/.claude/plugins/cache/
  superpowers-marketplace/superpowers/{4.1.1,5.1.0,6.1.1}/skills/` 底下確實快取了展開後的 skill
  內容（曾被安裝過或曾被其他專案啟用），此 repo 的有效設定裡它**未被列為啟用 plugin**。
  `~/.claude/plugins/marketplaces/superpowers-marketplace/` 也只是市集索引（`README.md`+
  `marketplace.json`），非啟用證據。**結論：確認未啟用，非僅「未驗證」**。2026-07-17 據此結論拿掉
  理論性 fallback 路由，改指 mattpocock 真實技術等價物 `to-prd`+`implement`（writing-plans）／
  `grilling`（brainstorming），不再保留 superpowers 路由，見上表第 37 列。
- **skill-bettor 本地同批移植 sibling 尚未落地**（`ls /Users/neon/ts-skill-bettor/.claude/skills/`
  於本次移植當下只見 `harness-wiki`/`loop-harness-standard`；`sdlc-plan-composer`/
  `judge-loop-chooser`/`external-verify`/`fold-in`/`html-for-decisions`/
  `loop-harness-review-handoff` 六個 sibling 皆為「同批平行移植中，尚未落地」——依任務指示視為
  真實將存在的 sibling，路由指向這些目標路徑，但不假裝現在就能 `ls` 出來）。
- **antigravity 源版事實**（供本表核對用，非 skill-bettor 本地事實）：`repo-agent-native`／
  `gemini-conversation-research`／`judge-loop-chooser`／`sdlc-plan-composer`／`truth-verify-loop`
  在 antigravity `.agents/skills/` 下均存在；`fidelity-handoff` 不存在（已被 antigravity 自己拿掉，
  `find` 確認缺席）；`judge-loop-chooser/SKILL.md` 不變量 #5 明文「無 code-branch」；
  `external-verify/SKILL.md` 核心程序是官方 primary source 六步查證,與「研究 Gemini 對話」的 DR
  管線無關。

若哪天有人往本 skill 塞回 `repo-wiki-converge`/`gemini-conversation-research`/`truth-verify-loop`
 的具體路由（在 skill-bettor 真的建出對應本地基座之前——`repo-agent-native` 已於 2026-07-11 補上，
不在此擋列），或把 `.agents/skills/`
路徑寫法搬回本檔，或把 `superpowers:*` 引註塞回 U1 路由表，那就是把不存在的架構前提/已拿掉的死 husk
搬回來——擋下。

---

## Sources / Lineage
- antigravity 源：`/Users/neon/antigravity/.agents/skills/unknown-discovery-composer/`（SKILL.md +
  `modules/retarget-map.md`，記 northstar → antigravity 那一環，本檔不重抄）。
- antigravity 下游 fork（讀取以確認拿掉/換掉是否成立）：
  `/Users/neon/antigravity/.agents/skills/judge-loop-chooser/SKILL.md`、
  `/Users/neon/antigravity/.agents/skills/external-verify/SKILL.md`、
  `/Users/neon/antigravity/.agents/skills/gemini-conversation-research/SKILL.md`。
- skill-bettor 既有同構：`ARCHITECTURE.md`（三層飛輪/家族結構/tier-dispatch）、`CLAUDE.md`
  （鐵律/核心指令）、`.claude/skills/loop-harness-standard/SKILL.md`（八基座卡 #7 = U2 棄跑紀律的
  本地錨）、`.claude/skills/harness-wiki/`（同批移植的姊妹範例，本檔遵循其 retarget-map 格式）。
- 同批平行移植 sibling（目標路徑，移植當下尚未落地，依任務指示視為將存在）：
  `.claude/skills/{sdlc-plan-composer,judge-loop-chooser,fold-in,html-for-decisions,
  loop-harness-review-handoff,external-verify}/`。

## 2026-07-19 增補(composer-integration Slice E 接線)

- U2 表插「斷言級證偽→execution-feedback 勾稽表→plan-delta 人閘」列、U3 表插「斷言級勾稽
  judge-verdict 比 quiz 更硬」列——對齊 antigravity 同名 skill :122/:134(其 slice 02 執行
  DELTA-2 KEEP 落的兩列),路徑指本地 `.claude/skills/loop-harness-standard/modules/
  execution-feedback.md`(2026-07-19 同批遷入)。首列尾注補「留給非斷言級小偏離」分工語。
  只指針不內嵌勾稽表 schema。


## 2026-07-22 增補：stateful workflow 主流程修復

本次修改不改 antigravity → skill-bettor 的 retarget 事實，也不新增下游能力。修復點是 `SKILL.md` 的資訊層級：舊版把 U0-U3 路由表、lineage、平台差異、能力差距同時放在主流程，讓 agent 容易把 skill 當成單一大 prompt 或歷史帳本來讀，而不是按狀態節點執行。

新主檔把 load-bearing 程序提升為 Match／Generate／Validate state graph：`M0 classify_fog`、`G0 disclose_startpoint`、`G1 quadrant_inventory`、`M1 route_match`、`G2 route_packet`、`V2 route_gate`、`H1 human_admit`、`M2 phase_transition`。`modules/retarget-map.md` 繼續作移植與能力差距帳本，只在路由目標真實性或 lineage 影響當前判斷時讀取。

同時接入 `judge-loop-chooser`／`skill-authoring` 已立的語意真相契約：skill 本文與 route packet 產物都必須讓 fresh LLM 不靠原對話也能判斷目標、證據、grounding、actor、validator、human admit、failure edge；不得留下 `Opus or Codex or agy`、`as needed`、`適當驗證` 這類未裁決語。
