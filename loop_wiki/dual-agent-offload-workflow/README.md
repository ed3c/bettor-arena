# Dual-Agent offload workflow — deterministic convergence

Status: **DA-WF-D documentation candidate for issue #207 under parent #184**.

This directory contains the deterministic workflow contract, history-only reducer, retry/timer/restart/cancel boundary, Human-wait boundary, compensation-request boundary, and complete replay matrix for the Dual-Agent local→cloud→local program. It does not create a second task-state authority and it does not prove a live durable-workflow engine.

## Read route

1. `AGENTS.md`
2. this `README.md`
3. `stack-index.json`
4. `preflight.json` and `matrix-preflight.json`
5. `workflow_contract.py`
6. `workflow_reducer.py`
7. `workflow_retry_restart.py`
8. `workflow_human_wait.py`
9. `workflow_compensation.py`
10. matching `test_workflow_*.py`
11. `loop_wiki/dual-agent-effect-ledger/README.md` and `AGENTS.md`
12. current GitHub PR and Actions state before any merge, close, admission, or handoff

The Stack index is a trace snapshot. GitHub current state remains the source for PR heads, review threads, checks, merge state, and branch movement.

## Authority map

```text
runtime-env/contracts/dual-agent
  exact offload and receipt wire contracts

this workflow subtree
  deterministic validation, replay, activity requests and proposals

loop_wiki/loopx-ledger
  only canonical task-state writer

loop_wiki/dual-agent-effect-ledger
  only canonical external-effect writer

agent-shield-monorepo
  provider, API/browser and sandbox observations

truth-verify-loop
  independent evidence/readback verification

Human / release system
  credentials, live target, production admission, merge/release/rollback
```

Workflow output remains `PROPOSAL_ONLY`. A write-class job may emit `EFFECT_ADMISSION_REQUEST`; it may not execute or commit the external effect.

## Exact upstream runtime contract

```text
repository   ed3c/runtime-env
contract PR  #69
source head  1fd6a65a2e628ba1b31e89800297e7202dadf126
source tree  cc287010c96391e0a718141c2f4afb92bac3db06
contract-set e6671977dbf0a378474f924a142a82843bc0e3429f4546ffb0145af73f7827fe
```

The runtime dependency is an immutable cross-repository process/evidence edge, not Git ancestry.

## Directory → State Machine → DAG owner

| Path | Responsibility | State transition / output | Canonical owner |
|---|---|---|---|
| `workflow_contract.py` | workflow, activity, terminal, authority and lane vocabulary | `SUBMITTED → contract-valid request` | workflow contract only |
| `workflow_reducer.py` | ordered hash-chained history replay | history → deterministic state + `PROPOSAL_ONLY` LoopX proposal | reducer; no canonical append |
| `workflow_retry_restart.py` | retry lineage, typed timer/deadline/cancel observations, fresh-process replay boundary | retry/cancel history → deterministic proposal | workflow boundary |
| `workflow_human_wait.py` | durable Human wait and exact approval/refusal binding | `WAITING_FOR_HUMAN → ADMITTED | POLICY_REFUSED` | external Human decision + workflow validation |
| `workflow_compensation.py` | compensation-request and cleanup lineage | committed reversible effect → `EFFECT_COMPENSATION_REQUEST` | effect ledger executes/commits |
| `test_workflow_matrix.py` | complete deterministic denominator and disagreement controls | exact sibling bytes → technical matrix verdict | evidence only |
| `stack-index.json` | exact subjects, CI receipts, authority and handoff | trace snapshot | #207; `canonical_write=NONE` |

Shared root composition, generated locks, release receipts, public MCP exposure, provider credentials, live namespace configuration, and production status remain outside this directory.

## Workflow State Machine

```text
SUBMITTED
→ ADMISSION_PENDING
→ ADMITTED
→ DELIVERY_PENDING
→ REMOTE_DISPATCHED
→ RUNNING
→ WAITING_FOR_RESULT | WAITING_FOR_HUMAN
→ VERIFYING
→ RECONCILING
→ COMPLETED
```

Typed alternatives remain distinct:

```text
RETRY_SCHEDULED
CANCEL_REQUESTED → CANCELLING → CANCELLED
DEADLINE_EXPIRED
POLICY_REFUSED
RUNTIME_ABSENT
ACTIVITY_FAILED
RESULT_STALE
RESULT_REFUSED
COMPENSATING → COMPENSATED | COMPENSATION_FAILED
FAILED_CLEANUP
FAILED
```

`WAITING_FOR_HUMAN` is not success. Refusal, timeout, cancellation, stale result, compensation failure, and cleanup failure cannot be recolored into `COMPLETED`.

## Process DAG

```text
runtime-env offload contracts
        ↓
DA-WF-C contract / PR #201
        ↓
DA-WF-K reducer / PR #202
        ├──────── DA-WF-R / PR #209
        ├──────── DA-WF-H / PR #210
        └──────── DA-WF-COMP / PR #211
                         ↓
DA-WF-E complete matrix / PR #232
                         ↓
DA-WF-D docs and handoff / #207
        ↓
Dual-Agent Effect Plane / #185
        ↓
provider / transport / identity live lanes
        ↓
physical canary / #186
        ↓
truth-verify-loop #22
        ↓
Human release / #68
```

Process dependencies do not manufacture Git ancestry.

## Git Stack and merge chain

```text
PR #201  DA-WF-C
└─ PR #202  DA-WF-K
   ├─ PR #209  DA-WF-R          absorbed by workflow convergence
   ├─ PR #210  DA-WF-H          absorbed by workflow convergence
   ├─ PR #211  DA-WF-COMP       absorbed by workflow convergence
   ├─ PR #216→#224→#225→#228→#229
   │  complete deterministic Effect Plane merged into #202
   └─ PR #232  DA-WF-E v2
      exact #209/#210/#211 bytes restacked on the effect-integrated parent
         └─ #207 documentation child
```

A true child consumes named unmerged parent bytes. Path-disjoint leaves are siblings. A convergence PR may materialize exact sibling Git blobs and must rerun the complete denominator. Absorbed leaves are closed without a second merge after byte identity and convergence tests are admitted.

## Deterministic data flow

```text
exact runtime offload packet
+ source/runtime/policy/tool/image/contract-set subjects
        ↓
workflow contract validation
        ↓
ordered typed history and activity observations
        ↓
history-only deterministic reducer
        ↓
retry/timer/cancel/Human/compensation boundary validation
        ↓
PROPOSAL_ONLY task-state proposal
        ↓
LoopX canonical task writer

write-class request
        ↓
EFFECT_ADMISSION_REQUEST
        ↓
dual-agent-effect-ledger
        ↓
policy/Human/precondition → provider attempt → target readback
```

Time, randomness, transport state, provider output, and Human decisions enter only as typed history/activity observations. The reducer performs no network, provider, shell, credential, or canonical-ledger I/O.

## Complete deterministic denominator

The exact workflow matrix covers:

```text
ordinary completion
retry
typed timer
deadline
fresh-process byte-identical replay
Human wait
Human resume
Human refusal
cancellation
stale result
activity failure
effect-admission request only
compensation
compensation failure
cleanup failure
```

It refuses sibling-byte drift, cross-subject history, missing attempts, non-byte-identical replay, direct LoopX append, direct provider effect execution, terminal-state laundering, runtime-contract drift, secret/private-reasoning persistence, and evidence-lane substitution.

## Evidence non-substitution laws

```text
transport ACK              != workflow/task/effect/user success
workflow COMPLETED         != effect commit
provider observation       != user-visible result
Human fixture              != live Human decision
fresh-process replay       != Temporal/cloud failover
package/provider presence  != provider execution
technical matrix PASS      != physical local→cloud→local PASS
CI PASS                    != merge, Human admission, or release
```

## Current exact deterministic candidate

```text
workflow contract PR #201
  56cb74650bda20adfe84cc522977419158437f53
  tree 3b2f1a351296f87f6570a182b2d72b46be181bac
  run  32263925774 PASS

workflow reducer original PR #202 subject
  7821e81f15d64ff3119d9bdb9278fc725e5aa398
  tree 60d486041b36608d5d03e33b2eb8944c9899b50b
  run  32264598907 PASS

workflow matrix v2 PR #232
  bf99eacaa848683a89d327e4c7899a452f2bbd99
  tree bdfd5080e8c4b2b0a3e84e4fc2d59d4bfc73c8b3
  run  32343897103 PASS

current PR #202 branch after Effect Plane + matrix convergence
  602134eb5f04b62776b7c1a787d6d8366e9f31af
  tree bdfd5080e8c4b2b0a3e84e4fc2d59d4bfc73c8b3
  workflow contract 32344035512 PASS
  workflow replay   32344035413 PASS
  workflow matrix   32344035463 PASS
  effect matrix     32344035489 PASS
  effect docs       32344035415 PASS
```

These are deterministic candidate receipts until the Stack is admitted to current `main`.

## Local Handoff Execution Queue

### `LH-WF-001` — durable workflow engine / issue #184

State: `HANDOFF_READY_NOT_EXERCISED`.

Required trusted execution:

1. pin the admitted workflow code, runtime contract set, namespace/queue and engine/provider identity;
2. submit one exact job and retain complete workflow/activity/attempt history;
3. kill and restart the Worker during retry, timer, and `WAITING_FOR_HUMAN` cases;
4. exercise cancellation and deadline propagation to transport/runtime adapters;
5. revalidate moved source/runtime/policy subjects before reconciliation;
6. route writes only through the admitted Effect Plane;
7. prove cleanup/residue for workers, leases, timers, queues, sockets, workspaces, and temporary artifacts;
8. emit content-addressed receipts for independent verification by `truth-verify-loop#22`.

Idempotency: retries and restarts preserve one logical workflow/job identity and the complete attempt denominator.

Timeout: timeout/deadline/cancellation remain typed terminal or nonterminal observations; none becomes `COMPLETED`.

Rollback: retain the exact pre-admission workflow subject and disable the disposable namespace/worker route without rewriting history.

## Evidence ceiling

Current ceiling:

```text
COMPLETE_DETERMINISTIC_WORKFLOW_AND_EFFECT_SUBTREE_ONLY
```

Not exercised here:

```text
Temporal or another live durable-workflow engine
physical transport partition/reconnect
live local/cloud identity
real provider/API/browser/gVisor execution
external effect and readback
live Human session
user-visible result
production HA
release and rollback
```
