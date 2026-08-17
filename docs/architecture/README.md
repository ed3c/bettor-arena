# Architecture documents

This directory contains repository-wide contracts and current-state ledgers. It is not a second implementation.

## Canonical documents

- [`PDF_HARNESS_INTEGRATION_AUDIT.md`](PDF_HARNESS_INTEGRATION_AUDIT.md) — attached 41-page Harness proposal mapped to exact current Bettor mechanisms, gaps and acceptance criteria.
- [`pdf-harness-integration.matrix.json`](pdf-harness-integration.matrix.json) — machine-readable integration matrix used by the offline gate.
- [`DIRECTORY_STATE_MACHINE_MAP.md`](DIRECTORY_STATE_MACHINE_MAP.md) — directory placement mapped to state-machine owner, input, output, transitions and automation boundary.
- [`modular-integration-requirements.md`](modular-integration-requirements.md) — normative modular-integration target.
- [`modular-integration-status.md`](modular-integration-status.md) — mutable current implementation ledger.
- [`STATE_MACHINES.md`](STATE_MACHINES.md) — current Macro/Micro/module/MCP/proof/project/origin machines and the missing LoopX target.
- [`DOCUMENT_ROUTING.md`](DOCUMENT_ROUTING.md) — standard root, owner, machine and evidence routes.
- [`agent-entrypoints.contract.json`](agent-entrypoints.contract.json) — required pointers and markers for `AGENTS.md` and `CLAUDE.md`.
- [`readme-coverage.contract.json`](readme-coverage.contract.json) — required human navigation surfaces.
- `agent-runtime-public-contract.json` — host-neutral runtime public contract when admitted.
- `context-materialization-contract.json` — Context Capsule/materialization contract when admitted.

## Source boundary

The PDF is `SOURCE_PROPOSAL_ONLY`. Its diagrams and examples cannot establish current implementation, live provider state, performance, security, license, cost or automated admission. The audit explicitly rejects raw shell strings, Worker-owned state, unscoped force-skip, checkpoint split-brain and private Thought Stream persistence.

## Validation

```sh
python3 scripts/gates/check_pdf_harness_integration.py
python3 scripts/gates/check_pdf_harness_integration.py --selftest
python3 scripts/gates/check_agent_docs.py
python3 scripts/gates/check_readme_coverage.py
python3 scripts/gates/check_module_catalog.py
```

The PDF gate also checks:

```text
desired module set == composition-lock module set
composition-lock module set == release-receipt module set
```

## Change discipline

A target document may describe planned mechanisms. A status document may only report mechanisms supported by current repository bytes and executable evidence. Adding a root-level placement requires updating `ARCHITECTURE.md` before the file lands. Closing a PDF gap requires updating the audit matrix, directory map, state machine, tests, Context Capsule and Stack index in the same terminal leaf.
