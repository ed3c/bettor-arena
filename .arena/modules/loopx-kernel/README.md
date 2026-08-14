# `loopx-kernel` module

`loopx-kernel` owns the strict, host-neutral task contract under [`../../../loop_wiki/loopx-kernel/`](../../../loop_wiki/loopx-kernel/). It provides `loopx.contracts/v1` and is intentionally not selected in the shared composition by this terminal leaf.

## Public control port

```sh
python3 loop_wiki/loopx-kernel/scripts/check_contracts.py
```

The port validates contract documents and the fixture bundle only. It does not create runtime state, dispatch an Agent, execute a gate, append a ledger event, advance a Todo, or perform Human Admit.

## State Machine and data flow

```text
Objective/Todos/Gates/Evidence/Quota contract
→ typed command proposal
→ Worker/Gate/Human event contract
→ append-only ledger contract boundary
→ reducer-owned snapshot contract
```

Issue `#62` owns this contract leaf. `#63` owns the future append-only ledger and deterministic reducer. Final selection, aggregate locks and release belong to the #61 convergence leaf.

## Evidence

```sh
python3 loop_wiki/loopx-kernel/scripts/check_contracts.py --selftest
python3 loop_wiki/loopx-kernel/scripts/control_contracts.py
```

The positive fixture, hollow fixture, and planted mutations are `FIXTURE_ONLY`; they do not establish live LoopX, host, provider, sandbox, HITL, memory, or production PASS.
