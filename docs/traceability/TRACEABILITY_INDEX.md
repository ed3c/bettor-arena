# Four-repository routing traceability index

## Trace chain

```text
source / incident
→ source classification
→ repository decision and plane owner
→ parent issue
→ molecular issue
→ sibling / true-child / terminal / convergence PR
→ State Machine transition
→ eval / disagreement control
→ immutable subject
→ receipt / current evidence state
→ Human Admit or rollback
```

## Documentation sibling set — current publication truth

| Plane | Issue | PR | Stack class | Current state |
|---|---|---|---|---|
| Parent integration contract | `#35` | n/a | parent | open |
| Integration / Acceptance | `#36` | `#37` | independent sibling | **MERGED** at `1f94d3d77992a1396959a15b2ada7836c07bf300` |
| Instruction / Method | `ed3c/skills-shared#84` | `ed3c/skills-shared#85` | independent sibling | **MERGED** at `e3b327ad49c088f1962c33167ecd5ac9d28125fb` |
| Runtime Contract | `ed3c/runtime-env#29` | `ed3c/runtime-env#30` | independent sibling | **MERGED** at `4a333ccf106ef60bc6942b922b7f5efffb3876f5` |
| Domain Product / Reference Consumer | `ed3c/agent-shield-monorepo#77` | `ed3c/agent-shield-monorepo#78` | independent terminal sibling | **MERGED** at `1af04c1ef5cb68eab198987feba008c93d3ec22f` |
| Exact merged index + cold-start audit | `#38` | `#58` contributes PDF/Stack audit; final cold-start convergence still pending | convergence workstream | **UNBLOCKED**; Claude/Codex cold-start remains `NOT_EXERCISED` |

The four documentation PRs are siblings because each edits only its own repository. They are no longer Draft or blockers. Issue #38 now owns exact merged route comparison and fresh Claude/Codex cold-start evidence.

## PDF modular-integration trace

| Hop | Exact subject | Current finding | Owner / next transition |
|---|---|---|---|
| Architecture source | `科技巨頭開源授權與AI框架v2.pdf`, pages 25–41 | target is `agent-shield-monorepo/`; prose claim of full integration is `SOURCE_PROPOSAL` | repository decision and evidence |
| Runtime contract baseline | `runtime-env` commit `4a333ccf106ef60bc6942b922b7f5efffb3876f5`, tree `68cda3d0ce7f1df26475a5d7322968194e794046` | evaluated implementation baseline | runtime-env |
| Bettor runtime projection | `.runtime-env/bindings/bettor-arena-local.json`, source commit `142e1ed278bf18f9c5c09186e28db16b623cdaee`, tree `1bd5c97e6f5519182d151055cf5f83fccb7ff5fa` | `STALE_SOURCE_PIN` versus evaluated baseline | dry-run sync + accept pin/apply decision |
| Bettor Integration / Acceptance | `.agents/`, `.runtime-env/`, `.arena/`, `loopctl/`, `proof_workflow/`, `data/` | deterministic named contracts present | exact gates and receipts |
| Agent Shield runtime foundation | issue `#38`, PR `#79`, merge `7d28a8cada03726b2b8966d9a229500f285d1b2b` | provider-neutral SPI implemented | native leaves `#39–#43`, convergence `#44` |
| Agent Shield product/mobile | issues `#45–#53` | incomplete / live product evidence not exercised | terminal leaves + #53 |
| Agent Shield security/settlement | issues `#54–#64` | native providers not implemented under current status | terminal leaves + #64 |
| Bettor reference consumer | issues `#65–#75` | parity/carrier/origin/release not exercised | Phase 6 Stack |
| Product-complete release | issue `#75` | aggregate release subject absent | Human Admit after exact evidence |

Canonical audit: [`../integration/AGENT_SHIELD_PDF_MODULAR_INTEGRATION_AUDIT.md`](../integration/AGENT_SHIELD_PDF_MODULAR_INTEGRATION_AUDIT.md).

## Documentation PR Stack for PDF audits

```text
main
└─ PR #57 docs/pdf-modular-integration-2026-08-14
   └─ PR #58 docs/agent-shield-runtime-pdf-audit-2026-08-14
```

PR #58 is a **true child** because it consumes PR #57's unmerged root README/AGENTS directory-State-Machine mapping and extends the same root documentation. Retarget or rebase #58 after #57 merges.

## Agent Shield molecular implementation Stack

The canonical Git Town configuration and detailed DAG are owned by `agent-shield-monorepo`.

```text
Phase 3 #38–#44  runtime fabric
  #38 foundation merged via PR #79
  #39–#43 terminal provider leaves
  #44 convergence

Phase 4 #45–#53  product/mobile
  #49 is a true child of Expo #48
  #53 convergence

Phase 5 #54–#64  security/hardware/settlement
  #63 is a true child of smart-account #62
  #64 convergence

Phase 6 #65–#75  Bettor reference consumer
  #67/#68 sibling Skill/runtime bindings after immutable #66 closure
  #70–#73 sibling carrier/origin canaries after #69 parity
  #74 origin convergence
  #75 release convergence
```

Git Town branch movement never replaces implementation, exact-head tests, review, merge, release or Human promotion evidence.

## Method lineage

- `knowledge-continuity`: every hop leaves a local summary; no hidden background or unexplained index-to-index outsourcing.
- `forgejo-delivery-loop`: local authoring, deterministic routing/outbox/recovery and receipt separation.
- `github-delivery-loop`: GitHub publication, Actions and merge-state separation.
- `git-town-stacked-pr-worker`: sibling, true-child, terminal leaf, convergence leaf, worktree/lease, no-push sync and Human boundaries.

## Machine authorities

- `.agents/shared-skills.requirements.json`, `.agents/bindings/`, `.agents/module-set.json`
- `.runtime-env/requirements.json`, bindings, workloads and policies
- `.arena/modules/`, compositions, locks, contexts, origins, browser and MCP policies
- `loopctl/contract.json` and the Bun/TypeScript MCP runtime
- `proof_workflow/` and `data/` receipts
- `runtime-env` catalog/contracts/modules/profiles/workloads/policies and exact source commit/tree
- Agent Shield module release/status/receipts, `.git-town.toml`, Stack plan, issues and PRs in its own repository

## Evidence boundary

Documentation completion does not imply a fresh runtime projection, route-checker execution, fresh Claude/Codex cold-start, GitHub/Forgejo equivalence, live browser/provider canaries, Agent Shield product acceptance, external-release promotion or production readiness.