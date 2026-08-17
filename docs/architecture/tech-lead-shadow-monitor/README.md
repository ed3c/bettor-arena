# Tech Lead + Shadow Architect Closure Monitor

This directory is the current closure-control surface for the order-13
Blindspots / Parallel Tech Lead / Code-Graph-RAG retirement program.

It does not own provider runtime, Git history reconciliation, Human admission,
PDF queue advancement, or release. It maps each real problem to one owner,
one State Machine, one evidence ceiling, and one next executable handoff.

## Read order

1. [`AGENTS.md`](AGENTS.md)
2. [`closure-matrix.json`](closure-matrix.json)
3. [`../../traceability/local-handoff-execution-queue.json`](../../traceability/local-handoff-execution-queue.json)
4. [`../../git/pdf-terminal-sequence.json`](../../git/pdf-terminal-sequence.json)
5. [`../../integration/CROSS_REPO_INTEGRATION.md`](../../integration/CROSS_REPO_INTEGRATION.md)
6. current GitHub issue / PR / exact head metadata

## Closure vocabulary

```text
SOURCE_PROPOSAL
→ MECHANISM_IMPLEMENTED
→ DETERMINISTICLY_VERIFIED
→ LIVE_OR_PHYSICAL_EXECUTED
→ HUMAN_ADMITTED
→ RELEASED
```

These stages do not collapse. A merged PR can implement a mechanism without
executing a live provider. A fixture can turn a mutation red without proving
production behavior. A Human-required transition cannot be imputed from green
CI. A release remains blocked until its own exact-subject admission exists.

## Tech Lead and Shadow ownership

| Role | Owns | Must not do |
|---|---|---|
| Tech Lead | problem decomposition, interface freeze, task DAG, writer/path/resource leases, convergence owner, Local Handoff Queue | self-certify the global objective, proxy live evidence, guess a semantic conflict |
| Shadow Architect | independent applicability review, contradiction detection, global-objective review, evidence-ceiling review, missing-owner registration | become a second state writer, silently edit the Builder branch, impute live PASS or Human Admit |

The Shadow reads the same exact subject through an independent evaluation path.
The Shadow emits findings and a closure verdict. The Tech Lead owns the change
plan and convergence. Neither role can replace a deterministic gate or Human
authority.

## Directory → State Machine → data contract

| Directory / route | Owner | State Machine | Inputs | Outputs | Evidence ceiling |
|---|---|---|---|---|---|
| `docs/architecture/tech-lead-shadow-monitor/` | closure monitor | `DISCOVER → CLASSIFY → MAP_OWNER → ASSERT_EVIDENCE → REGISTER_GAP → HANDOFF` | source proposals, issues/PRs, contracts, receipts | closure matrix, DAG, Agent route | document + deterministic consistency |
| `docs/traceability/local-handoff-execution-queue.json` | local handoff | `FREEZE_SUBJECT → ONE_ACTIVE_ITEM → RESOLVE_COMMAND → EXECUTE → ASSERT_RECEIPT → NEXT_EPOCH/BLOCK` | exact GitHub subject + host observations | host-private receipt + next epoch | local receipt required |
| `loop_wiki/code-truth-graph-v2/` | Blindspots/context funnel | `OBSERVE → COVERAGE/FRESHNESS → SOURCE READBACK → FOUND/CONTESTED/NO_FLOW/UNKNOWN` | source tree + deterministic/provider candidates | SQLite evidence + context plan | static unless a live receipt exists |
| `loop_wiki/parallel-agent-tech-lead/` | Parallel Tech Lead | `REQUEST → CONTRACT → CAPABILITY DAG → WORKERS → ATTEMPTS → CONVERGENCE → GLOBAL OBJECTIVE` | frozen task, context receipt, budgets, leases | Worker packets + comparison receipt | planner/fixture until physical run |
| `scripts/gates/` | deterministic gates | `LOAD SUBJECT → ASSERT → CONTROL/MUTATION → 0/2/64/70` | contracts, fixtures, exact bytes | typed verdict | declared gate subject only |
| `.runtime-env/` | runtime consumer | `DECLARE → RESOLVE → REBIND → MATERIALIZE → CANARY → RECEIPT` | immutable runtime release + local host root | secret-free binding + canary receipt | not exercised until local receipt |
| `docs/git/pdf-terminal-sequence.json` | PDF queue | `PREDECESSOR COMPLETE → ONE ACTIVE → TERMINAL RECEIPT → ADMIT → ADVANCE` | terminal receipts + GitHub metadata | active-order transition | order 13 remains active |
| `.arena/compositions/`, `data/module-proof/` | final convergence #68 | `SELECT → LOCK → PROVE → LIVE CANARIES → ADMIT → RELEASE/ROLLBACK` | admitted terminal subjects | immutable release + rollback | blocked by predecessors |

## Current process DAG

This is a **process/evidence dependency graph**, not a Git ancestry chain.

```text
#172 dual-origin reconciliation                         ACTIVE
  ↓ freeze a newly accepted exact subject
#161 runtime-env rebind + scheduler/process-worktree   BLOCKED
  ↓ exact local runtime receipt
#146 physical Tech Lead + independent Shadow run       BLOCKED
  ↓ exact aggregate physical receipts
#140 Human terminal admission + typed queue transition BLOCKED
  ↓ order-13 admission
#68 final composition / release / rollback             FINAL CONVERGENCE
```

Independent control-plane siblings:

```text
#173 closure monitor + Local Handoff authority
#174 workflow-lock receipt-status laundering
#175 origin-projection freshness
```

They do not consume #172's unmerged bytes and must not be represented as Git
children of #172.

## Molecular implementation and evidence index

| PR / issue | Relation | Delivered subject | State | Proven ceiling |
|---|---|---|---|---|
| PR #153 / #140 | `ROOT_AFTER_PREDECESSOR` | Blindspots SQLite evidence ledger | `MERGED_TO_MAIN` | deterministic static evidence |
| PR #155 / #138 | `ROOT_AFTER_PREDECESSOR` | exact-subject context funnel | `MERGED_TO_MAIN` | deterministic static evidence |
| PR #156 / #139 | `ROOT_AFTER_PREDECESSOR` | repository-owned Tech Lead planner | `MERGED_TO_MAIN` | planner/fixture; no physical Worker |
| PR #157 / #140 | `ROOT_AFTER_PREDECESSOR` | Code-Graph-RAG canonical retirement | `MERGED_TO_MAIN` | provider/route retirement |
| PR #158 / #140 | `CONVERGENCE` | deterministic order-13 convergence | `MERGED_TO_MAIN` | no queue advancement |
| PR #159 / #146 | `ROOT_AFTER_PREDECESSOR` | physical-run readiness | `MERGED_TO_MAIN` | readiness only |
| PR #169 | `ROOT_AFTER_PREDECESSOR` | old `#161 → #146 → #140` handoff contract | `MERGED_TO_MAIN` | queue declaration, not execution |
| PR #154 / #146 | `ROOT_AFTER_PREDECESSOR` | Parallel Tech Lead consumer adoption | `MERGED_TO_MAIN` | contract adoption, not Worker run |
| issue #172 | `PROCESS_DEPENDENCY` | dual-origin reconciliation | `ACTIVE` | no reconciliation receipt yet |
| issue #161 | `PROCESS_DEPENDENCY` | exact runtime rebind/canary | `BLOCKED_BY_PREDECESSOR` | no local receipt yet |
| issue #146 | `PROCESS_DEPENDENCY` | physical Tech Lead/Shadow golden run | `BLOCKED_BY_PREDECESSOR` | no physical run yet |
| issue #140 | `PROCESS_DEPENDENCY` | Human order-13 admission | `BLOCKED_BY_PREDECESSOR` | Human Admit absent |
| issue #174 | `SIBLING` | receipt-status repair | `PLANNED` | confirmed deterministic defect |
| issue #175 | `SIBLING` | origin freshness repair | `PLANNED` | confirmed deterministic defect |
| issue #68 | `CONVERGENCE` | final release/rollback | `FINAL_CONVERGENCE` | not performed |

PR #81 is a merged historical governance foundation (`9b4a30e835b22f48a7ee8b3c26a44d89929eb63d`).
It introduced earlier README/AGENTS/Stack governance, but its machine snapshot
was not current for the order-13 closure subject. PR #176 refreshes the current
snapshot; it does not replace or undo PR #81's admitted bytes.

## Source-proposal problem closure

| Problem from the source proposal | Mechanism | Deterministic | Live / physical | Human | Release |
|---|---|---|---|---|---|
| deterministic → semantic → deterministic → Human pipeline | CTL contracts/linter/evidence lanes | `PASS` for shipped deterministic controls | semantic rewrite and carrier runs `NOT_EXERCISED` | safety/compliance required | blocked |
| Project TN/TV termbase | fixture contracts exist | fixture controls `PASS` | production termbase `ABSENT` | terminology admission required | blocked |
| Warning/Caution meaning preservation | structured preservation contracts exist | fixture controls exist | production manual review `NOT_EXERCISED` | required | blocked |
| confidential/local execution | privacy routing contract exists | policy controls `PASS` | external confidential canary `NOT_EXERCISED` | approval required | blocked |
| multi-hop Agent docs | root routes + this nearest route | repository checks | passive-context/live host load varies | not a substitute for admission | n/a |
| atomic Stack traceability | shared Git Town procedure + current index | deterministic index controls | Git Town executable/no-push run `NOT_EXERCISED` | semantic conflict/merge required | blocked |
| intent promotion and memory hygiene | promotion contracts exist | deterministic controls `PASS` | production writeback `NOT_IMPLEMENTED` | durable/root promotion required | blocked |
| physical parallel Tech Lead | planner/readiness exist | contracts/fixtures `PASS` | `NOT_EXERCISED` | final admission required | blocked |
| independent Shadow/global objective | Shadow procedure exists | fixture/rubric controls `PASS` | same-subject independent run `NOT_EXERCISED` | final admission required | blocked |

## Current Local Handoff epoch

Canonical queue:

```text
docs/traceability/local-handoff-execution-queue.json
```

Deprecated duplicate removed:

```text
docs/git/local-handoff-execution-queue.json
```

Current epoch:

```text
subject: GitHub publication main
commit: 4655b18a150716ad7a3a0edbe3201fd2927eef80
tree:   849328ac84c770d5932a16b4a3a9f0946dff8dba

ACTIVE: #172 dual-origin reconciliation
NEXT:   none in this epoch
```

After #172 produces an admitted reconciliation receipt, generate a **new queue
epoch** bound to the new exact subject for `#161 → #146 → #140`. Do not edit the
old epoch to chase mutable `main`.

## End-to-end data flow

```text
PDF / article / issue / current repository observation
        ↓ classify SOURCE_PROPOSAL vs current fact
Tech Lead task and capability decomposition
        ↓
Shadow independent applicability / contradiction / evidence-ceiling review
        ↓
exact task DAG + one writer/path/resource lease per leaf
        ↓
deterministic Blindspots/context/plan gates
        ↓
Local Handoff Queue when host/runtime evidence is unavailable
        ↓
dual-origin reconciliation receipt
        ↓ new immutable queue epoch
runtime rebind + process/worktree canary
        ↓
physical Tech Lead attempts + independent Shadow/global objective
        ↓
exact aggregate receipts + cleanup
        ↓
Human order-13 admission
        ↓
typed queue advance
        ↓
remaining terminals
        ↓
#68 final composition, live canaries, release and rollback
```

## Local Handoff Execution Queue for the Tech Lead

```text
P0  #172 reconcile local / Forgejo / GitHub exact histories
P1  emit a newly frozen subject and next queue epoch
P2  #161 bind runtime-env and run scheduler/process-worktree canary
P3  #146 run physical Tech Lead plus independent Shadow
P4  #140 obtain Human terminal admission and use typed queue transition
P5  continue order 14+ and converge through #68
```

Separate path-disjoint queue:

```text
S1  #174 repair workflow-lock receipt-status admission
S2  #175 bind origin projection freshness to exact-tree admission
```

## Evidence boundary

This monitor can prove document routing, one queue authority, exact subject
binding, DAG consistency, issue/PR lineage, and honest evidence ceilings.

It cannot prove:

```text
dual-origin reconciliation
local scheduler/worktree execution
live GrepAI / SCIP / LSP / Tree-sitter / Serena
physical multi-Agent behavior
live Codex / Claude carrier quality
Git Town execution or remote publication
production TN/TV or manual safety
confidential external processing approval
Human admission
release or rollback
```
