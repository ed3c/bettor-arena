# LoopX Strategy + HITL v1

This module adds a proposal-only strategy port and a subject-bound Human-in-the-loop
interrupt/resume protocol. It does not make LangGraph, a checkpoint store, a Web UI,
a Worker, or a model a second state authority.

```text
canonical LoopX snapshot
→ strategy proposal
→ trusted validator
→ typed command proposal
→ Worker / Gate observations
→ LoopX reducer
→ retry | HITL_PENDING | terminal state
```

When a task reaches `HITL_PENDING`:

```text
interrupt projection
→ signed Human decision
→ signature-verification artifact
→ exact subject/revision/expiry/scope checks
→ resume plan
→ required revalidation
→ LoopX reducer commits the next event
```

## Authority law

```text
Strategy proposes
Worker executes
Gates observe
LoopX reducer commits
Human admits scoped exceptions, promotion, and rollback
```

Neither the strategy port nor this HITL coordinator appends to the canonical ledger.
They emit proposals and content-addressed decision artifacts for the Ledger/Reducer.

## Human decisions

Allowed decisions:

- `RETRY_AFTER_FIX`
- `UPDATE_CONTRACT`
- `CANCEL_TASK`
- `SCOPED_EXCEPTION`

There is no generic `force_skip`.

A scoped exception must include:

- exact repository/commit/tree/task subject;
- exact interrupt and expected state revision;
- non-empty Todo/Gate scope;
- a bounded rationale artifact;
- signer identity and role;
- detached-signature artifact and independent verification artifact;
- expiry;
- mandatory revalidation;
- an explicit `COMPLETED_WITH_EXCEPTION` consequence when completion is later admitted.

## LangGraph boundary

The optional adapter emits a rebuildable checkpoint projection:

```text
ledger-head digest
+ state digest
+ state revision
+ interrupt digest
+ graph thread ID
```

The checkpoint contains no canonical task state and cannot resume without a checked
Human decision. Actual LangGraph package execution remains `NOT_EXERCISED` in this
leaf.

## Public CLI

```sh
python3 scripts/hitl.py validate-proposal --snapshot <snapshot.json> --proposal <proposal.json>
python3 scripts/hitl.py interrupt --snapshot <snapshot.json> --request <interrupt-request.json> --output <fresh-dir>
python3 scripts/hitl.py decide --interrupt <interrupt.json> --decision <decision.json> --at <RFC3339>
python3 scripts/hitl.py resume --snapshot <snapshot.json> --interrupt <interrupt.json> --decision <decision.json> --at <RFC3339> --output <fresh-dir>
python3 scripts/hitl.py checkpoint --snapshot <snapshot.json> --interrupt <interrupt.json> --thread-id <id> --output <fresh-dir>
python3 scripts/hitl.py selftest
```

Exit codes:

```text
0   checked contract/proposal/decision/plan passed
2   checked policy, subject, revision, signature, expiry, scope or transition failed
64  malformed invocation, missing input, unreadable JSON or output collision
```

## Evidence

```sh
sh tests/run-all.sh
```

The suite includes positive retry/cancel/exception/checkpoint paths, one hollow
`force_skip`, and planted mutations for stale revision, wrong subject, unsigned
decision, expired exception, empty scope, bypassed revalidation, strategy state
write, graph checkpoint authority, Worker Human decision, private Thought Stream,
promotion, provider verdict, decision-ID collision and replay drift.

## Non-goals

- no merge or Human Admit;
- no production signing key;
- no live LangGraph package execution;
- no Worker execution;
- no Gate evaluation;
- no direct ledger append;
- no composition selection, MCP exposure, production promotion or rollback.
