# Bettor Arena documentation index

## Root routes

- [`../README.md`](../README.md) — project role, current modular verdict, directory/State Machine/data flow and Stack.
- [`../AGENTS.md`](../AGENTS.md) — mandatory Agent procedure, LoopX PDF protocol and completion contract.
- [`../CLAUDE.md`](../CLAUDE.md) — Claude Code thin projection.
- [`../CONTEXT.md`](../CONTEXT.md) — bounded handoff/glossary.
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — stable placement and engineering invariants.

## Standard multi-hop routes

- [`architecture/DOCUMENT_ROUTING.md`](architecture/DOCUMENT_ROUTING.md) — route names and assertions.
- [`architecture/STATE_MACHINES.md`](architecture/STATE_MACHINES.md) — Macro/Micro/module/MCP/proof/provider/LoopX state machines.
- [`integration/CROSS_REPO_INTEGRATION.md`](integration/CROSS_REPO_INTEGRATION.md) — four-repository contract flow.
- [`traceability/TRACEABILITY_INDEX.md`](traceability/TRACEABILITY_INDEX.md) — source/decision/issue/PR/eval/receipt index.

## PDF architecture audits

- [`architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md) — 《LLM 泛化：模型權重與 Harness》, 41-page modular audit.
- [`architecture/pdf-loopx-harness.integration.json`](architecture/pdf-loopx-harness.integration.json) — executable requirement/owner/State Machine/data-flow/Stack contract.
- [`architecture/pdf-loopx-harness.integration.schema.json`](architecture/pdf-loopx-harness.integration.schema.json) — schema.
- [`architecture/PDF_SKILL_MCP_TRACEABILITY.md`](architecture/PDF_SKILL_MCP_TRACEABILITY.md) — separate SKILL.md + MCP PDF audit.

Verification:

```sh
python3 scripts/gates/check_pdf_loopx_harness_integration.py
python3 scripts/gates/check_pdf_loopx_harness_integration.py --selftest
```

## Canonical modular contracts

- [`architecture/modular-integration-requirements.md`](architecture/modular-integration-requirements.md) — complete target.
- [`architecture/modular-integration-status.md`](architecture/modular-integration-status.md) — implemented/unexercised status.
- [`agent-runtime-integration.md`](agent-runtime-integration.md) — Skill/runtime/host aggregate.
- [`runtime-env-integration.md`](runtime-env-integration.md) — runtime projection and consumer verification.

## Machine and local-owner routes

- [`.arena/`](../.arena/README.md) — module/composition/context/origin/browser control plane.
- [`.agents/`](../.agents/README.md) — Skill requirements, bindings and local projections.
- [`.runtime-env/`](../.runtime-env/README.md) — secret-free runtime consumer projection.
- [`.skill-bindings/`](../.skill-bindings/README.md) — consumer bindings.
- [`loopctl/`](../loopctl/README.md) — canonical CLI and stateless MCP.
- [`proof_workflow/`](../proof_workflow/README.md) — proof/control/mutation.
- [`knowledge-providers/`](knowledge-providers/README.md) — capability providers and proposal-only memory.
- [`data/`](../data/README.md) — generated snapshots and receipts.

The nearest README routes to machine authority. Prose never overrides manifests, contracts, scripts, tests, receipts or Git history.
