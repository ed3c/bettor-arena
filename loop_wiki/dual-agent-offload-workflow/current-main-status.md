# Dual-Agent workflow current-main status

## Verdict

```text
WORKFLOW CONTRACT / REDUCER / OPERATIONAL MATRIX
MERGED_DETERMINISTIC

DURABLE ENGINE / CLOUD WORKER / LIVE HUMAN / PROVIDER
NOT_EXERCISED
```

## Admitted implementation

```text
PR #201  DA-WF-C
→ PR #202  DA-WF-K
   ├─ PR #209  DA-WF-R
   ├─ PR #210  DA-WF-H
   └─ PR #211  DA-WF-COMP
          ↓
       PR #215 DA-WF-E
```

PR #215 materialized and reverified the exact operational sibling bytes. PRs #209/#210/#211 are closed as absorbed rather than merged a second time.

## Completed issues

```text
#199  workflow contract
#200  deterministic reducer/replay
#203  retry/timer/restart/cancel/deadline
#204  Human wait/scoped decision/revalidation
#205  compensation request/cleanup lineage
#206  complete replay/mutation matrix
```

Issue #207 owns this current-main documentation convergence. Parent #184 remains open.

## What is merged

- typed workflow state vocabulary and transition legality;
- exact runtime-contract binding;
- ordered hash-chained history and byte-identical replay;
- retry/attempt lineage and typed timer observations;
- cancellation and deadline alternatives;
- durable Human-wait semantics and decision-subject revalidation;
- compensation request and cleanup-lineage semantics;
- complete deterministic convergence matrix;
- single LoopX task-writer and separate effect-writer laws.

## What is not exercised

```text
Temporal or another durable-engine server/namespace
real worker crash/failover/restart
physical transport/network
live local/cloud identity and credentials
live Human UI/session
provider/API/browser/sandbox execution
real external effect/readback/compensation
user-visible result
physical local→cloud→local canary #186
Human admission, release, rollback
```

## Evidence ceiling

`COMPLETE_DETERMINISTIC_WORKFLOW_REPLAY_MATRIX_ONLY`.

A green workflow matrix proves deterministic state/replay/refusal semantics on the admitted code. It does not prove service durability, provider correctness, user success, or production reliability.
