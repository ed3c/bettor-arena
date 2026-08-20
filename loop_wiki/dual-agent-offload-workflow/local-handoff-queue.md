# Dual-Agent workflow Local Handoff Execution Queue

This queue begins after the deterministic workflow documentation convergence is admitted. It requires an authorized local/trusted runtime; GitHub fixtures cannot close its live states.

## Queue law

- Rebind current `main`, exact runtime contract set, workflow code, namespace/server/worker identity and rollback.
- Use one isolated worktree and one writer per path/authority lease.
- Preserve complete typed history, failed attempts, retries, timeout, cancellation, stale result, Human refusal, compensation failure and cleanup residue.
- Durable decision code remains history-only; external observations enter as typed events.
- Stop for Human/trusted authority on credentials, billing, live targets, external writes, destructive cleanup, merge, release or rollback.

## LH-W01 — Current-main deterministic readback

```text
fetch current main
→ bind exact workflow/runtime-contract subjects
→ run contract + reducer + operational leaves + complete matrix
→ run repository gates
→ record commit/tree, runtime versions and rollback
```

Required output: current-main deterministic receipt. Historical PR CI is retained evidence, not a substitute.

## LH-W02 — Durable-engine topology admission

Owner: parent #184 plus trusted runtime/operator.

Required inputs:

```text
engine/server/version and binary/image digest
namespace/task-queue identity
worker code/image/process identity
persistence/storage identity
TLS/identity/credential handles
retry/timer/cancellation/deadline configuration
retention and cleanup plan
safe non-production job
```

Stop if the server/namespace/worker, credentials, billing or cleanup authority is missing.

## LH-W03 — Durable start, timer and process restart

```text
submit exact job
→ ADMISSION_PENDING → ADMITTED
→ schedule typed timer/retry
→ terminate Worker process
→ restart Worker
→ replay immutable history
→ byte-identical decision state
```

Controls:

- reducer reads wall clock/random/network directly;
- history event inserted/deleted/reordered/tampered;
- wrong job/workflow/runtime subject;
- retry budget exceeded;
- untyped timer or lost parent attempt;
- process restart loses history or changes decision bytes.

## LH-W04 — Cancellation and deadline propagation

```text
RUNNING
→ CANCEL_REQUESTED → CANCELLING → CANCELLED

RUNNING
→ typed deadline observation
→ DEADLINE_EXPIRED
```

Verify activity cancellation acknowledgement, descendant cleanup and that no event is appended after terminal state.

## LH-W05 — Live Human wait and revalidation

```text
WAITING_FOR_HUMAN
→ process restart/replay
→ still WAITING_FOR_HUMAN
→ exact scoped Human decision
→ revalidate job/tenant/source/runtime/policy/evidence subjects
→ resume or typed refusal
```

Worker/model self-approval, stale approval, wrong tenant/job, missing evidence and fixture-as-live must fail closed.

## LH-W06 — Effect and compensation handoff

Workflow may emit only:

```text
EFFECT_ADMISSION_REQUEST
EFFECT_COMPENSATION_REQUEST
```

Bind exact effect identity, idempotency key, parent attempt/history and effect-owner subject. Real provider attempt/readback/commit/compensation remains the Effect plane; workflow must not self-commit.

## LH-W07 — Crash/retry/cleanup matrix

Exercise at least:

```text
ordinary completion
activity failure and retry
worker crash before/after activity observation
timeout / connection unknown
stale result
Human refusal
cancellation
deadline
compensation success/failure
cleanup failure
```

Record process/workspace/socket/lease/queue/storage cleanup independently from task outcome.

## LH-W08 — Workflow convergence packet

Produce:

```text
exact main commit/tree and rollback
engine/server/namespace/worker identities
runtime-contract and policy digests
complete ordered workflow history
replay result and finding digests
activity/provider request/observation refs
Human decision refs without secret/session values
effect/compensation request lineage
cleanup/residue inventory
all failures/blocks/skips
remaining NOT_EXERCISED states
operator/Human decisions
```

Update #184, #185 prerequisites, the program Stack index and `bettor-arena#186`. Close #184 only if its full durable/live acceptance criteria are actually satisfied.

## Completion packet

Every handoff must state:

```text
subject commit/tree
branch/worktree/writer lease
engine/runtime/provider versions
configuration and identity/policy digests
commands and observations
complete state-transition/attempt history
positive and disagreement-control results
artifacts/receipt digests
cleanup/residue
known limitations
NOT_EXERCISED / HUMAN_REQUIRED / NOT_PERFORMED
rollback
next owner and transition
```
