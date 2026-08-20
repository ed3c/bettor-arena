# Bettor Agentic Engineering workflow

This document binds Bettor to the Kenn-derived, human-led Agentic Engineering method without making Kenn tools canonical. Shared method authority remains in `ed3c/skills-shared`; Bettor owns consumer adapters, runtime subjects, provider identities, receipts, worktrees, issues/PRs and exact verification.

## Consumer State Machine

```text
SOURCE_OR_INTENT_BOUND
→ SHARED_METHOD_BOUND
→ HUMAN_DESIGN_ACTIVE
→ DESIGN_ADVERSARY_COMPLETE
→ HUMAN_DESIGN_ADMITTED
→ BETTOR_CONTRACT_COMPILED
→ CAPABILITY_DAG_ASSERTED
→ TASK_DAG_ASSERTED
→ WORKSPACE_LEASED
→ IMPLEMENTATION_ACTIVE
→ COMMIT_CREATED
→ REVIEW_EVIDENCE_BOUND
→ BETTOR_NATIVE_GATES_VERIFIED
→ BRANCH_GLOBAL_OBJECTIVE_VERIFIED
→ LIVING_CONTEXT_SYNCED
→ STACK_PR_READY
→ HUMAN_ADMIT_REQUIRED
```

`REVIEW_EVIDENCE_BOUND` is not correctness PASS. Bettor native/domain gates remain the owning correctness lane.

## Directory / responsibility DAG

```text
shared human-led method
→ immutable `.skill-bindings` subject
→ Bettor agentic-engineering adapter surface
   ├─ intent adapter
   ├─ review adapter
   ├─ observability adapter
   ├─ workspace adapter
   └─ session carrier adapter
→ Bettor proof/control/mutation gates
→ Bettor-owned receipts
→ Git Town Stack delivery
→ Human merge authority
```

No provider adapter can weaken shared hard laws or expand repository/network/secret/merge authority.

## Data flow

```text
GitHub issue / human request / source proposal
  ↓
Human design snapshot
  ↓
independent design challenge
  ↓
Human design-admit receipt
  ↓
Tech Lead task + capability contracts
  ↓
leased Bettor worktree/Worker
  ↓
exact commit/tree
  ├─ optional roborev evidence
  ├─ Bettor deterministic/domain verification
  └─ Shadow architecture delta observation
  ↓
branch/global-objective receipt
  ↓
AGENTS/README/ARCHITECTURE/CONTEXT update as appropriate
  ↓
Stack PR traceability
  ↓
Human/trusted delivery decision
```

## Provider policy

| Capability | Primary/allowed provider | Integration boundary | Evidence ceiling |
|---|---|---|---|
| intent | GitHub Issues; optional Kata | adapter/CLI | intent/work ledger only |
| commit review | native gates; optional roborev | adapter/CLI | candidate review evidence |
| session observability | native telemetry; optional AgentsView | read-only adapter | advisory/cost/session evidence |
| worktree | Git Town + optional kwt | local runtime | workspace identity/lifecycle |
| maintainer UI | existing GitHub/Forgejo; optional Kenn Forge | external process/API only | presentation/maintainer action surface |
| terminal/session UI | existing carriers; optional Ghosthub | external process only | session presentation only |

License-sensitive defaults:

```text
roborev     MIT          permissive adapter
Kata        MIT          permissive adapter
AgentsView  MIT          permissive adapter
kwt         Apache-2.0   permissive adapter/dependency
Kenn Forge  Elastic-2.0  external-only by default
Ghosthub    AGPL-3.0     external-only by default
```

Restricted provider source must not be vendored or relicensed into Bettor's Apache-2.0 core without a separate rights review.

## Shadow Architect monitor

The Shadow is read-only and observes the same immutable subject as the Tech Lead. It checks:

```text
architecture delta
provider authority widening
missing exact-subject receipt
review-vs-native evidence laundering
license boundary regression
lease overlap / false dependency
suppressed dissent
local success vs global objective conflict
living-context drift
```

A valid Shadow blocker cannot be outvoted by Worker/model consensus.

## Stack PR decomposition

```text
B1 kenn-ae/consumer-binding
   issue #189
   class: ROOT / CONTRACT+DOC BINDING
   owns this workflow and adapter directory contracts

B2 review-provider leaf
   class: SIBLING when path-disjoint
   consumes admitted shared ReviewProviderPort

B3 intent-ledger leaf
   class: SIBLING when path-disjoint

B4 observability leaf
   class: SIBLING when path-disjoint

B5 consumer convergence
   class: CONVERGENCE
   owns shared indexes, aggregate docs, exact-head closure receipt and handoff
```

The open shared `skills-shared#234` Git Town/dual-forge canary is a process/evidence dependency, not a Git parent. Cross-repository dependencies bind immutable commits/releases rather than mutable sibling checkouts.

## Closure status

```text
independent Shadow enforcement      VERIFIED in shared issue #232
real Git Town/dual-forge canary     OPEN in shared issue #234
Human Design Gate method            OPEN/INTEGRATING in shared issue #392
commit/branch review provider       OPEN in shared issue #393
intent + observability ports        OPEN in shared issue #394
Bettor consumer binding             OPEN in Bettor issue #189
```

Do not upgrade these states from documentation alone.
