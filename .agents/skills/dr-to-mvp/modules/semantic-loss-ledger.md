# Module: dr-to-mvp — Semantic Loss Ledger

> 屬 [`dr-to-mvp`](../SKILL.md)。本檔是 2026-07 state graph 重構的資訊保全帳。
> Source baseline = `git show 9600c79:.claude/skills/dr-to-mvp/SKILL.md`。
> 原文級保全 = [legacy-skill-2026-07-22.md](legacy-skill-2026-07-22.md)。
> Verdict：未發現需要保留卻無 durable home 的舊語意；主路由降噪後，非主路由資訊已分流到本 skill 的 `reference/` 或 `modules/`，或明確指向 owner skill。舊版 domain wording 逐字保存在 legacy snapshot，不能只靠本 ledger 摘要復原。

## Legend

| Label | Meaning |
|---|---|
| `ACTIVE_IN_SKILL` | 必須留在主 `SKILL.md`，因為它會改變 route/actor/validator/failure edge。 |
| `PRESERVED_IN_MODULE` | 不該佔主路由，但必須有 module/reference durable home。 |
| `CANONICAL_OWNER_WITH_LEGACY_COPY` | 真 SSOT 在 owner skill 或 repo 文件；本 skill 只指針，舊文仍在 legacy snapshot。 |
| `LEGACY_ARCHIVED` | 舊敘述不再作為 active route，但逐字保存在 legacy snapshot，供語意審計與 wording 復原。 |

## Loss Ledger

| Old semantic unit | Classification | Current durable home | Check |
|---|---|---|---|
| 冷啟動新家族 vs 既有家族日常演化疆界 | `ACTIVE_IN_SKILL` | `SKILL.md` M0 + Not For | M0 handoff to `product-ops`。 |
| recipe-not-engine，每 Phase 間人 admit | `ACTIVE_IN_SKILL` | `SKILL.md` state graph + Invariants | Every V node has SURFACE/human edge。 |
| Phase R/G/M 定序 | `ACTIVE_IN_SKILL` | `SKILL.md` State Graph | M1 routes to G0/G1/G2。 |
| owner skill 指針 | `ACTIVE_IN_SKILL` | `SKILL.md` Owner 指針 | Phase R/G/M owner paths remain visible。 |
| DR 不是 prototype 入口 | `PRESERVED_IN_MODULE` + `ACTIVE_IN_SKILL` | `SKILL.md` Invariants; `reference/guiding-prompt.md` §0 | Main invariant retained; full topology in reference。 |
| 兩種 prototype 消歧 | `ACTIVE_IN_SKILL` + `PRESERVED_IN_MODULE` | `SKILL.md` G1/V1; `reference/guiding-prompt.md` §0 | D4 retained-not-promoted; MVP seed route explicit。 |
| D4 artifact 留錨不刪、不升格 | `ACTIVE_IN_SKILL` | `SKILL.md` G1/V1; `modules/domain-terms-and-intake.md` §5 | Reason preserved：delete loses re-verification anchor。 |
| Mode A/Mode B input classification | `ACTIVE_IN_SKILL` | `SKILL.md` M1; `modules/domain-terms-and-intake.md` §2 | M1 route plus domain definition。 |
| Phase R T0 四閘 + D3 adopt | `ACTIVE_IN_SKILL` | `SKILL.md` G0/V0; `reference/guiding-prompt.md` Phase R | Validators named, not reimplemented。 |
| D3 `origin_question` / Half-Bridge | `ACTIVE_IN_SKILL` + `PRESERVED_IN_MODULE` | `SKILL.md` V0/G0; `modules/domain-terms-and-intake.md` §2 | Domain term defined and gate retains failure edge。 |
| Phase G KU/UK/UU routing | `ACTIVE_IN_SKILL` + `PRESERVED_IN_MODULE` | `SKILL.md` G1; `modules/domain-terms-and-intake.md` §2 | Terms expanded in canonical table。 |
| ANSWER→fresh judge→absorb order | `ACTIVE_IN_SKILL` | `SKILL.md` G1/V1 + Gotchas; `reference/guiding-prompt.md` Phase G | Absorb-before-judge remains stop condition。 |
| Antigravity D4 failure file path | `LEGACY_ARCHIVED` | [legacy-skill-2026-07-22.md](legacy-skill-2026-07-22.md); lesson retained in `SKILL.md` Gotchas | External path is not local SSOT, but exact old wording remains recoverable。 |
| Phase M `DESIGN-SCORE.md`, `_template`, `engine.sh`, dispatches | `ACTIVE_IN_SKILL` | `SKILL.md` G2/V2; `reference/guiding-prompt.md` Phase M | Main has output artifact and validators。 |
| dual-score AND graduation | `ACTIVE_IN_SKILL` | `SKILL.md` V2 + Invariants; `reference/guiding-prompt.md` Phase M | Design + implementation gates explicit。 |
| families-type homing destination | `ACTIVE_IN_SKILL` + `PRESERVED_IN_MODULE` | `SKILL.md` G3/V3; `modules/retarget-map.md`; `modules/domain-terms-and-intake.md` | Destination and non-applicable homing types preserved。 |
| `__file__` relative path after homing | `ACTIVE_IN_SKILL` + `PRESERVED_IN_MODULE` | `SKILL.md` G3/V3; `reference/guiding-prompt.md` Phase M | Final-location verify retained。 |
| family runtime must not cite `proposals/` | `ACTIVE_IN_SKILL` | `SKILL.md` G3/V3 + Gotchas; `reference/guiding-prompt.md` §0 | Illegal back-reference remains explicit。 |
| `families/agent-harness` live anchor and metrics | `PRESERVED_IN_MODULE` | `reference/guiding-prompt.md` §2; `modules/retarget-map.md`; `SKILL.md` References | Main only points to worked instance; detail retained elsewhere。 |
| eval harness design-only status | `PRESERVED_IN_MODULE` | `reference/guiding-prompt.md` §2 | Not a routing edge; kept in honesty ledger。 |
| antigravity 2×2 host matrix removed | `LEGACY_ARCHIVED` + `PRESERVED_IN_MODULE` | [legacy-skill-2026-07-22.md](legacy-skill-2026-07-22.md); `modules/retarget-map.md`; `reference/guiding-prompt.md` §2 | Not applicable to Claude-Code-only repo, but original host wording remains recoverable。 |
| live browser DR `:9333` occupancy | `CANONICAL_OWNER_WITH_LEGACY_COPY` + `ACTIVE_IN_SKILL` | `SKILL.md` Gotchas; `reference/guiding-prompt.md`; `modules/retarget-map.md`; legacy snapshot | Owner is `dr-research-loop`; main keeps conditional warning。 |
| S0/S1 保真語料 intake | `PRESERVED_IN_MODULE` | `modules/domain-terms-and-intake.md` §3; `SKILL.md` M1 pointer | Recovered after initial state refactor。 |
| post-cutoff 實體雙向警戒 | `PRESERVED_IN_MODULE` | `modules/domain-terms-and-intake.md` §3 | Recovered as Mode B intake discipline。 |
| Domain terms such as Path B, SURFACE, LAND-DECISION | `PRESERVED_IN_MODULE` + `ACTIVE_IN_SKILL` | `modules/domain-terms-and-intake.md` §2; `SKILL.md` Output Contract | First-use expansion rule added。 |
| Trigger terms `SYNTHESIS` / MVP-builder wording | `LEGACY_ARCHIVED` + `PRESERVED_IN_MODULE` | [legacy-skill-2026-07-22.md](legacy-skill-2026-07-22.md); `modules/domain-terms-and-intake.md` can host glossary deltas if needed | Current terms are `verified base` and Phase M/G2; old trigger wording remains recoverable。 |
| Anti-husk pointer-only discipline | `ACTIVE_IN_SKILL` | `SKILL.md` Invariants; `modules/retarget-map.md`; this ledger | Owner SSOT rule retained and audited。 |

## Result

No old load-bearing semantic unit is unaccounted for. Non-local antigravity history/path anchors and old trigger wording are not active route rules, but they are preserved verbatim in the legacy snapshot. Domain terms have a durable home and an output rule requiring first-use expansion.
