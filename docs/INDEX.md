# Bettor Arena documentation index

## Root routes

- [`../README.md`](../README.md) — role, PDF verdict, directory/State Machine map, data flow and Stack quick view.
- [`../AGENTS.md`](../AGENTS.md) — mandatory Agent procedure, Git Town route and completion contract.
- [`../CLAUDE.md`](../CLAUDE.md) — Claude Code thin projection.
- [`../CONTEXT.md`](../CONTEXT.md) — current handoff and glossary.
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — placement and engineering invariants.

## Architecture routes

- [`architecture/DOCUMENT_ROUTING.md`](architecture/DOCUMENT_ROUTING.md)
- [`architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](architecture/PDF_HARNESS_INTEGRATION_AUDIT.md)
- [`architecture/pdf-harness-integration.matrix.json`](architecture/pdf-harness-integration.matrix.json)
- [`architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md)
- [`architecture/pdf-loopx-harness.integration.json`](architecture/pdf-loopx-harness.integration.json)
- [`architecture/DIRECTORY_STATE_MACHINE_MAP.md`](architecture/DIRECTORY_STATE_MACHINE_MAP.md)
- [`architecture/STATE_MACHINES.md`](architecture/STATE_MACHINES.md)
- [`architecture/modular-integration-requirements.md`](architecture/modular-integration-requirements.md)
- [`architecture/modular-integration-status.md`](architecture/modular-integration-status.md)

## Git Town / Stacked-PR routes

- [`git/README.md`](git/README.md) — repository adoption boundary and State Machine.
- [`git/REPO_PROFILE.md`](git/REPO_PROFILE.md) — exact repository profile and admission states.
- [`git/STACKED_PRS.md`](git/STACKED_PRS.md) — current sibling/child/terminal/convergence graph.
- [`git/WORKER_PROTOCOL.md`](git/WORKER_PROTOCOL.md) — task packet and exclusive lease.
- [`git/GIT_TOWN_ADMISSION.md`](git/GIT_TOWN_ADMISSION.md) — executable/config/license/SBOM/legal/live canaries.
- [`git/stack-prs.index.schema.json`](git/stack-prs.index.schema.json) — machine contract.
- [`git/stack-prs.index.json`](git/stack-prs.index.json) — current snapshot.
- [`traceability/STACK_PR_INDEX.md`](traceability/STACK_PR_INDEX.md) — historical and current human traceability.

## Cross-repository and runtime routes

- [`integration/CROSS_REPO_INTEGRATION.md`](integration/CROSS_REPO_INTEGRATION.md)
- [`traceability/TRACEABILITY_INDEX.md`](traceability/TRACEABILITY_INDEX.md)
- [`agent-runtime-integration.md`](agent-runtime-integration.md)
- [`runtime-env-integration.md`](runtime-env-integration.md)
- [`knowledge-providers/README.md`](knowledge-providers/README.md)

## Machine/local-owner routes

- [`.arena/`](../.arena/README.md)
- [`.agents/`](../.agents/README.md)
- [`.runtime-env/`](../.runtime-env/README.md)
- [`.skill-bindings/`](../.skill-bindings/README.md)
- [`loopctl/`](../loopctl/README.md)
- [`proof_workflow/`](../proof_workflow/README.md)
- [`data/`](../data/README.md)

## Validation

```sh
python3 scripts/gates/check_git_town_stack_docs.py
python3 scripts/gates/check_git_town_stack_docs.py --selftest
python3 scripts/gates/check_pdf_harness_integration.py
python3 scripts/gates/check_pdf_loopx_harness_integration.py
python3 scripts/gates/check_agent_docs.py
python3 scripts/gates/check_readme_coverage.py
python3 scripts/gates/check_module_catalog.py
```

Nearest README and machine contract win over prose summaries. GitHub metadata is the current PR-state authority.
