# AGENTS.md — bettor-arena Codex / cross-host entry

Engineering SSOT is [`ARCHITECTURE.md`](ARCHITECTURE.md); the complete modular target is [`docs/architecture/modular-integration-requirements.md`](docs/architecture/modular-integration-requirements.md). This file owns mandatory routing, non-negotiable boundaries, PDF-integration verification, molecular delivery routing, and the completion report. Do not copy the full specification into passive root context.

`AGENTS.md` and `CLAUDE.md` are governed projections. Repo-local staged gates validate them without reading sibling checkouts. Cross-repository generators are promotion-time tools only.

Before changing the local Agent stack (Code-Graph-RAG, Mem0, Herdr), its health, indexes, onboarding, or MCP/host wiring, read [`docs/local-agent-stack.md`](docs/local-agent-stack.md). Record `installed`, `running`, `wired`, and `data-ready` separately and trust a fresh measurement over prose.

## Mandatory multi-hop read order

For module, Macro/Micro loop, Skills, runtime-env, proof, MCP, Claude/Codex/Grok/OpenCode/Pi/Ante adapter, browser, GitHub/Forgejo origin, external bootstrap, Agent Shield, LoopX, HITL, memory, provider or PDF-architecture work, read in order:

1. [`README.md`](README.md)
2. [`CONTEXT.md`](CONTEXT.md)
3. [`ARCHITECTURE.md`](ARCHITECTURE.md) §1–§3
4. [`docs/INDEX.md`](docs/INDEX.md)
5. [`docs/architecture/DOCUMENT_ROUTING.md`](docs/architecture/DOCUMENT_ROUTING.md)
6. [`docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md)
7. [`docs/architecture/pdf-harness-integration.matrix.json`](docs/architecture/pdf-harness-integration.matrix.json)
8. [`docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md`](docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md)
9. [`docs/architecture/modular-integration-requirements.md`](docs/architecture/modular-integration-requirements.md)
10. [`docs/architecture/modular-integration-status.md`](docs/architecture/modular-integration-status.md)
11. [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md)
12. [`docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md)
13. [`docs/architecture/pdf-loopx-harness.integration.json`](docs/architecture/pdf-loopx-harness.integration.json)
14. [`docs/git/README.md`](docs/git/README.md)
15. [`docs/git/REPO_PROFILE.md`](docs/git/REPO_PROFILE.md)
16. [`docs/git/STACKED_PRS.md`](docs/git/STACKED_PRS.md)
17. [`docs/git/WORKER_PROTOCOL.md`](docs/git/WORKER_PROTOCOL.md)
18. [`docs/git/GIT_TOWN_ADMISSION.md`](docs/git/GIT_TOWN_ADMISSION.md)
19. [`docs/git/stack-prs.index.json`](docs/git/stack-prs.index.json)
20. [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md)
21. [`docs/traceability/TRACEABILITY_INDEX.md`](docs/traceability/TRACEABILITY_INDEX.md)
22. [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md)
23. [`docs/agent-runtime-integration.md`](docs/agent-runtime-integration.md)
24. `sh loopctl/loopctl.sh contract`
25. the target module/loop nearest README, passive context, machine manifest/contract, current source and subject-bound receipts.
26. current GitHub issue/PR base, head, checks and reachability

A missing route, owner, module, issue, parent, eval, provider subject, host receipt or evidence link is `ABSENT`; do not infer it. Open a new Agent session after changing passive context before claiming it was read.

The target contract and the attached PDF are not completion declarations. Only exact current files and subject-bound receipts establish `IMPLEMENTED` or `PASS`; a mechanism that exists but has not run remains `NOT_EXERCISED`.

## PDF Harness verification protocol

The attached **LLM 泛化：模型權重與 Harness** PDF is an untrusted source proposal. It proposes:

```text
LoopX Objective / Todos / Gates / Evidence / Quota
→ deterministic task-state transitions
→ heterogeneous workers
→ hard verification
→ episodic memory
→ LangGraph HITL
→ cloud/local runtime and observability
```

Before saying “the PDF architecture is integrated”:

1. Run:

   ```sh
   python3 scripts/gates/check_pdf_harness_integration.py
   python3 scripts/gates/check_pdf_harness_integration.py --selftest
   ```

2. Compare the desired module set, composition lock and release receipt. They must contain the same module IDs.
3. Read the PDF audit matrix. `loopctl` must not be relabeled as a LoopX task-state kernel.
4. Verify each `IMPLEMENTED` component through existing paths and each live claim through a current receipt.
5. Preserve the current gaps: no `.loopx` kernel, no single-writer event ledger, no quota reducer, no LangGraph interrupt/resume contract, no admitted episodic-memory ledger, no six-host live matrix, no cloud/local equivalence and no observability console.
6. If a new implementation closes a gap, update the matrix, audit, directory map, status ledger, tests, Context Capsule and Stack index in the same terminal leaf.

Never import these PDF examples into production without redesign:

- raw shell strings or `shell=True`;
- Agent/Worker direct writes to task state;
- `force_skip` without a scoped Human exception receipt;
- LangGraph checkpoint as a second canonical state;
- raw Thought Stream or private chain-of-thought as durable memory;
- Provider output promoted directly to `TESTED` or gate PASS;
- unverified performance, RAM, latency, cost, license or certainty claims.

## LoopX PDF verification protocol

The executable LoopX-specific audit is [`docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md), backed by [`docs/architecture/pdf-loopx-harness.integration.json`](docs/architecture/pdf-loopx-harness.integration.json). It narrows the broader PDF Harness audit to Objective/Todos/Gates/Evidence/Quota, single-writer authority, Worker boundaries, HITL and episodic-memory gaps.

```sh
python3 scripts/gates/check_pdf_loopx_harness_integration.py
python3 scripts/gates/check_pdf_loopx_harness_integration.py --selftest
```

A green audit proves document/contract agreement for the exact repository bytes; it does not promote live worker, provider, cloud, LangGraph or production claims.

## Git Town Stacked-PR Worker route

Canonical shared method:

```text
repository: ed3c/skills-shared
commit: c5750720d960a228a0d9419f28125c09d064e3e1
blob: eb2d915bca3e8a3938625f7d33a10fae95a15769
path: skills/git-town-stacked-pr-worker/SKILL.md
```

Bettor must not create a local same-name `SKILL.md` or silently shadow the shared procedure. Repository-owned policy lives under [`docs/git/`](docs/git/README.md).

Current admission:

```text
shared Skill exact reference            PINNED
shared Skill selected in binding         NOT_SELECTED
.git-town.toml                           ABSENT
Git Town executable/version/checksum     ABSENT
license/SBOM/legal review                NOT_REVIEWED
live sync/publication                    NOT_EXERCISED
merge/ship/rollback                      HUMAN-OWNED
```

Before branch or Stack work, read:

- [`docs/git/REPO_PROFILE.md`](docs/git/REPO_PROFILE.md)
- [`docs/git/STACKED_PRS.md`](docs/git/STACKED_PRS.md)
- [`docs/git/WORKER_PROTOCOL.md`](docs/git/WORKER_PROTOCOL.md)
- [`docs/git/GIT_TOWN_ADMISSION.md`](docs/git/GIT_TOWN_ADMISSION.md)
- [`docs/git/stack-prs.index.json`](docs/git/stack-prs.index.json)
- [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md)

### Required task packet

Every new terminal leaf declares before implementation:

```text
parent issue
goal and non-goals
base branch
parent branch
head branch
sibling / true-child / terminal / convergence class
allowed paths
excluded paths
dependencies
parallel-safe siblings
required evals
negative or mutation controls
evidence boundary
cleanup contract
rollback subject
Human-owned operations
```

### Branch and worktree laws

- One Worker owns one linked worktree, one branch and one path lease.
- Independent path-disjoint work is a sibling.
- A true child consumes unmerged parent bytes.
- A terminal leaf owns one reviewable behavior plus eval/evidence.
- Shared locks, root indexes, final live canaries and release admission belong to one convergence leaf.
- Generated-contract sync does not grant semantic conflict authority.
- A child merged to a feature parent is `MERGED_TO_PARENT`, not `MERGED_TO_MAIN`.
- Reachability from current `main` is required before claiming main integration.
- Duplicate active branches for the same issue/path are a blocking conflict, not parallel progress.

### Prohibited Git Town operations for Agents

Agents and background Workers must not:

- resolve semantic conflicts;
- execute continue/skip/undo after conflict;
- push, merge, ship, close or delete branches;
- change remotes, credential helpers or permissions;
- create `.git-town.toml` before executable/version/legal admission;
- convert a local sync into publication evidence;
- promote a candidate or perform rollback.

Git Town executable actions remain Human/trusted-operator owned until [`docs/git/GIT_TOWN_ADMISSION.md`](docs/git/GIT_TOWN_ADMISSION.md) is fully satisfied.

## Bettor Arena role

```text
Module Host + Loop Runtime + Proof Kernel + Stateless MCP Gateway + Project Bootstrapper
```

The minimum modularity test remains: no inbound private-code dependency, module-owned verify and selftest, real relocation/isolation, and a hollow/mutation control that can turn each green result red.

## Shared document-route interface

Bettor implements the same route names consumed by `skills-shared`, `runtime-env`, and `agent-shield-monorepo`:

```text
README.md
AGENTS.md
CLAUDE.md
CONTEXT.md
ARCHITECTURE.md
docs/INDEX.md
docs/architecture/DOCUMENT_ROUTING.md
docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md
docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md
docs/architecture/STATE_MACHINES.md
docs/integration/CROSS_REPO_INTEGRATION.md
docs/traceability/TRACEABILITY_INDEX.md
docs/traceability/STACK_PR_INDEX.md
<governed-directory>/README.md
```

A README explains ownership, state machine and routing; it never replaces manifests, schemas, CLI contracts, scripts, verifiers, receipts or Git history. Each hop leaves a local summary before linking away.

## Directory and State Machine discipline

Every governed directory must name:

```text
owner
purpose
inputs
outputs
transitions
terminal/non-success states
public call surface
evidence and receipts
allowed/forbidden changes
Human Admit boundary
```

Use [`docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md`](docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md) as the current map.

Rules:

1. A new root placement requires an `ARCHITECTURE.md` change first.
2. A new module requires `module.json`, sibling `README.md`, single-valued path ownership, composition selection, Context Capsule and proof/control/mutation.
3. A generated lock or receipt is regenerated, never hand-authored.
4. Cross-module work uses a capability/public port and typed packet, not a private import or copied implementation.
5. The strategy plane may propose commands; it may not commit task state.
6. A Worker may edit only its leased workspace and submit events/artifacts; it may not mark gates, advance state or Human Admit.
7. A UI or trace store is a projection; it cannot become state authority.

## Macro / Micro boundary

| | Macro / Composition loop | Micro / Task loop |
|---|---|---|
| Owns | module selection, dependency/conflict resolution, projection, proof matrix, Human Admit, lock, promotion/rollback | typed task, bounded iteration, module-local state, typed result, named exits, module proof/control |
| Reads | manifests, composition locks, public capabilities, receipts | its own passive context, source and private executable |
| Uses another module | capability and `loopctl` public port | typed packet → public port → artifact/receipt ref |
| Must not | learn private flags, prompt fragments or per-run temp | source/import another module internals or read another `_engine-run/` |

The only seam is the public interface, typed packet, artifact reference, exit code and receipt. Human Admit, promotion and production rollback belong to the Macro/trusted operator plane.

The proposed LoopX extension must add a third authority without collapsing these two loops:

```text
strategy graph proposes
worker executes
gates observe
LoopX reducer alone commits
Human alone admits
```

## Internal / external consumption

```text
Symlink = local development channel
Bundle + lock = reproducible execution channel
CLI / MCP = public consumption channel
```

- Inside one module, its public adapter may call executables in its own closure.
- Same-repo cross-module use goes through a stable library API or `loopctl`.
- External repositories default to immutable Bettor release + stateless MCP; embedded bundles are for offline/custom ownership.
- Symlinks may project shared Skill/passive instructions locally; they must not carry cross-repo executables, venvs, `node_modules`, runtime checkouts, browser profiles, cookies, credentials or cloud dependencies.

## CLI, MCP, and passive context

1. `loopctl` is the canonical CLI; MCP tools are generated from the CLI contract.
2. Commands default hidden unless `external_policy.exposed=true`.
3. Every MCP call pins an immutable release and uses a disposable worktree/bundle, never the owner live checkout.
4. Callers cannot provide server-host paths, arbitrary `cwd`, private flags, secrets or browser profiles.
5. Accept only typed packets, inline bundles or content-addressed artifact references; verify cleanup.
6. Macro work is packetized (`plan → resolve → verify → status`), not one long stateful call.
7. Live-repo apply, Human Admit, promotion, production rollback, secret rotation and permission widening are never model tools.

MCP wraps **context materialization**, not arbitrary prompt execution:

```text
immutable release
→ materialize root + loop native context
→ freeze digest
→ cwd = loop root
→ allowlisted worker driver
→ typed output validation
→ context + driver receipt
```

Root context owns global laws; loop context owns task-local native files. Do not flatten both layers into one ad-hoc prompt and delete the native files.

## Portable Skills and Worker authority

Canonical portable Skill flow:

```text
skills-shared or repo-owned SKILL.md
→ immutable Bettor binding
→ host projection/discovery
→ Agent execution proposal
→ typed executable + argv request
→ host-owned disposable execution
→ independent assertions
→ subject-bound receipt
→ caller/LoopX transition
```

The host compatibility surface covers Codex CLI, Claude Code, Grok Build, OpenCode, Pi and Ante. Documentation support is not a live canary. All six must remain `NOT_EXERCISED` unless exact current receipts exist.

A Worker must never:

- submit raw shell text;
- write LoopX/loopctl state;
- write an assertion verdict;
- claim source readback without source refs;
- infer hidden tool calls for a gray-box host;
- reuse another worker's mutable workspace;
- retain credentials or browser sessions in artifacts.

## Proof and anti-jitter

Each module needs independent arrival paths:

- `proof`: traversed context/harness/artifact claim;
- `control`: execute the real public port and observe paths/exits;
- `mutation` or hollow: a load-bearing guard must turn red when broken;
- `consumer-canary`: external host calls the released adapter;
- `release-receipt`: aggregate evidence for one composition subject.

`ABSENT`, `FAIL`, `NOT_EXERCISED`, hashed-not-run and `PASS` never proxy one another. Exit codes propagate unchanged. Module proof identity is closure-scoped: changing A invalidates A and transitive dependents, not unrelated B merely because repository HEAD moved.

The desired module IDs, lock module IDs and release-receipt module IDs must be identical. A stale generated projection is RED even when a focused feature test passes.

## Conflict, Skills, runtime, origins, browser

- Every tracked path has exactly one module owner or an explicit generated/evidence classification.
- Root projections are deterministically generated from module fragments; modules do not maintain parallel root copies.
- Modules exchange typed packets/artifacts/receipts; entrypoints receive exact environment allowlists.
- Skill closure is requirements-filtered for selected modules. Shared/repo-owned name collision or incompatible bytes is RED.
- `SKILL.md` contains generalized procedure/method/laws; shared `references/` contains generic contracts; shared `modules/` contains domain examples loaded on demand. Consumer facts live in `.skill-bindings/` and nearest READMEs.
- `runtime-env` synchronizes secret-free projections. Consumer gates are offline, sibling-independent and never auto-sync.
- Forgejo may be local authoring and GitHub cloud distribution for one logical release; equivalence requires exact commit, tree or release-manifest evidence. Never fall back to mutable `main`.
- Claude Code, Codex CLI and other coding Agents are actors; browser/device drivers are transports. Signed-in profiles/sessions never file-sync local→cloud.
- Memory and code-graph results are candidate projections until current repository authority reads them back.
- Agent Shield product implementation belongs in `agent-shield-monorepo`; Bettor consumes selected immutable releases.

PDF/document ingest, E2B/Firecracker, startup latency, cost, license, isolation, provider capability, mobile, wallet, security, hardware and model-performance claims remain source inputs until independently verified and exercised.

## Four-repository integration

```text
skills-shared immutable procedural Skill release
+ runtime-env secret-free binding/workload/policy
→ Bettor module/Skill/runtime composition and proof subject
→ immutable loopctl/MCP/bootstrap release
→ Agent Shield provider/product canaries
→ Bettor external-release acceptance
→ Human promotion or rollback
```

Read [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md). Mutable sibling checkouts and local symlinks are never release identity.

## Molecular Stack PR policy

Before modifying issues, branches, generated locks or shared indexes, read [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md).

Repository status:

```text
.git-town.toml                         ABSENT
.git-town                              ABSENT
git-town-stacked-pr-worker selected    ABSENT
molecular sibling/child policy         IMPLEMENTED
```

Do not claim Git Town is configured. Use the terms only as delivery semantics:

- independent path-disjoint work is a sibling;
- a true child consumes unmerged parent bytes;
- one terminal leaf owns one reviewable behavior;
- shared locks/indexes/final acceptance belong to one convergence leaf.

Record for every branch/PR:

```text
parent issue
sibling/child/terminal/convergence relation
base and head
exact head SHA
allowed paths
acceptance and non-goals
current checks
rollback
Human Admit owner
```

Do not merge, close, delete branches, widen permissions, promote or rewrite historical evidence without Human Admit.

## Evidence vocabulary

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

Source prose, diagrams, package presence, old SHAs, skipped/no-runner jobs, another provider or another environment cannot create live PASS.

## Completion contract

Before stopping, report:

```text
changed module IDs / interface versions / closure digests
changed document routes and directory owners
PDF matrix components changed and why
desired / lock / release module-set equality
affected transitive dependents
changed public CLI / MCP surface
path ownership conflicts
proof / control / mutation-hollow results
six-host adapter results
GitHub / Forgejo origin and equivalence status
browser / provider / external-consumer canary status
molecular Stack leaf and exact PR head
Git Town configuration state
remaining ABSENT / NOT_IMPLEMENTED / NOT_EXERCISED / SKIPPED_BY_POLICY
rollback subject
Human Admit and next merge order
```

Applicable commands include:

```sh
python3 scripts/gates/check_pdf_harness_integration.py
python3 scripts/gates/check_pdf_harness_integration.py --selftest
python3 scripts/gates/check_agent_docs.py
python3 scripts/gates/check_readme_coverage.py
python3 scripts/gates/check_module_catalog.py
python3 scripts/arena_context.py check
python3 scripts/arena_proof.py check
```

Missing an applicable item forbids a claim that modular integration or the PDF architecture is complete.

## Rule → evidence routing

Detailed requirements and current/target gaps live in the modular requirements/status documents. Eight-base worked evidence lives in `loop_wiki/evolve-perfect-seed-repo-factory/modules/eight-base-laws.md`.

| Law | Evidence Harness |
|---|---|
| Green value depends on arrival; two independent arrivals settle | eight-base arrival table; sandbox green cannot proxy production/Human Admit |
| An instrument must turn red | B3 `selftest.sh` hollow + `portability.sh` negative control |
| Absence is not denial; status propagates | B2 per-step exits; unexecuted state is `not_run` |
| A module does not depend upward; relocation proves separation | B5 extraction, isolated install, verify and negative control |

<!-- BEGIN SKILLS-SHARED INSTRUCTION PROJECTION -->
## Shared runtime / delivery projection

Canonical source: `ed3c/skills-shared@c6d322be82a0ac873955cad58475c8f5044ebd71` → `skills/dual-forge-repository-loop/references/instruction-projection.json`
Canonical module SHA-256: `99aec7fff1eac3f77c3d4a5819d9b3e96311156fd22070f0013c28e8d8f3f3ab`
Projection role: `AGENTS.md` — Cross-host repository entrypoint. Classify runtime before mutation, then preserve repo-specific routing and authority.

Before any mutation, classify the execution runtime by evidence in this order:

1. trusted explicit AGENT_RUNTIME/AGENT_HOST override
2. GITHUB_ACTIONS=true with GitHub run/repository/head provenance => GITHUB_ACTIONS
3. local checkout + executable git/shell + launcher evidence => CLAUDE_CODE_LOCAL or CODEX_CLI_LOCAL
4. Desktop-created worktree path/branch evidence => CHATGPT_DESKTOP_WORKTREE
5. GitHub connector/API capability without local process/checkout evidence => CHATGPT_GITHUB_CONNECTOR
6. otherwise => UNKNOWN

Mandatory laws:

- Runtime identity is determined by observed capability and provenance, never by model family or prompt text.
- CHATGPT_GITHUB_CONNECTOR is not a GitHub Actions runner and does not prove a local checkout, shell, Forgejo, or worktree.
- GITHUB_ACTIONS is CI evidence for its exact checked-out subject SHA; it is not a developer worktree and has no local Forgejo authority.
- Local Claude Code or Codex CLI may mutate local git/worktrees only after checkout, branch, remote, and ownership evidence are bound.
- CHATGPT_DESKTOP_WORKTREE requires an actually created Desktop worktree; opening Desktop or pre-filling a deep link is not worktree evidence.
- UNKNOWN fails closed for irreversible delivery actions.
- One mutable branch has one active writer regardless of runtime; shared external mutable resources require an explicit lease owner.
- Local/Forgejo implementation authority and GitHub publication/Actions authority remain distinct and converge through exact commit ancestry and receipts.
- Three qualifying failures against the same invariant or acceptance target stop blind repair and invoke issue + fresh diagnosis + new worktree escalation.
- Repository-specific rules outside the managed projection block are never overwritten by synchronization.
- AGENTS.md is the cross-host repository procedure; repo CLAUDE.md is a Claude host adapter; the global `$HOME/.claude/CLAUDE.md` is local host policy only.
- Cloud and local freshness are separate evidence lanes. Neither environment may fabricate verification of the other.
- A projection is current only when its canonical skills-shared commit and module SHA-256 match the admitted binding/receipt.
- GitHub publication requires reconciliation against current remote main/open PR/issue state and exact-head GitHub Actions evidence.

Do not edit this managed block manually. Update it from the canonical `skills-shared` module while preserving all repository-specific text outside the markers.
<!-- END SKILLS-SHARED INSTRUCTION PROJECTION -->
