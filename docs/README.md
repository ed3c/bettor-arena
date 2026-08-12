# bettor-arena documentation

This directory is the human navigation layer. It does not replace the machine-readable contracts under `.arena/`, the public CLI contract under `loopctl/`, or executable evidence under `data/`.

## Authority order

| Layer | Authority | Purpose |
|---|---|---|
| Engineering SSOT | [`../ARCHITECTURE.md`](../ARCHITECTURE.md) | Placement, invariants and repository-wide engineering rules |
| Normative target | [`architecture/modular-integration-requirements.md`](architecture/modular-integration-requirements.md) | Complete modular-integration target contract |
| Mutable status | [`architecture/modular-integration-status.md`](architecture/modular-integration-status.md) | What has actually landed and what remains unexercised |
| Machine control plane | [`.arena/`](../.arena/) | Manifests, schemas, requirements, locks, policies and Context Capsules |
| Public runtime | [`loopctl/`](../loopctl/) | Stable CLI/MCP surface and wiring |
| Proof semantics | [`proof_workflow/`](../proof_workflow/) | Receipts, controls, negative controls and named exclusions |
| Generated evidence | [`data/`](../data/) | Checked-in snapshots and receipts; not hand-edited claims |

When prose and executable bytes disagree, the executable contract and its current gate/receipt win. The prose must then be corrected.

## Documentation map

- [`architecture/README.md`](architecture/README.md) — architecture contracts and status ledgers.
- [`adr/README.md`](adr/README.md) — admitted Architecture Decision Records.
- [`audits/README.md`](audits/README.md) — commit/branch-scoped review handoffs.
- [`plans/README.md`](plans/README.md) — dated execution plans and as-run ledgers.
- [`agent-runtime-integration.md`](agent-runtime-integration.md) — skills/runtime-env/host adapter integration.
- [`runtime-env-integration.md`](runtime-env-integration.md) — secret-free runtime projection and consumer verification.
- [`../.arena/modules/README.md`](../.arena/modules/README.md) — current module catalog for humans.
- [`../README.md`](../README.md) — repository entrypoint and quick verification.

## Writing rules

1. Keep `AGENTS.md` and `CLAUDE.md` thin; point to canonical documents instead of copying them.
2. Put stable rules in the normative contract, mutable completion state in the status ledger, and run-specific facts in receipts.
3. Do not describe `NOT_EXERCISED`, ABSENT or source proposals as PASS.
4. Do not put local absolute paths, credentials, cookies, OAuth material, `.env` values or browser profiles in documentation.
5. Every admitted module manifest needs a sibling `README.md`; `scripts/gates/check_readme_coverage.py` enforces this.
6. Per-run and digest directories inherit their parent README. Do not duplicate a README into every generated run directory.
