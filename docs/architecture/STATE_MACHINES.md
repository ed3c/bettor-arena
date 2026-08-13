# Bettor Arena state machines — route summary

The full normative target is [`modular-integration-requirements.md`](modular-integration-requirements.md); current state is [`modular-integration-status.md`](modular-integration-status.md). This file is the same-name routing summary.

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

Owner: module catalog/resolver and Human governance. Not externally MCP-exposed.

## Micro task loop

```text
TYPED_TASK
→ PUBLIC MODULE PORT
→ BOUNDED PRIVATE ITERATIONS
→ TYPED RESULT + NAMED EXIT
→ ARTIFACTS
→ PROOF/CONTROL/MUTATION RECEIPT
```

A micro loop may read its own private closure; it uses other modules only through typed/public boundaries.

## Module lifecycle

```text
MANIFEST_ADMITTED
→ OWNERSHIP/CAPABILITIES RESOLVED
→ CLOSURE DIGESTED
→ MODULE PROOF/CONTROL/MUTATION
→ SELECTED IN COMPOSITION
→ RELEASE SUBJECT
```

Documentation-only changes must not invalidate implementation closure unless the contract/context authority changed.

## Context Capsule and driver

```text
ROOT + LOOP CONTEXT SELECTED
→ IMMUTABLE BYTES MATERIALIZED
→ DIGEST FROZEN
→ CLAUDE/CODEX FIXED DRIVER
→ TYPED OUTPUT
→ CONTEXT/DRIVER RECEIPT
```

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

Unexposed commands default deny. Human Admit, promotion, secret rotation, production rollback, and generic shell are not tools.

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
