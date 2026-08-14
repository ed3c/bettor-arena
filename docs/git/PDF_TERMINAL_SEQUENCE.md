# Ordered PDF terminal Git Town Stack

## Purpose

This document is the repository-owned execution queue for the remaining architecture in the 41-page **LLM 泛化：模型權重與 Harness** source proposal.

The PDF proposes a model-independent Harness around:

```text
Objective + Todos + Gates + Evidence + Quota
→ dispatch
→ isolated Worker execution
→ out-of-band deterministic verification
→ retry / quota debit
→ HITL or completion
```

It also proposes Strategy Graphs, episodic memory, heterogeneous Agents, worktree fleets, cloud/local execution, OpenWiki/vector retrieval, observability and a HITL console. The PDF is a requirement and hypothesis source, not current repository truth.

Machine companion:

- [`pdf-terminal-sequence.json`](pdf-terminal-sequence.json)
- [`pdf-terminal-sequence.schema.json`](pdf-terminal-sequence.schema.json)

Program and final convergence:

```text
program issue:     #61
index issue:       #102
current item:      order 0 / issue #82
final convergence: order 25 / issue #68
```

## Two graphs, one ordered completion rule

The **completion queue** and the **Git branch graph** are related but not identical.

```text
Completion queue
  serializes when a terminal may be called complete

Git Town branch graph
  records actual byte dependency
  ├─ sibling: independent path-disjoint bytes
  ├─ true child: consumes unmerged parent bytes
  └─ convergence: owns shared locks, indexes and release
```

A global order does not justify a 26-deep branch chain. Future branches remain uncreated until their queue item becomes active. When a predecessor has merged, the next path-disjoint terminal starts from the new `main`; when it needs unmerged predecessor bytes, it becomes a true child.

Only one queue item may be `ACTIVE`. A later item cannot be reported complete unless every predecessor is complete on an immutable subject or a Human has recorded an explicit scoped waiver.

A landed stage is marked `COMPLETE`, and the `ACTIVE` item is **derived**: it is the lowest-ordered item that is not `COMPLETE`. The gate checks that relation rather than naming a stage, so advancing the queue is a data change and not a gate change — the earlier rule pinned the head to *order 0 / issue 82*, which made finishing a stage require editing the assertion, and the snapshot went stale instead of advancing.

`COMPLETE` items must form a prefix. A stage finished ahead of its predecessor leaves a hole that reads correctly item by item and is wrong only in sequence, so `STRICT_GLOBAL_COMPLETION` requires the Human waiver named above to be recorded rather than left as a gap.

## Authority law

```text
Strategy proposes
Worker executes
Gates observe
LoopX reducer alone commits canonical task state
Human alone admits semantic conflict, scoped exceptions, merge, promotion and rollback
```

Git Town may eventually synchronize an admitted local branch hierarchy. It cannot decide semantic conflicts, publish remotely, merge, ship, promote or roll back.

## Current foundation already reachable from `main`

The following bytes have landed through PR #74 and its children:

| Issue / PR | Mechanism | Reachability | What it does not prove |
|---|---|---|---|
| #62 / #74 | LoopX Contract v1 | `MERGED_TO_MAIN` | live runtime, composition selection or release |
| #63 / #75 | append-only Ledger and reducer | `MERGED_TO_MAIN` through #74 | distributed lease or production activation |
| #64 / #76 | host-neutral Worker Gateway | `MERGED_TO_MAIN` through #74 | any real Codex/Claude/Grok/OpenCode/Pi/Ante run |
| #42 / #78 | Decision Memory contracts | `MERGED_TO_MAIN` through #74 | durable memory event lifecycle or Mem0 |
| #69 / #79 | Code Truth Graph v2 | `MERGED_TO_MAIN` through #74 | live LSP, provider or production telemetry coverage |

PR #77 is a closed superseded Worker Gateway candidate. Issue #82 owns executable comparison and disposition of its eight unique files.

## Ordered terminal queue

| Order | Issue(s) | Expected branch | Terminal behavior | Queue state |
|---:|---|---|---|---|
| 0 | #82 | `feat/loopx-worker-gateway-residue-v1` | fold or reject PR #77-only files with execution evidence | `COMPLETE` |
| 1 | #90 | `feat/loopx-stage0-validation-v1` | validate current-main Contract/Ledger/Gateway/Memory/CTG | `COMPLETE` |
| 2 | #65 | `feat/loopx-strategy-hitl-v1` | Strategy Graph plus interrupt/resume/scoped exception | `COMPLETE` |
| 3 | #67 | `feat/loopx-observability-v1` | redacted event projection and signed HITL requests | `COMPLETE` |
| 4 | #66 | `feat/loopx-runtime-fabric-v1` | physical runtime leases, isolation, cleanup and local/cloud parity | `COMPLETE` |
| 5 | #94 | `feat/loopx-worker-fleet-v1` | Herdr/tmux-compatible queue, worktree and resource leases | `COMPLETE` |
| 6 | #97 | `feat/loopx-resource-gc-v1` | worktree/artifact/cache/vector/graph/WAL retention and GC | `COMPLETE` |
| 7 | #96 | `feat/loopx-lsp-pool-v1` | worktree-aware LSP pool and bounded CLI fallback | `ACTIVE` |
| 8 | #103 | `feat/loopx-decision-memory-runtime-v1` | Human-admitted canonical memory events and lifecycle | `BLOCKED_BY_PREDECESSOR` |
| 9 | #93 | `feat/loopx-mem0-projection-v1` | Mem0 as an optional rebuildable projection | `BLOCKED_BY_PREDECESSOR` |
| 10 | #104 | `feat/loopx-notes-source-ingest-v1` | authorized YT/PDF/transcript/keyframe source manifest | `BLOCKED_BY_PREDECESSOR` |
| 11 | #105 | `feat/loopx-notes-retrieval-v1` | OpenWiki static plus optional vector/graph Notes projections | `BLOCKED_BY_PREDECESSOR` |
| 12 | #92 | `feat/loopx-code-intelligence-canaries-v1` | live Serena/GrepAI freshness and source-readback canaries | `BLOCKED_BY_PREDECESSOR` |
| 13 | #41 | `feat/code-graph-rag-readonly-admission-v1` | read-only Code-Graph-RAG runtime admission | `BLOCKED_BY_PREDECESSOR` |
| 14 | #70 | `feat/loopx-notes-scaffold-v1` | evidence/cards/spec/CodeOp to disposable scaffold | `BLOCKED_BY_PREDECESSOR` |
| 15 | #71 | `feat/loopx-code-knowledge-foldback-v1` | verified code/runtime delta to knowledge patch | `BLOCKED_BY_PREDECESSOR` |
| 16 | #95 | `feat/loopx-context-assembly-v1` | prompt-cache-stable prefix and bounded dynamic suffix | `BLOCKED_BY_PREDECESSOR` |
| 17 | #72 | `feat/loopx-skill-prompt-evolution-v1` | current/candidate/no-skill, mutations and sealed holdout | `BLOCKED_BY_PREDECESSOR` |
| 18 | #98 | `feat/loopx-ci-parity-v1` | local/native/optional-act versus exact-head GitHub CI | `BLOCKED_BY_PREDECESSOR` |
| 19 | #91 | `feat/loopx-six-host-live-matrix-v1` | Codex, Claude, Grok Build, OpenCode, Pi and Ante receipts | `BLOCKED_BY_PREDECESSOR` |
| 20 | #45 | `feat/loopx-codex-claude-ab-v1` | paired Codex/Claude behavioral A/B | `BLOCKED_BY_PREDECESSOR` |
| 21 | #46 / #56 | `eval/loopx-provider-convergence-v1` | provider/control comparison and evaluator convergence | `BLOCKED_BY_PREDECESSOR` |
| 22 | #99 | `feat/loopx-harness-console-v1` | task graph, evidence, diff, quota and signed HITL UI | `BLOCKED_BY_PREDECESSOR` |
| 23 | #100 | `feat/loopx-benchmark-v1` | profile-scoped runtime/context/LSP/host/local-cloud evidence | `BLOCKED_BY_PREDECESSOR` |
| 24 | #101 | `feat/git-town-runtime-admission-v1` | pinned Git Town executable/config and no-push canaries | `BLOCKED_BY_PREDECESSOR` |
| 25 | #68 | `integration/loopx-harness-convergence-v1` | shared composition, cold-start/live acceptance, release and rollback | `FINAL_CONVERGENCE` |

The machine queue contains prerequisites, path owners, acceptance evidence and Human boundaries for every row.

## Directory → State Machine responsibility

| Directory or planned route | State Machine | Inputs | Outputs | Authority ceiling |
|---|---|---|---|---|
| `loop_wiki/loopx-kernel/` | `TASK_DECLARED → TODO_READY → GATES → QUOTA → TERMINAL` | typed task/command/event | validated contract/snapshot | schema and reducer law |
| `loop_wiki/loopx-ledger/` | `APPEND → HASH/LEASE → REDUCE → SNAPSHOT → REPLAY` | accepted events | canonical ledger and rebuildable snapshot | sole task-state writer |
| `loop_wiki/loopx-strategy-hitl/` | `SNAPSHOT → PROPOSE → INTERRUPT → SIGNED DECISION → REVALIDATE` | ledger-bound snapshot | command/decision proposal | proposal only |
| `loop_wiki/loopx-runtime-fabric/` | `PROBE → LEASE → MATERIALIZE → EXECUTE → COLLECT → CLEANUP` | Worker request and policy | attested runtime receipt | physical execution only |
| `loop_wiki/loopx-worker-fleet/` | `QUEUE → BRANCH/WORKTREE/PATH LEASE → DISPATCH → GC` | task packet/dependencies | Worker and lease receipts | scheduling only |
| `loop_wiki/loopx-resource-gc/` | `INVENTORY → DRY PLAN → ADMIT → CLEAN → RESIDUE/REBUILD` | leases and retention | cleanup/tombstone receipt | no silent history deletion |
| `loop_wiki/lsp-pool/` | `SERVER/WORKSPACE PIN → QUERY → FRESHNESS → EVICT` | exact workspace subject | diagnostics/reference receipt | candidate evidence only |
| `loop_wiki/loopx-decision-memory/runtime/` | `PROPOSE → VALIDATE → HUMAN ADMIT → LEDGER EVENT → EXPIRE/DELETE` | evidence-bound proposal | canonical memory event | reducer/Human only |
| `notes-ingest/` | `DECLARE → AUTHORIZE → CAPTURE → HASH → LOCATE → MANIFEST` | YT/PDF/transcript/frame/code/log | immutable source/evidence manifest | no fabricated media/locator |
| `notes-retrieval/` | `PIN NOTES → BUILD STATIC/VECTOR/GRAPH → QUERY → READBACK → REBUILD` | Notes Repo release | retrieval projection | never source truth |
| `loop_wiki/notes-scaffold/` | `EVIDENCE → CARDS → SPEC IR → CODEOP → SCAFFOLD → GATES` | knowledge release | candidate scaffold and mapping | no automatic code/knowledge admit |
| `loop_wiki/code-knowledge-foldback/` | `DIFF/RUNTIME → AFFECTED KNOWLEDGE → PATCH → HUMAN ADMIT` | verified code evidence | update/supersede/conflict/noop patch | no automatic rewrite |
| `loop_wiki/loopx-context-assembly/` | `PROMPT IR → STABLE PREFIX → BOUNDED SUFFIX → HOST PROJECTION` | Skills/cards/memory/task | content-addressed host prompts | rendering only |
| `evals/loopx-skill-prompt/` | `BASELINE/CANDIDATE → DEV/MUTATION → HOLDOUT → CROSS-HOST` | identical execution contract | candidate recommendation | no automatic promotion |
| `data/host-canaries/` | `IDENTITY → EXECUTE → GATES → CLEANUP → RECEIPT` | six host adapters | independent host states | no cross-host proxy |
| `apps/harness-console/` | `PROJECT → INSPECT → DRAFT SIGNED REQUEST → LOOPX VALIDATE` | redacted ledger/evidence | UI and decision request | read/proposal only |
| `benchmarks/loopx/` | `PIN → RAW TRIALS → COMPARABILITY → PROFILE REPORT` | exact workload/environment | raw trials and scoped claims | no universal overreach |
| `docs/git/runtime/` | `PIN TOOL → DRY NO-PUSH → LIVE NO-PUSH → PUBLICATION GATE` | Git Town Skill/profile | local sync/publication receipts | no merge/ship authority |
| `.arena/compositions/`, locks and `data/module-proof/` | `SELECT → RESOLVE → LOCK → PROVE → RELEASE` | admitted terminal subjects | final immutable release | owned only by #68 |

## End-to-end ordered data flow

```text
PDF / issue / source incident
  ↓ source authority and destination authorization
#104 immutable Notes source manifest
  ↓
#105 OpenWiki + vector/graph candidate projections
  ↓
#70 evidence/assertions/cards/System Spec IR/CodeOp
  ↓
#66/#94 disposable leased execution
  ↓
#65 strategy proposal → Worker Gateway → host execution
  ↓
host-owned Gates + Ledger reducer
  ├─ failure → Quota → #103 memory proposal/event → retry/HITL
  └─ pass    → verified code/runtime artifacts
                   ↓
                  #71 fold-back candidate
                   ↓
                  #95 Context Assembly
                   ↓
                  #72 Skill/Prompt evolution
                   ↓
                  #91 six-host matrix + #92/#41/#93 providers
                   ↓
                  #98 CI parity + #67/#99 observability/HITL
                   ↓
                  #100 scoped benchmark + #101 Git Town runtime
                   ↓
                  #68 final composition/cold-start/release
                   ↓
                  Human Admit → promote | rollback
```

No provider, graph, memory cache, OpenWiki page, UI state, local CI simulator, Git Town exit code or model prose can skip the Gate, reducer and Human boundaries.

## Terminal completion contract

A terminal may advance the queue only when all of the following are attached to one immutable subject:

```text
machine contract
nearest README with State Machine and data flow
positive execution or bounded fixture
independent control
hollow or planted mutation that turns red
exact commit/tree/tool/context identities
bounded artifacts and cleanup/residue receipt
rollback subject
honest PASS / FAIL / ABSENT / NOT_IMPLEMENTED / NOT_EXERCISED / SKIPPED_BY_POLICY state
exact-head GitHub checks when a PR exists
Human review for merge or activation
```

A fixture PASS cannot proxy live host/provider/runtime health. `MERGED_TO_PARENT` cannot proxy `MERGED_TO_MAIN`. Current-main reachability cannot proxy composition selection or production promotion.

## Unsafe source examples that remain rejected

The PDF includes useful architectural proposals and unsafe illustrative shortcuts. Production terminals must continue to reject:

- raw shell strings and `shell=True`;
- Agent or Worker direct writes to task state or Gate verdicts;
- generic `force_skip`;
- LangGraph checkpoint, trace store, UI or memory index as canonical state;
- raw Thought Stream or private chain-of-thought persistence;
- provider/model output promoted to `TESTED` or PASS;
- automatically merging branches after a Gate;
- performance, memory, cost, security or license claims without exact receipts.

## Update protocol

Whenever a queue item, issue, branch, PR, exact head, path lease or state changes, update together:

1. [`pdf-terminal-sequence.json`](pdf-terminal-sequence.json)
2. this document
3. [`STACKED_PRS.md`](STACKED_PRS.md)
4. [`../traceability/STACK_PR_INDEX.md`](../traceability/STACK_PR_INDEX.md)
5. root `README.md` and `AGENTS.md` when active item or route changes
6. deterministic sequence verifier and exact-head checks

Do not create future implementation branches merely to make the tree look complete. Create the next branch only after the queue advances or a Human records a scoped exception.
