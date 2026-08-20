# Dual-Agent workflow Agent instructions

These instructions scope `loop_wiki/dual-agent-offload-workflow/**`. Repository-root `AGENTS.md` and the canonical LoopX/Effect contracts remain authoritative for their own planes.

## Required read order

1. this `AGENTS.md`
2. `README.md`
3. `stack-index.json`
4. `preflight.json`
5. `matrix-preflight.json`
6. `workflow_contract.py`
7. `workflow_reducer.py`
8. the boundary module owned by the current task
9. matching tests
10. `loop_wiki/loopx-ledger/` authority docs
11. `loop_wiki/dual-agent-effect-ledger/README.md` and `AGENTS.md`
12. current GitHub base/head/check/review state

Never rely on an old PR body or a checked-in Stack index without rereading current GitHub state.

## Authority map

```text
runtime-env
  offload/runtime wire contracts

Dual-Agent workflow subtree
  validation, deterministic reduction, activity request and proposal only

LoopX ledger/reducer
  sole canonical task-state writer

Dual-Agent Effect Ledger
  sole canonical effect writer

Agent Shield
  provider/API/browser/sandbox observations only

Truth Verify Loop
  independent evidence/readback verification

Human/trusted system
  credentials, live target/provider, production admission, merge/release/rollback
```

This subtree has `canonical_write=NONE`. It cannot append canonical LoopX task state, commit an effect, approve a Human gate, execute a provider, or release.

## Path leases

### DA-WF-C / issue #199

Owns contract vocabulary, exact upstream binding, contract tests, and targeted workflow only.

### DA-WF-K / issue #200

Owns the history-only reducer, replay bytes, reducer tests, and replay workflow.

### DA-WF-R / issue #203

Owns retry/timer/restart/cancel boundary and its tests. It does not own Human, compensation, shared docs, or canonical state.

### DA-WF-H / issue #204

Owns Human-wait/approval/refusal validation and its tests. It never creates a live Human decision.

### DA-WF-COMP / issue #205

Owns compensation-request and cleanup lineage. It emits `EFFECT_COMPENSATION_REQUEST`; it does not call a provider or commit an effect.

### DA-WF-E / issue #206

Owns exact sibling materialization, convergence preflight, complete denominator, matrix tests, and matrix workflow. It must not silently rewrite sibling semantics.

### DA-WF-D / issue #207

Sole shared documentation/trace owner for this subtree: README, AGENTS, Stack index, docs tests/workflow, and consumer handoff. It does not own workflow implementation logic.

## Git Stack law

A true child consumes named unmerged parent bytes.

- Path-disjoint implementation leaves are siblings.
- A Process DAG edge is not automatically Git ancestry.
- Cross-repository dependencies are commit/tree/schema/digest bindings, never fake Git parents.
- A convergence branch may materialize exact sibling Git blobs and must rerun the complete denominator.
- Absorbed sibling PRs close without a second merge after byte identity, matrix coverage, and target-branch admission are verified.
- Current-main movement requires restack and exact-head checks; old green checks do not transfer.
- `mergeable=true` is not implementation, live, Human, or release evidence.

## Workflow State Machine laws

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

Keep these branches distinct:

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

Never use a catch-all transition to recolor refusal, timeout, cancellation, stale result, compensation failure, or cleanup failure as completion.

## Determinism laws

Workflow decisions read ordered typed history only. Direct use of wall clock, randomness, network, provider SDK, shell/process execution, credential values, or mutable global state in the reducer is forbidden.

External observations must enter as typed events or activity receipts with exact job/workflow/attempt and producer subjects. Exact history plus exact code/contract subject must produce byte-identical replay output.

## Evidence non-substitution laws

```text
transport ACK                 != workflow/task/effect/user success
workflow COMPLETED            != effect commit
provider SUCCESS              != effect commit
provider observation          != user-visible result
Human fixture                 != live Human approval
fresh-process replay          != durable-engine failover
runtime/provider package      != live execution
technical matrix PASS         != physical E2E PASS
CI PASS                       != merge/release
skipped workflow              != PASS
```

`WAITING_FOR_HUMAN` is not success. `RESULT_UNKNOWN`, timeout, connection loss, retries, failed attempts, cancellation, compensation failure, and cleanup residue remain in the denominator.

## Task and Effect writer separation

```text
workflow output
  PROPOSAL_ONLY

LoopX
  canonical task writer

workflow write request
  EFFECT_ADMISSION_REQUEST

Dual-Agent Effect Ledger
  canonical effect writer
```

Never let workflow state, provider response, provider-native idempotency, or transport ACK write canonical effect state. Compensation is a new linked effect, not history deletion or rewrite.

## Sensitive-data boundary

Do not persist raw credentials, cookies, tokens, browser profiles/storage state, session bytes, private reasoning, chain-of-thought, operator home paths, or provider-private filesystem paths in workflow history or docs. Persist only admitted opaque references, exact public/evidence-safe subjects, and digests.

## Current deterministic frontier

```text
PR #201 DA-WF-C  deterministic contract PASS
PR #202 DA-WF-K  deterministic reducer and integrated Effect subtree candidate
PR #209 DA-WF-R  exact bytes absorbed by PR #232
PR #210 DA-WF-H  exact bytes absorbed by PR #232
PR #211 DA-WF-COMP exact bytes absorbed by PR #232
PR #232 DA-WF-E v2 complete workflow matrix PASS
issue #207 DA-WF-D docs/trace convergence
```

Rebind all heads, trees, runs, and review threads before acting.

## Shadow stop conditions

Stop and create or update Local Handoff rather than self-promote when the next transition requires:

- live Temporal or another durable-workflow engine;
- physical transport partition/reconnect;
- live workload identity, credential, policy, revocation, or rotation;
- provider/API/browser/gVisor execution;
- external effect or target readback;
- live Human approval;
- user-visible result verification;
- production HA, merge to protected main, release, or rollback.

Use `NOT_EXERCISED`, `HUMAN_REQUIRED`, `UNVERIFIABLE`, or `NOT_PERFORMED` as appropriate. Do not self-approve.

## Local Handoff — `LH-WF-001` / #184

Trusted executor requirements:

1. reread current main, #184, runtime-env #73/#83, Agent Shield live issues, effect #223, physical #186, truth #22, and release #68;
2. pin exact workflow code/tree, contract set, namespace/queue, Worker build, provider and policy subjects;
3. use a disposable non-production environment and authorized opaque credential handles only;
4. exercise restart during retry, timer and Human wait;
5. exercise cancellation/deadline propagation and stale subject refusal;
6. route every write through the Effect Plane;
7. retain complete attempts, observations, cleanup and residue receipts;
8. submit the resulting bundle to independent verification;
9. leave release/Human state external.

Completion packet:

```text
exact base/head/tree and rollback
workflow/namespace/queue/Worker identities
job/workflow/activity/attempt graph
complete ordered history and replay digest
retry/timer/Human/cancel/deadline receipts
effect request and disposition
cleanup/residue inventory
all failed/blocked/skipped attempts
remaining NOT_EXERCISED lanes
independent verifier result
Human decision
```
