# Module: repo-agent-native — antigravity → skill-bettor retarget 映射 + 誠實帳本

> 屬 [`repo-agent-native`](../SKILL.md)。本檔＝移植的命門與誠實帳本：哪些機制一對一映到 skill-bettor、
> 哪些因為架構前提不同被拿掉/降級、為何拿掉不是簡化。**這是 northstar→antigravity→skill-bettor 鏈的
> 第三環**——antigravity 版本身已對 northstar 版做過一次 retarget(見 antigravity 版自己的
> `modules/retarget-map.md`，記錄 northstar→antigravity 那一環，本檔不重抄，只承接 antigravity→
> skill-bettor 這一段)。

---

## 0. 本次 port 的起點事實(誠實記錄，非事後包裝)

寫本檔前，`ls /Users/neon/ts-skill-bettor/.claude/skills/repo-agent-native/` 已存在但**空目錄**(只有一個
`modules/` 空資料夾)——本次 port 是首次填入內容，非覆蓋既有版本。同時，`sdlc-plan-composer` 的 S-1 章節
與其 `modules/retarget-map.md` 已經**明確記錄** skill-bettor「沒有 `repo-agent-native` 這類自動不變量
抽取工具，是真實能力差距」，並把 S-1 降為手動盤點程序當暫代——本次 port 的目的正是把那個暫代升級為
真委派對象。這代表本檔完成後，`sdlc-plan-composer` 與另外三個已落地 skill
(`unknown-discovery-composer`／`harness-wiki`／`path-b-reduction`)裡「repo-agent-native 在 skill-bettor
無本地基座」的敘述**會變成過期陳述**——這不是本次任務要處理的範圍(任務明言不需要我自己去改
`sdlc-plan-composer`)，但誠實記錄在 §6 開放問題，供協調 session 核對。

## 1. 為何多數推理內容能逐字映(而非像 loop-harness-standard 那樣大改)

antigravity 版 `repo-agent-native` 本身已經是 northstar 版的一次 retarget，**核心推理紀律(9 階段／
三類不變量／破盒推論五步／OPBE／Evidence Level／source_ref 鐵律／8 條 implicit-design probe／
evaluator-first／RIP 封頂)在那一環就已經被驗證為「與平台無關」**，antigravity 版把它們原樣映過去了。
這次 skill-bettor port 面對的情況相同：這些是純推理框架，不依賴任何特定 KG／索引平台／host 矩陣，
`modules/extraction-methodology.md` 與 `modules/codebase-mastery-methodology.md` 因此**近乎逐字映**，
改動集中在兩處：① antigravity 專屬的 **sink 層**(KG 入庫)——**整支拿掉**；② antigravity 的兩個
cross-reference 目標(`repo-wiki-converge`／`repo-fullstack-debugger`)與 Specs-as-Code 層的一個餵軸
(`gemini-conversation-research`)——`repo-wiki-converge` 已在 2026-07-23 以
`.claude/skills/repo-wiki-converge/` 補成本地 port；另外兩項仍無本地基座，誠實標記缺口。

---

## 2. 逐機制 retarget 映射表

| antigravity 機制 | skill-bettor 對應物 | 為何這樣映／拿掉了什麼 |
|---|---|---|
| S3 INDEX：`python3 -m indexing.ingest_repodoc_cli <OUT>/invariants/<slug>/`(→ RepoDoc lane，`kind: invariants` frontmatter，可 `--embed` 進 ChromaDB `antigravity_repodocs` 集) | **不接入本 workflow**，S3 WRITE 直接寫 plain markdown 到 `docs/plans/<date>-<topic>/invariants/<slug>/<page>.md`，**檔案本身即產物** | skill-bettor 現有 `indexing/` RepoDoc lane，但本 skill 沒有被承認的 KG sink 消費契約；`rag-local` 也與本 repo 隔離。未有下游契約前自動入庫會產生第二份未受管轄的事實面。 |
| `<OUT>`＝中性 scratch 目錄(KG 中性暫存站，非 TARGET 內) | `docs/plans/<date>-<topic>/invariants/<slug>/`(**plan-scoped**，非中性暫存) | **設計理由(非簡化)**：現有 indexing lane 不是本 skill 的受承認消費者；現行下游是同一份計劃的 `sdlc-plan-composer` S-1。因此輸出直接落計劃目錄，這是 **KG-scoped → plan-scoped** 的邊界選擇，非對 `indexing/` 存在性的否認。 |
| Codebase Mastery 三檔輸出 `<TARGET>/.knowledge_base/{architecture_map,data_flow_and_api,security_and_bottlenecks}.md`(寫進 target repo 自己) | **依 target 類型二選一**：target 是 skill-bettor 家族 → `families/<family>/specs/{同三檔}.md`(family-local 常駐資產)；target 不是家族 → `docs/plans/<date>-<topic>/invariants/<slug>/specs/{同三檔}.md`(plan-scoped) | antigravity 原版把 mastery 規格寫進 target 自己，因為那是 target 的常駐資產。skill-bettor 沒有「target 自己的 repo」這個概念可寫(target 常常就是 skill-bettor 自己的一部分)，`families/<family>/` 是最貼近的等價物(家族架構規格是會被反覆諮詢的資產，理應跟著家族走)；非家族 target 才退回 plan-scoped。目錄名從 `.knowledge_base/`(dot-prefixed)改成 `specs/`(plain)，對齊 skill-bettor 沒有 dot-prefixed 內容目錄的既有習慣。 |
| `repo-wiki-converge`(Non-Overlap 對照表＋S0 SCOPE 的 wiki-seed hint) | **補成本地 port**：`.claude/skills/repo-wiki-converge/` owns L1 openwiki convergence; S0 SCOPE 可讀 `repo/[repo_name]/openwiki/` 當 candidate seed | 2026-08-04 起本地 L1 改走 langchain-ai/openwiki **官方**程序的 host-native 移植（無 agy、無 API key），並有 KG ingestion（`indexing.ingest_repodoc_cli`）。openwiki 可餵 SCOPE，但 load-bearing facts 仍要 repo-agent-native 回源碼複驗。 |
| `repo-fullstack-debugger`(Handoff on Persistent Black-Box) | **拿掉，改為指向內建 `diagnose`／`diagnosing-bugs`**，並明確標註「交棒後紀律會變」(通用重度除錯迴圈 vs 本 skill 的源碼級隱含依賴推導框架，兩者不是同一件事的改名) | skill-bettor **無此 skill**(`test -e` 確認不存在，見 §5)。全局可用的 `diagnose`／`diagnosing-bugs` 是最近替代，但誠實記錄：那是「heisenbug/性能回歸/反覆失敗」的重度診斷迴圈，不是「用已知事實破盒推論隱含依賴」的框架——交棒不是無縫升級，是換了一套完全不同的方法論。 |
| Specs-as-Code Step 3：`gemini-conversation-research` 迭代多 DR(S7 gap→S8 multi-DR→回 S7 重算 coverage，收斂上限 3 輪) | **條件式交棒**：只在外部引擎已受承認時使用；否則標 `⚠ 需人工二次確認`或單次 `research` | `gemini-conversation-research` 現已有本地 port，但其 live browser/DR 能力明文有 `external_engine_required` 邊界。skill 存在不等於引擎已可用。 |
| S2/S2.5 抽取工具鏈：`grepai_search`／`grepai_trace_callers/graph`(A-/B+ 級)、條件式 Serena LSP | **能力常駐，信任不升級**：GrepAI 當 semantic candidate finder；Serena 當常駐 LSP 上限；Python 候選再進 repo-bound、SHA-256 evidence-budget context pack；`rg`/Read/git 為定案主路 | 2026-07-29 實測：`.grepai/` 索引存在，semantic search 命中 normalizer，但 trace 漏 known caller；Serena 能找同檔 reference，但原設定只有 TypeScript 且漏跨檔 tests。本次已把 Python、只讀 9-tool policy 與 pinned revision收進版本控制，並移除可跨 repo 切換的 `activate_project`。context pack 明標 partial 且只支援 Python；三者輸出仍必須交叉核對，不得單獨宣稱 technical_equivalent／complete。 |
| Evidence Level A/B/C/D 分級語意 | **原樣映**(語意與底層工具無關) | 抽取工具換了(northstar→antigravity 那環已換過一次)，等級語意本身通用，不需要再改。 |
| S2.5 破盒推論五步／OPBE 三步／8 條 implicit-design probe | **原樣映**(純推理框架) | 平台無關，見 §1。範例從 ixsecurity/nats/gopush 換成 skill-bettor 本地可指的對象(`runner.py`／`engine.sh`／`agy` quota)，方法論字句不變。 |
| Empty-Output fail-loud contract(`extraction_failure_reason`＋SURFACE 標 `EMPTY_FAILED`) | **原樣映** | 純紀律，與 KG／host 矩陣無關。 |
| S4 AUDIT SURFACE(`a_ratio`／`unverified_count`，無機器閘) | **原樣映** | skill-bettor 同 antigravity 皆無 `hallucination_audit.py` 這類機器污染矩陣，人裁一致。 |
| S6/S8 漂移偵測(`git rev-parse HEAD` vs 頁面 `commit_hash`) | **原樣映** | 純 git 機制，不需要 KG 才能做。 |
| 雙平台(`.agents/skills/`＋`.claude/commands/` 薄轉發層)、`/specs-as-code` 薄 router command | **拿掉，單一 `.claude/skills/repo-agent-native/`**，Codebase Mastery 層直接是本 skill 的一部分，不另立第二入口 | skill-bettor 是 Claude-Code-only 單 host(CLAUDE.md 明文)，無 Antigravity CLI/Gemini host 需要雙平台轉發——與 `loop-harness-standard`／`judge-loop-chooser` 已定案的單 host 事實一致，不是本 skill 新拿掉的維度。 |
| antigravity 慣例引用「antigravity-skill-authoring」(見 antigravity 版 retarget-map 的 Sources/Lineage) | **改指向 Claude Code 內建 `write-a-skill`** | 同批次其他 port 的一致做法(sdlc-plan-composer/loop-harness-standard 等皆已改用內建 `write-a-skill`)；skill-bettor 是 Claude Code 平台自己的 skill 格式規範，非 Antigravity CLI 的 `.agents/skills/` 規範，兩者 frontmatter/封裝不同不可混用。 |
| `external-verify`／`path-b-reduction` cross-reference | **保留，指向本地 sibling** `.claude/skills/external-verify/`／`.claude/skills/path-b-reduction/` | 兩者本批次均已落地(`test -e` 確認，見 §5)，路由不需要改，只是指標從 antigravity 路徑換成本地路徑。 |
| （antigravity 版無此段，本次新增）與 `sdlc-plan-composer` 的 S-1 delegate 契約 | **新增整節**於 `../SKILL.md` §與 sdlc-plan-composer 的整合 | antigravity 原版沒有這個整合段，因為 antigravity 版 `sdlc-plan-composer` 本來就直接委派本 skill，關係是既定的。skill-bettor 版 `sdlc-plan-composer` S-1 目前還是手動盤點程序的暫代寫法，本次 port 需要**明確定義**輸入/輸出契約，供協調 session 日後接線核對(見 §6)。 |

---

## 3. 拿掉/降級的東西分三種情況，不是「簡化」

- **不引入不存在的架構前提(雙平台矩陣、`/specs-as-code` 獨立入口)**：skill-bettor 單 host 事實，
  loop-harness-standard/judge-loop-chooser 已立先例，不重新論證。
- **沒有基座、真實能力差距、誠實標記缺口**：目前只剩
  `repo-fullstack-debugger`(黑盒交棒)是缺席資產。`gemini-conversation-research` 與 `indexing/` 已存在，
  但各自的 external-engine/sink 邊界仍要受承認才能接入本 workflow。
- **新增本地 port，但非 antigravity 等價執行器**：`repo-wiki-converge` 現在存在，作用是 openwiki
  生成/驗證/瓶頸盤點；不代表 `kb-ingest`、agy-pass、KG ingestion 已移植。
- **活基座換掉、精神不變**：`grepai` 索引存在但必須每次核實健康與時效；Serena 依人裁常駐但維持只讀
  9-tool 上限；Python 候選可進 source-bound context pack；輸出落點從 `<OUT>` 中性暫存
  改成 `docs/plans/` plan-scoped(有明確設計理由，非隨意簡化，見 §2 表格與 `../SKILL.md` 內文)。

---

## 4. 為何 Codebase Mastery / Specs-as-Code 層決定保留(非默認省略)

任務要求對這層做出取捨判斷，理由記錄如下(供未來覆核)：
1. **方法論本身與 KG/host 平台無關**——4 步配方(SOURCE=SSOT 漏斗→8 probe→外部缺口處理→evaluator-first
   ＋RIP 封頂)全部是推理紀律，唯一觸碰 antigravity 專屬基座的只有 Step 3 的 `gemini-conversation-research`
   一環，其餘 100% 可映。
2. **skill-bettor 的 `repo-wiki-converge` 只補 L1 openwiki，不替代 L2 source-grounded extraction**：
   antigravity 語境下這層明言「不跟 repo-wiki-converge 競爭第二個 wiki」；skill-bettor 現在也維持
   這條邊界。wiki 是範圍/敘事種子，不是源碼事實裁決者。
3. **只有一處需要真降級(Step 3)**，且降級有現成先例可循(`unknown-discovery-composer` 已示範同一個
   「DR 迭代收斂 → 單次 research」降級模式)，不是要自己發明一套全新的權宜方案。
4. **不保留的代價 > 保留的維護成本**：這層唯一的活躍消費場景是「高風險 family-wide 整改前的深度審計」
   ——`ARCHITECTURE.md` §10 D2 就規劃了第一條真實演化 op(`refine repaint-detection`)，這類操作前跑一輪
   本層檢查（尤其 P2 determinism/P4 bounded-loop probe 直接對應 `judge.py`/`engine.sh` 的核心合約）
   是任務背景第 3 點要求的具體使用情境，不是空想的假設用途。

**優先序判斷**：核心 9 階段不變量抽取(SKILL.md 主體)是 S-1 的**主要**委派對象，日常 brownfield 判定
只需要它；Codebase Mastery 層是**選配深化**，只在高風險整改前才值得完整跑一輪——這個優先序已寫進
`../SKILL.md` 對應段落，避免被誤讀成「每次 S-1 都要跑三檔規格」。

---

## 5. 判別「retarget 成立」的鐵錨(本檔撰寫時逐一驗證)

**skill-bettor 側(已確認存在)**：
- `.claude/skills/{external-verify,path-b-reduction,fold-in,loop-harness-standard,harness-wiki,
  judge-loop-chooser,sdlc-plan-composer,unknown-discovery-composer,html-for-decisions,
  loop-harness-review-handoff}/` — `ls /Users/neon/ts-skill-bettor/.claude/skills/` 逐一確認存在。
- `families/pinescript-audit/...` 是源 repo 的 lineage，不是本 TypeScript mirror 當前實體：2026-07-29
  `test -e families` 為 false。舊版「`ls -R` 逐一確認存在」是錯誤敘述，已撤回；在本 checkout 不得拿它當
  worked instance 或 source anchor。
- `loop_wiki/engine.sh` 的 exit code 語意 — `grep -nE "exit (10|20|21|22|64)" loop_wiki/engine.sh` 確認
  `exit 10`(候選待人 admit)／`exit 20`(exhausted)／`exit 21`(no-progress)／`exit 22`／`exit 64`
  (usage error)皆存在(`die64()` 函數與對應行號)。
- `sdlc-plan-composer` S-1 章節明確記錄「沒有 `repo-agent-native` 這類自動不變量抽取工具，真實能力
  差距」——`grep -n "repo-agent-native" .claude/skills/sdlc-plan-composer/{SKILL.md,
  modules/retarget-map.md}` 確認多處引用，見 §0。
- `~/.claude/skills/{diagnose,diagnosing-bugs,write-a-skill}` 全局 skill 存在(session 可用 skill 清單
  已列出，本檔撰寫時亦確認 `diagnose`/`diagnosing-bugs` 出現在清單中)。

**skill-bettor 側(2026-07-29 重新審計)**：
- 仍不存在：`.claude/skills/repo-fullstack-debugger/`。
- 仍不存在：`families/`；`ARCHITECTURE.md` 的目錄圖與本 mirror 實體漂移，需獨立治理，不以本次 MCP
  落地暗示已修復。
- 現已存在：`.claude/skills/gemini-conversation-research/`、`.grepai/`、`indexing/`、`docs/`、
  `indexing/ingest_repodoc_cli.py`。這些是活基座，不得繼續引用 port 當時的 absence 結論。
- 現已存在：`mcp/context-pack/`，含官方 Python MCP SDK 精確鎖版、repo-bound Python evidence pack、
  單元／stdio 整合測試與並列 benchmark；它不替代源碼 body，也不提供 TypeScript context pack。
- `.grepai/` 為 gitignored 可再生狀態；實測 semantic search 可用，trace 不完整。每次使用前要驗 target/時效。
- `indexing/` 存在不等於本 skill 已受承認要入庫；本 skill 的現行 Output Contract 仍是 plan-scoped Markdown。
- `rag-local` 仍不是本 repo 的 sink；`indexing/store.py` 明文宣告與它隔離。

**antigravity 源側(已確認存在，供追溯)**：
- `.agents/skills/repo-agent-native/{SKILL.md,modules/{extraction-methodology,
  codebase-mastery-methodology,specs-as-code-prompt,retarget-map}.md}` — `test -e` 逐一確認。
- `.agents/skills/{repo-wiki-converge,repo-fullstack-debugger,gemini-conversation-research}/SKILL.md`
  — `test -e` 逐一確認在 antigravity 側存在；其中前者與後者現也已有 skill-bettor port，
  只剩 `repo-fullstack-debugger` 是真實落差。

---

## 6. 開放問題(留給協調 session 核對，非本檔可獨立解決)

1. **`sdlc-plan-composer` S-1 章節需要接線更新**：現行 S-1 §(b) 手動盤點五步、§(c) 反幻覺 SURFACE
   缺席、S-1 GATE 規則表消費「手動盤點條目(無 typed ID，散文格式)」——這三處在本 skill 落地後都有更好的
   委派對象：手動盤點五步 → 直接委派本 skill 的 9 階段核心管線；反幻覺 SURFACE 缺席 → 本 skill 的 S4
   AUDIT 產出 `a_ratio`/`unverified_count` 補上這道防線；GATE 表消費格式 → 可以改回引用真正的
   `INV-*`/`NEG-*`/`IMPL-*` typed ID(本 skill 產出這個格式，不再是「沒有工具支撐的偽造編號」)。**本檔
   只確保 §與 sdlc-plan-composer 的整合 那節的輸入/輸出契約寫清楚，實際接線改動留給協調 session**。
2. **`unknown-discovery-composer`／`harness-wiki`／`path-b-reduction` 三個已落地 skill 裡「repo-agent-
   native 在 skill-bettor 無本地基座」的敘述會變成過期陳述**——這三處目前都明確寫著「拿掉，退化為人工
   讀源碼/grep」或等價語句(見 §0)。本次任務範圍不包含修改這三個既有 skill，但誠實記錄這個連動效應，
   供未來一次性同批修正(避免多處各自零散更新造成新的漂移)。
3. **grepai 索引健康仍是執行期條件**：目前 `.grepai/` 存在不代表永久新鮮。呼叫者必須以
   `grepai_index_status` 或 `grepai status` 查 target、last update 與 scope；不健康就 fail closed 回 `rg`/Read。
4. **Codebase Mastery 層尚未有 skill-bettor 本地 worked instance**：如同 antigravity 版當初也沒有
   sandcastle 那樣的本地案例(見 antigravity 源 Sources/Lineage 段)，skill-bettor 版目前也還沒有第一次
   `specs/` 三檔輸出可以拿來當 answer-key 或驗證輸出格式是否好用。首次真實調用(可能是 `ARCHITECTURE.md`
   §10 D2 規劃的 `refine repaint-detection` 之前)即為本地首個 worked instance。

---

## Sources / Lineage
- antigravity 源：`/Users/neon/antigravity/.agents/skills/repo-agent-native/`(SKILL.md +
  `modules/{extraction-methodology,codebase-mastery-methodology,specs-as-code-prompt,retarget-map}.md`
  ，其中 `modules/retarget-map.md` 記錄的是 northstar→antigravity 那一環，本檔不重抄，只在 §1/§0 摘要
  引用其結論)。
- skill-bettor 既有同構：`ARCHITECTURE.md`(宣告的家族/loop_wiki 目錄契約，但 `families/` 在本 mirror
  缺席)、`CLAUDE.md`(root 被動上下文)、`loop_wiki/engine.sh`(RIP 載具與 P2/P4 probe 範例的真實素材)、
  `mcp/context-pack/`(本 repo 的 source-bound context adapter worked instance)。
- 同批移植先例(同一 rigor 要求，判斷邏輯沿用)：
  [`loop-harness-standard/modules/retarget-map.md`](../../loop-harness-standard/modules/retarget-map.md)、
  [`judge-loop-chooser/modules/retarget-map.md`](../../judge-loop-chooser/modules/retarget-map.md)、
  [`sdlc-plan-composer/modules/retarget-map.md`](../../sdlc-plan-composer/modules/retarget-map.md)
  (本檔要接線的下游消費者，§6 開放問題 1 的完整背景)、
  [`unknown-discovery-composer/modules/retarget-map.md`](../../unknown-discovery-composer/modules/retarget-map.md)
  (Step 3 降級判斷的先例來源，§2/§6 引用)。
