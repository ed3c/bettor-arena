# Strategy/HITL current-main validation

## Role

This directory receives the bounded Stage-2 validation receipt for issue #110. The validation re-executes the `loopx-strategy-hitl` contracts and controls on one exact checkout after Stage 1 (#90 / PR #109).

It does not host canonical task state, a LangGraph checkpoint store, Human signer service, Web UI, model output or production recovery state.

## State Machine

```text
STAGE_1 RECEIPT PINNED
→ CURRENT MAIN + PR #106 MERGE PINNED
→ MODULE / CONTRACT / SCHEMA DIGESTS VERIFIED
→ POSITIVE PIPELINE
→ CONTROL + MUTATION + PROBE CONTROLS
→ CHECKPOINT / DECISION / EXCEPTION AUTHORITY CHECKS
→ COMPOSITION / LOOPCTL / MCP NON-ADMISSION
→ EXACT-SUBJECT RECEIPT
→ HUMAN REVIEW
```

## Data flow

```text
data/stage0-validation/stage1-receipt.json
+ PR #106 immutable implementation identities
+ .arena/modules/loopx-strategy-hitl/module.json
+ loop_wiki/loopx-strategy-hitl/contracts/manifest.json
+ current checkout source and fixtures
        ↓
scripts/gates/check_strategy_hitl_current.py
        ├─ verify
        ├─ independent control
        ├─ selftest / mutations
        ├─ per-control reason probe
        └─ non-admission checks
        ↓
content-addressed JSON receipt emitted to a caller-owned path
        ↓
exact-head GitHub check
        ↓
Human review
```

## Evidence boundary

A `PASS` from this Stage means:

- the checked current subject contains the Strategy/HITL mechanism;
- all five schema digests agree with the contract manifest;
- deterministic fixture and mutation/control commands returned zero;
- planner/checkpoint/decision/exception authority boundaries remain enforced;
- the module is not selected or publicly exposed.

It does **not** mean:

```text
real LangGraph backend             TESTED
real Human signer/authentication   IMPLEMENTED
production interrupt/resume        TESTED
Harness Console                    IMPLEMENTED
shared composition selected        YES
production release promoted        YES
```

Those states remain `NOT_IMPLEMENTED`, `NOT_EXERCISED` or `NOT_PERFORMED` until their own ordered terminal receipts exist.

## Public invocation

```sh
python3 scripts/gates/check_strategy_hitl_current.py \
  --observed-at <stable-label-or-time> \
  --output /tmp/stage2-strategy-hitl-receipt.json

python3 scripts/gates/check_strategy_hitl_current.py --selftest
python3 -m unittest -q tests/test_strategy_hitl_current.py
```

Exit semantics:

```text
0   checked PASS
2   checked invariant or command FAIL
64  invalid invocation or unreadable repository state
```

The receipt output path is caller-owned. It must not contain secrets, private reasoning or mutable provider state.
