# Git Town Stacked-PR Worker protocol

## Scope

This is the Bettor repository-owned execution contract derived from the shared `git-town-stacked-pr-worker` procedure. The repository now implements a typed fail-closed controller and physical controls; it does not bundle/admit the Git Town executable or authorize publication.

## Authority model

```text
Task owner
  defines issue, goal, paths, dependencies, evals and rollback

Worker
  owns one linked worktree, one branch and one path lease

Git Town
  may synchronize an admitted local branch hierarchy

GitHub
  owns publication metadata and exact-head checks

Human
  resolves semantic conflicts and owns merge/ship/promotion/rollback
```

## Worker State Machine

```text
PACKET_RECEIVED
→ PACKET_VALIDATED
→ STACK_RELATION_VALIDATED
→ LEASE_REQUESTED
→ LEASE_GRANTED
→ WORKTREE_MATERIALIZED
→ IMPLEMENTING
→ EVALS_RUNNING
   ├─ PASS → CANDIDATE_READY
   ├─ FAIL → REPAIR_WITHIN_BUDGET
   ├─ CONFLICT → RETURN_CONTROL
   └─ BLOCKED → STOP
→ CLEANUP_VERIFIED
→ RECEIPT_EMITTED
→ HUMAN_REVIEW
```

Current implementation state:

```text
packet/document contract     IMPLEMENTED
typed Git Town controller    IMPLEMENTED by PR #133
linked-worktree controls     PASS in 13 real-repository canaries
Git Town executable/config   ABSENT
local sync                   NOT_EXERCISED
publication                  NOT_EXERCISED
```

## Required task packet

```yaml
parent_issue: integer
goal: string
non_goals:
  - string
base_branch: string
parent_branch: string
head_branch: string
stack_class: sibling | true-child | terminal | convergence
allowed_paths:
  - repository-relative path or glob
excluded_paths:
  - repository-relative path or glob
dependencies:
  - issue/PR/branch identity
parallel_safe_siblings:
  - branch identity
required_evals:
  - typed argv description
negative_or_mutation_controls:
  - planted failure
evidence_boundary: string
cleanup_contract: string
rollback_subject: exact commit or release subject
human_owned_operations:
  - operation
```

Rules:

- all paths are repository-relative;
- no `..`, absolute path or secret-bearing value;
- branch names are explicit;
- parent equals base only for a root/sibling leaf;
- a true child targets the unmerged parent branch;
- a convergence leaf is the only owner of shared final indexes/selection.

## Lease contract

One active Worker lease contains:

```json
{
  "issue": 80,
  "worker_id": "external-runtime-identity",
  "branch": "feat/git-town-stack-governance-v1",
  "worktree_ref": "host-owned-reference",
  "allowed_paths": ["docs/git/**"],
  "base_subject": "ffbcd91a9eae1f6171fc7c42f0300bb83fac1b90",
  "state": "LEASED"
}
```

The example is a contract illustration only. No runtime lease file is admitted in this leaf.

### Lease invariants

```text
one Worker → one linked worktree
one Worker → one branch
one branch → one active issue owner
one tracked path → one active writer or explicit child sequencing
primary checkout → no unattended edits
generated aggregate paths → convergence owner
```

## Sibling versus child decision

Use a sibling only when all are true:

```text
does not require unmerged parent bytes
path lease is disjoint
tests can execute independently
failure does not invalidate sibling subject
```

Use a true child when any are true:

```text
imports parent code
uses parent contract
changes the same routed root documents intentionally
must test against parent behavior
```

Issue #80 is a true child of PR #60 because both own the same routed root documentation.

## Stable outcomes

Every wrapper or controller must map observations into:

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
CONFLICT
DIRTY
STALE
LEASE_CONFLICT
BLOCKED_DUPLICATE_TERMINAL
```

No prose-only success state.

## Command boundary

Future admitted wrapper commands must be typed arrays:

```json
{
  "executable": "git-town",
  "argv": ["sync", "--dry-run"],
  "cwd": ".",
  "timeout_ms": 120000
}
```

Forbidden:

```text
raw shell string
shell=True
bash -c
arbitrary cwd
caller-selected executable
credential-bearing environment
automatic continue/skip/undo
push/ship/merge
```

This leaf does not verify a real Git Town CLI syntax or version. The example only illustrates the no-shell boundary.

## Conflict protocol

On a semantic conflict:

```text
capture exact command and exit
capture conflicted files and repository status
stop the Worker
preserve worktree and branch
emit CONFLICT receipt
return control to Human
```

A Worker must not:

```text
guess conflict intent
choose ours/theirs
continue
skip
undo
force reset
force push
```

## Evaluation protocol

Minimum terminal leaf evidence:

```text
positive case
independent control
hollow or planted mutation
exact branch/base/head subject
path lease check
cleanup check
Stack graph check
```

Future Git Town executable admission additionally needs:

```text
sibling sync positive
true-child restack positive
mainline rewrite detection
semantic conflict stop
dirty worktree stop
duplicate branch/path lease stop
no-push assertion
publication separation
rollback control
```

## Publication boundary

```text
local Git Town sync
  ≠ GitHub branch publication
  ≠ exact-head checks
  ≠ merge
  ≠ release promotion
```

Only the `github-delivery-loop` publication owner or a trusted operator may perform the later GitHub edge after all local evidence settles.

## Cleanup contract

A successful Worker run must show:

```text
no unexpected tracked paths
no orphan process
no credential residue
no abandoned temporary worktree unless conflict preservation requires it
no automatic branch deletion
```

Conflict preservation may intentionally keep a worktree; that is `CONFLICT`, not cleanup PASS.

## Rollback boundary

Rollback requires:

```text
exact pre-operation subject
content-bound after state
Human authorization
verification after rollback
receipt
```

No Agent may reset, rebase, force-push or delete to simulate rollback.

## Historical duplicate conflict

PR #76 and PR #77 violated the single active issue/path writer rule. The resolution is retained as evidence:

```text
PR #76: admitted and reachable from main
PR #77: SUPERSEDED_CANDIDATE
issue #82 residual disposition: COMPLETE
conflict state: RESOLVED_BY_HUMAN
```

The next active queue owner is #92; no duplicate live provider lease may be inferred from this historical resolution.
