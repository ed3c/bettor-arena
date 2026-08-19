# Dual-Agent Effect Ledger — DA-EF-C

Status: deterministic effect-contract/interface candidate for issue #208. This directory does **not** perform an external write and is not selected into release composition.

## Authority

```text
Dual-Agent workflow / PR #202
  emits EFFECT_ADMISSION_REQUEST only
        ↓
this contract
  validates effect identity / policy / precondition / readback law
        ↓
canonical effect writer = dual-agent-effect-ledger
        ↓
provider adapter / target readback
  NOT_EXERCISED in DA-EF-C
```

`loopx-ledger` remains the sole canonical **task** writer. `dual-agent-effect-ledger` is the declared canonical **effect** writer. A Worker, provider, model, browser/API adapter, transport ACK, workflow state, fixture, or PR #196 SQLite substrate cannot self-commit either authority.

## Exact inputs

```text
workflow reducer / PR #202
commit 7821e81f15d64ff3119d9bdb9278fc725e5aa398
tree   60d486041b36608d5d03e33b2eb8944c9899b50b
blob   12f1048d5abf4fbfd8970815bc46bfdc797cb3d8

runtime-env / PR #69
commit 1fd6a65a2e628ba1b31e89800297e7202dadf126
tree   cc287010c96391e0a718141c2f4afb92bac3db06
contract-set e6671977dbf0a378474f924a142a82843bc0e3429f4546ffb0145af73f7827fe
effect-intent blob 7a50a125e77dc4daa9c4721fce0fa2fc9b37fc3b

PR #196 durability/readback substrate reference
commit c2613432736c65756ed13d871feb2df486c69118
tree   53680d47048f88b9402c6320355121b7ec2f7244
effect_contract.py blob fedd4e6a7ee18438c122995be96694c8d26cf242
reconciliation_worker.py blob 7884038ee68a3eee08324b41c338c6001b8518a7
reuse mode REFERENCE_SUBSTRATE_ONLY
writer authority NONE
```

The PR #196 SQLite fixture demonstrates useful durable `RESERVED → ATTEMPTED → UNKNOWN_EFFECT → readback → COMMITTED` mechanics, but its own contract explicitly says it is not a production queue or remote-effect authority. DA-EF-C therefore binds it as exact reference/substrate evidence only; this directory does not import it.

## Effect identity

One effect admission request binds at least:

```text
tenant + project + logical operation
effect_id + idempotency_key + normalized request digest
exact source + workflow + task + attempt identity
exact provider subject + resource + action
policy digest + approval receipt
precondition digest + expected remote version
expected evidence class = TARGET_READBACK
compensation contract
runtime contract-set digest
```

An exact duplicate is refused without re-execution. The same idempotency/effect identity with different request bytes is an identity collision. Cross-tenant reuse is refused.

## State Machine

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

`RESULT_UNKNOWN` cannot become `EFFECT_COMMITTED` without reconciliation and target readback. Provider-native idempotency is useful transport/provider behavior but is not canonical ledger authority.

## Data flow

```text
runtime effect-intent
+ workflow EFFECT_ADMISSION_REQUEST
+ exact source/task/attempt/provider subjects
+ policy/approval/precondition bindings
        ↓
validate identity and authority
        ↓
reserve one canonical logical effect
        ↓
provider attempt (outside DA-EF-C)
        ├─ known failure → ATTEMPT_FAILED
        ├─ unknown/timeout → RESULT_UNKNOWN → readback/reconcile
        └─ observation → target readback
                              ↓
                    EFFECT_COMMITTED only after agreement
```

## Evidence boundary

This atom can prove deterministic contract shape, identity collision refusal, authority separation, state-transition law, and readback-gated commit semantics for fixtures.

It does **not** prove a real provider write, provider-native idempotency behavior, target readback, exactly-once observable effect, compensation execution, user outcome, Human approval, merge, release, or rollback.

Evidence ceiling: `DETERMINISTIC_EFFECT_CONTRACT_INTERFACE_ONLY`.
