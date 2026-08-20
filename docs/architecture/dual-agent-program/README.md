# Dual-Agent program integration state

This directory is the current integration control surface for the PDF-driven local↔cloud Agent architecture. It records what is merged, what is only a deterministic Draft candidate, what still requires a physical runtime, and which authority owns the next transition.

It does **not** replace repository-local contracts, GitHub state, live receipts, Human admission, or release authority.

## Read route

1. `AGENTS.md`
2. this `README.md`
3. `stack-index.json`
4. `merge-review.md`
5. `local-handoff-queue.md`
6. repository-local README / AGENTS / exact PR / Actions subjects named by the index
7. current GitHub state before any merge, close, promotion, or handoff

## Real problem denominator

The source architecture requires all of the following to work together:

- a local sovereign Agent that owns local code, files, device state, and data that must not leave the machine;
- an always-on cloud Agent/runtime that can continue bounded work while the local machine is offline;
- durable offline enqueue, reconnect, duplicate delivery, retry, cancellation, restart, and local result reconstruction;
- API-first external integration with browser automation only as a policy-admitted fallback;
- explicit identity, audience, policy, secret-handle, effect, artifact, cleanup, and Human boundaries;
- independent readback and verification rather than trusting the executing Agent's narrative.

The deterministic implementation program closes interfaces and refusal semantics. It does not by itself prove the physical local→cloud→local product loop.

## Repository authority map

| Repository | Authority | Must not become |
|---|---|---|
| `skills-shared` | portable method, invariants, Agent workflow | runtime or credential owner |
| `runtime-env` | exact wire/runtime contracts, transport and identity bindings | workflow, effect, Human, or release authority |
| `bettor-arena` | workflow orchestration, task/effect admission, composition | provider self-report or independent truth authority |
| `agent-shield-monorepo` | provider, API/browser, sandbox and isolation adapters | task/effect/release writer |
| `truth-verify-loop` | independent evidence/readback and existing closure vocabulary | transport, workflow, effect, provider, Human, or release authority |
| Human/trusted runtime | credentials, terms, live target, provider billing, admission, release and rollback | deterministic fixture |

## Directory → State Machine ownership

```text
skills-shared/
  method contract
  SOURCE_PROPOSAL → METHOD_BOUND → CONSUMER_HANDOFF

runtime-env/contracts + transport + identity
  METHOD_BOUND → WIRE_CONTRACT_BOUND
  → OUTBOX_COMMITTED → DELIVERED/REDELIVERED
  → INBOX_COMMITTED → RECONCILED
  → IDENTITY/POLICY_REVALIDATED

bettor-arena/loop_wiki/dual-agent-offload-workflow
  SUBMITTED → ADMITTED → DISPATCHED → RUNNING
  → WAITING_FOR_RESULT/HUMAN
  → VERIFYING → RECONCILING → COMPLETED | typed terminal alternative

bettor-arena/loop_wiki/dual-agent-effect-ledger
  EFFECT_PROPOSED → INTENT_VALIDATED
  → IDEMPOTENCY_RESERVED → PRECONDITION_REVALIDATED
  → EFFECT_ATTEMPTED → READBACK
  → COMMITTED | RESULT_UNKNOWN | COMPENSATION_REQUIRED

agent-shield-monorepo/services/runtime-fabric
  ROUTE_REQUESTED → API_SELECTED | BROWSER_FALLBACK_SELECTED | REFUSED
  SANDBOX_CANDIDATE → POLICY_ADMITTED → PLAN_ONLY
  → LIVE_EXECUTION_REQUIRED

truth-verify-loop/harness/dual_agent_evidence
  BUNDLE_PROPOSED → SUBJECTS_AND_DENOMINATOR_VALIDATED
  → DLV/EF/ART/USER_CHECKED
  → TECHNICAL_MATRIX_PASS
  → UNVERIFIABLE_PENDING_SEMANTIC_OR_LIVE_EVIDENCE

bettor-arena#186 physical canary
  LOCAL_REQUESTED → OFFLINE_OUTBOX → RECONNECT
  → CLOUD_WORKFLOW → SANDBOX/API_OR_BROWSER
  → RESULT/ARTIFACT → LOCAL_INBOX/RESTART
  → USER_RESULT → CLEANUP → HUMAN_REVIEW
```

## Program Process DAG

```text
skills-shared method
        ↓
runtime-env wire contracts
        ├──────── transport / restart / NATS
        └──────── identity / policy / secret handles
                         ↓
bettor durable workflow
        ↓
bettor effect admission and reconciliation
        ↓
agent-shield route + sandbox providers
        ↓
truth-verify-loop independent verification
        ↓
physical local→cloud→local canary
        ↓
Human Admit
        ↓
selected content-addressed release / rollback
```

A process edge is not automatically Git ancestry. A true Git child exists only when it consumes named unmerged parent bytes. Path-disjoint leaves remain siblings. A convergence branch materializes or combines exact sibling bytes and reruns the full denominator.

## End-to-end data flow

```text
local request + exact source/method/runtime/policy subjects
        ↓
SQLite durable outbox while offline
        ↓ at-least-once transport
cloud workflow admission and replay history
        ↓
identity/policy/secret-handle revalidation
        ↓
API-first route or bounded browser fallback
        ↓
sandbox/provider observation
        ↓
effect intent / idempotency / readback when a write exists
        ↓
content-addressed result and artifact receipts
        ↓
local inbox + second restart + projection rebuild
        ↓
user-visible result and cleanup receipts
        ↓
independent DLV / EF / ART / USER verification
        ↓
existing Evidence Closure vocabulary
        ↓
Human review and release decision
```

## Current integrated state

### Merged and closed

`truth-verify-loop` now carries the independent deterministic verification subtree on `main` through the minimal convergence route:

```text
PR #29  green baseline
→ PR #39 DA-TV-C
→ PR #44 DA-TV-E
→ PR #45 DA-TV-D
```

Issues #31–#37 are closed as completed. Leaf PRs #40–#43 were closed without a second merge because PR #44 materialized and reverified their exact implementation/test blobs. Parent issue #22 remains open because semantic and physical evidence are not complete.

### Implemented deterministic Draft candidates

The following families have exact candidate PRs and prior green targeted CI, but require current-main restack/readback before merge credit:

- `runtime-env`: wire contracts; SQLite outbox/inbox; restart/replay; bounded NATS adapter contract; local/cloud identity and policy revalidation.
- `bettor-arena`: workflow contract/reducer; retry/timer/cancel; Human wait; compensation; complete workflow matrix; effect contract/reducer/policy/provider-readback/compensation/matrix/docs.
- `agent-shield-monorepo`: API-first/browser-fallback route matrix and docs; gVisor/runsc admission/plan/policy/matrix/docs; non-promoting shared candidate.

`DRAFT_CANDIDATE` is not `MERGED`, `LIVE_PASS`, `HUMAN_ADMITTED`, or `RELEASED`.

### Not exercised

- physical NATS/JetStream disconnect and reconnect;
- live local/cloud workload enrollment, credential issuance, revocation and rotation;
- real API/browser provider target and signed-in session boundaries;
- real gVisor/runsc OCI execution and isolation readback;
- one reversible external effect with target readback and compensation;
- full offline local→cloud→local run and user-visible reconstruction;
- Human admission, release and rollback.

## Evidence non-substitution laws

```text
source proposal             != implementation
Draft PR / mergeable        != merged
CI PASS                     != live provider PASS
transport ACK               != task or user success
workflow completion         != effect commit
provider result             != user-visible result
API evidence                != browser evidence
sandbox package/source      != physical isolation
artifact manifest/hash      != independently read-back bytes
screenshot                  != semantic proof
technical matrix PASS       != SUPPORTED/REFUTED
Human/release fixture       != Human/release evidence
```

## Merge and close policy

A PR may enter merge review only when:

1. its exact head and current base are known;
2. all required exact-head checks are green and not merely skipped;
3. unresolved review threads are empty or explicitly dispositioned;
4. no second writer owns the same shared paths or authority;
5. the PR body and docs state the correct evidence ceiling;
6. live/Human/release absence is not represented as PASS;
7. child PRs are either restacked to the admitted parent or deliberately absorbed by an exact-byte convergence PR.

An issue closes only after its acceptance criteria are present on the admitted target branch, or after it is explicitly superseded with preserved traceability. Parent/live/release issues stay open when only deterministic children are complete.

## Stack index

`stack-index.json` is the machine-readable snapshot. It records:

- exact candidate PRs and known heads/runs;
- merged, Draft, superseded, live-required and Human-required states;
- convergence versus sibling relationships;
- evidence ceilings;
- retained blockers and next transition.

Always reread GitHub before acting. The index is a trace snapshot, not a substitute for current GitHub state.

## Local Handoff

`local-handoff-queue.md` is the current execution queue. The hard next boundary is the physical canary in `bettor-arena#186`, fed by the live transport, identity, provider, effect and independent-verification owners. No public CI fixture may close that issue.
