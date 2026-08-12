# Architecture documents

This directory contains repository-wide contracts. It is not a second implementation.

## Canonical documents

- [`modular-integration-requirements.md`](modular-integration-requirements.md) — normative target contract.
- [`modular-integration-status.md`](modular-integration-status.md) — current implementation ledger.
- [`agent-entrypoints.contract.json`](agent-entrypoints.contract.json) — required pointers and markers for `AGENTS.md` and `CLAUDE.md`.
- [`readme-coverage.contract.json`](readme-coverage.contract.json) — required human navigation surfaces.
- `agent-runtime-public-contract.json` — host-neutral agent runtime public contract when admitted.
- `context-materialization-contract.json` — Context Capsule/materialization contract when admitted.

## Change discipline

A target document may describe planned mechanisms. A status document may only report mechanisms supported by current repository bytes and executable evidence. Adding a new root-level placement requires updating `ARCHITECTURE.md` before the file lands.
