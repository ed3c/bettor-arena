---
name: skill-authoring
description: |
  skill-bettor 的 skill 設計規範(家規層)——新建/重構/審查本 repo 任一 skill 前先讀。
  涵蓋 portable Agent Skills core、Codex/Claude host projection、兩類 skill 分界、typed execution、
  hard/advisory assertions、slim+modules、semantic loss ledger、canonical terms 與行為 A/B。
  觸發詞:新建 skill、skill 規範、skill 設計、frontmatter、固化範例、skill-authoring。
  NOT for:判「該不該新建」(先走 fold-in 不變量 1);執行某支既有 skill 的業務程序。
metadata:
  version: "4"
  entrypoint-line-budget: "120"
---

# Skill: skill-authoring — skill-bettor 的 skill 設計規範(家規層)

> **Role**:官方共同面與 host 差異由
> [official-agent-skills-profile](modules/official-agent-skills-profile.md) 固定；本檔負責
> **skill-bettor 家規**、兩類 skill 分界與 acceptance。**本檔自己也用此規範寫
> (dogfood):portable core + slim + 指針不抄**。「該不該新建」的判準不在本檔——先走
> [fold-in](../fold-in/SKILL.md) 不變量 1 (預設 fold 不造新;真未覆蓋
> niche+人核才新建)。

## Current procedure

1. **Match**：先找 2–3 個相似 Skill 與現有 owner；能 additive fold-in 就不另建同義 Skill。
2. **Freeze baseline**：重構前固定 exact commit/blob digest，建立 semantic-loss ledger；每個舊語意只能標 `ACTIVE_IN_SKILL`、`PRESERVED_IN_MODULE`、`LEGACY_ARCHIVED` 或 `CANONICAL_OWNER_WITH_LEGACY_COPY`。
3. **Write portable core**：canonical package 住 `.agents/skills/<name>`；frontmatter 只用 portable fields；`scripts/`、`references/`、`assets/` 可選，`modules/` 是 Bettor extension。500 行只是 repo ceiling；重構須以 metadata 預先登記更小的 `entrypoint-line-budget` 並由 gate 執行。
4. **Preserve continuity**：外部指針前先留本地摘要，縮寫首次展開，`PASS`、`NOT_EXERCISED`、`NOT_CONFIGURED` 等狀態不折疊；`CONTEXT.md`/ADR/README 是 domain context，不是 discovery format。
5. **Design execution**：Skill 只提程序；runner 接 typed `executable` + `argv[]`，明示 cwd/env/timeout/network/writable paths，禁止 raw shell string、absolute host path、path traversal、secret value 與 implicit branch。
6. **Design assertions**：把可判 claim 寫成 stable predicate ID/operator/value/source，由 evaluator 對 exact subject 獨立重觀測；hard assertions 用 exit/schema/hash/diff/AST/LSP/test report，模型自述與文字 alias 只可 advisory，不能影響 admission 或覆寫 hard failure。
7. **Build the gate**：至少一個 positive、一個 hollow，且每條 load-bearing rule 各有 planted mutation；同一問題最多三次修正。
8. **Project hosts**：Codex 用 canonical `.agents/skills` 與可選 `agents/openai.yaml`；Claude 用 `.claude/skills/<name>` thin symlink；不得複製第二份 `SKILL.md`。
9. **Prove behavior**：先依 outcome/evidence surface 選 reusable profile：source-grounded analysis、artifact transformation、transactional effect、routing/composition 或 interactive judgment；這五類不是業務 domain。再預登記 task families、metamorphic variants 與 task-specific oracle。控制臂由 profile 宣告，不固定成三臂：新 Skill 可只做 candidate/no-skill；routing/composition 可用 `composed_skills`/`wrong_skill`/`no_skill`。subject/evaluator 以 case 固定；common-task/environment/tool-policy 以 case×harness×repetition 跨臂固定；runner/model 只要求同一 harness 內固定，跨 harness 可不同；treatment digest 以 condition 固定且 `no_skill` 必須為 null。用 explicit relation receipt、hard capability、paired conservative bound、worst-family 與 cross-host gap 分開判。public protocol conformance 只能證量測器能紅；physical sealed holdout 才可能 unlock，仍須 Human Admit。
10. **Deliver**：receipt 證明 exact head 某次發生什麼；GitHub/Forgejo live audit 另證明當下狀態；promotion/merge 留 Human Admit。

Repository conformance 的實際入口：

```text
python3 scripts/gates/check_skill_conformance.py --selftest
python3 scripts/gates/check_skill_conformance.py --root .
```

## Current invariants

- `SKILL.md` 程序不等於真執行；script 存在、MCP wired 或模型聲稱已測試都不等於 PASS。
- 收據綁 exact repository commit、context digest、Skill digest、command、observed exit、artifact digests、assertions 與 cleanup。
- Current source/tests/receipts 優先於 semantic index、graph projection、memory projection 與模型記憶。
- `no_skill` 只代表未安裝 treatment Skill；不代表自動知道程序或呼叫 semantic/symbol/graph/memory provider。共同 schema adapter 不得洩漏答案或 Skill procedure。
- ecosystem/runtime quality 與 verified behavior/capability 分開出表；security hard failure 不可被品質加權補償，也不可用單一總分吞掉 generalization gap。
- Skill 名、family/case/capability ID、輸出行順序與註冊順序改名後，數值結論必須不變；否則是在量 alias 或 evaluator fit，不是程序性泛化。每個新 Skill 必須進 shared catalog，未分類直接 fail closed；catalog coverage 不等於該 Skill 已跑 physical A/B。
- 新檔先對映 `ARCHITECTURE.md` §2，再更新 nearest README/catalog/lock；收手前正常跑 hook，禁止 `--no-verify`。
- YAML block scalar 內 ASCII colon 合法；用 parser 驗格式，不用字元迷信。
- Codex `$skill-name` 與 Claude `/skill-name` 是不同 host surface；`allowed-tools` 不是 portable sandbox。

## Modules

按任務只載入必要細節：

- [Official Agent Skills profile](modules/official-agent-skills-profile.md)：portable core、Codex/Claude host projections 與官方 primary sources。
- [Execution and assertions](modules/execution-and-assertions.md)：typed execution、hard/advisory assertions、subject-bound receipts、profile-bound controls 與跨 harness 泛化量測。
- [Authoring clauses](modules/authoring-clauses.md)：Bettor 既有產品/工程 Skill 的進階條款。
- [Semantic-loss ledger](modules/semantic-loss-ledger.md)：舊語意的 durable home 與檢查。
- [Archived legacy Skill](modules/legacy-skill-2026-08-14.md)：移出 model-visible core 的歷史家規與 domain instances；不作 current truth。
