# Dual-Agent program integration state

This directory is the current cross-repository integration control surface for the PDF-driven local↔cloud Agent architecture. It records what is on public `main`, what remains a deterministic candidate, what requires physical execution, and which authority owns each next transition.

It does **not** replace repository-local contracts, current GitHub state, live receipts, Human admission, or release authority.

## Read route

1. `AGENTS.md`
2. this `README.md`
3. `stack-index.json`
4. `merge-review.md`
5. `local-handoff-queue.md`
6. repository-local README / AGENTS / exact PR / Actions subjects named by the index
7. current GitHub state before any merge, close, promotion, live execution, or handoff

## Real problem denominator

The target product loop requires all of the following to work together:

- a local sovereign Agent that owns local code, files, device state, and data that must not leave the machine;
- an always-on cloud Agent/runtime that can continue bounded work while the local machine is offline;
- durable offline enqueue, reconnect, duplicate delivery, retry, cancellation, restart, and local result reconstruction;
- API-first external integration with browser automation only as a policy-admitted fallback;
- explicit identity, audience, policy, secret-handle, effect, artifact, cleanup, and Human boundaries;
- independent readback and verification rather than trusting the executing Agent's narrative.

The deterministic implementation program now closes several interfaces and refusal semantics on public `main`. It still does **not** close the physical local→cloud→local product loop.

```text
program state
DETERMINISTIC_RUNTIME_WORKFLOW_EFFECT_TRUTH_MERGED
+
PROVIDER_AND_PHYSICAL_LOOP_OPEN
```

## Repository authority map

| Repository | Authority | Must not become |
|---|---|---|
| `skills-shared` | portable method, invariants, Agent workflow | runtime or credential owner |
| `runtime-env` | exact wire/runtime contracts, transport and identity bindings | workflow, effect, Human, or release authority |
| `bettor-arena` | workflow orchestration, canonical task/effect admission, composition | provider self-report or independent truth authority |
| `agent-shield-monorepo` | provider, API/browser, sandbox and isolation adapters | task/effect/release writer |
| `truth-verify-loop` | independent evidence/readback and existing closure vocabulary | transport, workflow, effect, provider, Human, or release authority |
| Human/trusted runtime | credentials, terms, live target, provider billing, admission, release and rollback | deterministic fixture |

## Directory → State Machine → DAG owner

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
  → VERIFYING → RECONCILING
  → COMPLETED | typed terminal alternative

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
Agent Shield route + sandbox providers
        ↓
truth-verify-loop independent verification
        ↓
physical local→cloud→local canary
        ↓
Human Admit
        ↓
content-addressed release / rollback
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

### `runtime-env` — merged deterministic runtime plane

```text
implementation merge
92feed7c4e671dc63238155da9d4f394aac80d90

README / AGENTS / Stack / Local Handoff merge
baa4ce25d32a9fb4383ea8bc3530f9fd80be9ae7
tree 117901dbd77cc93993ddc388682b7ab26a00d544
```

Admitted deterministic scope:

```text
wire contracts
SQLite durable outbox/inbox
restart and replay semantics
bounded NATS adapter contract
local/cloud identity binding
policy epoch and reconnect revalidation
runtime README / AGENTS / Stack
LH-TR-001 and LH-ID-001
```

Still open:

```text
#58 / #73 physical NATS/JetStream/TLS reconnect
#59 / #83 live workload identity, secret resolution, revocation and rotation
```

State: `MERGED_DETERMINISTIC_RUNTIME_SUBTREE`.

### `bettor-arena` — merged deterministic Workflow + Effect planes

```text
main merge
74d1e75c61589dcd163c7412e1345f726781ffb4
tree 0de94032a3227ad04dde52f138041294ef9cb810
```

Admitted Workflow Stack:

```text
PR #201 DA-WF-C
└─ PR #202 DA-WF-K
   ├─ #209 DA-WF-R       absorbed by #232
   ├─ #210 DA-WF-H       absorbed by #232
   ├─ #211 DA-WF-COMP    absorbed by #232
   ├─ PR #232 DA-WF-E v2 complete matrix
   └─ PR #233 DA-WF-D README/AGENTS/Stack/LH-WF-001
```

Admitted Effect Stack:

```text
PR #216 DA-EF-C
→ #224 DA-EF-K
→ #225 DA-EF-P
   ├─ #226 DA-EF-A       absorbed by #228
   └─ #227 DA-EF-COMP    absorbed by #228
→ #228 DA-EF-E
→ #229 DA-EF-D
→ merged through #202 / #201
```

State: `MERGED_DETERMINISTIC_WORKFLOW_EFFECT_SUBTREE`.

Still open:

```text
#184 live durable-workflow engine and physical restart/timer/Human/cancel path
#185 live effect parent
#223 real reversible provider effect/readback/compensation
#186 physical offline local→cloud→local canary
#68 Human release/rollback
```

### `truth-verify-loop` — merged deterministic independent verification

```text
PR #29 green baseline
→ PR #39 DA-TV-C
→ PR #44 DA-TV-E
→ PR #45 DA-TV-D
```

Issues #31–#37 are closed. Leaf PRs #40–#43 were absorbed by #44 and closed without a second merge. Parent #22 remains open because real physical/live/semantic evidence is absent.

Technical result remains:

```text
technical matrix PASS
semantic closure UNVERIFIABLE
canonical_write NONE
```

State: `MERGED_DETERMINISTIC_SUBTREE`.

### `agent-shield-monorepo` — current deterministic merge frontier

Route Stack candidate:

```text
#162 DA-INT-C
├─ #163 DA-INT-API
├─ #164 DA-INT-BR
└─ #165 DA-INT-POL
        ↓
     #166 DA-INT-E
        ↓
     #167 DA-INT-D
```

gVisor Stack candidate:

```text
#174 DA-GV-C
├─ #175 DA-GV-A
└─ #176 DA-GV-P
        ↓
     #177 DA-GV-E
        ↓
     #178 DA-GV-D
```

Shared non-promoting candidate: PR #180. Current main remains `30e12cc917503b56b002aa7351428811f20fea8e` / tree `6f465f936515d81ed51c5b80595de530593f25fc`.

These candidates need current-main reread/restack and exact-head CI before merge. Live network #95, API/browser #161, and runsc/gVisor #173 remain open.

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

- merged runtime, workflow/effect and truth subjects;
- Agent Shield candidates and current merge frontier;
- absorbed leaves and completed child Issues;
- exact evidence ceilings;
- live/Human/release blockers and next transitions.

Always reread GitHub before acting. The index is a trace snapshot, not a substitute for current GitHub state.

## Local Handoff

`local-handoff-queue.md` is the current execution queue. The remaining hard boundary is:

```text
Agent Shield current-main admission
→ physical transport and identity
→ live durable workflow and provider routes
→ reversible effect/readback
→ bettor-arena#186 physical canary
→ truth-verify-loop#22 real-bundle verification
→ Human #68 release decision
```

No public CI fixture may close these live Issues.
