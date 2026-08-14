# LoopX Ledger v1 — append-only task history and single-writer reducer

Status: **terminal implementation candidate for issue #63**. This module depends on the unmerged LoopX Contract v1 leaf (#62 / PR #74). It implements local POSIX append, replay, snapshot verification, idempotency, torn-tail recovery, and a deterministic reducer. It does not provide the six-host Worker Gateway, LangGraph strategy plane, HITL UI, decision-memory store, cloud sandbox, OpenTelemetry backend, composition selection, production promotion, or Human Admit.

The source architecture describes `Objective + Todos + Gates + Evidence + Quota` as persistent task state. This implementation changes the unsafe mutable-file example into an append-only authority:

```text
strategy/Agent/Human proposes typed input
Worker and Gate engines submit observations
        ↓
single POSIX writer validates exact subject + expected revision
        ↓
append canonical event + fsync
        ↓
deterministic reducer replays the full history
        ↓
rebuildable snapshot bound to ledger head
```

No Agent, Worker, Gate provider, graph checkpoint, memory projection, trace store, or UI can edit canonical task state directly.

## Directory structure

```text
loop_wiki/loopx-ledger/
├── README.md
├── contracts/
│   ├── manifest.json
│   ├── ledger-contract.schema.json
│   ├── store-manifest.schema.json
│   ├── append-request.schema.json
│   └── operation-receipt.schema.json
├── scripts/
│   ├── ledger_common.py
│   ├── ledger_contract.py
│   ├── ledger_reduce.py
│   ├── ledger_store.py
│   ├── ledger_engine.py
│   ├── ledger.py
│   ├── check_contracts.py
│   └── control_ledger.py
└── tests/
    ├── run-all.sh
    └── fixtures/
        ├── good/
        │   ├── contract.json
        │   ├── events/*.json
        │   └── expected-snapshot.json
        └── hollow/contract.json
```

Machine module authority: [`.arena/modules/loopx-ledger/module.json`](../../.arena/modules/loopx-ledger/module.json).

## Runtime store layout

Runtime state is generated outside Git-tracked module bytes:

```text
<store>/
├── contract.json      immutable task/gate/command/initial-state contract
├── store.json         exact subject, paths, writer policy and contract digest
├── events.jsonl       one canonical event per fsynced line
├── snapshot.json      reducer-owned, rebuildable cache
└── .writer.lock       POSIX `flock` writer lease
```

A consumer may place the store under a host-owned `.loopx/` runtime directory, but no checked-in `.loopx/state.json` becomes canonical authority.

## State Machine

```text
EMPTY
→ INITIALIZED (revision 0, empty ledger)
→ TASK_INITIALIZED
→ COMMAND_ACCEPTED | COMMAND_REJECTED
→ WORKER_OBSERVED
→ GATE_OBSERVED
→ QUOTA_DEBITED
→ RETRY | HITL_PENDING | TODO_COMPLETED
→ NEXT_TODO | TASK_COMPLETED | TASK_FAILED | CANCELLED
```

Reducer rules include:

- `TASK_INITIALIZED` is valid only at sequence `0` against a `READY` initial state.
- `COMMAND_ACCEPTED` dispatches only `READY` or `RETRY` Todos.
- `WORKER_OBSERVED` may attach artifacts and debit one attempt; it cannot submit a Gate verdict.
- `GATE_OBSERVED` accepts only deterministic observations with evaluator/artifact digests.
- `QUOTA_DEBITED` adds non-negative observed usage. Exhaustion deterministically moves the active task to `HITL_PENDING`.
- ordinary completion requires every critical Gate to be `PASS` and no exception reference.
- `COMPLETED_WITH_EXCEPTION` requires a signed, scoped Human decision recorded in history.
- every committed event increments `state_revision` and becomes `ledger_head_digest`.

## Hash chain and compare-and-swap

Each event carries:

```text
event_id
sequence
previous_event_digest
event_digest
exact repository / commit / tree / task subject
actor class + authority class
typed payload
```

`event_digest` is computed over canonical JSON excluding the digest field. Appends require:

```text
request.expected_state_revision == current snapshot revision
sequence == current event count
previous_event_digest == current ledger head
```

An identical repeated `event_id` and identical event bytes is `NOOP`; the same ID with different bytes is RED. Two processes cannot both acquire the non-blocking POSIX writer lease.

## Crash and recovery model

The append sequence is:

```text
validate and reduce in memory
→ append one JSONL line
→ fsync events file
→ atomically replace snapshot
```

A crash after event fsync but before snapshot replacement leaves a stale snapshot. `verify` and the next append perform full replay and reject the disagreement. A complete but invalid event is never silently removed.

Only a partial final JSONL line is classified as `TORN_TAIL`. Recovery is two-step:

```text
recover                  inspect only; emits FAIL and exit 2
recover --apply          truncate only the invalid tail, fsync, replay, rewrite snapshot
```

Committed historical events are not rewritten. The recovery receipt identifies the removed byte range and digest.

## CLI

```sh
python3 loop_wiki/loopx-ledger/scripts/ledger.py init \
  --contract task.json \
  --store runtime/.loopx/task-001 \
  --created-at 2026-08-14T00:00:00Z \
  --receipt artifacts/init.json \
  --operation-id init-task-001

python3 loop_wiki/loopx-ledger/scripts/ledger.py append \
  --store runtime/.loopx/task-001 \
  --request event-request.json \
  --receipt artifacts/append.json \
  --operation-id append-event-003

python3 loop_wiki/loopx-ledger/scripts/ledger.py verify \
  --store runtime/.loopx/task-001 \
  --receipt artifacts/verify.json \
  --operation-id verify-task-001

python3 loop_wiki/loopx-ledger/scripts/ledger.py replay \
  --store runtime/.loopx/task-001 \
  --snapshot-out artifacts/replayed-snapshot.json \
  --receipt artifacts/replay.json \
  --operation-id replay-task-001

python3 loop_wiki/loopx-ledger/scripts/ledger.py recover \
  --store runtime/.loopx/task-001 \
  --receipt artifacts/recovery-inspection.json \
  --operation-id inspect-task-001
```

Exit semantics:

```text
0   operation or checked NOOP/RECOVERED completed
2   contract, CAS, chain, authority, reducer, snapshot, writer, or torn-tail disagreement
64  invalid invocation, absent/unreadable input, or unsupported host prerequisite
```

## Evidence and controls

```sh
sh loop_wiki/loopx-ledger/tests/run-all.sh
```

The suite exercises:

- four strict local schemas and their content hashes;
- seven-event positive replay and checked expected snapshot;
- repeated replay byte identity;
- idempotent duplicate `NOOP` and ID collision rejection;
- stale expected revision;
- event deletion, reordering, digest, previous-digest, subject and sequence mutations;
- Worker authority violation and invalid transition;
- snapshot drift;
- Quota exhaustion and blocked completion;
- torn-tail inspect/recover/reverify;
- concurrent writer contention;
- hollow contract;
- independent subprocess control for `0 / 2 / 64`.

Fixtures prove the mechanism only. They do not prove a live Agent, physical network isolation, cloud parity, production storage durability, multi-host availability, or Human promotion.

## Platform ceiling

The current writer lease uses Python `fcntl.flock` and is therefore POSIX-only. It is appropriate for one host/local filesystem. Shared network filesystems, Windows, distributed writers, consensus, remote object stores, and database-backed leases remain `NOT_IMPLEMENTED` until separately designed and tested. The final runtime-fabric leaf (#66) owns provider and local/cloud behavior.

## Molecular boundary

This is a true child of #62 because it consumes the unmerged `loopx.contracts/v1` capability. It may be catalogued but is not selected in the root Bettor composition. Shared selection, `loopctl`/MCP exposure, aggregate locks, live canaries, release receipt, promotion, and rollback remain owned by convergence issue #68.

Merge remains a Human decision.
