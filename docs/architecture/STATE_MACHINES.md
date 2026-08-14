# Bettor Arena state machines — route summary

The full normative target is [`modular-integration-requirements.md`](modular-integration-requirements.md); current state is [`modular-integration-status.md`](modular-integration-status.md). LoopX/PDF mapping is [`PDF_LOOPX_HARNESS_TRACEABILITY.md`](PDF_LOOPX_HARNESS_TRACEABILITY.md). This file is the same-name State Machine route summary.

## Macro composition

```text
GOAL_RECEIVED
→ MODULE_REQUIREMENTS_SELECTED
→ CAPABILITY/CONFLICT_RESOLVED
→ SKILL/RUNTIME/HOST PROJECTIONS
→ PROOF MATRIX
→ HUMAN ADMIT
→ COMPOSITION LOCK
→ IMMUTABLE RELEASE / ROLLBACK
```

Owner: module catalog/resolver and trusted Human governance. Not externally MCP-exposed.

## Micro task loop

```text
TYPED_TASK
→ PUBLIC MODULE PORT
→ BOUNDED PRIVATE ITERATIONS
→ TYPED RESULT + NAMED EXIT
→ ARTIFACTS
→ PROOF/CONTROL/MUTATION RECEIPT
```

A Micro loop may read its own closure; it uses other modules only through typed/public boundaries. It cannot Human Admit, promote or perform production rollback.

## Module lifecycle

```text
MANIFEST_ADMITTED
→ OWNERSHIP/CAPABILITIES_RESOLVED
→ CLOSURE_DIGESTED
→ MODULE PROOF/CONTROL/MUTATION
→ SELECTED IN COMPOSITION
→ RELEASE SUBJECT
```

Documentation-only changes do not imply runtime PASS. A context/contract change may still invalidate the owning closure.

## Context Capsule and driver

```text
ROOT + LOOP CONTEXT SELECTED
→ TRACKED PATHS VERIFIED
→ IMMUTABLE BYTES MATERIALIZED
→ DIGEST FROZEN
→ ALLOWLISTED HOST DRIVER
→ TYPED OUTPUT
→ CONTEXT/DRIVER RECEIPT
```

Context Capsules are immutable projections. They are not another state authority.

## Stateless MCP

```text
IMMUTABLE REF
→ EXPLICIT POLICY ALLOWLIST
→ SELECTED MODULE CLOSURE
→ DISPOSABLE WORKTREE/BUNDLE
→ FIXED PUBLIC PORT
→ BOUNDED TYPED RESULT
→ CLEANUP VERIFIED
```

Unexposed commands default deny. Human Admit, promotion, secret rotation, production rollback and generic shell are not tools.

## Portable Skill execution

```text
EXACT SUBJECT + SKILL DIGEST + ASSERTION DIGEST
→ REQUEST VALIDATED
→ DISPOSABLE WORKTREE
→ EXECUTABLE + ARGV
→ OS/ARTIFACT OBSERVATIONS
→ INDEPENDENT HARD ASSERTIONS
→ SUBJECT-BOUND RECEIPT
→ CLEANUP VERIFIED
```

The Worker cannot write gate verdicts or LoopX state. The local-process adapter does not claim network/filesystem isolation it cannot attest.

## Project bootstrap

```text
CONSUMER REQUIREMENTS
→ PLAN (READ-ONLY)
→ CONFLICT/OWNERSHIP CHECK
→ APPLY TRANSACTION
→ VERIFY
→ ROLLBACK ONLY IF AFTER-BYTES UNCHANGED
```

Remote consumer and embedded module modes remain distinct.

## Proof kernel

```text
PROOF CLAIM
+ INDEPENDENT CONTROL
+ HOLLOW/MUTATION
+ EXTERNAL CONSUMER CANARY
→ MODULE RECEIPT
→ COMPOSITION RELEASE RECEIPT
```

No absence or `NOT_EXERCISED` is promoted to PASS.

## Knowledge-provider query and memory

```text
PROVIDER MANIFEST
→ EXACT SUBJECT + QUERY DIGEST
→ READ-ONLY CANDIDATE RESULT
→ CURRENT SOURCE/TEST/RECEIPT READBACK
→ ADMISSION CANDIDATE
```

```text
OBSERVED INCIDENT / PREFERENCE / DEAD END
→ EVIDENCE-BOUND MEMORY PROPOSAL
→ SCOPE / RETENTION / PRIVACY / CONFLICT CHECK
→ HUMAN ADMIT WHEN DURABLE
→ OPTIONAL REBUILDABLE PROJECTION
```

Provider and memory output cannot advance LoopX state, waive a gate, mark `TESTED` or override current authority.

## Origin/browser/external release

```text
LOGICAL RELEASE
→ GITHUB/FORGEJO ORIGIN RECEIPTS
→ EQUIVALENCE
→ BROWSER/DRIVER/PROVIDER CANARIES
→ EXTERNAL RELEASE ACCEPTANCE
→ HUMAN PROMOTION
```

Each provider/carrier remains independently evidenced.

## LoopX compatibility state machine

The PDF’s Objective, Todos, Gates, Evidence and Quota are translated into existing modular authorities:

```text
OBJECTIVE_ACCEPTED
  → MODULE_REQUIREMENTS_RESOLVED            # Objective / scope
  → TYPED_TODO_DISPATCHED                   # one bounded Todo
  → HOST_EXECUTION_OBSERVED                 # Worker output is untrusted
  → HARD_GATES_EVALUATED                    # Gates
      ├─ PASS → EVIDENCE_SUBJECT_BOUND      # Evidence
      │          → READY_FOR_HUMAN_ADMIT
      │          → RELEASED | ROLLED_BACK
      └─ FAIL → RETRY_BUDGET_DECREMENTED    # Quota
                 ├─ RETRY_ALLOWED
                 └─ HUMAN_REVIEW_REQUIRED
```

### Current implementation split

| LoopX concept | Current owner | Current state |
|---|---|---|
| Objective/scope | Macro composition requirements | `IMPLEMENTED` |
| Bounded Todo | typed Micro task/public port | `IMPLEMENTED` |
| Host execution observation | portable Skill runner / MCP carrier | `IMPLEMENTED` |
| Hard gate verdict | independent assertions + proof kernel | `IMPLEMENTED`, universal LSP gate schema `PARTIAL` |
| Evidence | subject-bound artifacts/receipts | `IMPLEMENTED` |
| Quota | bounded retry/resource policy distributed by loop/provider | `PARTIAL` |
| Single writer | trusted reducer principle | `PARTIAL`; append-only LoopX ledger `NOT_IMPLEMENTED` |
| Human pause/resume | Human Admit boundary | governance present; LangGraph runtime `NOT_IMPLEMENTED` |
| Episodic memory | proposal-only provider contract | `PARTIAL`; distiller/writeback live path `NOT_EXERCISED` |
| Web UI | read projection | `NOT_IMPLEMENTED` |

### Required authority separation

```text
Worker proposes actions
Host executes typed argv
Gates observe OS/artifacts
Trusted reducer commits state
Human admits exception/release/rollback
```

A future LangGraph graph may propose routing and preserve checkpoints, but it cannot write canonical LoopX completion or compete with release/Human authority.

### Named non-success branches

```text
GATE_FAIL
RETRY_BUDGET_EXHAUSTED
HUMAN_REVIEW_REQUIRED
CAPABILITY_MISMATCH
STALE_SUBJECT
ABSENT_PROVIDER
NOT_EXERCISED
SKIPPED_BY_POLICY
ROLLBACK_REQUIRED
```

None is normalized into PASS.
