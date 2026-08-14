# bettor-arena

> **Module Host + Loop Runtime + Proof Kernel + Stateless MCP Gateway + Project Bootstrapper**

`bettor-arena` 將多個 bounded loops、portable Skills、runtime projections、proof controls 與 release evidence 組合成可追溯的 Agent Harness。外部 consumer 只依賴穩定的 `loopctl`／MCP contract；內部 implementation 透過 module、typed packet、subject-bound receipt 與 Human Admit 演進。

## Current publication subject

```text
GitHub repository: ed3c/bettor-arena
current main:      10380005fa485d6035539589c01b9f740acff15d
documentation parent PR: #60
parent branch:     feat/pdf-loopx-modular-verifier-v1
parent head:       ffbcd91a9eae1f6171fc7c42f0300bb83fac1b90
this terminal issue: #80
this branch:       feat/git-town-stack-governance-v1
```

GitHub base/head metadata and exact-head checks are publication truth. This Markdown is a routed snapshot, not a substitute for GitHub.

## PDF Harness Integration verdict

The attached 41-page **LLM 泛化：模型權重與 Harness** PDF is a requirement/hypothesis source. It proposes a LoopX state kernel around Objective, Todos, Gates, Evidence and Quota, deterministic out-of-band verification, heterogeneous workers, LangGraph HITL, episodic memory, worktree fleets, cloud/local execution and observability.

Current repository verdict:

```text
modular control-plane foundation                IMPLEMENTED
hard gates / proof / control / mutation         IMPLEMENTED
portable Skill → host-owned execution           IMPLEMENTED
Context Capsules / OpenWiki / Code Truth        IMPLEMENTED
provider-neutral query and memory contracts     IMPLEMENTED

complete LoopX task-state kernel on main        NOT_IMPLEMENTED
LoopX contract candidate                        OPEN STACK PR #74
append-only ledger candidate                    MERGED INTO #74 PARENT, NOT MAIN
six-host Worker Gateway candidates              OPEN / DUPLICATE ACTIVE TERMINALS
LangGraph strategy + HITL                       NOT_IMPLEMENTED
evidence-bound durable decision memory          NOT_IMPLEMENTED ON MAIN
six-host live execution matrix                  NOT_EXERCISED
cloud/local equivalent execution                NOT_EXERCISED
observability / signed HITL console              NOT_IMPLEMENTED
Git Town executable/config/live sync            ABSENT / NOT_EXERCISED
```

The correct conclusion is:

> Bettor has a modular Harness foundation and several unmerged LoopX terminal candidates. It has not completed or Human-admitted the full PDF architecture.

Read:

- [`docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md)
- [`docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md)
- [`docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md`](docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md)
- [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md)

## Read order

1. [`AGENTS.md`](AGENTS.md) or [`CLAUDE.md`](CLAUDE.md)
2. [`ARCHITECTURE.md`](ARCHITECTURE.md)
3. [`CONTEXT.md`](CONTEXT.md)
4. [`docs/INDEX.md`](docs/INDEX.md)
5. [`docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md)
6. [`docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md`](docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md)
7. [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md)
8. [`docs/git/README.md`](docs/git/README.md)
9. [`docs/git/REPO_PROFILE.md`](docs/git/REPO_PROFILE.md)
10. [`docs/git/STACKED_PRS.md`](docs/git/STACKED_PRS.md)
11. [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md)
12. the nearest module README, `module.json`, contracts, source, tests and current receipts

## Directory → State Machine ownership

| Directory / route | Owner | State Machine | Inputs | Outputs / evidence | Current state |
|---|---|---|---|---|---|
| root `*.md` | `arena-core` | `ENTRY → ROUTE → OWNER → CONTRACT → EVIDENCE` | task + exact repo subject | bounded Agent read route | `IMPLEMENTED` |
| `docs/git/` | repository Git governance | `PROFILE → TASK PACKET → STACK GRAPH → LEASE → DRY RUN → EVAL → HUMAN ADMIT` | shared Skill pin, GitHub metadata, task packet | profile, Stack snapshot, governance diagnostics | repo-owned docs `IMPLEMENTED`; Git Town runtime `ABSENT` |
| `docs/traceability/` | delivery traceability | `SOURCE → ISSUE → TERMINAL → PR → EXACT HEAD → CHECKS → ADMIT` | GitHub issue/PR metadata | human Stack index | `IMPLEMENTED`, snapshot-bound |
| `.agents/` | `agent-runtime-integration` | `REQUIRE → RESOLVE → BIND → PROJECT → DISCOVER` | shared/repo-owned Skill requirements | immutable Skill binding and host projections | `IMPLEMENTED`; Git Town Skill selection `NOT_SELECTED` |
| `.skill-bindings/` | consumer bindings | `UPSTREAM PROCEDURE → RETARGET → ASSERT → RECEIPT` | immutable shared Skill | repo-specific facts and assertions | `IMPLEMENTED` for selected bindings |
| `.runtime-env/` | runtime consumer projection | `DECLARE → RESOLVE → MATERIALIZE → OFFLINE VERIFY → LIVE CANARY` | secret-free runtime release | binding/workload/policy projection | mechanism `IMPLEMENTED`; live routes vary |
| `.arena/modules/` | `module-catalog` | `PROPOSED → CONTRACTED → COMPOSED → PROVED → RELEASED` | module manifests | owners, capabilities and proof commands | `IMPLEMENTED` |
| `.arena/compositions/` | `module-catalog` | `DESIRED → DEPENDENCY/CONFLICT RESOLVE → CANDIDATE` | module/component requirements | desired composition | `IMPLEMENTED` |
| `.arena/locks/` | generated control plane | `REQUIREMENTS → RESOLVE → DIGEST → LOCK` | manifests and requirements | deterministic composition lock | `IMPLEMENTED`; regenerate only |
| `.arena/contexts/` | `loop-runtime` + owners | `SELECT → MATERIALIZE → FREEZE → DRIVER PREPARE → CANARY` | immutable repository ref + native files | Context Capsule digest | offline `IMPLEMENTED`; live hosts vary |
| `loopctl/` | `loop-runtime` | `PARSE → VALIDATE → DISPATCH PUBLIC PORT → PROPAGATE 0/2/64` | typed CLI request | typed artifacts/receipt | `IMPLEMENTED` |
| `mcp/` | `mcp-adapters` | `DEFAULT DENY → TOOL PROJECT → DISPOSABLE CALL → CLEANUP` | CLI contract + explicit policy | JSON-RPC result | `IMPLEMENTED` for admitted tools |
| `proof_workflow/` | `proof-kernel` | `CLAIM → TRAVERSAL → CONTROL → MUTATION → RECEIPT` | public port + context | proof/control/mutation evidence | `IMPLEMENTED` |
| `data/module-proof/` | generated evidence | `SUBJECTS → CLOSURE → RELEASE AGGREGATION` | locks + proof specs | subject lock + release receipt | mechanism `IMPLEMENTED` |
| `loop_wiki/evolve-perfect-seed-repo-factory/` | `perfect-seed-factory` | `PACKET → BUILD → QUALITY → OPERATOR → VALIDATOR → HUMAN EDGE` | typed source/task packet | seed repo + wiki request | `IMPLEMENTED` |
| `kb-ingest/`, `openwiki/` | `openwiki` | `REQUEST → DRY/FULL OPT-IN → VERIFY → RECEIPT` | wiki-update request | tracked projection | mechanism `IMPLEMENTED` |
| `loop_wiki/code-truth-graph/` | `code-truth-graph` | `PACKET → PARSE/BUILD → VERIFY → GRAPH ARTIFACT` | exact source packet | graph/result artifact | `IMPLEMENTED` |
| `docs/knowledge-providers/` | `knowledge-providers` | `MANIFEST → QUERY/PROPOSAL → SOURCE READBACK → ADMIT` | exact subject + capability | candidate result or memory proposal | contracts `IMPLEMENTED`; live providers vary |
| `.github/workflows/` | cloud verifier | `EVENT → EXACT CHECKOUT → DETERMINISTIC GATE → STATUS` | push/PR subject | GitHub check | `IMPLEMENTED`; skipped/stale is not PASS |
| proposed LoopX kernel | future `loopx-kernel` | `OBJECTIVE → TODO → DISPATCH → GATES → REDUCE → RETRY/HITL/COMPLETE` | task contract + events | canonical ledger + derived snapshot | candidate stack, not on main |
| proposed strategy/HITL | future strategy plane | `SNAPSHOT → PROPOSE → INTERRUPT → SIGNED DECISION → RESUME` | LoopX snapshot | typed command/decision receipt | `NOT_IMPLEMENTED` |
| proposed runtime fabric | future execution plane | `PROBE → LEASE → MATERIALIZE → EXECUTE → COLLECT → DISPOSE` | worker request + policy | attested execution receipt | `NOT_IMPLEMENTED` |
| proposed observability/UI | projection plane | `EVENT → REDACT → PROJECT → INSPECT → SIGNED HUMAN REQUEST` | immutable refs | trace/dashboard/request | `NOT_IMPLEMENTED` |

Detailed map: [`docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md`](docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md).

## End-to-end data flow

```text
PDF / issue / source incident
        ↓ classify as proposal, fact, observation or decision
skills-shared immutable Skill release ──────┐
                                            ├─→ .agents binding / repo profile
runtime-env secret-free release ────────────┘
                                                     ↓
                                  module + Stack task requirements
                                                     ↓
                         composition graph + Git branch dependency graph
                          ├─ module capability/dependency/conflict resolve
                          └─ sibling/true-child/path-lease validation
                                                     ↓
                             immutable Context Capsule + task packet
                                                     ↓
                    loopctl / default-deny MCP / trusted local public port
                                                     ↓
                     leased disposable worktree + typed Worker request
                                                     ↓
          Codex / Claude / Grok Build / OpenCode / Pi / Ante candidate output
                                                     ↓
                  diff + stdout/stderr + content-addressed artifacts
                                                     ↓
                  host-owned hard Gates + independent control/mutation
                                                     ↓
                  subject-bound receipt / LoopX event proposal
                          ├─ failure → Quota debit / handoff / memory proposal
                          └─ pass    → next Todo / release candidate
                                                     ↓
                                  convergence leaf aggregates
                                                     ↓
                                      Human Admit
                                  ├─ merge / promote
                                  └─ reject / rollback
```

No Worker, provider, graph checkpoint, UI, memory store, vector index or model prose can skip the Gate/reducer/Human boundaries.

## Git Town Stacked-PR governance

Canonical shared method:

```text
repository: ed3c/skills-shared
commit:     c5750720d960a228a0d9419f28125c09d064e3e1
blob:       eb2d915bca3e8a3938625f7d33a10fae95a15769
path:       skills/git-town-stacked-pr-worker/SKILL.md
```

Bettor does **not** copy a local same-name `SKILL.md`. It owns only the repository profile, work packets, path leases, Stack index, wrappers/evals and Human policy described under [`docs/git/`](docs/git/README.md).

Current admission:

```text
shared Skill exact reference            PINNED
shared Skill selected in Bettor binding NOT_SELECTED
.git-town.toml                           ABSENT
Git Town executable/version/checksum     ABSENT
license/SBOM/legal admission             NOT_REVIEWED
live git town sync                       NOT_EXERCISED
publication canary                       NOT_EXERCISED
merge / ship / rollback                  HUMAN-OWNED
```

### Current molecular Stack

```text
main @ 10380005fa485d6035539589c01b9f740acff15d
│
├─ PR #60 feat/pdf-loopx-modular-verifier-v1
│    └─ PR #81 feat/git-town-stack-governance-v1
│         issue #80; true-child documentation/governance terminal; OPEN DRAFT
│
├─ PR #74 feat/loopx-contract-v1
│    ├─ PR #75 feat/loopx-ledger-v1
│    │    MERGED INTO #74 PARENT — NOT ON MAIN
│    ├─ PR #76 feat/loopx-worker-gateway-v1
│    ├─ PR #77 feat/loopx-worker-gateway-terminal-v1
│    │    #76/#77 overlap the same issue and paths: BLOCKED_DUPLICATE_TERMINAL
│    ├─ PR #78 feat/loopx-decision-memory-v1
│    └─ PR #79 feat/loopx-code-truth-graph-v2
│
├─ PR #56 provider admission evaluations
│    focused fixture value; publication remains separate
├─ PR #53 historical aggregate
│    non-authoritative until unique delta is extracted
└─ issue #68 final LoopX convergence
     shared composition/index/live canary/release owner only
```

Full human index: [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md).  
Machine snapshot: [`docs/git/stack-prs.index.json`](docs/git/stack-prs.index.json).

## Stable public surfaces

### `loopctl`

```sh
sh loopctl/loopctl.sh contract
sh loopctl/loopctl.sh --selftest
```

`loopctl/contract.json` is the canonical external surface. Private module flags and temporary paths are not public contract.

### Stateless MCP

MCP tools derive from the canonical CLI contract and `.arena/mcp-policy.json`, default deny. Callers cannot provide generic shell text, arbitrary host paths, secrets, browser profiles or Human Admit operations.

### Git Town governance verifier

```sh
python3 scripts/gates/check_git_town_stack_docs.py
python3 scripts/gates/check_git_town_stack_docs.py --selftest
python3 -m unittest -q tests/test_git_town_stack_docs.py
```

This checks documentation/profile/index consistency only. It does not run Git Town.

## Evidence model

```text
PASS ≠ FAIL ≠ ABSENT ≠ NOT_IMPLEMENTED ≠ NOT_EXERCISED
```

Additional Stack states:

```text
MERGED_TO_MAIN
MERGED_TO_PARENT
OPEN
BLOCKED_DUPLICATE_TERMINAL
SUPERSEDED_CANDIDATE
NOT_CREATED
```

A child marked `merged=true` may have merged only into its feature parent. Only reachability from current `main` proves `MERGED_TO_MAIN`.

## Human-owned boundaries

A model or background Worker must not:

- resolve semantic Git conflicts;
- continue, skip or undo a blocked Git Town operation;
- change remotes or credential helpers;
- push, merge, ship, close or delete branches;
- widen permissions;
- select production providers;
- Human Admit a release;
- perform production rollback.

## Current boundary

This branch adds repository-owned Git Town governance documents and a machine-readable Stack snapshot. It does not install Git Town, create `.git-town.toml`, execute `git town sync`, change runtime/provider implementation, select unmerged LoopX modules, expose new MCP tools, merge any PR or perform Human Admit.
