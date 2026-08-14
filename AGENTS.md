# AGENTS.md — bettor-arena Codex / cross-host entry

Engineering SSOT is [`ARCHITECTURE.md`](ARCHITECTURE.md). The normative modular target is [`docs/architecture/modular-integration-requirements.md`](docs/architecture/modular-integration-requirements.md). This file owns mandatory routing, non-negotiable authority boundaries, PDF verification, Git Town Stack governance and the completion report. It does not replace machine contracts, tests, receipts or GitHub metadata.

`AGENTS.md` and `CLAUDE.md` are governed projections. Repo-local gates validate repository bytes without reading mutable sibling checkouts.

## Mandatory multi-hop read order

For module, Macro/Micro loop, Skill, runtime-env, proof, MCP, provider, LoopX, worker, HITL, memory, Git Town, branch Stack or PDF architecture work, read in order:

1. [`README.md`](README.md)
2. [`CONTEXT.md`](CONTEXT.md)
3. [`ARCHITECTURE.md`](ARCHITECTURE.md)
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
20. [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md)
21. [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md)
22. [`docs/agent-runtime-integration.md`](docs/agent-runtime-integration.md)
23. `sh loopctl/loopctl.sh contract`
24. the target module/loop nearest README, `module.json`, contracts, source, tests and exact-subject receipts
25. current GitHub issue/PR base, head, checks and reachability

A missing route, owner, branch edge, path lease, eval, receipt, provider subject or exact head is `ABSENT`; do not infer it. Open a new Agent session after changing passive context before claiming it was read.

## PDF Harness verification protocol

The attached **LLM 泛化：模型權重與 Harness** PDF is an untrusted requirement/hypothesis source. It proposes:

```text
Objective / Todos / Gates / Evidence / Quota
→ deterministic task transitions
→ heterogeneous Workers
→ hard verification
→ episodic memory
→ LangGraph HITL
→ cloud/local runtime
→ observability
```

Before saying “the PDF architecture is integrated”:

```sh
python3 scripts/gates/check_pdf_harness_integration.py
python3 scripts/gates/check_pdf_harness_integration.py --selftest
python3 scripts/gates/check_pdf_loopx_harness_integration.py
python3 scripts/gates/check_pdf_loopx_harness_integration.py --selftest
```

Then compare repository bytes, composition requirements, locks, proof subjects, release receipt and current GitHub Stack metadata.

Never import these PDF examples without redesign:

- raw shell strings or `shell=True`;
- Agent/Worker direct task-state writes;
- plain `force_skip`;
- LangGraph checkpoint as canonical truth;
- raw Thought Stream or private chain-of-thought persistence;
- provider/model prose promoted to `TESTED` or Gate PASS;
- unverified latency, RAM, license, cost, security or certainty claims.

## LoopX PDF verification protocol

The executable LoopX audit is:

- [`docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md)
- [`docs/architecture/pdf-loopx-harness.integration.json`](docs/architecture/pdf-loopx-harness.integration.json)

A green audit proves document/contract agreement for exact repository bytes. It does not prove a live Worker, cloud sandbox, LangGraph runtime, provider or production promotion.

Authority law:

```text
strategy proposes
Worker executes
Gates observe
LoopX reducer alone commits canonical task state
Human alone admits scoped exceptions, merge, promotion and rollback
```

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

## Current molecular Stack truth

```text
main @ 10380005fa485d6035539589c01b9f740acff15d
│
├─ PR #60 feat/pdf-loopx-modular-verifier-v1
│    └─ issue #80 / feat/git-town-stack-governance-v1
│         true-child docs/governance terminal
│
├─ PR #74 feat/loopx-contract-v1
│    ├─ PR #75 feat/loopx-ledger-v1
│    │    MERGED_TO_PARENT; not reachable from main
│    ├─ PR #76 feat/loopx-worker-gateway-v1
│    ├─ PR #77 feat/loopx-worker-gateway-terminal-v1
│    │    duplicate issue/path lease with #76; Human resolution required
│    ├─ PR #78 feat/loopx-decision-memory-v1
│    └─ PR #79 feat/loopx-code-truth-graph-v2
│
├─ PR #56 provider admission evaluation lane
├─ PR #53 historical aggregate, non-authoritative
└─ issue #68 final convergence owner
```

GitHub metadata remains fresher than this snapshot. Update both Stack indexes when base/head/state changes.

## Directory and State Machine discipline

Every governed directory names:

```text
owner
purpose
inputs
outputs
transitions
non-success and terminal states
public call surface
evidence and receipts
allowed/forbidden changes
Human Admit boundary
```

Use [`docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md`](docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md).

Rules:

1. A new root placement requires `ARCHITECTURE.md` first.
2. A new module requires `module.json`, sibling README, single path owner, composition policy and proof/control/mutation.
3. A generated lock or receipt is regenerated, never hand-authored.
4. Cross-module work uses capabilities/public ports and typed packets.
5. Strategy may propose; it cannot commit state.
6. Worker may modify only its leased workspace and cannot write verdict/admission state.
7. UI, trace, graph, vector and memory stores are projections.
8. `docs/git/` owns repository Git policy; it does not own GitHub or Git Town runtime truth.
9. Stack state changes update `README.md`, `docs/git/STACKED_PRS.md`, `docs/git/stack-prs.index.json` and `docs/traceability/STACK_PR_INDEX.md` in one governed workstream.

## Macro / Micro boundary

| | Macro / Composition | Micro / Task |
|---|---|---|
| Owns | module and Stack selection, dependencies, conflicts, proof matrix, Human Admit, lock, promotion/rollback | typed task, bounded iteration, module-local state, typed result, named exits |
| Reads | manifests, profile, branch graph, locks, receipts | own passive context, source, private executable |
| Crosses modules | capability/public port | typed packet → public port → artifact/receipt |
| Must not | learn private flags or per-run temp | import another module internals or read another run directory |

The proposed LoopX reducer is a third authority between orchestration and execution; it does not collapse Macro and Micro.

## CLI, MCP, and passive context

1. `loopctl` is the canonical CLI.
2. MCP derives from canonical CLI + explicit allowlist and defaults deny.
3. Every external call pins an immutable subject and uses disposable materialization.
4. Caller cannot provide arbitrary host paths, raw shell, secrets or browser profiles.
5. Human Admit, merge, ship, production rollback, secret rotation and permission widening are never model tools.
6. MCP wraps context/materialization and typed execution, not arbitrary prompts.

## Portable Skills and Worker authority

```text
canonical SKILL.md
→ immutable consumer binding
→ host projection/discovery
→ Agent proposal
→ typed executable + argv
→ host-owned disposable execution
→ independent assertions
→ subject-bound receipt
→ LoopX/caller transition
```

Codex CLI, Claude Code, Grok Build, OpenCode, Pi and Ante remain independently evidenced. Documentation support or source visibility is not a live canary.

## Proof and anti-jitter

Each module/terminal needs:

```text
proof traversal
independent control
hollow or planted mutation
exact subject
cleanup result
consumer/live canary where applicable
```

`ABSENT`, `FAIL`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, skipped and PASS never proxy one another.

## Four-repository integration

```text
skills-shared immutable procedure
+ runtime-env secret-free runtime contract
→ Bettor composition/Stack/proof subject
→ immutable loopctl/MCP/bootstrap release
→ Agent Shield provider/product canary
→ Bettor acceptance
→ Human promotion or rollback
```

Mutable sibling checkouts and symlinks are development projections, not release identity.

## Molecular Stack PR policy

Repository profile and machine snapshot are under `docs/git/`. Publication truth is current GitHub metadata.

Do not merge, close, delete, retarget, ship, widen permission, promote or rollback without Human Admit.

## Evidence vocabulary

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
MERGED_TO_MAIN
MERGED_TO_PARENT
BLOCKED_DUPLICATE_TERMINAL
SUPERSEDED_CANDIDATE
```

## Completion contract

Before stopping, report:

```text
changed document routes and directory owners
shared Skill exact subject and selection state
Git Town executable/config/legal/live states
Stack parent/base/head and observed exact SHA
path lease and overlap conflicts
changed module IDs / interface versions / closure digests
desired / lock / release module-set equality
changed CLI / MCP surface
proof / control / mutation results
six-host/provider/live canary states
remaining ABSENT / NOT_IMPLEMENTED / NOT_EXERCISED
rollback subject
Human-owned next operation
```

Applicable commands:

```sh
python3 scripts/gates/check_git_town_stack_docs.py
python3 scripts/gates/check_git_town_stack_docs.py --selftest
python3 -m unittest -q tests/test_git_town_stack_docs.py
python3 scripts/gates/check_pdf_harness_integration.py
python3 scripts/gates/check_pdf_loopx_harness_integration.py
python3 scripts/gates/check_agent_docs.py
python3 scripts/gates/check_readme_coverage.py
python3 scripts/gates/check_module_catalog.py
python3 scripts/arena_context.py check
python3 scripts/arena_proof.py check
```

A missing applicable item forbids a claim that modular integration or Git Town adoption is complete.
