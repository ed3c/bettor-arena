# bettor-arena

> **Module Host + Loop Runtime + Proof Kernel + Stateless MCP Gateway + Project Bootstrapper**

`bettor-arena` 將 bounded loops、portable Skills、runtime projections、proof controls、knowledge projections 與 release evidence 組合成可追溯的 Agent Harness。外部 consumer 只依賴穩定的 `loopctl`／MCP contract；內部 implementation 透過 module、typed packet、subject-bound receipt、ordered terminal queue 與 automated admission 演進。

## Current publication subject

```text
logical repository:     ed3c/bettor-arena
observed:               2026-08-16 (GitHub REST + local Git objects)
local main:             8d47fc1c9dfd1550c1f45504f6c11fc1f04f6a0b
forgejo/main:           8d47fc1c9dfd1550c1f45504f6c11fc1f04f6a0b
github/main:            ad0fdde3e46aa6ab6c59ced145bead7fa4fc72d3
observed relation:      local/Forgejo relation NOT_REOBSERVED for this convergence subject
program / index:        #61 / #102 (both planning/index history)
current active item: #140 (order 13)
final convergence:      #68
```

The three refs above are an observed Git-object relation, not a regenerated origin receipt. Tracked [`data/origins/status.json`](data/origins/status.json) still says both live probes and equivalence are `NOT_EXERCISED`; do not relabel that receipt as PASS. GitHub base/head metadata, reachability and exact-head checks remain publication truth. Markdown and machine indexes are reviewed snapshots, not substitutes for GitHub.

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

LoopX Contract / Ledger / Strategy / HITL mechanisms     IMPLEMENTED
Runtime Fabric / Worker Fleet / GC / LSP mechanisms      IMPLEMENTED
Decision Memory / Mem0 projection mechanisms             IMPLEMENTED
YT/PDF Notes ingest and retrieval mechanisms             IMPLEMENTED
Notes compiler / fold-back / Context Assembly            IMPLEMENTED
Skill evolution / CI parity / Console / benchmark        IMPLEMENTED
ordered acceptance through order 12                      COMPLETE
order 12 Serena/GrepAI live canaries                     ADMITTED / COMPLETE
six-host live execution matrix                           NOT_EXERCISED
Code-Graph-RAG canonical route / order-13 #140             RETIRED_FROM_CANONICAL_ROUTE / ACTIVE / HUMAN_ADMIT_REQUIRED
final LoopX modules selected into release composition    ABSENT
Git Town controller/controls                              IMPLEMENTED / PASS
Git Town executable/config/live no-push sync             ABSENT / NOT_EXERCISED
final content-addressed release and rollback              NOT_PERFORMED
```

The correct conclusion is:

> Bettor now has most terminal mechanism bytes on `main`, but the selected release composition still contains only 14 base modules, its aggregate release receipt is `NOT_EXERCISED`, and the ordered live-acceptance queue is now active at #140. "已合併"不能改寫成「已整合／已發布」。

Read:

- [`docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md)
- [`docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md)
- [`docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md`](docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md)
- [`docs/git/PDF_TERMINAL_SEQUENCE.md`](docs/git/PDF_TERMINAL_SEQUENCE.md)
- [`docs/git/pdf-terminal-sequence.json`](docs/git/pdf-terminal-sequence.json)
- [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md)

### Missing LoopX control flow: final admitted subject

The repository has the component mechanisms but still lacks one admitted end-to-end subject:

```text
Objective + Todos + Gates + Evidence + Quota
→ canonical append-only single-writer Ledger
→ Strategy proposal
→ leased Runtime Fabric / Worker Fleet execution
→ host-owned hard Gates
→ LoopX reducer commit
→ Decision Memory / retry / HITL / complete
→ observability and Console projections
→ final composition and automated release
```

The blocking gap is composition selection plus exact-subject live evidence, not another round of architecture prose. Contract or current-main reachability is not equivalent to composition selection, live execution, cloud isolation or production promotion.

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
| `docs/git/` | Git governance | `METHOD PIN → PROFILE → QUEUE → STACK/LEASE → EVAL → PUBLICATION BOUNDARY` | shared Skill pin + GitHub metadata | Stack snapshots and queue | governance `IMPLEMENTED`; active #140 |
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
| `data/module-proof/` | `proof-kernel` projection | `SUBJECTS → CLOSURE → RELEASE AGGREGATION` | locks/proof specs | subject lock/release receipt | 14 selected modules; aggregate `NOT_EXERCISED` |
| `loop_wiki/loopx-kernel/` | `loopx-kernel` | `DECLARE → VALIDATE → TODO/GATE/QUOTA → TERMINAL` | task/command/event | contract and snapshot law | mechanism `IMPLEMENTED`; not selected |
| `loop_wiki/loopx-ledger/` | `loopx-ledger` | `APPEND → HASH/LEASE → REDUCE → SNAPSHOT → REPLAY` | accepted events | canonical Ledger/snapshot | mechanism `IMPLEMENTED`; not selected |
| `loop_wiki/loopx-strategy-hitl/` | `loopx-strategy-hitl` | `SNAPSHOT → PROPOSE → INTERRUPT → SIGN → REVALIDATE` | Ledger snapshot + Human decision | command/decision proposal | PR #106 merged; not selected |
| `loop_wiki/loopx-worker-gateway/` | `loopx-worker-gateway` | `REQUEST → ADAPTER → OBSERVE → RECEIPT → CLEANUP` | exact subject/Skill/context | Worker observation | mechanism `IMPLEMENTED`; six-host live pending |
| `loop_wiki/loopx-runtime-fabric/` | `loopx-runtime-fabric` | `POLICY → LEASE → MATERIALIZE → EXECUTE → COLLECT → CLEANUP` | Worker request + runtime policy | workspace/runtime receipt | PR #117 merged; live parity pending |
| `loop_wiki/loopx-worker-fleet/` | `loopx-worker-fleet` | `QUEUE → WORKTREE/PATH LEASE → DISPATCH → RECOVER` | task/dependency/resource facts | lease/Worker receipt | PR #122 merged; live fleet pending |
| `loop_wiki/loopx-resource-gc/` | `loopx-resource-gc` | `INVENTORY → DRY PLAN → ADMIT → CLEAN → REBUILD/CHECK` | leases + retention | cleanup/tombstone receipt | PR #123 merged; production cleanup not exercised |
| `loop_wiki/lsp-pool/` | `lsp-pool` | `PIN SERVER/WORKSPACE → QUERY → FRESHNESS → EVICT` | exact workspace | diagnostics/reference receipt | PR #124 merged; live provider #92 complete; #140 active |
| `loop_wiki/code-truth-graph-v2/` | `code-truth-graph-v2` | `OBSERVE → COMPILE → QUERY → SOURCE READBACK` | T0–T6 observations | evidence graph/query result | mechanism `IMPLEMENTED`; not selected |
| `loop_wiki/loopx-decision-memory/` | `loopx-decision-memory` | `PROPOSE → AUTOMATED ADMIT → LEDGER EVENT → PROJECT → EXPIRE/DELETE` | evidence-bound proposal | memory event/projection | PR #125/#126 merged; not selected |
| `loop_wiki/loopx-source-ingest/` | `loopx-source-ingest` | `DECLARE → AUTHORIZE → CAPTURE → HASH → MANIFEST` | media/text/code source refs | immutable evidence manifest | PR #127 merged; not selected |
| `loop_wiki/loopx-notes-retrieval/` | `loopx-notes-retrieval` | `PIN NOTES → BUILD → QUERY → READBACK → REBUILD` | Notes release | static/vector/graph projection | PR #128 merged; not selected |
| `loop_wiki/loopx-knowledge-compiler/` | `loopx-knowledge-compiler` | `EVIDENCE → CARDS → SPEC IR → CODEOP → CANDIDATE` | knowledge release | scaffold/code-operation candidate | PR #118 merged; queue admission pending |
| `loop_wiki/loopx-knowledge-foldback/` | `loopx-knowledge-foldback` | `DIFF/RUNTIME → AFFECTED KNOWLEDGE → PATCH → ADMIT` | verified code/runtime evidence | knowledge revision proposal | PR #119 merged; queue admission pending |
| `loop_wiki/loopx-context-assembly/` | `loopx-context-assembly` | `PROMPT IR → STABLE PREFIX → BOUNDED SUFFIX → HOST RENDER` | Skills/cards/memory/task | content-addressed host prompts | PR #129 merged; queue admission pending |
| `loop_wiki/loopx-skill-evolution/` | `loopx-skill-evolution` | `BASELINE/CANDIDATE → MUTATION → HOLDOUT → RECOMMEND` | identical execution contract | candidate release proposal | PR #120 merged; queue admission pending |
| `loop_wiki/loopx-observability/` | `loopx-observability` | `EVENT → REDACT → PROJECT → INSPECT → HITL REQUEST` | immutable Ledger/artifact refs | trace/UI projection | PR #116 merged; not selected |
| `apps/harness-console/`, `packages/harness-console-contracts/`, `services/hitl-api/` | `harness-console` | `PROJECT → INSPECT → DRAFT REQUEST → LOOPX VALIDATE` | redacted ledger/evidence | console + signed request | PR #131/#134 merged; not selected |
| `loop_wiki/loopx-benchmark/` | `loopx-benchmark` | `PIN → TRIALS → COMPARABILITY → SCOPED CLAIM` | exact workload/environment | raw trials/report | PR #132/#135 merged; not selected |
| `scripts/git-town/`, `tests/git-town/`, `docs/git/runtime/` | `git-town-runtime` | `CONTRACT → PREFLIGHT → CONTROL → DECISION → RECEIPT` | profile/task packet/executable evidence | local sync/publication decision lanes | mechanism + 13 controls PASS; executable `ABSENT` |
| `kb-ingest/`, `openwiki/` | `openwiki` | `REQUEST → DRY/FULL OPT-IN → VERIFY → RECEIPT` | wiki request | tracked projection | mechanism `IMPLEMENTED` |
| `docs/knowledge-providers/` | `knowledge-providers` | `MANIFEST → QUERY/PROPOSAL → SOURCE READBACK → ADMIT` | exact subject/capability | candidate result | contracts `IMPLEMENTED`; live varies |
| `.github/workflows/` | cloud verifier | `EVENT → EXACT CHECKOUT → DETERMINISTIC GATE → STATUS` | push/PR subject | GitHub check | `IMPLEMENTED`; skipped/stale is not PASS |
| final convergence artifacts (`.arena/compositions/`, locks, `data/module-proof/`) | #68 | `PIN TERMINALS → SELECT → LOCK → PROVE → LIVE CANARIES → AUTOMATED RELEASE` | admitted terminal subjects | immutable release/rollback | `BLOCKED_BY_PREDECESSORS` |

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
                                  Automated admission
                                  ├─ promote
                                  └─ reject / rollback
```

No Worker, provider, graph checkpoint, UI, memory store, vector index, local CI simulator, Git Town exit code or model prose can skip the Gate, reducer and automated-admission boundaries.

## Git Town Stacked-PR governance

Canonical shared method:

```text
repository: ed3c/skills-shared
commit:     c5750720d960a228a0d9419f28125c09d064e3e1
blob:       eb2d915bca3e8a3938625f7d33a10fae95a15769
path:       skills/git-town-stacked-pr-worker/SKILL.md
```

Bettor does **not** copy a local same-name `SKILL.md`. It owns the repository profile, task packets, path leases, queue/index, wrappers/evals and automated-admission policy under [`docs/git/`](docs/git/README.md).

The repository's current shared-Skills binding pins `b3c722da1c40301b0a12e0ef99848d884bfc720b`; that tree contains the same Git blob `eb2d915bca3e8a3938625f7d33a10fae95a15769` at the path above. This is byte-equivalence evidence for the method reference, not runtime selection.

The repository's current shared-Skills binding pins `b3c722da1c40301b0a12e0ef99848d884bfc720b`; that tree contains the same Git blob `eb2d915bca3e8a3938625f7d33a10fae95a15769` at the path above. This is byte-equivalence evidence for the method reference, not runtime selection.

Current admission:

```text
shared Skill exact reference            PINNED
shared Skill selected in Bettor binding NOT_SELECTED
.arena git-town-runtime module           IMPLEMENTED
typed controller/selftest/physical controls PASS
.git-town.toml                           ABSENT
Git Town executable/version/checksum     ABSENT
license/SBOM/legal admission             NOT_REVIEWED
live no-push sync                        NOT_EXERCISED
publication canary                       NOT_EXERCISED
merge / ship / rollback                  AUTOMATION-POLICY-OWNED
```

## Ordered PDF terminal Stack

Canonical ordered queue:

- [`docs/git/PDF_TERMINAL_SEQUENCE.md`](docs/git/PDF_TERMINAL_SEQUENCE.md)
- [`docs/git/pdf-terminal-sequence.json`](docs/git/pdf-terminal-sequence.json)
- [`docs/git/pdf-terminal-sequence.schema.json`](docs/git/pdf-terminal-sequence.schema.json)

```text
completed prefix: orders 0–11
current active item: #92 (order 12)
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

## Git Town / molecular Stack PR index

<!-- Molecular Stack PR index -->

The table intentionally separates byte delivery from ordered acceptance. `MERGED_TO_MAIN` in the fourth column never promotes a later blocked row to `COMPLETE`.

| Order | Issue | Directory/module terminal | Implementation PR(s) | Main-byte state | Ordered acceptance |
|---:|---:|---|---:|---|---|
| foundation | #62/#63/#64/#42/#69 | Contract/Ledger/Gateway/Memory/CTG v2 | #74/#75/#76/#78/#79 | `MERGED_TO_MAIN` | consumed by order 1 |
| 0 | #82 | Worker Gateway duplicate disposition | #76/#77 | #76 merged; #77 `SUPERSEDED_CANDIDATE` | `COMPLETE` |
| 1 | #90 | current-main foundation validation | #109 | `MERGED_TO_MAIN` | `COMPLETE` |
| 2 | #65 | `loopx-strategy-hitl` | #106 | `MERGED_TO_MAIN` | `COMPLETE` |
| 3 | #67 | `loopx-observability` | #116 | `MERGED_TO_MAIN` | `COMPLETE` |
| 4 | #66 | `loopx-runtime-fabric` | #117 | `MERGED_TO_MAIN` | `COMPLETE` |
| 5 | #94 | `loopx-worker-fleet` | #122 | `MERGED_TO_MAIN` | `COMPLETE` |
| 6 | #97 | `loopx-resource-gc` | #123 | `MERGED_TO_MAIN` | `COMPLETE` |
| 7 | #96 | `lsp-pool` | #124 | `MERGED_TO_MAIN` | `COMPLETE` |
| 8 | #103 | Decision Memory runtime | #125 | `MERGED_TO_MAIN` | `COMPLETE` |
| 9 | #93 | Mem0 projection | #126 | `MERGED_TO_MAIN` | `COMPLETE` |
| 10 | #104 | Notes source ingest | #127 | `MERGED_TO_MAIN` | `COMPLETE` |
| 11 | #105 | Notes retrieval | #128 | `MERGED_TO_MAIN` | `COMPLETE` |
| 12 | #92 | Serena/GrepAI live canaries | — | no terminal PR | `ACTIVE` |
| 13 | #41 | Code-Graph-RAG read-only admission | — | no terminal PR | `BLOCKED_BY_PREDECESSOR` |
| 14 | #70 | Knowledge compiler | #118 | `MERGED_TO_MAIN` | `BLOCKED_BY_PREDECESSOR` |
| 15 | #71 | Knowledge fold-back | #119 | `MERGED_TO_MAIN` | `BLOCKED_BY_PREDECESSOR` |
| 16 | #95 | Context Assembly | #129 | `MERGED_TO_MAIN` | `BLOCKED_BY_PREDECESSOR` |
| 17 | #72 | Skill/Prompt evolution | #120 | `MERGED_TO_MAIN` | `BLOCKED_BY_PREDECESSOR` |
| 18 | #98 | CI parity | #130 | `MERGED_TO_MAIN` | `BLOCKED_BY_PREDECESSOR` |
| 19 | #91 | six-host live matrix | — | no terminal PR | `BLOCKED_BY_PREDECESSOR` |
| 20 | #45 | Codex/Claude paired A/B | — | no terminal PR | `BLOCKED_BY_PREDECESSOR` |
| 21 | #46/#56 | provider evaluation convergence | #56 | `MERGED_TO_MAIN` evaluator bytes | `BLOCKED_BY_PREDECESSOR` |
| 22 | #99 | Harness Console | #131/#134 | `MERGED_TO_MAIN` | `BLOCKED_BY_PREDECESSOR` |
| 23 | #100 | Harness benchmark | #132/#135 | `MERGED_TO_MAIN` | `BLOCKED_BY_PREDECESSOR` |
| 24 | #101 | Git Town admission mechanism | #133 | mechanism `MERGED_TO_MAIN`; executable `ABSENT` | `BLOCKED_BY_PREDECESSOR` |
| 25 | #68 | final composition/live/release | — | no convergence PR | `FINAL_CONVERGENCE` |

Governance history: PR #60, PR #81 and PR #107/#121 established the verifier, Git Town policy and ordered queue. PR #136 closed the dual-origin publication repair. The #76/#77 duplicate remains indexed as `RESOLVED_BY_HUMAN` so conflict detection cannot be erased by later success.

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

The lock and release receipt contain exactly these 14 IDs. LoopX modules are catalogued and many are reachable from `main`, but none is selected in the final shared composition; every module evidence lane in the aggregate receipt remains `NOT_EXERCISED`. Selection and aggregate release remain #68.

## Stable public surfaces

### `loopctl`

```sh
sh loopctl/loopctl.sh contract
sh loopctl/loopctl.sh --selftest
```

`loopctl/contract.json` is the canonical external surface. Private module flags and temporary paths are not public contract.

### Stateless MCP

MCP tools derive from the canonical CLI contract and `.arena/mcp-policy.json`, default deny. Callers cannot supply generic shell text, arbitrary host paths, secrets or browser profiles; irreversible operations require named automated-admission tools.

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
BLOCKED_POLICY
RESOLVED_BY_HUMAN
```

A merged child is `MERGED_TO_MAIN` only when current-main reachability proves it. A later queue item is not complete merely because its issue, branch or fixture exists.

## Automated-admission boundaries

A model or background Worker may invoke push, merge, queue, provider, promotion
and rollback operations only through the named exact-subject typed controllers in
[`docs/git/AUTOMATED_ADMISSION.md`](docs/git/AUTOMATED_ADMISSION.md). It must not:

- guess a semantic Git conflict winner or continue, skip or undo outside policy;
- create a future terminal branch before queue activation or a scoped waiver;
- change remotes, credential helpers or permissions;
- use raw push, merge, ship, close or delete paths;
- select production providers, models, runtimes or credentials without the required manifest, bounds and receipt;
- issue an unscoped exception;
- admit a release or perform rollback outside the exact-subject automated controller.

## Current boundary

This branch records and validates the complete ordered PDF terminal queue. It does not install Git Town, create `.git-town.toml`, execute `git town sync`, implement any runtime terminal, activate a host/provider, modify production credentials, merge a PR, promote a release or perform rollback.
