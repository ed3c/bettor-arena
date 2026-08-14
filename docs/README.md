# bettor-arena documentation

This directory is the human navigation layer. It does not replace machine-readable contracts under `.arena/`, the public CLI contract under `loopctl/`, executable evidence under `data/`, or current GitHub metadata.

## Authority order

| Layer | Authority | Purpose |
|---|---|---|
| Engineering SSOT | [`../ARCHITECTURE.md`](../ARCHITECTURE.md) | placement and repository invariants |
| Agent entry | [`../AGENTS.md`](../AGENTS.md) / [`../CLAUDE.md`](../CLAUDE.md) | mandatory routing and completion contract |
| Bounded context | [`../CONTEXT.md`](../CONTEXT.md) | current handoff and glossary |
| PDF audit | [`architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](architecture/PDF_HARNESS_INTEGRATION_AUDIT.md) | source proposal versus current bytes |
| LoopX audit | [`architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md) | Objective/Todo/Gate/Evidence/Quota mapping |
| Directory/state map | [`architecture/DIRECTORY_STATE_MACHINE_MAP.md`](architecture/DIRECTORY_STATE_MACHINE_MAP.md) | owner, inputs, outputs and transitions |
| Normative target | [`architecture/modular-integration-requirements.md`](architecture/modular-integration-requirements.md) | target contract |
| Mutable status | [`architecture/modular-integration-status.md`](architecture/modular-integration-status.md) | landed versus unexercised |
| Git/Stack profile | [`git/README.md`](git/README.md) | repository-owned Git Town adoption and Stack policy |
| Stack history | [`traceability/STACK_PR_INDEX.md`](traceability/STACK_PR_INDEX.md) | issue/PR/head/check/reachability trace |
| Machine control plane | [`.arena/`](../.arena/) | manifests, requirements, locks and Context Capsules |
| Public runtime | [`loopctl/`](../loopctl/) | stable CLI/MCP surface |
| Proof semantics | [`proof_workflow/`](../proof_workflow/) | proof, control and mutation |
| Generated evidence | [`data/`](../data/) | snapshots and receipts |

Executable contracts and current receipts win when prose disagrees.

## PDF architecture routes

```text
PDF proposal
→ architecture/PDF_HARNESS_INTEGRATION_AUDIT.md
→ architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md
→ architecture/DIRECTORY_STATE_MACHINE_MAP.md
→ architecture/modular-integration-status.md
→ git/STACKED_PRS.md
→ traceability/STACK_PR_INDEX.md
→ machine contracts and exact receipts
```

Current conclusion:

```text
supporting modular Harness foundation   IMPLEMENTED
complete LoopX runtime on main          NOT_IMPLEMENTED
unmerged LoopX terminal candidates      OPEN STACK
live six-host/provider/cloud matrix     NOT_EXERCISED
Git Town executable/config              ABSENT
```

Validation:

```sh
python3 scripts/gates/check_pdf_harness_integration.py
python3 scripts/gates/check_pdf_harness_integration.py --selftest
python3 scripts/gates/check_pdf_loopx_harness_integration.py
python3 scripts/gates/check_git_town_stack_docs.py
python3 scripts/gates/check_git_town_stack_docs.py --selftest
```

## Documentation map

- [`INDEX.md`](INDEX.md) — standard routes.
- [`agents/README.md`](agents/README.md) — Agent domain and issue policy.
- [`architecture/README.md`](architecture/README.md) — architecture contracts and status.
- [`architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](architecture/PDF_HARNESS_INTEGRATION_AUDIT.md) — PDF verdict.
- [`architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md) — LoopX gap trace.
- [`architecture/DIRECTORY_STATE_MACHINE_MAP.md`](architecture/DIRECTORY_STATE_MACHINE_MAP.md) — directory State Machines.
- [`architecture/STATE_MACHINES.md`](architecture/STATE_MACHINES.md) — current and missing machines.
- [`git/README.md`](git/README.md) — Git Town adoption route.
- [`git/REPO_PROFILE.md`](git/REPO_PROFILE.md) — closed repository profile.
- [`git/STACKED_PRS.md`](git/STACKED_PRS.md) — current molecular graph.
- [`git/WORKER_PROTOCOL.md`](git/WORKER_PROTOCOL.md) — one Worker/worktree/branch/path lease.
- [`git/GIT_TOWN_ADMISSION.md`](git/GIT_TOWN_ADMISSION.md) — executable/config/license/SBOM/legal/live admission.
- [`git/stack-prs.index.json`](git/stack-prs.index.json) — machine Stack snapshot.
- [`traceability/TRACEABILITY_INDEX.md`](traceability/TRACEABILITY_INDEX.md) — source/decision/eval/receipt index.
- [`traceability/STACK_PR_INDEX.md`](traceability/STACK_PR_INDEX.md) — human Stack authority snapshot.
- [`agent-runtime-integration.md`](agent-runtime-integration.md) — Skills/runtime/host aggregate.
- [`runtime-env-integration.md`](runtime-env-integration.md) — runtime projection.
- [`knowledge-providers/README.md`](knowledge-providers/README.md) — provider boundaries.
- [`../.arena/modules/README.md`](../.arena/modules/README.md) — module catalog.

## Git Town shared-method route

Canonical procedure reference:

```text
ed3c/skills-shared@c5750720d960a228a0d9419f28125c09d064e3e1
skills/git-town-stacked-pr-worker/SKILL.md
blob eb2d915bca3e8a3938625f7d33a10fae95a15769
```

Bettor keeps no local same-name Skill. The repository-owned profile and Stack policy live under [`git/`](git/README.md).

Current state:

```text
shared method reference      PINNED
consumer binding selection   NOT_SELECTED
Git Town binary/config       ABSENT
live sync/publication        NOT_EXERCISED
Human Admit                  NOT_PERFORMED
```

## Repository-analysis route

```text
README.md
→ AGENTS.md or CLAUDE.md
→ ARCHITECTURE.md + CONTEXT.md
→ PDF audit / modular target / current status
→ directory State Machine map
→ docs/git profile and Stack graph when branch work is involved
→ nearest module README and machine contract
→ source/tests/receipts
→ exact issue / PR / head / checks
```

Missing context, branch edge, path lease, source subject or receipt remains `ABSENT`.

## Writing rules

1. Keep Agent entry documents routed; do not replace machine contracts with prose.
2. Put stable rules in normative contracts, current state in status/index documents and run facts in receipts.
3. Do not promote `NOT_EXERCISED`, `ABSENT`, `NOT_IMPLEMENTED` or source proposals to PASS.
4. Do not store absolute host paths, credentials, cookies, OAuth data, `.env` values or signed-in content.
5. Every admitted module needs a sibling README; `scripts/gates/check_readme_coverage.py` enforces this.
6. A configured provider, Skill reference or branch graph does not prove runtime health.
7. `MERGED_TO_PARENT` is not `MERGED_TO_MAIN`.
8. A duplicate active issue/path writer is blocking data, not parallel-safe progress.
9. Update both Stack indexes whenever base/head/state/check/reachability changes.
10. Merge, ship, conflict resolution, promotion and rollback remain Human-owned.
