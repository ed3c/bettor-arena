# Bettor Arena documentation index

## Root routes

- [`../README.md`](../README.md) — project role, PDF-integration verdict, directory/state map and public entrypoints.
- [`../AGENTS.md`](../AGENTS.md) — mandatory Agent procedure, PDF verification and completion contract.
- [`../CLAUDE.md`](../CLAUDE.md) — Claude Code thin projection.
- [`../CONTEXT.md`](../CONTEXT.md) — current four-repository/PDF handoff and glossary.
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — stable placement and engineering invariants.

## Standard multi-hop routes

- [`architecture/DOCUMENT_ROUTING.md`](architecture/DOCUMENT_ROUTING.md) — route names and assertions.
- [`architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](architecture/PDF_HARNESS_INTEGRATION_AUDIT.md) — 41-page source proposal versus current Bettor mechanisms.
- [`architecture/pdf-harness-integration.matrix.json`](architecture/pdf-harness-integration.matrix.json) — machine-readable component states and evidence paths.
- [`architecture/DIRECTORY_STATE_MACHINE_MAP.md`](architecture/DIRECTORY_STATE_MACHINE_MAP.md) — directory owners, inputs, outputs, transitions and data flow.
- [`architecture/STATE_MACHINES.md`](architecture/STATE_MACHINES.md) — current state machines and missing LoopX target.
- [`architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md) — LoopX-specific requirement, authority and gap audit.
- [`architecture/pdf-loopx-harness.integration.json`](architecture/pdf-loopx-harness.integration.json) — executable LoopX audit contract.
- [`git/README.md`](git/README.md) — repository-owned Git Town adoption and Stack policy.
- [`git/REPO_PROFILE.md`](git/REPO_PROFILE.md) — observed repository shape the Stack policy is bound to.
- [`git/STACKED_PRS.md`](git/STACKED_PRS.md) — stacked-PR construction, retarget and land order.
- [`git/WORKER_PROTOCOL.md`](git/WORKER_PROTOCOL.md) — what a Worker session may and may not do to a Stack.
- [`git/GIT_TOWN_ADMISSION.md`](git/GIT_TOWN_ADMISSION.md) — admission state of the Git Town binary itself.
- [`git/stack-prs.index.json`](git/stack-prs.index.json) — machine-readable Stack topology, checked by `scripts/gates/check_git_town_stack_docs.py`.
- [`integration/CROSS_REPO_INTEGRATION.md`](integration/CROSS_REPO_INTEGRATION.md) — four-repository ownership and release flow.
- [`traceability/TRACEABILITY_INDEX.md`](traceability/TRACEABILITY_INDEX.md) — source/decision/issue/PR/eval/receipt index.
- [`traceability/STACK_PR_INDEX.md`](traceability/STACK_PR_INDEX.md) — molecular sibling/child/terminal/convergence topology.

## Canonical modular contracts

- [`architecture/modular-integration-requirements.md`](architecture/modular-integration-requirements.md) — complete target contract.
- [`architecture/modular-integration-status.md`](architecture/modular-integration-status.md) — current implemented/unexercised status.
- [`agent-runtime-integration.md`](agent-runtime-integration.md) — Skill/runtime/host adapter aggregate.
- [`runtime-env-integration.md`](runtime-env-integration.md) — runtime projection and consumer verification.

## Machine and local-owner routes

- [`.arena/`](../.arena/README.md) — module/composition/context/origin/browser control plane.
- [`.agents/`](../.agents/README.md) — Skill requirements, bindings, module set and local projections.
- [`.runtime-env/`](../.runtime-env/README.md) — secret-free runtime consumer projection.
- [`.skill-bindings/`](../.skill-bindings/README.md) — repo-owned domain bindings for shared procedures.
- [`loopctl/`](../loopctl/README.md) — canonical CLI and stateless MCP runtime.
- [`proof_workflow/`](../proof_workflow/README.md) — proof/control/mutation semantics.
- [`data/`](../data/README.md) — generated snapshots and receipts.

## Validation

```sh
python3 scripts/gates/check_pdf_harness_integration.py
python3 scripts/gates/check_pdf_harness_integration.py --selftest
python3 scripts/gates/check_agent_docs.py
python3 scripts/gates/check_readme_coverage.py
python3 scripts/gates/check_module_catalog.py
```

The nearest README routes to machine authority. Prose never overrides manifests, contracts, scripts, tests, receipts or Git history.
