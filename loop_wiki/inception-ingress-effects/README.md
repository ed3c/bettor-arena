# Inception A6 — durable ingress, effect identity and restart reconciliation

Status: **PUBLIC RESTART + UNKNOWN_EFFECT RECONCILIATION CANDIDATE**
Upstream profile issue: `ed3c/enterprise_agent_system#18`
Owner issue: `ed3c/bettor-arena#193`

This leaf implements a bounded file-backed fixture for authenticated event admission, replay/dedupe identity, typed reversible `WriteIntent`, effect reservation, timeout-to-`UNKNOWN_EFFECT`, blind-retry refusal and exact remote-version readback before `COMMITTED`. P4 now kills the worker process after `UNKNOWN_EFFECT`, reopens the SQLite state in a fresh process and verifies reconciliation. It does not accept production credentials or perform a real external write.

## Implementation subjects

```text
effect_contract.py
test_effect_contract.py
reconciliation_worker.py
test_reconciliation_matrix.py
```

The public fixture uses SQLite WAL + `synchronous=FULL` and refuses `:memory:` as durable-ingress evidence. Event identity and effect identity remain separate across restart.

## State Machine

```text
EVENT_RECEIVED
→ AUTHENTICATED
→ REPLAY_CHECKED
→ INBOX_PERSISTED
→ TASK_ADMITTED
→ WRITE_INTENT_VALIDATED
→ EFFECT_RESERVED
→ EXTERNAL_EXECUTION_ATTEMPTED
→ REMOTE_READBACK_VERIFIED
→ COMMITTED | UNKNOWN_EFFECT | COMPENSATED | HUMAN_ESCALATED
```

## Restart reconciliation matrix

```text
persist authenticated event
→ reserve effect
→ ATTEMPTED
→ timeout after possible mutation
→ UNKNOWN_EFFECT committed
→ os._exit() without close
→ fresh SQLite process
→ state readback = UNKNOWN_EFFECT
→ blind retry = false
├─ stale remote version → refuse; remain UNKNOWN_EFFECT
└─ exact version + readback digest → COMMITTED
→ close / reopen
→ COMMITTED + idempotent event identity persist
```

The matrix also proves that event/effect identity collisions remain refused after restart. A local reversible test double is not a provider API/browser receipt.

## Contract laws

```text
signature_verified = true before durable inbox admission
event timestamp and evaluation clock are timezone-aware
replay window is explicit
duplicate event identity is idempotent
same event ID with different payload is a collision
effect ID binds operation digest + expected remote version + capability
public fixture requires reversible=true
timeout after possible mutation → UNKNOWN_EFFECT
UNKNOWN_EFFECT → blind retry forbidden
COMMITTED requires readback digest and exact expected remote version
```

These remain separate facts:

```text
HTTP 202
inbox persistence
task admission
effect reservation
external attempt
UNKNOWN_EFFECT
remote readback
COMMITTED
compensation
Human escalation
```

## Existing canonical mechanisms reused

| Existing path | Reusable responsibility | Boundary |
|---|---|---|
| `loop_wiki/loopx-ledger/` | append-only/CAS/idempotency vocabulary | no external-effect semantics |
| `loop_wiki/loopx-worker-gateway/` | typed Worker requests/receipts/cleanup | Worker cannot self-create PASS |
| `loop_wiki/loopx-kernel/` | task/Gate/Quota authority | contracts are not execution |
| `docs/git/AUTOMATED_ADMISSION.md` | guarded irreversible operations | missing intent fails closed |
| `loop_wiki/loopx-resource-gc/` | residue/protected-evidence handling | no silent destructive cleanup |

No second generic queue, reducer or production effect ledger is introduced.

## Writer lease

```text
loop_wiki/inception-ingress-effects/**
.arena/modules/inception-ingress-effects/**
data/inception-ingress-effects/**
.github/workflows/inception-a6-ingress-effects.yml
```

Production credentials, shared queues, provider sessions, root `loopctl`/MCP surfaces, release indexes and terminal queues remain forbidden.

## Next transition

`RUN_REVERSIBLE_COMPENSATION_FIXTURE_THEN_PROVIDER_ADAPTER_CANARY`

Compensation must receive its own receipt before any provider adapter or real effect is considered. This restart matrix does not imply compensation occurred.

## Evidence ceiling

```text
durable inbox/effect contract      DETERMINISTIC_PASS candidate
abrupt UNKNOWN_EFFECT restart       TARGETED_PUBLIC_CANARY
blind-retry persistence             TARGETED_PUBLIC_CANARY
local readback reconciliation       TARGETED_PUBLIC_CANARY
real external write                 NOT_PERFORMED
real remote reconciliation          NOT_EXERCISED
compensation                        NOT_EXERCISED
production credentials              ABSENT
Human admission / release           NOT_PERFORMED
```

Machine authority: [`preflight.json`](preflight.json).
