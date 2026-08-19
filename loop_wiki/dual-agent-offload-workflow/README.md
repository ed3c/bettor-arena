# Dual-Agent offload workflow — deterministic contract root

Status: **DA-WF-C candidate for #199 / parent #184**.

This directory defines the provider-neutral workflow contract for Dual-Agent offload. It does not create a second task-state store: `loop_wiki/loopx-ledger/` remains the canonical single writer. This leaf validates exact subjects, workflow/activity vocabulary, bounded retry/deadline inputs, evidence lanes and effect-routing law; it performs no network/provider call and no external effect.

## Exact upstream runtime contract

```text
repo         ed3c/runtime-env
PR           #69
commit       1fd6a65a2e628ba1b31e89800297e7202dadf126
tree         cc287010c96391e0a718141c2f4afb92bac3db06
contract-set e6671977dbf0a378474f924a142a82843bc0e3429f4546ffb0145af73f7827fe
offload $id  https://runtime-env.invalid/contracts/dual-agent/offload-job.v1.schema.json
```

The cross-repository edge is an immutable process/evidence binding, not Git ancestry.

## Directory ownership

```text
loop_wiki/dual-agent-offload-workflow/
├── README.md
├── workflow_contract.py
├── test_workflow_contract.py
└── preflight.json
```

Shared `.arena/modules`, compositions, locks, root status, MCP, release receipts and public indexes remain convergence-owned.

## State Machine

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

Terminal/refusal states cannot be recolored into `COMPLETED`. `WAITING_FOR_HUMAN` is not success.

## Authority and data flow

```text
runtime-env offload packet + exact contract-set digest
        ↓
DA-WF-C validate subject / bounds / lane separation
        ↓
typed workflow history + activity requests
        ↓
DA-WF-K deterministic reducer/replay (#200)
        ↓
PROPOSAL_ONLY LoopX event proposal
        ↓
LoopX ledger/reducer (only canonical task writer)
```

For write-class jobs the workflow can only emit an effect-admission request for #185. It cannot execute or commit the external effect itself.

## Determinism boundary

Workflow decisions accept only ordered history. Wall-clock time, randomness, network state and provider output must arrive as typed activity/history observations. Provider identity or health cannot become workflow/task/Gate truth.

## Evidence lanes

The contract receipt keeps workflow, transport, provider, effect, Gate, task, user-outcome and release evidence independent. This leaf can prove `DETERMINISTIC_WORKFLOW_CONTRACT_ONLY`; it cannot prove Temporal/durable-engine execution, process restart, physical transport, provider isolation, external effects, Human wait, user outcome, merge or release.

## Test

```sh
python3 loop_wiki/dual-agent-offload-workflow/test_workflow_contract.py
```
