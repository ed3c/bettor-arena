# Dual-Agent Effect Ledger

Status: deterministic Effect Plane candidate under #185. The current subtree closes the contract/reducer/admission/provider-boundary/compensation **deterministic** denominator through PR #228. It does **not** prove a real external effect, live target readback, Human admission, merge, release, or production operation.

## Read route

```text
README.md
→ AGENTS.md
→ stack-index.json
→ effect_contract.py          DA-EF-C
→ effect_reducer.py           DA-EF-K
→ effect_policy_gate.py       DA-EF-P
→ effect_provider_adapter.py  DA-EF-A
→ effect_compensation.py      DA-EF-COMP
→ effect-matrix-preflight.json / test_effect_matrix.py  DA-EF-E
```

## Authority

```text
runtime-env effect-intent/v1
        ↓
Bettor workflow / PR #202
EFFECT_ADMISSION_REQUEST only
        ↓
Dual-Agent Effect Plane
canonical effect writer = dual-agent-effect-ledger
        ↓
provider/readback observation boundary
        ↓
commit proposal
        ↓
canonical effect writer alone may accept commit
```

`loopx-ledger` remains the sole canonical **task** writer. `dual-agent-effect-ledger` is the sole canonical **effect** writer. Worker, model, provider, browser/API adapter, transport ACK, workflow state, provider-native idempotency, fixture, or the PR #196 SQLite substrate cannot self-commit either authority.

PR #196 remains an immutable reference substrate only:

```text
commit c2613432736c65756ed13d871feb2df486c69118
tree   53680d47048f88b9402c6320355121b7ec2f7244
reuse  REFERENCE_SUBSTRATE_ONLY
writer NONE
```

Its durable `RESERVED → ATTEMPTED → UNKNOWN_EFFECT → readback → COMMITTED` fixture is reusable evidence, not a second canonical ledger.

## Directory → State Machine → owner

| Path | State-machine responsibility | Output authority |
|---|---|---|
| `effect_contract.py` | identity/state vocabulary and transition law | contract only |
| `effect_reducer.py` | ordered reservation/attempt/readback/commit replay | effect proposals/receipts only |
| `effect_policy_gate.py` | policy + Human + precondition admission | execution authorization packet |
| `effect_provider_adapter.py` | provider attempt/result/readback observations | observation + commit proposal only |
| `effect_compensation.py` | linked compensation effect identity/lineage | compensation proposal only |
| `test_effect_matrix.py` | complete deterministic denominator + disagreement controls | verification receipt only |
| `stack-index.json` | exact PR/commit/tree/CI routing | traceability only |

## Effect State Machine

```text
EFFECT_PROPOSED
→ INTENT_VALIDATED
→ POLICY_AND_APPROVAL_CHECKED
→ IDEMPOTENCY_RESERVED
→ PRECONDITION_REVALIDATED
→ EXECUTION_AUTHORIZED
→ EFFECT_ATTEMPTED
→ EFFECT_OBSERVED
→ EFFECT_COMMITTED
```

Alternatives remain distinct:

```text
READ_ONLY_NO_EFFECT
DUPLICATE_REFUSED
POLICY_REFUSED
APPROVAL_REQUIRED
PRECONDITION_STALE
ATTEMPT_FAILED
RESULT_UNKNOWN
→ RECONCILIATION_REQUIRED
COMPENSATION_REQUIRED
→ COMPENSATING
→ COMPENSATED | COMPENSATION_FAILED
```

Hard laws:

```text
RESULT_UNKNOWN != EFFECT_COMMITTED
provider success != EFFECT_COMMITTED
transport ACK != EFFECT_COMMITTED
workflow completed != EFFECT_COMMITTED
provider idempotency != canonical authority
fixture readback != live readback
```

A commit requires the canonical effect identity, complete attempt denominator, accepted policy/Human/precondition subject, and exact target readback/version/digest agreement.

## Process DAG

```text
runtime-env PR #69
wire effect-intent
        ↓
PR #202 DA-WF-K
workflow effect-admission request
        ↓
PR #216 DA-EF-C
contract / authority root
        ↓
PR #224 DA-EF-K
reservation + commit/reconciliation reducer
        ↓
PR #225 DA-EF-P
policy / Human / precondition gate
        ├─────────────────┐
        ▼                 ▼
PR #226 DA-EF-A      PR #227 DA-EF-COMP
provider/readback     linked compensation
        └─────────┬───────┘
                  ▼
PR #228 DA-EF-E
complete deterministic matrix
                  ↓
this docs convergence
                  ↓
#223 DA-EF-LIVE
real reversible provider effect + readback
                  ↓
#186 physical local→cloud→local canary
                  ↓
truth-verify-loop #22
                  ↓
#68 Human Admit / release / rollback
```

Actual Git ancestry follows byte dependency. Cross-repository dependencies are exact commit/tree/schema/digest edges, not Git parentage. PR #226 and PR #227 are sibling children of PR #225; PR #228 is based on PR #225 and byte-preserves their implementation/test blobs as convergence inputs.

## Data flow

```text
runtime effect-intent
+ workflow EFFECT_ADMISSION_REQUEST
+ tenant/project/effect/idempotency/request identity
+ exact source/workflow/task/attempt/provider subjects
        ↓
DA-EF-C contract validation
        ↓
DA-EF-K canonical reservation + ordered attempt denominator
        ↓
DA-EF-P policy/Human/precondition authorization
        ↓
DA-EF-A provider attempt observation
        ├─ FAILURE → ATTEMPT_FAILED
        ├─ TIMEOUT/CONNECTION_LOST → RESULT_UNKNOWN
        └─ SUCCESS → readback still required
                              ↓
                     exact target readback
                              ↓
                    EFFECT_COMMIT_PROPOSAL
                              ↓
              canonical effect writer decision

reversible committed parent
        ↓
DA-EF-COMP linked child effect
        ↓
its own admission + attempt + readback
        ↓
COMPENSATED | COMPENSATION_FAILED
```

## Deterministic denominator

PR #228 jointly exercises:

```text
exact duplicate
idempotency collision
cross-tenant collision
policy refusal
approval required
precondition stale
provider failure
timeout/connection unknown
RESULT_UNKNOWN
reconciliation
verified readback commit proposal
readback disagreement
compensation required
compensated
compensation failure
cleanup residue
```

Its matrix also refuses sibling blob drift, incomplete denominator, evidence laundering, provider-native idempotency as authority, provider self-commit, fixture-as-live promotion, mutable provider subjects, raw credentials, unresolved effect hidden by task completion, unresolved effect commit, double commit, and compensation audit deletion.

## Molecular Stack index

```text
PR #216  DA-EF-C
└─ PR #224  DA-EF-K
   └─ PR #225  DA-EF-P
      ├─ PR #226  DA-EF-A
      ├─ PR #227  DA-EF-COMP
      └─ PR #228  DA-EF-E convergence
           └─ #222 DA-EF-D docs convergence
```

See `stack-index.json` for exact heads/trees/run IDs. `skipped` workflows never count as PASS.

## Evidence boundary

Closed deterministically:

```text
identity/state contract
single effect-writer law
reservation/idempotency semantics
ordered attempt denominator
RESULT_UNKNOWN reconciliation law
policy/Human/precondition contract
provider/readback adapter contract
linked compensation contract
complete deterministic mutation matrix
```

Still outside this evidence ceiling:

```text
real credential resolution
real provider write
live target readback
provider-native idempotency behavior
live Human approval
live policy engine
exactly-once observable external effect
physical NATS / identity runtime
local→cloud→local user outcome
merge / release / rollback / production operation
```

Current evidence ceiling: `COMPLETE_DETERMINISTIC_EFFECT_MATRIX_ONLY`.

The next evidence transition is #223. It requires an explicitly safe reversible target plus trusted/Human authorization for credentials, provider enrollment, execution, readback, optional compensation, and cleanup. A GitHub fixture or Actions job cannot satisfy that live lane.
