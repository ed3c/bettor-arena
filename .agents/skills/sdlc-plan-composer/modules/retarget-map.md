# Module: sdlc-plan-composer — antigravity → skill-bettor retarget 映射 + 誠實帳本

> 屬 [`sdlc-plan-composer`](../SKILL.md)。本檔＝移植的命門與誠實帳本：哪些機制一對一映到
> skill-bettor、哪些沒基座被拿掉/降級、為何不是簡化。**本移植是 northstar → antigravity → skill-bettor
> 這條鏈的第三環**，其中 S-1 帶一層本次獨有、比前一環更深的降級。

---

## 0. Lineage 摘要（northstar → antigravity 那一環，不重新評估）

antigravity 版 `sdlc-plan-composer` 已經把 northstar 專屬治理基座拿掉一次：`hallucination_audit.py`
機器閘（降為 SURFACE）、`provenance.yaml`/`cross-repo-topology.yaml`/`registry.yaml`（併入單一不變量
頁）、`fidelity-handoff`（退化裸 `handoff`）、
encd-infrastructure-hub/skill-cycle 整合接點（無此編排層）、`task-graph-decomposer` 模型路由（改獨立性
tier）、編號 ADR 系統（改散文決策記錄）。**這些「antigravity 也沒有」的東西，skill-bettor 自然也沒有
——不重新評估、不重新論證，直接沿用 antigravity 版已經做過的判斷**（詳見
`/Users/neon/antigravity/.agents/skills/sdlc-plan-composer/modules/retarget-map.md`，該檔記錄的是
northstar→antigravity 那一環，僅供追溯脈絡，不是本檔要重抄的內容）。`autoresearch-composer`（優化迴圈
委派）原本也在這個「沒基座」清單裡，但 2026-07-17 antigravity 與 skill-bettor 已同日補上本地 fork，見
§5 開放問題第 2 條與下表 S5 該行。

本檔只記錄 **antigravity → skill-bettor** 這一環新增的差異，核心是 §1 的 S-1 二層降級。

---

> **⚠ 本節已被 2026-07-11 同批稍後的移植部分超越**：`repo-agent-native` 已補上本地移植版
> （`.claude/skills/repo-agent-native/`），S-1 已改回委派它，§2 表格第一列的「拿掉，無替代 delegate」
> 判斷已過期。本節保留**原樣**（不刪除、不改寫歷史判斷）當作「兩層降級疊加曾經真實存在過」的完整
> 記錄——這段推理過程本身有價值（示範「委派對象消失時如何誠實記錄能力差距，而非假裝不適用」）。
> **現況以 SKILL.md §S-1 為準**：委派為主路徑，本節描述的手動盤點程序降為該路徑不可用時的 fallback。

## 1. 為何 S-1 是本次移植的最高判斷點——兩層降級疊加（歷史記錄，見上方超越說明）

northstar 原版：`repo-agent-native` 委派靠**機器閘**（`hallucination_audit.py`）+ 三個獨立 YAML
（`invariants.yaml`/`cross-repo-topology.yaml`/`hallucination-ledger.yaml`）。

antigravity 版（第一層降級）：機器閘降為 SURFACE（`a_ratio`/`unverified_count` 一行，人裁）；三個 YAML
併成一頁多條目（`INV-*`/`NEG-*`/`IMPL-*`）；**但抽取本身依然自動**——antigravity 有真本地 fork
`repo-agent-native`，跑 9 階段（SCOPE→INGEST→INVARIANT→IMPLICIT-DEP→INDEX→AUDIT→SSOT→FEEDBACK），
用 grepai/ripgrep/Serena 做四層精準度抽取，每條事實仍有 Evidence Level(A/A-/B+/B/C/D) 分級。

skill-bettor（第二層降級，本次移植獨有）：**連這個委派對象都不存在**。skill-bettor 沒有 grepai 業務
不變量索引管線、沒有 Evidence Level 分級工具、沒有 source_ref 強制鐵律的任何機制。S-1 從「委派另一個
skill 做自動抽取」整個降為「本檔內建的人工盤點程序」——**這不是 antigravity 已經降過一次之後的又一次
簡化，而是同一維度上更深一層的真實能力差距**：antigravity 版還能保證「至少有工具跑過、有 Evidence
Level 分級、有 absence 的機械確認」；skill-bettor 版**唯一的防線是計劃撰寫者自己有沒有認真讀
`SKILL.md`/`FAMILY.yaml`/`shared/`/`evals/`**。誠實記錄這一點，不偽裝成「brownfield 概念在 skill-bettor
不適用」（brownfield 規劃任務在此 repo 絕對會發生，見 SKILL.md §S-1(a) 判據）。

## 2. 逐機制 retarget 映射表

| antigravity 機制 | skill-bettor 對應物 | 為何這樣映 / 拿掉了什麼 |
|---|---|---|
| S-1 委派 `repo-agent-native`（antigravity 本地 fork，9 階段自動抽取，Evidence Level 分級，單一不變量頁 `INV-*`/`NEG-*`/`IMPL-*`） | **拿掉，無替代 delegate**——降為 SKILL.md 內建的「手動盤點五步」（讀家族 `SKILL.md`/`FAMILY.yaml`/`shared/conventions.md`+`shared/glossary.md`/grep `evals/cases`+`evals/holdout`/grep `loop_wiki/engine.sh`） | skill-bettor 沒有任何自動不變量抽取工具鏈（無 grepai 業務索引、無 Evidence Level 分級器）。這是本移植**最深的一層真實能力差距**，見 §1。手動盤點的五個目標選得對應 antigravity 三類條目的最近親替代：家族 `SKILL.md`＝API 合約類比 `INV-API-*`；`shared/conventions.md`＝顯性契約類比 `INV-Message-*`；evals fixtures＝behavioral 契約類比 `IMPL-*`/planted-defect。 |
| S-1(f) 反幻覺 SURFACE：`a_ratio`/`unverified_count` 一行（repo-agent-native 自己的 S4 AUDIT 產出） | **連這道 SURFACE 都沒有**，改為人工在每條盤點條目後標 `(unverified，未讀源碼，僅印象)` | 這個 SURFACE 本身是 repo-agent-native 工具鏈的產出物；工具鏈不存在，SURFACE 也就無法自動產生，只能靠撰寫者手動標注——比 antigravity 更弱一層的誠實防線。 |
| S-1 GATE 表消費 `INV-*`/`NEG-*`/`IMPL-*` typed 條目 | **改消費手動盤點條目**（無 typed ID，用「檔案路徑:行號/段落 — 內容 — 信心」的散文格式） | 沒有工具產出 typed ID，只能用散文格式記錄；GATE 判準邏輯（否證/對齊/垂直切片/介面不撞約）精神保留，只是「引用什麼」換了形態。 |
| S-1 引用慣例 `INV-*`/`NEG-*`/`IMPL-*` 前綴格式 | **拿掉**，改用檔案路徑+行號的自然語言引用 | 沒有 ID 系統可維護，強行編號=偽造沒有工具支撐的機器可讀假象。 |
| S5 委派 `judge-loop-chooser`（antigravity 本地 fork，四分支：DR報告/COMPLETENESS矩陣/技術選型fit/code-review、四層獨立性階梯 T0-T3） | **retarget 為 skill-bettor 本地移植版**（同批平行移植，`.claude/skills/judge-loop-chooser/` 撰寫本檔時**尚未落地**）——分支語言依 ARCHITECTURE.md §4/§5 推斷換成：family eval report/G1-G5 gate（T0 機械）、holdout 畢業判（semantic fresh subagent）、技術選型 fit（沿用）、code-review（沿用） | judge-loop-chooser 本身正在同批移植，本檔只能**推斷**其落地後的分流語言，已在 SKILL.md §S5 明確標注「推斷非核實」並留一個回頭核對的待辦（見 §5）。 |
| S5「代碼產物→直接 `code-review`」 | **原樣映，路由不變**——`code-review` 已確認是 skill-bettor 本地 session 一級可用 skill | 不需要 retarget，路由目標本來就同時對 antigravity 和 skill-bettor 可用。 |
| S0「掃 `~/.agents/skills/` + 本 repo `.agents/skills/`」 | **retarget 為「掃 `~/.claude/skills/`（mattpocock 全局）+ 本 repo `.claude/skills/`（composer skills）+ `families/*/SKILL.md`（家族路由器）」** | 目錄命名平台差異（`.agents` → `.claude`，Claude Code 原生慣例）；**新增第三項**——skill-bettor 有 antigravity 沒有的「業務資產目錄」層（`families/`），S0 查重若不掃這層，會漏掉「其實某家族子技能已經解過類似問題」的重造風險。 |
| S3「決策記錄稀疏三條件 → `docs/decisions/<slug>.md`」 | **原樣映**（skill-bettor 同 antigravity 皆無編號 ADR 系統） | 平台/repo 無關的紀律，antigravity 已經做過這次 retarget（northstar 編號 ADR → 散文），skill-bettor 沿用同一結論，不重新論證。 |
| S4 delegate `superpowers:subagent-driven-development`/`superpowers:dispatching-parallel-agents` | **2026-07-17 retarget：拿掉理論性 fallback，改指 Claude Code 原生 `Agent`/`Workflow` 工具 ＋ `codex:codex-rescue`（OpenAI）＋既有 `agy`（Gemini）三個 backend，人工三選一** | 2026-07-11 驗證過 marketplace/cache 有快取但未列於可用 skill 清單（見下方 §4 舊記錄）；不再等待驗證，直接對齊 antigravity 同日 retarget 結論——這兩個 superpowers skill 教的「怎麼手動 dispatch subagent」現在是 harness 原生能力，且 skill-bettor 已有成熟 `agy`/`codex` 派工慣例（`ARCHITECTURE.md` §5 tier-dispatch），不需要理論性 plugin 依賴。 |
| S5「`handoff` 前自查有無漏 load-bearing negative（antigravity 無 `fidelity-handoff` 覆蓋閘，裸 handoff 靠自律）」 | **原樣映，沿用同一舊差距**——不重新論證，也不是本次新增的降級 | 這格是 northstar→antigravity 那一環已經記錄過的差距；skill-bettor 沒有更好或更差的等價物，直接繼承同一句話，避免誤植成「本次移植又發現一個新缺口」。 |
| S5「優化迴圈委派 `autoresearch-composer`」 | **2026-07-17 更新：已港補齊**——`.claude/skills/autoresearch-composer/SKILL.md` 本地 fork 落地，S5 該行改指回它 | §5 開放問題第 2 條記錄的「潛在重新評估點」今日兌現：外部 autoresearch 引擎（`~/.claude/commands/autoresearch/`）確認全局裝、非 project-scoped，一直可用，缺的只是 northstar 那層路由/讓位/契約注入邏輯——今日把該邏輯 port 進來（直接參照 antigravity 同日 retarget 版本，非重新從 northstar 原檔推導），逐機制映射見 `autoresearch-composer/modules/retarget-map.md`（本表不重複，指針即可）。 |
| 「整合接點：不經任何編排層」 | **原樣映**（skill-bettor 同 antigravity 皆無 ENCD/skill-cycle） | 無需 retarget。 |
| Output Contract `docs/plans/<date>-<topic>/` + `implement/`/`fold-in/` diff 鏡像約定 | **原樣映**（平台/repo 無關的目錄契約，`ARCHITECTURE.md` 目前未列 `docs/`，但本 skill 本來就是要新引入這個計劃輸出慣例，同 antigravity 當初引入時一樣是新增而非既有） | 純方法論，無 host/driver 依賴；`fold-in/` 鏡像引用改指本地 `fold-in` skill（同批移植中）。 |

## 3. 拿掉的東西不是「簡化」，而是「不存在對應工具/尚未落地/沿用舊差距」三種情況分開記

- **本次移植獨有的真實能力差距（新增，比 antigravity 更深）**：S-1 自動抽取整個拿掉，降為手動盤點程序；
  連 SURFACE 反幻覺這道最後防線都沒有，只能人工標 `(unverified)`。這是本檔的核心誠實帳目。
- **同批平行移植、暫時推斷、非核實**：S5 judge-loop-chooser 的分支語言——不是「拿掉」，是「還沒落地
  所以只能猜」，已標記待回頭核對（§5）。
- **沿用 antigravity 已經記錄過的舊差距，非本次新增**：`fidelity-handoff` 覆蓋閘缺席、
  編號 ADR 系統缺席、ENCD/skill-cycle 整合接點缺席——這些在
  antigravity 版就已經是「無基座」，skill-bettor 沒有比 antigravity 更好或更差，直接繼承，不重新評估。
  `autoresearch-composer` 曾在此列，2026-07-17 已補齊，見 §5。

## 4. 判別「retarget 成立」的鐵錨

本次 port 逐一 `test -e`/`ls` 驗證過：

- 本地活基座：`loop_wiki/engine.sh`（含 `exit 10/20/21/22/64` 與 stop-loss 門檻註解，已用
  `grep -nE "exit (10|20|21|22|64)|no-progress|exhausted"` 驗證存在）、`loop_wiki/_template/`。
- 本地 worked instance：`families/pinescript-audit/{SKILL.md,FAMILY.yaml,shared/conventions.md,
  shared/glossary.md,evals/cases,evals/holdout}` 全部存在於 disk。
- mattpocock 全局 skill：`~/.claude/skills/{grill-with-docs,grill-me,to-prd,to-issues,tdd,diagnose,
  design-an-interface,improve-codebase-architecture,handoff,claude-handoff,implement,write-a-skill}`
  均以 `test -e` 驗證存在。
- `superpowers:*`：`~/.claude/plugins/marketplaces/superpowers-marketplace`（marketplace 註冊目錄）+
  `~/.claude/plugins/cache/superpowers-marketplace/superpowers/6.1.1/skills/{subagent-driven-development,
  dispatching-parallel-agents,writing-plans,brainstorming}/SKILL.md`（快取內容）均存在，但 2026-07-11
  查證 `~/.claude/settings.json` `enabledPlugins` 無 `superpowers-marketplace` 鍵——**確認未啟用**。
  2026-07-17 據此拿掉全部理論性 superpowers 路由（S4 兩處＋SKILL.md「Not For」與邊界段的
  writing-plans/brainstorming），改指 mattpocock 真實等價物與 harness 原生能力，不再保留「未現場驗證」
  的持有狀態。
- 同批移植 sibling：撰寫本檔當下，`ls /Users/neon/ts-skill-bettor/.claude/skills/` 只有
  `loop-harness-standard`/`harness-wiki` 兩個已落地；`judge-loop-chooser`/`unknown-discovery-composer`/
  `fold-in`/`html-for-decisions`/`loop-harness-review-handoff`/`external-verify` 六個尚未落地——本檔
  §S5 的分支語言、`unknown-discovery-composer`/`fold-in` 的邊界引用皆已標記「同批移植中，落地後互相
  核對」，不假裝已核實。

若哪天有人往本 skill 塞回 antigravity 具體的 `INV-*`/`NEG-*`/`IMPL-*` typed ID 引用格式、假裝
skill-bettor 有 Evidence Level 分級工具、或把 S-1 寫成「brownfield 不適用」而非「無工具、真實差距」，
那就是把不存在的能力搬回來，或把誠實的能力差距偽裝成設計選擇——擋下。

## 5. 開放問題（留給後續核對，非本檔可獨立解決）

1. **（已核對，2026-07-11）judge-loop-chooser 落地**：其 D1-D4 deliverable 表與本檔原推斷大致一致
   （family eval report/G1-G3→D1、holdout 畢業判→D2、code-review 分工→一致），**但技術選型
   fit-to-plan／5-axis 分支judge-loop-chooser 並未落地**（其 retarget-map 記為刻意範圍縮減：
   skill-bettor 目前無「該不該採用某 OSS 堆疊」決策需求）。SKILL.md §S5 已改用 D1-D4 實際分類詞彙並
   移除該分支，此項已解決。
2. **（已解決，2026-07-17）`autoresearch` 系列在 skill-bettor session 實際可用**：確認外部 autoresearch
   引擎全局裝於 `~/.claude/commands/autoresearch/`（非 project-scoped），與 S5「優化迴圈委派無基座、誠實
   留白」的既有判斷之間的張力已兌現重新評估——2026-07-17 使用者明確要求把 `autoresearch-composer`
   （northstar/antigravity 專屬 composer 名，非泛指整個 autoresearch 系列）港進來，`.claude/skills/
   autoresearch-composer/` 已落地，`sdlc-plan-composer` S5 已改指回它。此項已解決。
3. **（已核對，2026-07-11）`unknown-discovery-composer` 落地**：其 SKILL.md 確實把 U1 多階段任務出口
   指回本 skill（`.claude/skills/sdlc-plan-composer/`），單階段當時仍走 `superpowers:writing-plans`，與
   本檔假設一致；**2026-07-17 兩檔同步 retarget 為 `to-prd`+`implement`**，此項已解決。
4. **（已解決，2026-07-17）S4/writing-plans/brainstorming 的 superpowers 理論性路由全數拿掉**：比照
   antigravity 同日 retarget 結論（`installed_plugins.json`/`enabledPlugins` 皆確認未啟用），S4 改指
   Claude Code 原生 `Agent`/`Workflow` 工具 + codex + agy 三 backend（見 §2 表與 SKILL.md 該行）；
   writing-plans → `to-prd`+`implement`；brainstorming → `grilling`。

---

## Sources / Lineage

- antigravity 源：`/Users/neon/antigravity/.agents/skills/sdlc-plan-composer/`（SKILL.md +
  `modules/retarget-map.md`，記錄的是 northstar→antigravity 那一環，本檔不重抄，只在 §0 摘要引用）。
- skill-bettor 既有同構：`ARCHITECTURE.md` §4（Verify 三層）、§5（tier-dispatch）——S5 判官分支語言的
  推斷依據；`families/pinescript-audit/`——S-1 手動盤點五步的真實 worked instance。
- 同批移植先例（本次任務的直接參照範例，非本 skill 的委派對象）：
  [`loop-harness-standard/modules/retarget-map.md`](../../loop-harness-standard/modules/retarget-map.md)、
  [`harness-wiki/modules/retarget-map.md`](../../harness-wiki/modules/retarget-map.md)。
- 下游委派目標（同批移植，已落地並於 2026-07-11 完成核對）：
  `.claude/skills/judge-loop-chooser/`、`.claude/skills/unknown-discovery-composer/`、
  `.claude/skills/fold-in/`。

---

## 2026-07-19 增補:S6′ 執行反哺+oracle-tier frontmatter(composer-integration Slice D)

- port FROM 上游 `/Users/neon/antigravity/.agents/skills/sdlc-plan-composer/SKILL.md:239-245`
  (S6′ 段)+`:271-273`(Output Contract 完成判準 bullet)。
- **改指本地**:上游 `harness-spec §5.1`→本地 `§4.5`(SKILL.md 本文不留上游編號,對映關係只記
  此處);execution-feedback 指針→本地 `../loop-harness-standard/modules/execution-feedback.md`
  (同批 Slice B 遷入,指針對象已 test -e 驗真在 disk,非偽委派)。
- 本計劃包(docs/plans/2026-07-19-composer-migration-handoff/)各切片已先行帶 oracle-tier
  frontmatter——「先實踐後成文」,非漂移。
