# Inception A6 — durable ingress, effect identity and readback

Status: **FIRST PUBLIC IMPLEMENTATION CANDIDATE**  
Upstream profile issue: `ed3c/enterprise_agent_system#18`  
Owner issue: `ed3c/bettor-arena#193`

This leaf implements a bounded file-backed fixture for authenticated event admission, replay/dedupe identity, typed reversible `WriteIntent`, effect reservation, timeout-to-`UNKNOWN_EFFECT`, blind-retry refusal and exact remote-version readback before `COMMITTED`. It does not accept production credentials or perform a real external write.

## Implementation subjects

```text
effect_contract.py
test_effect_contract.py
```

The public fixture uses SQLite WAL + `synchronous=FULL` and refuses `:memory:` as durable-ingress evidence. It stores event identity separately from effect identity and retains state across close/reopen.

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

The current implementation covers the public deterministic path through `EFFECT_RESERVED`, a simulated `ATTEMPTED → UNKNOWN_EFFECT` timeout, and exact readback-to-`COMMITTED` against a reversible local fixture. It does not execute a provider API or browser effect.

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

Therefore these remain different facts:

```text
HTTP 202
inbox persistence
task admission
effect reservation
external attempt
remote readback
COMMITTED
```

## Existing canonical mechanisms reused

| Existing path | Reusable responsibility | Boundary |
|---|---|---|
| `loop_wiki/loopx-ledger/` | append-only/CAS/idempotency vocabulary | no external-effect semantics |
| `loop_wiki/loopx-worker-gateway/` | typed Worker requests/receipts/cleanup | Worker cannot self-create PASS |
| `loop_wiki/loopx-kernel/` | task/Gate/Quota authority | contracts are not execution |
| `docs/git/AUTOMATED_ADMISSION.md` | guarded irreversible operations | missing intent fails closed |
| `loop_wiki/loopx-resource-gc/` | residue/protected-evidence handling | no silent destructive cleanup |

No second generic queue, reducer or production effect ledger is introduced by this leaf.

## Writer lease

```text
loop_wiki/inception-ingress-effects/**
.arena/modules/inception-ingress-effects/**
data/inception-ingress-effects/**
.github/workflows/inception-a6-ingress-effects.yml
```

Production credentials, shared queues, provider sessions, root `loopctl`/MCP surfaces, release indexes and terminal queues remain forbidden.

## Next transition

`RUN_RESTART_UNKNOWN_EFFECT_RECONCILIATION_AND_CLEANUP_MATRIX`

The next atom must expand restart/fault injection around UNKNOWN_EFFECT reconciliation and terminal cleanup before any real provider adapter is considered.

## Evidence ceiling

```text
durable inbox/effect fixture  DETERMINISTIC_CANDIDATE
duplicate/collision controls  DETERMINISTIC_CANDIDATE
UNKNOWN_EFFECT refusal        DETERMINISTIC_CANDIDATE
close/reopen readback         DETERMINISTIC_CANDIDATE
real external write           NOT_PERFORMED
independent reconciliation    NOT_EXERCISED
production credentials        ABSENT
Human admission               NOT_PERFORMED
```

Machine authority: [`preflight.json`](preflight.json).
