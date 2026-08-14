# LoopX Contract v1 — task-state authority boundary

Status: **contract and deterministic validation only**. This module does not yet implement the append-only ledger, reducer, Worker fleet, strategy graph, HITL runtime, memory writeback, cloud sandbox, trace backend, UI, release promotion, or a checked-in runtime `.loopx/state.json`.

The source architecture proposes a model-agnostic kernel around Objective, Todos, Gates, Evidence, and Quota. Bettor keeps that useful boundary while rejecting raw shell execution, Agent-owned state writes, unscoped force-skip, private Thought Stream persistence, and graph/UI/provider state as a second authority.

## Authority law

```text
strategy proposes a typed command
Worker executes in a leased workspace
Gate engine submits deterministic observations
LoopX reducer alone commits canonical task state
Human signs scoped decisions, promotion, and rollback
```

This leaf defines the packets on each arrow. Issue `#63` owns storage and reduction.

## Directory structure

```text
loop_wiki/loopx-kernel/
├── README.md
├── contracts/
│   ├── manifest.json
│   ├── task-state.schema.json
│   ├── gate-definition.schema.json
│   ├── command.schema.json
│   ├── event.schema.json
│   └── snapshot.schema.json
├── scripts/
│   ├── check_contracts.py
│   └── control_contracts.py
└── tests/
    ├── run-all.sh
    └── fixtures/
        ├── good/bundle.json
        ├── hollow/bundle.json
        └── mutations.json
```

The sibling module authority is `.arena/modules/loopx-kernel/module.json`.

## Contract State Machine

```text
TASK_DECLARED
→ TODO_READY
→ COMMAND_PROPOSED
→ COMMAND_ACCEPTED | COMMAND_REJECTED
→ WORKER_OBSERVED
→ GATES_OBSERVED
→ QUOTA_ACCOUNTED
→ RETRY | HITL_PENDING | TODO_COMPLETED
→ NEXT_TODO | TASK_COMPLETED | TASK_FAILED | CANCELLED
```

The schemas define legal identities and packet shapes. They do not themselves perform these transitions.

## Data flow

```text
immutable repository/task subject
+ Objective / Todos / Gate definitions / Quota
        ↓
strategy command proposal with expected state revision
        ↓
Worker result reference (observation only)
        ↓
Gate observation with evaluator and artifact digests
        ↓
append-only events (contract only in this leaf)
        ↓
reducer-owned snapshot bound to ledger head
```

### `task-state.schema.json`

Owns the reducer projection: exact subject, objective scope/non-goals, ordered Todos, gate references/results, content-addressed Evidence, Quota, lifecycle, state revision, and ledger-head digest.

### `gate-definition.schema.json`

Owns out-of-band validation requests. Commands are `executable + argv[]`; raw command strings, `shell`, arbitrary paths, secret-bearing environment values, and model-written verdicts are forbidden.

### `command.schema.json`

Owns intent proposals. Strategy, Agent, operator, or system actors can request bounded actions against an expected revision. They cannot set status, gate verdict, sequence, Human Admit, promotion, or rollback state directly.

### `event.schema.json`

Owns the append-only event shape reserved for issue `#63`: actor/authority class, monotonic sequence, previous digest, event digest, typed payload, exact subject, and bounded artifact references.

### `snapshot.schema.json`

Owns a rebuildable reducer projection. It binds state revision, ledger head, task-state digest, event count, and content digest. A graph checkpoint, UI cache, trace database, or memory store cannot replace it.

## Evidence and epistemic states

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

The checked positive bundle is explicitly `FIXTURE_ONLY`. Passing it proves contract and validator behavior, not a live LoopX engine or host execution.

## Verification

```sh
python3 loop_wiki/loopx-kernel/scripts/check_contracts.py
python3 loop_wiki/loopx-kernel/scripts/check_contracts.py --selftest
python3 loop_wiki/loopx-kernel/scripts/control_contracts.py
sh loop_wiki/loopx-kernel/tests/run-all.sh
```

Exit semantics:

```text
0   checked contract PASS
2   checked contract/control disagreement
64  invalid invocation, unreadable input, or missing dependency
```

The independent control executes the validator as a child process and observes positive `0`, checked-negative `2`, and input/invocation `64` paths without importing validator internals.

## Negative controls

The planted mutations cover raw shell, absolute `cwd`, Agent status write, Worker gate verdict, negative or falsely available Quota, completed Todo without critical gates, unsigned Human exception, sequence gap, inline/unbounded Evidence, graph checkpoint authority, promotion field, invalid transition, digest drift, unscoped `force_skip`, and private Thought Stream persistence.

## Runtime and Human boundaries

This module may be catalogued before it is selected in the `bettor-arena` composition. Catalog presence is not release inclusion. This terminal leaf does not expose MCP tools or update production state.

Human Admit remains required for merge, later module selection, public-surface changes, scoped exceptions, provider/host activation, durable memory, release promotion, and rollback.
