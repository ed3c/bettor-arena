---
name: autoresearch-composer
description: |
  autoresearch 迭代迴圈計劃編排器（薄層 router+composer）—— 把外部 autoresearch（uditgoenka
  v2.1.0：全局裝於 `~/.claude/commands/autoresearch/`，`/autoresearch` 核心 + 12 個
  `/autoresearch:<sub>` slash 命令）的自主迭代能力路由成 repo-conformant 的「計劃階段」入口，並在
  「優化/迭代迴圈」類計劃切片裡把 autoresearch 的有界迴圈契約（Goal/Scope/Metric/Direction/Verify/
  Guard/Iterations）編入計劃文件骨架。平行於 `sdlc-plan-composer`（本地同批移植 sibling）：後者編
  Matt Pocock 六階段通用 SDLC，本 skill 只負責「有界 modify→verify→keep/discard 對某指標迭代」這一
  垂直切片，是 `sdlc-plan-composer` S5「該 task 是優化迴圈」分支的委派目標。帶讓位優先級規則——
  debug/security/TDD/設計辯論等已有原生治理 skill 的需求讓位給原生，只有真正的指標迭代迴圈才路由外部
  slash 命令。本身不執行迴圈，只把迭代紀律與命令路由編進計劃。
  port 自 northstar `autoresearch-composer` v0.3.0（經 antigravity 2026-07-17 同日 retarget 版本，
  非直接抄 northstar 原檔）；逐機制 retarget 帳本 → modules/retarget-map.md。這是 `sdlc-plan-composer`
  §5 開放問題（見其 modules/retarget-map.md §5）2026-07-11 標記的「潛在重新評估點」的落地。
---

# autoresearch-composer

> **Role**：規劃一個含「優化/迭代迴圈」的任務時調用
> ——某個垂直切片是「針對一個可量測指標，
> 反覆 `modify → verify → keep/discard`，
> 直到收斂或耗盡迭代預算」。
>
> **Stateful workflow，不是單一 prompt**：
> 匹配、生成、驗證必須拆成 state graph 節點。
> §1 Gate 只做 route match；§2 只做 slash 命令/讓位選擇；
> §3 只做 contract generation；§3.7/§5 做 validation 與缺失資訊回補。
> 輸出仍是**計劃文件**，不是程式碼、不是迴圈執行本身。
>
> ```mermaid
> flowchart LR
>   S0["S0 intake<br/>保留低壓縮上下文"] --> S1["S1 match<br/>真迭代迴圈?"]
>   S1 -->|否| X["退回 sdlc-plan-composer / 原生 skill"]
>   S1 -->|是| S2["S2 route<br/>slash 命令+讓位"]
>   S2 -->|讓位| Y["原生治理 skill"]
>   S2 -->|路由外部| S3["S3 generate<br/>contract block"]
>   S3 --> S4["S4 validate<br/>metric/guard/cases/A-B"]
>   S4 -->|缺資訊| S5["S5 recover<br/>缺失資訊與 Domain terms"]
>   S5 --> S3
>   S4 -->|通過| Z["計劃切片候選"]
> ```
>
> **結構**：本檔 = Gate + 路由表 + Contract block + 不變量；
> port 的命門與誠實帳本 →
> [modules/retarget-map.md](modules/retarget-map.md)。
>
> **與 families/ 的邊界（重要）**：
> 本 skill 是 `.claude/skills/` 層的**流程/路由 meta-skill**
> （如 `sdlc-plan-composer`/`unknown-discovery-composer` 同批），
> **不是** `families/` 層的業務資產
> ——它沒有自己的可執行代碼、
> 不走 families 的 proposals→eval-gate→admit→merge 流程。
> 但它現在必須走 `repo/agent-skills-repo` 的 skill-asset governance gate：
> `cases.json` + A/B ablation + lifecycle validator。
> 若某天要把 autoresearch 迭代出的產物本身包成一個
> `families/<name>` 業務資產，
> 那是完全不同的、需要真代碼+真 evals 的另一個決定，
> 本 skill 不預設它會發生。

## When to Use

規劃一個任務時，其中某個垂直切片是
「對某指標反覆 modify→verify→keep/discard，直到收斂或迭代預算耗盡」。
核心契約：
- **路由 + 受治理**
  → 外部 autoresearch slash 命令透過本 skill 的讓位規則被選用，
  而非裸 `/autoresearch:X` 直呼。
- **迴圈紀律編入計劃**
  → 每個迭代切片帶一個填好的 Iteration-Loop Contract block（§3），
  缺欄位即 INCOMPLETE。
- **本身不執行**
  → 與 `sdlc-plan-composer` 同邊界：
  只到「計劃寫好」為止，
  執行交回 `/autoresearch:<sub>` slash 命令。
- **必帶行為證據**
  → 每次修改本 skill 必須維持 10-20 個 behavior cases；
  production hard gate 需跑 A/B ablation，證明有 skill 比無 skill 更能產出完整迭代契約。

## Not For

- ❌ **執行迭代迴圈**：
  本 skill 只產計劃。
  執行走 `/autoresearch` 或 `/autoresearch:<sub>` slash 命令
  （已全局裝於 `~/.claude/commands/autoresearch/`，
  skill-bettor 無 ENCD/`cycle-dispatch` 這類中介層，
  執行完直接交回主會話或既有 harness 消化）。
- ❌ **通用多階段計劃**：
  非迭代迴圈的多階段任務用 `sdlc-plan-composer`
  （六階段 SDLC，本地同批移植 sibling）。
  本 skill 只覆蓋其優化迴圈垂直切片，
  是它 S5 的特化委派，非替代。
- ❌ **產出一個 `families/` 業務資產**：
  那需要真代碼 + eval harness
  （mock/真跑/holdout/judge/baseline），
  走 `families/` 自己的 proposals→eval-gate→admit→merge 流程，
  本 skill 不涉入、不替代。
- ❌ **路由已有原生治理 skill 的需求**
  （核心 anti-duplication，見 §2 讓位規則）：
  - 通用 bug/排錯、難復現/效能回歸
    → `diagnose` / `diagnosing-bugs`
    （**不**路由 `/autoresearch:debug`）。
  - 寫碼/修錯
    → `tdd`
    （**不**路由 `/autoresearch:fix`，
    除非是「錯誤計數歸零」型有界量測迴圈且 TDD 不適用）。
  - 安全審計
    → `/security-review` + `sast-validator`
    （**不**路由 `/autoresearch:security`）。
  - 需求澄清/設計辯論
    → `grilling` / `grill-with-docs` / `grill-me`
    （**不**路由 `/autoresearch:predict` `:reason` `:probe`）。
  - 只有當需求是 autoresearch **唯一**獨有的
    「有界 metric-driven keep/discard 迴圈 + Guard」時
    才路由外部 slash 命令。
- ❌ **取代 `to-prd`+`implement`**：
  那是通用計劃骨架；
  本 skill 在其之上疊加迭代迴圈契約。
- ❌ **決定一個迭代需求該不該存在**：
  那是人類 go/no-go，本 skill 只提供契約骨架。
- ❌ **無 Verify 可量化的「優化」**：
  若指標無法用一條輸出數字的 shell 命令量測，
  不是 autoresearch 迴圈
  ——退回 `grilling`/`grill-with-docs` 先把成功準則量化。

## §1 — Iteration-Loop Gate（進路由前的判據）

一個計劃切片要走本 skill，必須**全部**成立
（任一不成立 → 退回 `sdlc-plan-composer` / 原生 skill）：

| 判據 | 問句 | 不成立 → 路由去向 |
|------|------|------------------|
| **可量測** | 是否有一條**輸出單一數字**的 `Verify` shell 命令？ | 無 → `grilling` 先把成功準則量化 |
| **有方向** | `Direction` 是 higher_is_better 還是 lower_is_better（明確）？ | 模糊 → 釐清後再進 |
| **可守護** | 有沒有一條**永遠必須 pass** 的 `Guard`（測試/build）防止迴圈把系統改壞？ | 無 Guard → 標風險，迴圈前必須補 |
| **有界** | `Iterations` 是有限 N（預設見 §2），還是明確 opt-in `unlimited`？ | 預設有界，unlimited 需顯式理由 |
| **keep/discard 語義** | 每次迭代是否「改一處 → 量測 → 變好則留、變差則丟」？ | 否（是線性多階段）→ `sdlc-plan-composer` |

## §1.5 — Stateful Workflow Nodes（匹配/生成/驗證分離）

本 skill 的執行心智必須保持 stateful，不可把整份需求壓成一個 prompt：

| state | owner | input | output | conditional edge |
|---|---|---|---|---|
| S0 intake | main session | 使用者原始需求、計劃上下文 | low-compression context packet | 缺上下文 → S5 recover |
| S1 match | autoresearch-composer | S0 context | `route_candidate` / `delegate_to_native` | 非 metric loop → `sdlc-plan-composer` 或原生 skill |
| S2 route | autoresearch-composer | route candidate | slash command + native-yield decision | 讓位命中 → native skill |
| S3 generate | autoresearch-composer + `/autoresearch:plan` | route decision | Iteration-Loop Contract block | 欄位缺失 → S5 recover |
| S4 validate | production repo gate | contract block + cases | PASS/FAIL + A/B delta | fail → S5 recover or S3 regenerate |
| S5 recover | judge-loop-chooser / repo-agent-native / human | missing fields, compressed terms | clarified context, domain glossary, unresolved-known-unknowns | recoverable → S3; unrecoverable → human_required |

### Conditional Edge Rules

- `conditional_edge.S1.no_numeric_metric`: 無單一數字 `Verify` → 不進 autoresearch。
- `conditional_edge.S2.native_skill_better`: debug/security/TDD/design debate → 讓位。
- `conditional_edge.S3.missing_domain_term`: 出現未定義 Domain term → 寫入 glossary，再生成。
- `conditional_edge.S3.compressed_context`: 上下文壓縮到 LLM 會模糊決策 → 回 S0 補低壓縮語意真相。
- `conditional_edge.S4.no_cases`: 無 10-20 cases → FAIL，不准產生完成判定。
- `conditional_edge.S4.ablation_not_positive`: A/B delta 未過門檻 → FAIL，不准 promotion。

## §1.6 — Missing Information And Domain Terms

被簡化或遺失的資訊不能默默猜：

- 缺 `Goal/Scope/Metric/Direction/Verify/Guard/Iterations` 任一欄位 → `INCOMPLETE`。
- 遺失 Domain 專有名詞 → 建 `domain_terms` 清單，逐項標 `known`, `candidate`, `unknown`。
- `candidate/unknown` 不得進 hard gate 結論；需要 `judge-loop-chooser` 或 human admit。
- 若資訊來自外部 autoresearch slash 命令版本或 post-cutoff runtime，標 `external-runtime`，不得當本地事實。
- 所有自動生成 contract 必須引用原始需求片段或計劃檔段落，避免缺上下文情況下讓 LLM 模糊決策。

## §1.7 — Semantic Truth Actor Routing（不可留下 Opus/Codex/agy 三選一）

`judge-loop-chooser` 的規則在本 skill 中具體化如下。不要寫
「Opus or Codex or agy 視情況判」；必須先判語意問題，再指定單一 actor 與輸出責任：

| semantic question | actor | output | not allowed |
|---|---|---|---|
| 計劃切片是否忠實保留原始需求、沒有把壓縮上下文當完整事實？ | Opus fresh judge / main session | findings-only route surface，標 `candidate` / `[推論]` / `human_required` | 不得直接 admit promotion |
| production repo 中的腳本、cases、A/B gate 是否真的存在且能跑？ | Codex engineering audit + T0 scripts | terminal evidence、diff/risk findings、修補建議 | 不得用文字相似宣稱 technical_equivalent |
| agy/Gemini runtime 或 autoresearch slash 命令行為是否為外部執行事實？ | agy findings 或 external-verify | execution transcript / observed model/runtime facts | 不得由本 skill 猜測外部 runtime |
| Domain term 是否足夠清楚讓 fresh LLM 不模糊決策？ | repo-agent-native / human glossary admit | `domain_terms` ledger：`known` / `candidate` / `unknown` | `candidate/unknown` 不得進 hard gate 結論 |

若沒有可引用的 evidence artifact，狀態必須是 `candidate` 或 `[推論]`；
只有真跑的 validator、cases、ablation telemetry、或已 admit 的 glossary
才能升成 `technical_equivalent`。

## §1.8 — Eval / Guardrail / Trace Lifecycle Gate

本 skill 的 lifecycle promotion 不只看文字是否合理，必須有本地優先的末端證據：

- **Golden Dataset**：`repo/agent-skills-repo/data/autoresearch_golden/pr_golden_set.json`
  與 `nightly_golden_set.jsonl` 覆蓋正向 route、native-yield 負例、壓縮上下文回復、
  eval/guardrail/trace/cloud-disabled-by-default 行為。
- **Deterministic Guardrails**：`repo/agent-skills-repo/scripts/eval_autoresearch_composer.py`
  先做 schema、route、`must_include`、`must_not_include` 檢查；不得先依賴外部 API。
- **LLM-as-a-Judge**：本地預設為 deterministic heuristic judge；雲端/API judge 接線可以存在，
  但 **cloud disabled by default**，除非顯式設定 `ENABLE_LLM_JUDGE=1` 與 API key。
- **pytest eval markers**：`evals`、`llm_judge`、`trace` 是正式測試入口，CI/CD 預設只跑本地可重現 gate。
- **local-first trace**：`repo/agent-skills-repo/scripts/sample_autoresearch_traces.py`
  驗證 trace sample 的 state nodes、route、verdict、sample_reason 與 cloud 關閉狀態。

若 final repo 的實作末端不能通過上述 gate，或只能用字面相似宣稱等價，
則判為不達標，必須把失敗上下文回饋到小迴圈自動提示重新跑計畫包。

## §2 — slash 命令路由表（帶讓位優先級，skill-bettor 版）

外部 autoresearch 13 slash 命令
（`/autoresearch` 核心 + `/autoresearch:<sub>` ×12，
已全局裝於 `~/.claude/commands/autoresearch/`，非 project-scoped）
→ 計劃切片需求映射。
**讓位規則優先**：
標 ⚠️ 者本 repo 有更治理的原生 skill，預設讓位，
僅當需求嚴格是「有界量測迴圈」且原生 skill 不適用時才路由外部。

| slash 命令 | 計劃切片需求 | 預設迭代 | 路由判定（skill-bettor 讓位對象） |
|---|---|---|---|
| `/autoresearch`（核心） | 對某指標 modify→verify→keep/discard | 25 | ✅ **獨有**——repo 無一級對應，路由 |
| `/autoresearch:evals` | 分析迭代結果（趨勢/高原/回歸） | N/A | ✅ **獨有**——迴圈後分析，路由；注意勿與 `families/*/evals/` 的量測管線混淆（那是量測「某個 skill 好不好」，這是量測「某次迭代迴圈的結果」，正交） |
| `/autoresearch:improve` | 研究 ICP 挑戰 → 發現改進 → 生 PRD | 15 | ✅ 配 `to-prd`（PRD 落地走 mattpocock 全局 to-prd） |
| `/autoresearch:scenario` | 跨 12 維度生邊界案例 | 20 | ✅ 大量邊界生成屬迭代型，路由；但測試設計諮詢用 `tdd`；若目的是給某 `families/*` 補 eval 案例，優先用該 family 自己的 `evals/` 慣例（`cases/`/`holdout`/`candidates`），不繞道 autoresearch |
| `/autoresearch:learn` | 掃 codebase → 生文檔 → 驗證 → 修迴圈 | 10 | ⚠️ 文檔生成讓位 `improve-codebase-architecture`（mattpocock 全局 skill）；純迭代驗證迴圈才路由 |
| `/autoresearch:ship` | 8 階段 ship（checklist→dry-run→deploy→verify） | N/A | **無讓位對象**——skill-bettor 無 devops-hub/部署管線治理層（本專案是 living-skills 資產工場，非要 ship 的部署型服務）；誠實留白，需要時直接路由，不硬造假讓位 |
| `/autoresearch:debug` | hypothesize→test→falsify 獵 bug | 15 | ⚠️ **讓位** `diagnose` / `diagnosing-bugs` |
| `/autoresearch:fix` | 逐一清零錯誤 | 20 | ⚠️ **讓位** `tdd`；僅「錯誤計數歸零」有界量測迴圈例外 |
| `/autoresearch:security` | STRIDE+OWASP 紅隊審計 | 15 | ⚠️ **讓位** `/security-review` + `sast-validator` |
| `/autoresearch:predict` | 5 專家人格實作前辯論 | N/A | ⚠️ **讓位** `grilling` |
| `/autoresearch:reason` | 盲評審對抗辯論至收斂 | 8 | ⚠️ **讓位** `grilling` / `grill-with-docs` |
| `/autoresearch:probe` | 8 人格審問需求至飽和 | 15 | ⚠️ **讓位** `grill-with-docs` / `grill-me` |
| `/autoresearch:plan` | 把 goal 轉成 validated Scope/Metric/Direction/Verify 配置 | N/A | ✅ 路由——**正是 §3 契約欄位的產出器**（見 §3） |

> **TCC 守門**：
> 讓位（⚠️）優先於路由外部。
> 每次選用外部 slash 命令時，計劃文件須記一行
> `> autoresearch-route: /autoresearch:<sub> (原生讓位已評估: <原生 skill or N/A> — 理由)`，
> 供人審計判定不是繞過治理。

## §3 — Iteration-Loop Contract Block（編入計劃切片）

> **產出方式（extend don't duplicate）**：
> 契約的 Goal/Scope/Metric/Direction/Verify 欄位**不手寫**
> ——跑 `/autoresearch:plan`
> （其本職正是把 goal 轉成 validated Scope/Metric/Direction/Verify 配置），
> 本 skill 只把它的輸出**嵌入計劃切片** +
> **補 Guard/Iterations/route/讓位評估**並受治理。
> `/autoresearch:plan` 缺 Guard 概念
> （autoresearch 的 Guard 是迴圈級安全網）
> → Guard 由本 skill 依 §1 判據補齊。

通過 §1 Gate 的每個迭代切片，在其 `NN-<slice>.md` 注入以下 block
（缺任一必填欄位 = INCOMPLETE）：

```yaml
# --- autoresearch iteration-loop contract (注入自 autoresearch-composer) ---
# Goal/Scope/Metric/Direction/Verify ← /autoresearch:plan 產出後填入；Guard/Iterations/route/executor ← 本 skill 補
goal:        "<要改進什麼>"                 # 必填（/autoresearch:plan）
scope:       "<file globs>"                  # 必填（/autoresearch:plan）——迴圈可改的檔案邊界
metric:      "<量測什麼>"                    # 必填（/autoresearch:plan）
direction:   higher_is_better               # 必填（/autoresearch:plan）——或 lower_is_better
verify:      "<輸出單一數字的 shell 命令>"   # 必填（/autoresearch:plan）——§1 可量測判據
guard:       "<永遠必須 pass 的 shell 命令>" # 必填（本 skill 補）——測試/build；無則顯式 `none` + 風險註記
iterations:  25                              # 有界預設見 §2；unlimited 需 justification 欄位
evals:       false                           # 是否 mid-loop checkpoint（→ /autoresearch:evals）
route:       "/autoresearch:<subcmd>"        # §2 選定的 slash 命令（裸迴圈用 /autoresearch）+ 讓位評估
executor:    "slash-command:/autoresearch:<subcmd>"  # skill-bettor 無 cycle-dispatch，一律 slash 命令直執行
# --- end contract ---
```

**安全不變量繼承**（外部 autoresearch SKILL.md §Safety Invariants）：
迴圈**不 push/deploy 不經明示批准**；
預設有界；
結果落 `autoresearch/{subcommand}-{YYMMDD}-{HHMM}/`。
本 skill 把這些寫進計劃切片的「執行契約」段，
讓執行半（`/autoresearch:<sub>` slash 命令）有據可循。

## §3.5 — rejection-log + edit-budget（選填特化，通用可攜）

§3 契約骨架可選加兩個選填槽（省略 = 現狀零變化）：

```yaml
rejection_log: "autoresearch/<run>/rejections.md"  # 選填——每次 discard 記變異+原因；下一迭代 modify 前讀，不重走已否決方向
edit_budget:   "linear-decay floor=1"              # 選填——迭代遞增收緊單次 modify 幅度；floor>0（預算永不凍結迴圈）
```

- **rejection_log** 只省 verify 成本（不重 walk 否決路徑），
  **不動** keep/discard 判準（Metric+Guard 仍唯一裁決）。
- **edit_budget** 只約束「一次改多大」，永不選方向、永不加迭代。
- 兩槽永不進 fitness 統計。

## §3.7 — Behavior Case And A/B Hard Gate

本 skill 必須有 `cases.json`，且維持：

- 10-20 cases；
- 至少 5 個 positive route cases；
- 至少 5 個 negative / native-yield cases；
- 每個 positive case 期望輸出包含 state graph、conditional edge、contract block、missing-info/domain-term handling；
- A/B ablation 必須證明 `with_skill` 輸出比 `without_skill` 更完整。

production gate 由
`repo/agent-skills-repo/scripts/check_autoresearch_lifecycle.py`
與 `repo/agent-skills-repo/scripts/ablation_engine.py --cases repo/agent-skills-repo/skills/autoresearch_composer/cases.json`
執行。未通過時，本 skill 不得被宣稱完成 lifecycle optimization。

## §4 — 與 sdlc-plan-composer 的組合（非競爭）

本 skill 是 `sdlc-plan-composer`（本地同批移植 sibling）
**S5 階段的特化委派**，不是替代：

```
sdlc-plan-composer S0..S4  →  S5 移交/維護紀律入計劃
                               └─ 若某 task 是「優化/迭代迴圈」
                                  → 委派 autoresearch-composer
                                     → §1 Gate → §2 路由 → §3 (/autoresearch:plan 產欄位 + 嵌入)
                                  → 回填該 NN-<slice>.md 的「執行契約」段
```

兩者 Output Contract 同構（落 `docs/plans/<date>-<topic>/`），
本 skill 只新增/充實「優化迴圈切片」的 Iteration-Loop Contract block，
不改 `sdlc-plan-composer` 的其餘骨架。
獨立調用（非經 `sdlc-plan-composer`）亦可
——直接對一個已知的優化迴圈任務產出帶 contract 的計劃切片。

## Output Contract（Boundary Artifact）

複用 `sdlc-plan-composer` 的計劃目錄，新增/充實優化迴圈切片：

```
docs/plans/<date>-<topic>/
├── 00-intent-and-knowhow.md        # （若獨立調用）記迭代意圖 + §1 Gate 判定 + 讓位評估
├── NN-<optimization-slice>.md      # 含 §3 Iteration-Loop Contract block + §2 route 行
└── （其餘骨架由 sdlc-plan-composer 提供）
```

## 整合接點（Wiring — 必為實接，非宣稱）

- **接 `sdlc-plan-composer` S5**：
  `.claude/skills/sdlc-plan-composer/SKILL.md` 的 S5 row 已委派本 skill
  （見其 modules/retarget-map.md 該格由
  「§5 開放問題/誠實留白」改為「已落地」）。
- **執行半委派**：
  Contract block `executor` = `/autoresearch:<sub>` slash 命令
  （全局裝於 `~/.claude/commands/autoresearch/`）。
  skill-bettor 無 ENCD/`cycle-dispatch`，
  含並行檔案變更的迭代直接交回主會話手動分治，
  不硬造一層中介 dispatch。
- **不跨層**：本 skill 只到「計劃寫好」；執行交回 `/autoresearch:*` slash 命令。
- **不接 `families/`**：
  本 skill 與 `families/*/evals/` 正交
  ——後者量測「一個 skill 好不好」，
  前者是「規劃一次迭代迴圈該怎麼委派」，
  兩者職責不重疊、不互相委派
  （見上方「與 families/ 的邊界」）。

## Experience Accumulation

每次調用後：
若發現新的迭代反模式
（無 Guard 的迴圈把系統改壞、Verify 不輸出數字、
讓位規則被繞過直路由已有原生 skill 的需求、unlimited 無 justification），
記為候選並回饋 §1 Gate / §2 讓位表。
若外部 autoresearch slash 命令集變動
（升版增刪 `~/.claude/commands/autoresearch/`），更新 §2 路由表。

*port 自 northstar `autoresearch-composer` v0.3.0
（經 antigravity 2026-07-17 retarget 版本再移植；
skill-bettor 版無
`encd-infrastructure-hub`/`skill-cycle`/liveness-grounding
YAML 治理欄位，
也不走 `families/` 的 eval-gate 流程，
但走 `repo/agent-skills-repo` production skill-asset governance gate，
故不帶那兩套系統
——本檔以 `~/.claude/commands/autoresearch/` 現存目錄 +
本地 `.claude/skills/` 現存目錄作為路由目標真實性的鐵錨
（見 modules/retarget-map.md）。*
