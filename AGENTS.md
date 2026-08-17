# AGENTS.md — bettor-arena cross-host router

Engineering SSOT: [`ARCHITECTURE.md`](ARCHITECTURE.md).  
Target modular contract: [`docs/architecture/modular-integration-requirements.md`](docs/architecture/modular-integration-requirements.md).  
Current handoff: [`CONTEXT.md`](CONTEXT.md).

This file is the mandatory routing and authority contract. It does not duplicate module contracts, State Machines, PDF audits, Stack indexes, provider state, receipts, or current forge metadata.

## Mandatory multi-hop read order

For every task:

1. Read [`README.md`](README.md) for repository role and concise topology.
2. Read [`CONTEXT.md`](CONTEXT.md) for the mutable current handoff.
3. Read [`ARCHITECTURE.md`](ARCHITECTURE.md) for stable placement and authority.
4. Read [`docs/INDEX.md`](docs/INDEX.md) and classify the task before selecting a topic route.
5. Read the nearest governed-directory `README.md` for local owner, State Machine, DAG, data flow, evidence ceiling, allowed changes, and forbidden changes.
6. Read the exact machine contract, source, tests, verifier, receipt, issue, PR base/head, and current checks required by that route.

A missing route, binding, owner, lease, evaluator, receipt, provider subject, or exact head is `ABSENT`. Do not reconstruct it from chat history, branch names, mutable sibling checkouts, package presence, or an old successful SHA.

### Conditional topic routes

| Trigger | Additional route |
|---|---|
| shared Skill, `.agents/`, `.skill-bindings/`, module, adapter, provider port, domain boundary | [`docs/architecture/AGENTS.md`](docs/architecture/AGENTS.md) → [`docs/architecture/DOMAIN_DECOUPLING.md`](docs/architecture/DOMAIN_DECOUPLING.md) |
| state, event, transition, terminal, evidence transition | [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md) |
| target/current modular architecture | [`docs/architecture/modular-integration-requirements.md`](docs/architecture/modular-integration-requirements.md) and [`docs/architecture/modular-integration-status.md`](docs/architecture/modular-integration-status.md) |
| source PDF integration | [`docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md) and [`docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md`](docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md) |
| LoopX source proposal | [`docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md) and [`docs/architecture/pdf-loopx-harness.integration.json`](docs/architecture/pdf-loopx-harness.integration.json) |
| Git Town, branch, Stack PR, publication | [`docs/git/README.md`](docs/git/README.md), [`docs/git/REPO_PROFILE.md`](docs/git/REPO_PROFILE.md), and [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md) |
| ordered terminal queue | [`docs/git/PDF_TERMINAL_SEQUENCE.md`](docs/git/PDF_TERMINAL_SEQUENCE.md) and [`docs/git/pdf-terminal-sequence.json`](docs/git/pdf-terminal-sequence.json) |
| Worker/Stack mechanics | [`docs/git/STACKED_PRS.md`](docs/git/STACKED_PRS.md), [`docs/git/WORKER_PROTOCOL.md`](docs/git/WORKER_PROTOCOL.md), [`docs/git/GIT_TOWN_ADMISSION.md`](docs/git/GIT_TOWN_ADMISSION.md), and [`docs/git/stack-prs.index.json`](docs/git/stack-prs.index.json) |
| irreversible delivery or provider operation | [`docs/git/AUTOMATED_ADMISSION.md`](docs/git/AUTOMATED_ADMISSION.md) |
| runtime/host adapter or public execution | [`docs/agent-runtime-integration.md`](docs/agent-runtime-integration.md) and the nearest `.runtime-env/` or `loopctl/` README |
| source → issue → PR → eval → receipt closure | [`docs/traceability/TRACEABILITY_INDEX.md`](docs/traceability/TRACEABILITY_INDEX.md) |
| cross-repository binding, origin, release, or three-strike handoff | [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md) |

Do not load all topic routes for every task. A task reads only the routes whose triggers match.

## Authority hierarchy

```text
Human / legal / permission boundary
→ exact machine contract and immutable subject
→ deterministic verifier and current receipt
→ source code and runtime evidence
→ stable architecture documents
→ AGENTS / README / CONTEXT navigation
→ source proposal, memory, search, model suggestion
```

Markdown is never a second CLI, schema, registry, verifier, receipt, workflow result, merge authority, capability unlock, or provider admission.

Evidence states remain distinct:

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
HUMAN_ADMIT_REQUIRED
BLOCKED_POLICY
CONFLICT
```

A fixture PASS, workflow definition, provider-health check, local symlink, mutable branch, model agreement, or source proposal cannot establish live or production PASS.

## Domain Decoupling contract

The shared procedural core and Bettor specialization are joined through exact bindings and domain ports:

```text
shared procedure
→ immutable consumer requirement/binding
→ Bettor domain adapter/module
→ runtime/public port
→ Bettor proof/control/mutation
→ Bettor-owned receipt
```

Read [`docs/architecture/DOMAIN_DECOUPLING.md`](docs/architecture/DOMAIN_DECOUPLING.md) only when its trigger matches. Bettor may tighten constraints, narrow effects, increase evidence, or reduce authority. Bettor must not weaken shared hard gates, copy a canonical shared `SKILL.md`, or use mutable/local/fixture state as release authority.

## PDF Harness verification protocol

The attached architecture PDF is `SOURCE_PROPOSAL`, not repository truth. For PDF work, follow the PDF route selected from `docs/INDEX.md`, then execute the declared gates, including:

```sh
python3 scripts/gates/check_pdf_harness_integration.py
python3 scripts/gates/check_pdf_harness_integration.py --selftest
```

A green document audit proves agreement for exact repository bytes only. It does not prove a live Worker, provider, cloud sandbox, model, Console, official standard, or release.

## LoopX PDF verification protocol

Use only the LoopX routes listed in the conditional table. Execute the owning verifier only when this route is selected:

```sh
python3 scripts/gates/check_pdf_loopx_harness_integration.py
python3 scripts/gates/check_pdf_loopx_harness_integration.py --selftest
```

Preserve this authority wording because the existing machine contract consumes these route anchors:

```text
strategy graph proposes
Worker/provider executes
hard Gates observe
LoopX reducer alone commits canonical task state
```

The admitted controller alone performs irreversible transitions. Presence of the LoopX documents does not mean the LoopX kernel or HITL runtime is implemented.

## Automated admission contract

[`docs/git/AUTOMATED_ADMISSION.md`](docs/git/AUTOMATED_ADMISSION.md) is the sole route for standing authorization to push, merge, advance a queue, activate an allowlisted provider, promote, or roll back.

Automation fails closed when an exact head, lease, required check, receipt, budget/data-scope bound, cleanup proof, or rollback subject is missing. Semantic conflict without a declared deterministic winner stops as `CONFLICT`; no Agent guesses a resolution.

## Three-strike recovery and dual-origin delivery

Three materially different failures against the same invariant stop blind repair. Read [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md) for the issue-first local/Forgejo/GitHub handoff, exact-subject packet, fresh diagnosis, WIP=1 reconciliation, and sync-back rules.

A checked-red receipt remains red. Exit `2` is an evaluated failure; exit `64` means the gate cannot evaluate. Neither may be recolored to unlock delivery.

## Ordered PDF terminal Stack protocol

Machine authority:

```text
docs/git/pdf-terminal-sequence.json
```

Human route:

```text
docs/git/PDF_TERMINAL_SEQUENCE.md
```

Read the current active item from the machine file. Do not duplicate the mutable queue in this document. Only one queue item may be ACTIVE. Do not create a future terminal branch before activation.

Queue order is a process dependency. Git ancestry follows actual byte dependency.

## Git Town Stacked-PR Worker route

Canonical shared method path:

```text
skills/git-town-stacked-pr-worker/SKILL.md
```

Bettor owns repository configuration, branches, worktrees, leases, CI, publication, and receipts. Before Stack work, read the Git routes in the conditional table and verify the current shared binding rather than trusting a hard-coded historical SHA.

No `git town continue`, `skip`, `undo`, semantic conflict resolution, force push, merge, ship, promotion, or rollback occurs outside the admitted typed controller and exact-subject policy.

## Macro / Micro boundary

```text
Macro loop
  module composition, task/capability DAG, routing, admission, release

Micro loop
  one typed task, one leased workspace, bounded execution, artifacts, named exits
```

A handoff is valid only for a named capability mismatch, quota exhaustion, domain boundary, independent review requirement, or runtime unavailable in the current lane. Preserve typed results, artifact refs, Gate results, unresolved gaps, context digest, and Worker receipt. Do not persist private chain of thought.

## CLI, MCP, and passive context

`loopctl/contract.json` is the public CLI authority. MCP is default-deny and derives from the typed CLI contract and policy. Generic shell, arbitrary host paths, credentials, browser profiles, and mutable sessions are not public MCP tools.

`CONTEXT.md` carries current handoff; `ARCHITECTURE.md` carries stable placement; `DOMAIN_DECOUPLING.md` carries core/port/module/adapter laws; nearest READMEs carry local topology; machine contracts and receipts decide exact execution.

After passive-context changes, start a fresh Agent session before claiming the new route was loaded.

## Proof and anti-jitter

Every material change binds:

```text
exact subject and rollback
positive execution
independent control
hollow or planted mutation
complete denominator
cleanup/residue state
current evidence ceiling
```

Do not retry without a changed hypothesis or external state. A local task PASS cannot hide a failed global objective. Deterministic failure vetoes advisory or model success.

## Molecular Stack PR policy

One Worker owns one branch/worktree/path lease. Use:

```text
SIBLING      path-disjoint work
TRUE_CHILD   consumes named unmerged parent bytes
TERMINAL     one reviewable behavior and proof
CONVERGENCE  one owner for shared locks/indexes/release integration
```

Current topology authority is [`docs/git/stack-prs.index.json`](docs/git/stack-prs.index.json); the human route is [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md). Process order, issue numbers, and review chronology do not manufacture child ancestry.

## Completion contract

Before claiming completion, report:

```text
changed paths and owner
selected multi-hop routes
shared core versus consumer/domain impact
State Machine, DAG, data-flow, interface or authority change
exact base/head/tree and rollback
positive/control/mutation results
owning workflows executed, skipped, or not run
remaining ABSENT / NOT_IMPLEMENTED / NOT_EXERCISED / SKIPPED_BY_POLICY / HUMAN_ADMIT_REQUIRED
cleanup and residue state
```

Do not claim merge, promotion, capability unlock, provider recovery, origin equivalence, model uplift, production success, release, or rollback without immutable evidence from the owning lane.
