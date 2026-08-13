# Issue and pull-request policy for coding Agents

## System of record

The exact task packet decides the issue/PR authority. GitHub is the cloud distribution and review surface for the current `ed3c/bettor-arena` work; local Forgejo remains a distinct authoring origin. Similar issue titles or branch names across origins are not the same subject.

For every task, capture:

```text
repository identity
issue number and immutable URL
PR number, base, head, and current head SHA
parent/sibling/child/terminal/convergence relation
acceptance criteria and non-goals
allowed and forbidden paths
evals, receipts, rollback, and Human Admit
```

## Read and write policy

Read current issue/PR bodies, comments, reviews, labels, base/head relations, and check executions before claiming state. A branch name, local commit, old comment, skipped workflow, or no-runner event does not prove the current PR.

Write operations require an explicit task or admitted delivery loop. Agents may create or update issues/PRs for the requested work, but they do not merge, close as completed, widen permissions, promote releases, or rewrite historical evidence without Human Admit.

Batch related updates. Do not publish every local checkpoint merely to expose progress. Preserve the repository's GitHub publication/billing circuit and exact-HEAD evidence rules.

## Cross-repository work

A `skills-shared` procedure PR and a Bettor consumer-binding PR are separate repository subjects. They may have a semantic dependency, but Git cannot make them one atomic stacked PR. Record exact external commit/release identities and block consumer promotion until the dependency is admitted.

Within one repository:

- independent path-disjoint tasks are siblings;
- a true child consumes unmerged parent bytes;
- one terminal leaf delivers one reviewable behavior plus eval/evidence;
- shared indexes, generated locks, and final acceptance belong to a convergence leaf.

## Traceability

Use this chain:

```text
source / incident / design intent
→ repository decision
→ parent issue
→ molecular slice issue
→ branch and PR
→ evals and planted negatives
→ immutable implementation subject
→ execution receipts
→ Human Admit
```

A missing link remains explicit. Memory, prose similarity, mutable `main`, package presence, or another environment's receipt cannot fill it.

## Evidence states

Use exactly:

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

## Change contract

A tracker-policy change requires current origin model, publication/permission impact, issue/PR graph impact, negative controls for stale or cross-origin confusion, rollback, exact issue/PR, and Human Admit.
