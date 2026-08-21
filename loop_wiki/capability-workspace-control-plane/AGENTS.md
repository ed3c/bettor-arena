# AGENTS.md — Capability Workspace Control Plane

Read `README.md`, `contracts/upstream-binding.json`, the exact KAW W4 Issue/PR/head, and Bettor Issue #197 before modifying this module.

Hard rules:

1. KAW route acknowledgement is not Worker execution.
2. Worker execution is not a Gate verdict; a Gate verdict is not domain truth.
3. KAW cannot write LoopX state, Gate results, Human admission, durable memory, promotion, or rollback.
4. The exact KAW commit/tree/router blob and Bettor worker-gateway manifest/receipt-schema blobs are immutable inputs.
5. The public consumer admits only `orchestrate.work`, `ORCHESTRATE_WORK`, `ORCHESTRATOR/bettor-arena`, PUBLIC subjects, and `SOURCE_ONLY|TECHNICAL` ceilings.
6. Request IDs are transport identities. Semantic fingerprint conflicts fail closed.
7. The existing Worker Gateway remains fixture-only and `NOT_EXERCISED`; do not recolor it as live.
8. Provider credentials, Bettor deployment, Worker runtime, budget, merge, and release remain external/Human authority.
9. Every change requires positive, idempotent, semantic-conflict, authority, privacy, and evidence-laundering controls.
10. Do not edit shared root indexes, LoopX ledger/reducer, Worker Gateway contracts, or release files from this leaf.
