# Inception A6 — durable ingress, effect ledger and writeback preflight

Status: **OWNER IMPLEMENTATION PREPARATION ONLY**  
Upstream profile issue: `ed3c/enterprise_agent_system#18`  
Owner issue: `ed3c/bettor-arena#193`

This leaf prepares the canonical route from provider-authenticated events to a
durable inbox, task admission, typed `WriteIntent`, effect reservation,
least-privilege execution, remote readback, unknown-effect reconciliation,
compensation and Human escalation. Preparation uses reversible test doubles only.

## Exact preparation subject

```text
repository        ed3c/bettor-arena
base commit       6bf8f7966c02b49294e22b329a6fce68fa50a815
base tree         05bc4982db6ea8a1609e4b5cc374a3db6a125da2
branch            agent/inception-a6-ingress-effects
controller commit 6e0a916fd06dd8635d77c9a8c4d1b475185ea13e
controller tree   c3851a6953d456d0342a9776eed28561c1af0ca1
packet digest     sha256:c464b74f13ca211e15f07d90b3d3e50a0298ac5aa178e69197390166a5bc98da
packet bundle     sha256:dc4473b3195a738e55eb49c43661b6e1f4ea7f95c66749454776f2003b18ebc3
```

## Source-proposal boundary

The source example accepts Jira/GitLab webhooks, returns HTTP `202`, dispatches a
background task and starts a Docker container. Those example transitions are not
durable task admission, hardened isolation, effect completion or remote readback.
This leaf keeps each fact separate.

## Existing canonical mechanisms to adapt

| Existing path | Reusable responsibility | Boundary |
|---|---|---|
| `loop_wiki/loopx-ledger/` | append-only events, CAS, idempotency and recovery | no external effect semantics |
| `loop_wiki/loopx-worker-gateway/` | typed Worker requests, receipts and cleanup | Worker cannot create Gate or canonical PASS |
| `loop_wiki/loopx-kernel/` | task/Gate/Quota state authority | contracts are not execution |
| `docs/git/AUTOMATED_ADMISSION.md` | exact-subject guarded operations and readback | missing intent fails closed |
| `loop_wiki/loopx-resource-gc/` | residue and protected evidence handling | no silent destructive cleanup |

## Target State Machine

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

`HTTP 202`, queue delivery, Worker exit zero and provider API success remain
distinct from `COMMITTED`.

## Data flow

```text
provider event bytes + provider identity
        ↓ signature/schema/replay gate
transactional inbox + dedupe identity
        ↓ task admission receipt
WriteIntent + expected remote version + capability
        ↓ effect reservation
reversible API or bounded-browser test-double attempt
        ↓ remote readback
        ├─ exact match → COMMITTED candidate receipt
        ├─ uncertain  → UNKNOWN_EFFECT, no blind retry
        └─ failure    → compensation or Human escalation
```

## Provisional lease

```text
loop_wiki/inception-ingress-effects/**
.arena/modules/inception-ingress-effects/**
data/inception-ingress-effects/**
.github/workflows/inception-a6-ingress-effects.yml
```

Production credentials, shared queues, provider sessions, root `loopctl`/MCP
surfaces, release indexes and ordered terminal queues are forbidden during this
stage.

## First implementation commit admission

The next commit must add strict event/inbox/WriteIntent/effect schemas and a
hollow or failing control against one reversible local test double. It must
include duplicate/replay, restart, stale expected version, timeout after unknown
remote state, blind retry, compensation and cleanup disagreement cases.

## Evidence ceiling

```text
OWNER_PREPARATION_READY
ingress implementation NOT_STARTED
reversible effect run   NOT_EXERCISED
remote readback         NOT_EXERCISED
production credentials ABSENT
external write          NOT_PERFORMED
Human admission         NOT_PERFORMED
```

Machine authority: [`preflight.json`](preflight.json).
