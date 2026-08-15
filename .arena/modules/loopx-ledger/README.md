# `loopx-ledger` module

`loopx-ledger` owns the append-only local task history and deterministic reducer under [`../../../loop_wiki/loopx-ledger/`](../../../loop_wiki/loopx-ledger/).

## Capabilities

```text
loopx.ledger/v1
loopx.reducer/v1
```

Required capability:

```text
loopx.contracts/v1
```

The module is a true child of issue #62/PR #74 and is intentionally not selected in the shared `bettor-arena` composition by this terminal leaf.

## Public control port

```sh
python3 loop_wiki/loopx-ledger/scripts/ledger.py <init|append|verify|replay|recover|selftest>
```

## State Machine

```text
immutable contract
→ single-writer lease
→ validate revision/hash chain/authority
→ append + fsync
→ deterministic replay
→ reducer-owned snapshot
→ operation receipt
```

## Boundaries

- Workers and Agents cannot write state or Gate verdicts.
- The snapshot is rebuildable and cannot outrank the ledger.
- Only partial final bytes may be removed by explicit torn-tail recovery.
- The current lease is POSIX-host-local; distributed consensus and cloud parity are not claimed.
- No MCP exposure, composition selection, live host/provider activation, Human Admit, promotion, or rollback occurs in this leaf.

## Evidence

```sh
sh loop_wiki/loopx-ledger/tests/run-all.sh
```

The tests include independent subprocess control, positive replay, hollow input, planted event/authority/transition mutations, Quota exhaustion, writer contention, and torn-tail recovery.
