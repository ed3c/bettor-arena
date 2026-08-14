# `loopx-strategy-hitl` module

Machine authority: [`module.json`](module.json)

## Role

Owns a proposal-only strategy port, exact-subject Human interrupt/decision/resume
contracts, and a projection-only LangGraph checkpoint adapter.

## State machine

```text
CANONICAL_SNAPSHOT
→ STRATEGY_PROPOSAL
→ TRUSTED_VALIDATION
→ COMMAND_PROPOSAL
→ LOOPX_REDUCER

HITL_PENDING
→ INTERRUPT_PROJECTION
→ SIGNED_HUMAN_DECISION
→ SIGNATURE/SUBJECT/REVISION/EXPIRY/SCOPE CHECKS
→ RESUME_PLAN
→ REQUIRED_REVALIDATION
→ LOOPX_REDUCER
```

## Capability boundary

Provides:

- `loopx.strategy-port/v1`
- `loopx.hitl/v1`

Requires:

- `loopx.contracts/v1`
- `loopx.ledger/v1`
- `arena.proof-kernel/v1`

The module does not append to the ledger, write Gate verdicts, invoke Workers,
perform Human Admit, promote a release, rollback production or expose a generic
`force_skip`.

## Evidence

```sh
sh loop_wiki/loopx-strategy-hitl/tests/run-all.sh
```

Actual LangGraph package execution and production signature-provider integration
remain `NOT_EXERCISED`.
