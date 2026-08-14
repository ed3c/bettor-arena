# Directory → State Machine ownership map

## Purpose

This document binds repository placement to state-machine responsibility. It is a human route over current machine contracts; it does not replace `module.json`, `loopctl/contract.json`, composition locks, scripts, tests or receipts.

A directory may own one of four things:

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
Skill requirement and repo-owned binding
        ↓
module composition requirements
        ↓
deterministic lock + Context Capsules
        ↓
loopctl public request
        ↓
bounded module runtime / disposable workspace
        ↓
proof + control + mutation/hollow
        ↓
subject-bound receipt
        ↓
Human Admit / merge / release / rollback
```

The PDF's proposed LoopX ledger would sit between the public request and module runtime. That ledger is not currently implemented.

## Directory ownership and state machines

| Directory or route | Owning plane/module | State machine | Inputs | Outputs | Current state |
|---|---|---|---|---|---|
| `README.md`, `AGENTS.md`, `CLAUDE.md`, `CONTEXT.md`, `ARCHITECTURE.md` | `arena-core` / repository law | `ENTRY → ROUTE → OWNER → CONTRACT → EVIDENCE` | task, repository subject | bounded read route | `IMPLEMENTED` |
| `docs/architecture/` | architecture/status owner | `SOURCE_PROPOSAL → TARGET → CURRENT STATUS → GAP → ACCEPTANCE` | PDF/design/incident | normative target and mutable status | `IMPLEMENTED` |
| `docs/traceability/` | delivery/traceability owner | `SOURCE → ISSUE → SLICE → PR → EVAL → RECEIPT → ADMIT` | issue/PR metadata | indexed molecular graph | `IMPLEMENTED` |
| `.agents/skills/` | projected Skill surface | `REQUIRE → RESOLVE → PROJECT → DISCOVER` | shared/repo-owned Skill requirement | one host-neutral Skill projection | `IMPLEMENTED` |
| `.skill-bindings/` | consumer/domain binding | `UPSTREAM SKILL → RETARGET → ASSERT → CONSUMER RECEIPT` | immutable Skill identity | repo-specific route/provider binding | `IMPLEMENTED` |
| `.runtime-env/` | runtime consumer projection | `DECLARE → RESOLVE → MATERIALIZE → OFFLINE VERIFY → LIVE CANARY` | secret-free runtime release | binding/workload/policy projection | mechanism `IMPLEMENTED`; live routes vary |
| `.arena/modules/` | `module-catalog` | `PROPOSED → CONTRACTED → COMPOSED → PROVED → RELEASED` | module manifests | capabilities, owners and proof commands | `IMPLEMENTED` |
| `.arena/compositions/` | `module-catalog` | `DESIRED MODULES → CAPABILITY RESOLUTION → CONFLICT CHECK` | requirements | desired composition | `IMPLEMENTED` |
| `.arena/locks/` | `module-catalog` generated projection | `REQUIREMENTS → RESOLVE → DIGEST → LOCK` | manifests and requirements | deterministic composition lock | mechanism `IMPLEMENTED`; exact lock must be current |
| `.arena/contexts/` | `loop-runtime` + module owners | `SELECT → MATERIALIZE → FREEZE → DRIVER PREPARE → CANARY` | immutable repo ref and native files | Context Capsule digest and driver receipt | offline mechanism `IMPLEMENTED`; live host canaries `NOT_EXERCISED` |
| `.arena/origins/`, `.arena/browser/` | `environment-contracts` | `DECLARE → PROBE → RECEIPT → EQUIVALENCE/ROUTE → ADMIT` | origin/browser contract | status and canary receipt | contracts `IMPLEMENTED`; external routes vary |
| `loopctl/` | `loop-runtime` | `PARSE → VALIDATE CONTRACT → DISPATCH PUBLIC PORT → PROPAGATE 0/2/64` | typed CLI request | named artifacts/receipts | `IMPLEMENTED` |
| `mcp/` | `mcp-adapters` | `POLICY DENY → TOOL PROJECT → IMMUTABLE WORKSPACE → EXECUTE → CLEANUP` | canonical CLI contract and policy | typed JSON-RPC result | `IMPLEMENTED` for admitted tools |
| `proof_workflow/` | `proof-kernel` | `CLAIM → PHYSICAL TRAVERSAL → INDEPENDENT CONTROL → MUTATION → RECEIPT` | module public port and context | proof/control/mutation evidence | `IMPLEMENTED` |
| `data/module-proof/` | generated evidence | `MODULE SUBJECTS → CLOSURE → RELEASE AGGREGATION` | locks and proof specs | subject lock and release receipt | mechanism `IMPLEMENTED`; current evidence may be `NOT_EXERCISED` |
| `loop_wiki/evolve-perfect-seed-repo-factory/` | `perfect-seed-factory` | `PACKET → BUILD → FAST QUALITY → OPERATOR → VALIDATOR → HUMAN EDGE` | typed task/source packet | seed repo and wiki-update request | `IMPLEMENTED` |
| `kb-ingest/`, `openwiki/` | `openwiki` | `REQUEST → CONTRACT CHECK → DRY RUN/FULL OPT-IN → VERIFY → RECEIPT` | wiki-update request | tracked wiki projection and receipt | mechanism `IMPLEMENTED`; full run subject-specific |
| `loop_wiki/code-truth-graph/` | `code-truth-graph` | `CLOSED PACKET → PIN TOOLS → PARSE/BUILD → VERIFY → GRAPH ARTIFACT` | source-bound packet | graph/result artifacts | `IMPLEMENTED` |
| `notebooklm/` | `notebooklm` | `TARGET → AUTH/RESOLVE → READ → OPTIONAL FOLLOW → SCRATCH CLEANUP → RECEIPT` | registry target or notebook title | bounded harvest artifacts | mechanism `IMPLEMENTED`; account route subject-specific |
| `docs/knowledge-providers/` | `knowledge-providers` | `MANIFEST → BOUNDED QUERY/PROPOSAL → RECEIPT → SOURCE READBACK → ADMIT` | exact subject and provider capability | candidate result or memory proposal | contracts `IMPLEMENTED`; live providers not admitted |
| `scripts/gates/`, `tests/` | `arena-core` / `proof-kernel` | `POSITIVE → HOLLOW/MUTATION → EXACT-TREE CHECK` | tracked tree | deterministic exit and diagnostics | `IMPLEMENTED` |
| `data/` | evidence projection | `EXECUTION → NORMALIZE → HASH → STORE → REPLAY/COMPARE` | tool/OS/runtime output | receipts and status snapshots | mixed by exact receipt |
| `.github/workflows/` | cloud verifier | `EVENT → CHECKOUT EXACT SUBJECT → GATE → STATUS` | PR/push subject | GitHub check | `IMPLEMENTED`; a stale head or skipped run is not PASS |
| `.loopx/` | proposed LoopX kernel | `INIT → DISPATCH → EXECUTE → GATE → REDUCE → RETRY/HITL/COMPLETE` | Objective/Todos/Gates/Evidence/Quota | event ledger and derived task snapshot | `NOT_IMPLEMENTED` |
| LangGraph strategy package | proposed strategy plane | `PLAN → PROPOSE COMMAND → INTERRUPT/RESUME` | LoopX snapshot and capabilities | typed command/decision receipt | `NOT_IMPLEMENTED` |
| worker fleet (`herdr`, Grok/OpenCode/Pi/Codex/Claude/Ante adapters) | proposed execution plane | `PROBE → LEASE → MATERIALIZE → EXECUTE → COLLECT → DISPOSE` | Context Capsule and task packet | normalized Worker result | contract fragments exist; live matrix `NOT_EXERCISED` |
| observability/UI | proposed projection plane | `EVENT → REDACT → PROJECT → INSPECT → SIGNED HUMAN ACTION` | immutable event/artifact refs | trace, dashboard and HITL receipt | `NOT_IMPLEMENTED` |

## Current Macro state machine

```text
MODULE PROPOSED
→ manifest + sibling README
→ tracked-path owner assigned
→ composition requirement selected
→ capability/dependency/conflict resolution
→ deterministic composition lock
→ Context Capsule lock
→ module closure subjects
→ proof/control/mutation evidence
→ release receipt
→ Human Admit
→ merge / promote / rollback
```

Macro owns composition and admission. It must not edit a module through private flags.

## Current Micro state machine

```text
typed packet or public CLI request
→ contract and subject validation
→ bounded runtime or disposable worktree
→ artifact capture
→ independent assertion/gate
→ named exit 0 / 2 / 64
→ receipt
→ caller decides next edge
```

Micro does not Human Admit, merge, promote, widen permissions or perform production rollback.

## Missing LoopX state machine

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
Human alone admits
```

The current repository does not yet provide this reducer or ledger.

## End-to-end current data flow

```text
shared Skill release ──┐
                       ├─→ Bettor binding + module composition
runtime-env release ───┘                │
                                        ▼
                               immutable context/lock
                                        │
                                        ▼
                               loopctl / default-deny MCP
                                        │
                                        ▼
                            bounded module or Skill runner
                                        │
                        ┌───────────────┴───────────────┐
                        ▼                               ▼
                 source/artifacts                 OS exit/logs
                        └───────────────┬───────────────┘
                                        ▼
                              proof/control/mutation
                                        │
                                        ▼
                               subject-bound receipt
                                        │
                                        ▼
                               Human Admit / release
```

## Change rules

1. New root directory: update `ARCHITECTURE.md` placement contract first.
2. New module: add `module.json`, sibling `README.md`, ownership, composition requirement, Context Capsule and proof spec.
3. State-machine change: name owner, inputs, outputs, transitions, terminal states, evidence and Human boundary.
4. Generated lock/receipt: regenerate; never hand-author a digest.
5. Cross-module call: use capability/public port and typed packet, not private imports.
6. New provider or worker: separate declaration, installation, health, data readiness, execution, proof and admission.
7. New Stack leaf: update [`../traceability/STACK_PR_INDEX.md`](../traceability/STACK_PR_INDEX.md).
