# bettor-arena

> **Module Host + Loop Runtime + Proof Kernel + Stateless MCP Gateway + Project Bootstrapper**

`bettor-arena` 將 bounded loops、portable Skills、runtime projections、proof controls、knowledge projections 與 release evidence 組合成可追溯的 Agent Harness。外部 consumer 只依賴穩定的 `loopctl`／MCP contract；內部 implementation 透過 module、typed packet、subject-bound receipt、ordered terminal queue 與 Human Admit 演進。

## Current publication subject

```text
GitHub repository:     ed3c/bettor-arena
observed main at start: 844b7121789e57ebe00f1a07a67b27c1542cf05b
program issue:          #61
index issue:            #102
branch:                 docs/pdf-terminal-stack-sequence-v1
current active item:    #82
final convergence:      #68
```

GitHub base/head metadata, reachability and exact-head checks are publication truth. Markdown and machine indexes are reviewed snapshots, not substitutes for GitHub.

## LoopX Harness PDF integration verdict

<!-- PDF Harness Integration verdict -->

The attached 41-page **LLM 泛化：模型權重與 Harness** PDF is a requirement and hypothesis source. It proposes a LoopX state kernel around Objective, Todos, Gates, Evidence and Quota, deterministic out-of-band verification, heterogeneous Workers, LangGraph HITL, episodic memory, worktree fleets, cloud/local execution, static/vector knowledge compilation and observability.

Current repository verdict:

```text
module composition / ownership / proof foundation        IMPLEMENTED
hard gates / control / mutation / subject receipts       IMPLEMENTED
portable Skill → host-owned typed execution              IMPLEMENTED
Context Capsules / OpenWiki / provider-neutral contracts IMPLEMENTED
LoopX Contract / Ledger / Gateway mechanisms on main     IMPLEMENTED FOUNDATION
Decision Memory contracts / Code Truth Graph v2 on main  IMPLEMENTED FOUNDATION

complete integrated LoopX runtime                        PARTIAL
Strategy Graph + signed HITL                             NOT_IMPLEMENTED
physical Runtime Fabric + local/cloud parity             NOT_IMPLEMENTED / NOT_EXERCISED
Worker Fleet / resource GC / LSP pool                    NOT_IMPLEMENTED
canonical Decision Memory lifecycle + Mem0 projection    NOT_IMPLEMENTED
YT/PDF Notes source ingest and retrieval release         NOT_IMPLEMENTED
Notes → Scaffold → Code → Knowledge fold-back            NOT_IMPLEMENTED
prompt-cache-stable Context Assembly                     NOT_IMPLEMENTED
Skill/Prompt evolution sealed holdout                     NOT_IMPLEMENTED
six-host live execution matrix                           NOT_EXERCISED
Serena/GrepAI/Code-Graph-RAG live admission               NOT_EXERCISED / NOT_IMPLEMENTED
observability / Harness Console                          NOT_IMPLEMENTED
Git Town executable/config/live no-push sync             ABSENT / NOT_EXERCISED
final content-addressed release and rollback              NOT_PERFORMED
```

The correct conclusion is:

> Bettor has a substantial modular Harness foundation and several current-main LoopX mechanisms. It has not completed or Human-admitted the full PDF architecture.

Read:

- [`docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md)
- [`docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md)
- [`docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md`](docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md)
- [`docs/git/PDF_TERMINAL_SEQUENCE.md`](docs/git/PDF_TERMINAL_SEQUENCE.md)
- [`docs/git/pdf-terminal-sequence.json`](docs/git/pdf-terminal-sequence.json)
- [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md)

### Missing LoopX control flow

The repository still lacks the complete admitted end-to-end runtime:

```text
Objective + Todos + Gates + Evidence + Quota
→ canonical append-only single-writer Ledger
→ Strategy proposal
→ leased Runtime Fabric / Worker Fleet execution
→ host-owned hard Gates
→ LoopX reducer commit
→ Decision Memory / retry / HITL / complete
→ observability and Console projections
→ final composition and Human release
```

Contract or current-main reachability is not equivalent to composition selection, live execution, cloud isolation or production promotion.

## Read order

1. [`AGENTS.md`](AGENTS.md) or [`CLAUDE.md`](CLAUDE.md)
2. [`ARCHITECTURE.md`](ARCHITECTURE.md)
3. [`CONTEXT.md`](CONTEXT.md)
4. [`docs/INDEX.md`](docs/INDEX.md)
5. [`docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md)
6. [`docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md`](docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md)
7. [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md)
8. [`docs/git/REPO_PROFILE.md`](docs/git/REPO_PROFILE.md)
9. [`docs/git/PDF_TERMINAL_SEQUENCE.md`](docs/git/PDF_TERMINAL_SEQUENCE.md)
10. [`docs/git/pdf-terminal-sequence.json`](docs/git/pdf-terminal-sequence.json)
11. [`docs/git/STACKED_PRS.md`](docs/git/STACKED_PRS.md)
12. [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md)
13. the current active issue/task packet
14. the nearest module README, `module.json`, contracts, source, tests and current receipts
15. current GitHub base, head, checks and main reachability

## Directory → State Machine → input/output/evidence

<!-- Directory → State Machine ownership -->

| Directory / route | Owner | State Machine | Inputs | Outputs / evidence | Current state |
|---|---|---|---|---|---|
| root `*.md` | `arena-core` | `ENTRY → ROUTE → OWNER → CONTRACT → EVIDENCE` | task + exact repo subject | bounded Agent read route | `IMPLEMENTED` |
| `docs/git/` | Git governance | `PROFILE → ORDERED QUEUE → TASK PACKET → STACK GRAPH → LEASE → EVAL → HUMAN ADMIT` | shared Skill pin + GitHub metadata | Stack snapshots and queue | governance `IMPLEMENTED`; runtime `ABSENT` |
| `docs/traceability/` | delivery traceability | `SOURCE → ISSUE → TERMINAL → PR → EXACT HEAD → CHECKS → ADMIT` | issue/PR metadata | human Stack index | `IMPLEMENTED`, snapshot-bound |
| `.agents/` | `agent-runtime-integration` | `REQUIRE → RESOLVE → BIND → PROJECT → DISCOVER` | shared/repo-owned Skill requirements | immutable binding and host projections | `IMPLEMENTED` |
| `.skill-bindings/` | consumer bindings | `UPSTREAM PROCEDURE → RETARGET → ASSERT → RECEIPT` | immutable shared Skill | repo-specific facts/assertions | `IMPLEMENTED` |
| `.runtime-env/` | `environment-contracts` | `DECLARE → RESOLVE → MATERIALIZE → OFFLINE VERIFY → LIVE CANARY` | secret-free runtime release | binding/workload/policy projection | contract `IMPLEMENTED`; live varies |
| `.arena/modules/` | `module-catalog` | `PROPOSED → CONTRACTED → COMPOSED → PROVED → RELEASED` | module manifests | owners/capabilities/proof commands | `IMPLEMENTED` |
| `.arena/compositions/` | `module-catalog` | `DESIRED → DEPENDENCY/CONFLICT RESOLVE → CANDIDATE` | module requirements | desired composition | `IMPLEMENTED` |
| `.arena/locks/` | generated control plane | `REQUIREMENTS → RESOLVE → DIGEST → LOCK` | manifests/requirements | deterministic lock | `IMPLEMENTED`; regenerate only |
| `.arena/contexts/` | `loop-runtime` + owners | `SELECT → MATERIALIZE → FREEZE → DRIVER PREPARE → CANARY` | repo ref + native files | Context Capsule digest | offline `IMPLEMENTED`; live varies |
| `loopctl/` | `loop-runtime` | `PARSE → VALIDATE → DISPATCH PUBLIC PORT → PROPAGATE 0/2/64` | typed request | typed artifact/receipt | `IMPLEMENTED` |
| `mcp/` | `mcp-adapters` | `DEFAULT DENY → TOOL PROJECT → DISPOSABLE CALL → CLEANUP` | CLI contract + policy | JSON-RPC result | admitted tools only |
| `proof_workflow/` | `proof-kernel` | `CLAIM → TRAVERSAL → CONTROL → MUTATION → RECEIPT` | public port/context | proof/control/mutation evidence | `IMPLEMENTED` |
| `data/module-proof/` | `proof-kernel` projection | `SUBJECTS → CLOSURE → RELEASE AGGREGATION` | locks/proof specs | subject lock/release receipt | mechanism `IMPLEMENTED` |
| `loop_wiki/loopx-kernel/` | catalogued LoopX mechanism | `TASK DECLARE → TODO → GATES → QUOTA → TERMINAL` | task/command/event | contract and snapshot law | `MERGED_TO_MAIN`; Stage #90 validation pending |
| `loop_wiki/loopx-ledger/` | catalogued LoopX mechanism | `APPEND → HASH/LEASE → REDUCE → SNAPSHOT → REPLAY` | accepted events | canonical Ledger/snapshot | `MERGED_TO_MAIN`; Stage #90 validation pending |
| `loop_wiki/loopx-worker-gateway/` | catalogued LoopX mechanism | `REQUEST → ADAPTER → EVENT → RECEIPT → CLEANUP` | exact subject/Skill/context | Worker receipt | `MERGED_TO_MAIN`; live matrix pending |
| `loop_wiki/loopx-decision-memory/` | catalogued memory contract | `PROPOSE → VALIDATE → CANDIDATE` | evidence-bound proposal | non-persisted candidate | `MERGED_TO_MAIN`; runtime #103 pending |
| `loop_wiki/code-truth-graph-v2/` | catalogued evidence projection | `OBSERVE → COMPILE → QUERY → READBACK` | T0–T6 observations | evidence graph/query result | `MERGED_TO_MAIN`; live providers pending |
| `kb-ingest/`, `openwiki/` | `openwiki` | `REQUEST → DRY/FULL OPT-IN → VERIFY → RECEIPT` | wiki request | tracked projection | mechanism `IMPLEMENTED` |
| `docs/knowledge-providers/` | `knowledge-providers` | `MANIFEST → QUERY/PROPOSAL → SOURCE READBACK → ADMIT` | exact subject/capability | candidate result | contracts `IMPLEMENTED`; live varies |
| `.github/workflows/` | cloud verifier | `EVENT → EXACT CHECKOUT → DETERMINISTIC GATE → STATUS` | push/PR subject | GitHub check | `IMPLEMENTED`; skipped/stale is not PASS |
| planned Strategy/HITL | #65 | `SNAPSHOT → PROPOSE → INTERRUPT → SIGNED DECISION → RESUME` | Ledger-bound snapshot | command/decision proposal | `NOT_IMPLEMENTED` |
| planned Runtime/Fleet/GC/LSP | #66/#94/#97/#96 | `PROBE → LEASE → EXECUTE → COLLECT → CLEANUP/REUSE` | Worker/policy/task | attested runtime receipts | `NOT_IMPLEMENTED` |
| planned Notes pipeline | #104/#105/#70/#71 | `SOURCE → MANIFEST → RETRIEVAL → SPEC/CODEOP → SCAFFOLD → FOLD-BACK` | YT/PDF/Notes/code evidence | traceable knowledge/code patches | `NOT_IMPLEMENTED` |
| planned observability/Console | #67/#99 | `EVENT → REDACT → PROJECT → INSPECT → SIGNED REQUEST` | Ledger/artifact refs | trace/UI/request | `NOT_IMPLEMENTED` |
| final convergence | #68 | `PIN TERMINALS → SELECT → LOCK → PROVE → LIVE CANARIES → HUMAN RELEASE` | admitted terminal subjects | immutable release/rollback | `BLOCKED_BY_PREDECESSORS` |

Detailed map: [`docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md`](docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md).

## End-to-end data flow

```text
PDF / issue / authorized source incident
        ↓ classify proposal, observation, decision or current fact
skills-shared immutable Skill ──────────────┐
                                            ├─→ .agents binding / Context policy
runtime-env secret-free release ───────────┘
                                                     ↓
                              ordered terminal task packet + path lease
                                                     ↓
                    module graph + dependency-driven Git branch graph
                                                     ↓
                        immutable Context Capsule / Prompt IR
                                                     ↓
                    loopctl / default-deny MCP / trusted local port
                                                     ↓
                  leased disposable workspace + typed Worker request
                                                     ↓
          Codex / Claude / Grok Build / OpenCode / Pi / Ante observation
                                                     ↓
               diff + stdout/stderr + content-addressed artifacts
                                                     ↓
                host-owned Gates + independent control/mutation
                                                     ↓
                         LoopX reducer / Ledger event
                ├─ FAIL → Quota → memory proposal → retry/HITL
                └─ PASS → Todo completion / verified candidate
                                                     ↓
                     Notes/code fold-back and projections
                                                     ↓
                  convergence composes exact terminal subjects
                                                     ↓
                                      Human Admit
                                  ├─ promote
                                  └─ reject / rollback
```

No Worker, provider, graph checkpoint, UI, memory store, vector index, local CI simulator, Git Town exit code or model prose can skip the Gate, reducer and Human boundaries.

## Git Town Stacked-PR governance

Canonical shared method:

```text
repository: ed3c/skills-shared
commit:     c5750720d960a228a0d9419f28125c09d064e3e1
blob:       eb2d915bca3e8a3938625f7d33a10fae95a15769
path:       skills/git-town-stacked-pr-worker/SKILL.md
```

Bettor does **not** copy a local same-name `SKILL.md`. It owns the repository profile, task packets, path leases, queue/index, wrappers/evals and Human policy under [`docs/git/`](docs/git/README.md).

Current admission:

```text
shared Skill exact reference            PINNED
shared Skill selected in Bettor binding NOT_SELECTED
.git-town.toml                           ABSENT
Git Town executable/version/checksum     ABSENT
license/SBOM/legal admission             NOT_REVIEWED
live no-push sync                        NOT_EXERCISED
publication canary                       NOT_EXERCISED
merge / ship / rollback                  HUMAN-OWNED
```

## Ordered PDF terminal Stack

Canonical ordered queue:

- [`docs/git/PDF_TERMINAL_SEQUENCE.md`](docs/git/PDF_TERMINAL_SEQUENCE.md)
- [`docs/git/pdf-terminal-sequence.json`](docs/git/pdf-terminal-sequence.json)
- [`docs/git/pdf-terminal-sequence.schema.json`](docs/git/pdf-terminal-sequence.schema.json)

```text
current active item: #82
current validation follower: #90
queue length: 26 terminal stages, orders 0–25
final convergence: #68
active limit: 1
future branch creation: blocked until its queue item is active
```

The completion queue is serial, but Git ancestry is dependency-driven. Path-disjoint terminals become new roots after predecessors land; a true child is used only when it consumes unmerged parent bytes. Do not create a 26-deep branch chain for appearance.

Condensed sequence:

```text
#82 → #90 → #65 → #67 → #66 → #94 → #97 → #96
→ #103 → #93 → #104 → #105 → #92 → #41 → #70 → #71
→ #95 → #72 → #98 → #91 → #45 → #46/#56 → #99 → #100
→ #101 → #68
```

## Molecular Stack PR index

<!-- Molecular Stack PR index -->

Historical and current foundation:

```text
PR #60 PDF/LoopX documentation verifier            MERGED_TO_MAIN
PR #81 Git Town governance                         MERGED_TO_MAIN
PR #74 LoopX Contract root                         MERGED_TO_MAIN
├─ PR #75 Ledger                                   MERGED_TO_MAIN through #74
├─ PR #76 Worker Gateway                           MERGED_TO_MAIN through #74
├─ PR #78 Decision Memory contracts                MERGED_TO_MAIN through #74
└─ PR #79 Code Truth Graph v2                      MERGED_TO_MAIN through #74

PR #77 duplicate Worker Gateway                    SUPERSEDED_CANDIDATE
#76/#77 conflict                                   RESOLVED_BY_HUMAN
issue #82                                          ACTIVE residual-file disposition
issue #102                                         OPEN ordered-queue documentation leaf
issue #68                                          FINAL_CONVERGENCE owner
```

Full human history: [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md).  
Historical machine snapshot: [`docs/git/stack-prs.index.json`](docs/git/stack-prs.index.json).  
Current ordered machine queue: [`docs/git/pdf-terminal-sequence.json`](docs/git/pdf-terminal-sequence.json).

## Current module catalog

The selected control-plane module IDs remain explicit for repository gates:

- `agent-runtime-integration`
- `arena-core`
- `code-truth-graph`
- `environment-contracts`
- `knowledge-providers`
- `loop-runtime`
- `mcp-adapters`
- `module-catalog`
- `notebooklm`
- `openwiki`
- `perfect-seed-factory`
- `project-bootstrapper`
- `proof-kernel`
- `technical-equivalence`

LoopX modules may be catalogued or reachable without being selected in the final shared composition. Selection and aggregate release remain #68.

## Stable public surfaces

### `loopctl`

```sh
sh loopctl/loopctl.sh contract
sh loopctl/loopctl.sh --selftest
```

`loopctl/contract.json` is the canonical external surface. Private module flags and temporary paths are not public contract.

### Stateless MCP

MCP tools derive from the canonical CLI contract and `.arena/mcp-policy.json`, default deny. Callers cannot supply generic shell text, arbitrary host paths, secrets, browser profiles or Human Admit operations.

### Ordered sequence verifier

```sh
python3 scripts/gates/check_pdf_terminal_sequence.py
python3 scripts/gates/check_pdf_terminal_sequence.py --selftest
python3 -m unittest -q tests/test_pdf_terminal_sequence.py
```

This validates repository bytes and queue invariants only. It does not execute Git Town, Workers, providers, cloud runtimes or release actions.

### Git Town governance verifier

```sh
python3 scripts/gates/check_git_town_stack_docs.py
python3 scripts/gates/check_git_town_stack_docs.py --selftest
python3 -m unittest -q tests/test_git_town_stack_docs.py
```

This validates the historical governance snapshot; current completion order is owned by the ordered sequence above.

## Evidence model

```text
PASS ≠ FAIL ≠ ABSENT ≠ NOT_IMPLEMENTED ≠ NOT_EXERCISED
```

Additional delivery and queue states:

```text
MERGED_TO_MAIN
MERGED_TO_PARENT
OPEN
SUPERSEDED_CANDIDATE
ACTIVE
BLOCKED_BY_PREDECESSOR
FINAL_CONVERGENCE
SKIPPED_BY_POLICY
```

Conflict states remain recorded:

```text
BLOCKED_HUMAN_DECISION
RESOLVED_BY_HUMAN
```

A merged child is `MERGED_TO_MAIN` only when current-main reachability proves it. A later queue item is not complete merely because its issue, branch or fixture exists.

## Human-owned boundaries

A model or background Worker must not:

- resolve semantic Git conflicts;
- continue, skip or undo a blocked Git Town operation;
- create a future terminal branch before queue activation;
- change remotes, credential helpers or permissions;
- push, merge, ship, close or delete branches;
- select production providers, models, runtimes or credentials;
- issue an unscoped exception;
- Human Admit a release;
- perform production rollback.

## Current boundary

This branch records and validates the complete ordered PDF terminal queue. It does not install Git Town, create `.git-town.toml`, execute `git town sync`, implement any runtime terminal, activate a host/provider, modify production credentials, merge a PR, promote a release or perform rollback.
