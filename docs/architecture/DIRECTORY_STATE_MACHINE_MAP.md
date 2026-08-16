# Directory → State Machine ownership map

## Purpose

This document binds repository placement to state-machine responsibility. It is a human route over current machine contracts; it does not replace `module.json`, `loopctl/contract.json`, composition locks, scripts, tests, receipts or GitHub metadata.

A directory may own one of:

```text
law / instruction
machine contract
runtime mechanism
evidence projection
```

It must not silently own all four.

## Repository-level flow

```text
source / issue / PDF proposal
        ↓
AGENTS + architecture + bounded context
        ↓
shared Skill reference + repo-owned profile/binding
        ↓
module requirements + Stack task packet
        ↓
module graph + branch graph + path-lease validation
        ↓
deterministic lock + Context Capsule
        ↓
loopctl / trusted public request
        ↓
leased bounded runtime / disposable worktree
        ↓
hard Gates + proof/control/mutation
        ↓
subject-bound receipt / LoopX event proposal
        ↓
convergence leaf
        ↓
Automated admission / merge / release / rollback
```

The repository now has a typed Git Town admission/controller mechanism, but no admitted executable or configuration. Local synchronization remains `NOT_EXERCISED`.

## Directory ownership and State Machines

| Directory or route | Owner | State Machine | Inputs | Outputs | Current state |
|---|---|---|---|---|---|
| root `README.md`, `AGENTS.md`, `CLAUDE.md`, `CONTEXT.md`, `ARCHITECTURE.md` | `arena-core` | `ENTRY → ROUTE → OWNER → CONTRACT → EVIDENCE` | task + repo subject | bounded Agent route | `IMPLEMENTED` |
| `docs/architecture/` | architecture/status owner | `SOURCE_PROPOSAL → TARGET → CURRENT → GAP → ACCEPTANCE` | PDF/design/incident | target and mutable status | `IMPLEMENTED` |
| `docs/git/` | repository Git governance | `METHOD PIN → PROFILE → QUEUE → STACK/LEASE → EVAL → PUBLICATION BOUNDARY` | shared Skill pin + GitHub metadata | profile, queue, Stack snapshot | `IMPLEMENTED`; active #92 |
| `docs/traceability/` | traceability owner | `SOURCE → ISSUE → TERMINAL → PR → EXACT HEAD → CHECKS → ADMIT` | issue/PR/check metadata | human index | `IMPLEMENTED`, snapshot-bound |
| `.agents/skills/` | `agent-runtime-integration` | `REQUIRE → RESOLVE → PROJECT → DISCOVER` | shared/repo-owned Skill requirements | host-neutral projections | `IMPLEMENTED`; Git Town method same-blob but `NOT_SELECTED` |
| `.skill-bindings/` | consumer bindings | `UPSTREAM SKILL → RETARGET → ASSERT → RECEIPT` | immutable Skill identity | repo-specific facts | selected bindings `IMPLEMENTED` |
| `.runtime-env/` | runtime projection | `DECLARE → RESOLVE → MATERIALIZE → OFFLINE VERIFY → LIVE CANARY` | secret-free release | policies/workload/binding | mechanism `IMPLEMENTED`; live varies |
| `.arena/modules/` | `module-catalog` | `PROPOSED → CONTRACTED → COMPOSED → PROVED → RELEASED` | manifests | capabilities/owners/proof | `IMPLEMENTED` |
| `.arena/compositions/` | `module-catalog` | `DESIRED → CAPABILITY/DEPENDENCY/CONFLICT RESOLVE` | requirements | desired composition | `IMPLEMENTED` |
| `.arena/locks/` | generated control plane | `REQUIREMENTS → RESOLVE → DIGEST → LOCK` | manifests + requirements | composition lock | `IMPLEMENTED`; regenerate only |
| `.arena/contexts/` | `loop-runtime` + owners | `SELECT → MATERIALIZE → FREEZE → DRIVER → CANARY` | immutable ref + native files | Context Capsule | offline `IMPLEMENTED`; live varies |
| `.arena/origins/`, `.arena/browser/` | `environment-contracts` | `DECLARE → PROBE → RECEIPT → EQUIVALENCE/ROUTE → ADMIT` | contract | status/canary | contracts `IMPLEMENTED` |
| `loopctl/` | `loop-runtime` | `PARSE → VALIDATE → DISPATCH → PROPAGATE 0/2/64` | typed CLI request | artifacts/receipts | `IMPLEMENTED` |
| `mcp/` | `mcp-adapters` | `DEFAULT DENY → TOOL PROJECT → IMMUTABLE CALL → CLEANUP` | CLI contract + policy | JSON-RPC result | admitted tools `IMPLEMENTED` |
| `proof_workflow/` | `proof-kernel` | `CLAIM → TRAVERSAL → CONTROL → MUTATION → RECEIPT` | public port + context | evidence | `IMPLEMENTED` |
| `data/module-proof/` | generated evidence | `SUBJECTS → CLOSURE → RELEASE AGGREGATION` | locks + proof specs | subject lock/receipt | 14 selected modules; aggregate `NOT_EXERCISED` |
| `loop_wiki/evolve-perfect-seed-repo-factory/` | `perfect-seed-factory` | `PACKET → BUILD → QUALITY → OPERATOR → VALIDATOR → AUTOMATION EDGE` | typed task/source | seed repo/wiki request | `IMPLEMENTED` |
| `kb-ingest/`, `openwiki/` | `openwiki` | `REQUEST → DRY/FULL OPT-IN → VERIFY → RECEIPT` | wiki request | projection | mechanism `IMPLEMENTED` |
| `loop_wiki/code-truth-graph/` | `code-truth-graph` | `PACKET → PIN → PARSE/BUILD → VERIFY → GRAPH` | source packet | graph/result | `IMPLEMENTED` |
| `notebooklm/` | `notebooklm` | `TARGET → AUTH/RESOLVE → READ/FOLLOW → CLEANUP → RECEIPT` | registry/target | bounded harvest | subject-specific |
| `docs/knowledge-providers/` | `knowledge-providers` | `MANIFEST → QUERY/PROPOSAL → RECEIPT → SOURCE READBACK → ADMIT` | exact subject + capability | candidate | contracts `IMPLEMENTED` |
| `scripts/gates/`, `tests/` | `arena-core` / `proof-kernel` | `POSITIVE → CONTROL → HOLLOW/MUTATION → EXACT SUBJECT` | tracked tree | deterministic exit | `IMPLEMENTED` |
| `data/` | evidence projection | `EXECUTE → NORMALIZE → HASH → STORE → REPLAY/COMPARE` | OS/tool output | receipts/status | exact receipt dependent |
| `.github/workflows/` | cloud verifier | `EVENT → EXACT CHECKOUT → GATE → STATUS` | PR/push subject | check | `IMPLEMENTED` |
| `loop_wiki/loopx-kernel/`, `loop_wiki/loopx-ledger/` | LoopX state plane | `TASK/EVENT → VALIDATE → APPEND → REDUCE → SNAPSHOT` | Objective/Todos/Gates/Evidence/Quota | canonical ledger/snapshot | mechanisms `IMPLEMENTED`; not selected |
| `loop_wiki/loopx-strategy-hitl/` | strategy/HITL plane | `SNAPSHOT → PROPOSE → INTERRUPT → SIGN → REVALIDATE` | Ledger snapshot | command/decision proposal | PR #106 merged; not selected |
| `loop_wiki/loopx-worker-gateway/` | execution adapter | `REQUEST → ADAPTER → OBSERVE → RECEIPT → CLEANUP` | host request/context | Worker observation | mechanism `IMPLEMENTED`; six-host live pending |
| `loop_wiki/loopx-runtime-fabric/`, `loop_wiki/loopx-worker-fleet/` | execution/scheduling plane | `POLICY/QUEUE → LEASE → MATERIALIZE → EXECUTE → COLLECT → RECOVER` | tasks/resources | runtime/lease receipts | PR #117/#122 merged; live parity pending |
| `loop_wiki/loopx-resource-gc/`, `loop_wiki/lsp-pool/` | resource/intelligence plane | `INVENTORY/PIN → QUERY/PLAN → FRESHNESS → EVICT/CLEAN` | leases/workspace | cleanup/diagnostic receipts | PR #123/#124 merged; live provider #92 active |
| `loop_wiki/loopx-decision-memory/` | memory plane | `PROPOSE → AUTOMATED ADMIT → EVENT → PROJECT → EXPIRE/DELETE` | evidence proposal | memory events/projection | PR #125/#126 merged; not selected |
| `loop_wiki/loopx-source-ingest/`, `loop_wiki/loopx-notes-retrieval/` | Notes input/projection | `DECLARE → CAPTURE/HASH → MANIFEST → BUILD/QUERY/READBACK` | authorized sources | evidence manifest + retrieval projection | PR #127/#128 merged; not selected |
| `loop_wiki/loopx-knowledge-compiler/`, `loop_wiki/loopx-knowledge-foldback/` | knowledge/code bridge | `EVIDENCE → SPEC/CODEOP → CANDIDATE → VERIFIED DIFF → PATCH` | Notes/code/runtime evidence | scaffold + knowledge patch | PR #118/#119 merged; ordered acceptance pending |
| `loop_wiki/loopx-context-assembly/`, `loop_wiki/loopx-skill-evolution/` | context/evolution plane | `PROMPT IR → HOST RENDER → BASELINE/CANDIDATE → HOLDOUT` | Skills/cards/memory/task | prompts/recommendation | PR #129/#120 merged; ordered acceptance pending |
| `loop_wiki/loopx-observability/`, `apps/harness-console/`, `services/hitl-api/` | projection/HITL surface | `EVENT → REDACT → PROJECT → INSPECT → REQUEST` | ledger/evidence refs | UI + decision request | PR #116/#131/#134 merged; not selected |
| `loop_wiki/loopx-benchmark/` | measurement plane | `PIN → TRIALS → COMPARABILITY → SCOPED CLAIM` | exact profile/workload | raw trials/report | PR #132/#135 merged; ordered acceptance pending |
| `scripts/git-town/`, `tests/git-town/`, `docs/git/runtime/` | `git-town-runtime` | `CONTRACT → PREFLIGHT → CONTROL → DECISION → RECEIPT` | profile/task/executable evidence | local sync/publication lanes | controller + 13 controls PASS; executable `ABSENT` |
| `.git-town.toml` | future admitted Git Town config | `PROFILE → CONFIG CANDIDATE → CANARIES → AUTOMATED ADMIT` | admitted executable + profile | deterministic local config | `ABSENT` |
| final composition/locks/receipts | issue #68 | `PIN TERMINALS → SELECT → LOCK → PROVE → LIVE → RELEASE` | admitted terminal subjects | release/rollback | blocked at active #92 |

## Git Town Stack State Machine

```text
SHARED METHOD PINNED
→ REPO PROFILE VALIDATED
→ TASK PACKET ACCEPTED
→ BRANCH GRAPH VALIDATED
→ WORKTREE / BRANCH / PATH LEASED
→ DRY RUN
→ LOCAL SYNC CANDIDATE
→ EVALS
→ EXACT-HEAD PUBLICATION CHECKS
→ CONVERGENCE
→ AUTOMATED ADMIT
→ MERGE / SHIP / ROLLBACK
```

Current state:

```text
method pin                  PINNED
profile/index docs          IMPLEMENTED
controller mechanism       IMPLEMENTED; 13 physical controls PASS
binary/config               ABSENT
local sync                  NOT_EXERCISED
publication                 NOT_EXERCISED
automated admission         NOT_EXERCISED
```

## Stack graph versus module graph

```text
module graph
  answers: which capabilities, dependencies, conflicts and proof subjects compose?

Stack graph
  answers: which unmerged branch depends on which parent, who owns each path and where evidence lands?

LoopX task graph
  answers: which Todo may transition after which Gates and Quota event?
```

They are separate graphs. A branch relation cannot create module admission, and a module dependency cannot grant Git conflict authority.

## Historical molecular conflict

```text
PR #76 issue #64
PR #77 issue #64
same parent: feat/loopx-contract-v1
overlap:
  .arena/modules/loopx-worker-gateway/**
  loop_wiki/loopx-worker-gateway/**
  loopctl/workflow.lock
state: RESOLVED_BY_HUMAN
resolution: PR #76 admitted, PR #77 superseded, issue #82 complete
```

The verifier keeps the conflict explicit after resolution so later success cannot erase the duplicate-writer observation.

## Macro State Machine

```text
MODULE PROPOSED
→ manifest + README
→ path owner
→ composition requirement
→ dependency/conflict resolution
→ lock
→ Context Capsule
→ proof subjects
→ proof/control/mutation
→ release receipt
→ automated admission
```

Macro does not execute another module through private flags.

## Micro State Machine

```text
typed packet
→ contract/subject validation
→ bounded runtime or disposable worktree
→ artifact capture
→ independent Gate
→ 0 / 2 / 64
→ receipt
→ caller selects next edge
```

Micro cannot directly merge, promote, widen permissions or admit; it submits evidence to the automated controller.

## Missing LoopX state machine: remaining integration state

```text
INIT
→ OBJECTIVE_LOCKED
→ TODO_READY
→ DISPATCHED
→ RUNNING
→ VERIFYING
   ├─ GATES_PASSED → MEMORY_PROPOSED → READY_FOR_ADMIT
   ├─ RETRYABLE_FAILURE → RETRY_SCHEDULED
   ├─ QUOTA_EXCEEDED → HITL_WAIT
   ├─ CAPABILITY_MISMATCH → HANDOFF_REQUIRED
   ├─ BLOCKED
   └─ FAILED_TERMINAL
```

Required authority rule:

```text
strategy graph proposes
worker executes
gates observe
LoopX reducer alone commits
Automated controller alone admits
```

The reducer, ledger and surrounding mechanisms now exist. The missing edge is their selection into one release subject plus live provider/host/runtime evidence and final #68 admission.

## Proposed LoopX authority

```text
strategy proposes
Worker executes
Gates observe
LoopX reducer alone commits
Automated controller alone admits
```

Git Town, LangGraph, GitHub Actions, providers and UI remain outside canonical task-state authority.

## End-to-end data flow

```text
shared Skill release ─────────────┐
runtime-env release ──────────────┼─→ Bettor binding/profile
GitHub issue/PR metadata ─────────┘          │
                                             ▼
                                  module + Stack resolution
                                             │
                                             ▼
                               lock + Context + task packet
                                             │
                                             ▼
                            leased runtime / Worker execution
                                             │
                           ┌─────────────────┴─────────────────┐
                           ▼                                   ▼
                     code/artifacts                       OS exits/logs
                           └─────────────────┬─────────────────┘
                                             ▼
                                  Gates/control/mutation
                                             │
                                             ▼
                              receipt / LoopX event proposal
                                             │
                                             ▼
                                    convergence leaf
                                             │
                                             ▼
                                  Automated admission
```

## Change rules

1. New root placement updates `ARCHITECTURE.md` first.
2. New module gets manifest, README, ownership and proof/control/mutation.
3. New Stack leaf gets issue task packet, branch relation, path lease, evals, rollback and automation boundary.
4. Generated locks/receipts are regenerated.
5. Cross-module calls use typed public boundaries.
6. New provider separates declaration, install, health, data, execution and admission.
7. New Stack fact updates `README.md`, `docs/git/STACKED_PRS.md`, `docs/git/stack-prs.index.json` and [`../traceability/STACK_PR_INDEX.md`](../traceability/STACK_PR_INDEX.md).
8. Merge, ship, policy-declared conflict resolution and rollback are automation-policy-owned.
