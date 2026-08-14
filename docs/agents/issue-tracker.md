# Issue and pull-request policy for coding Agents

## System of record

The exact task packet decides issue/PR authority. GitHub is the cloud distribution and review surface for current `ed3c/bettor-arena` work; local Forgejo remains a distinct authoring origin. Similar issue titles or branch names across origins are not the same subject.

For every task, capture:

```text
repository identity
issue number and immutable URL
PR number, base, head and current head SHA
parent/sibling/child/terminal/convergence relation
acceptance criteria and non-goals
allowed and forbidden paths
evals, receipts, rollback and Human Admit
```

## Mandatory trace route

Before branch or PR work, read:

1. [`../traceability/TRACEABILITY_INDEX.md`](../traceability/TRACEABILITY_INDEX.md)
2. [`../traceability/STACK_PR_INDEX.md`](../traceability/STACK_PR_INDEX.md)
3. current GitHub issue/PR bodies, comments, reviews and checks.

The Markdown index records relation and last observed immutable subjects. GitHub metadata remains authoritative for current head/check/open state.

## Git Town status

```text
.git-town.toml                         ABSENT
.git-town                              ABSENT
git-town-stacked-pr-worker selected    ABSENT
```

Do not claim Git Town is configured. Molecular terms are still used as delivery policy:

- **sibling** — independent path-disjoint task;
- **true child** — consumes unmerged parent bytes;
- **terminal leaf** — one reviewable behavior plus eval/evidence;
- **convergence leaf** — shared indexes, generated locks and final acceptance.

If Git Town configuration or the selected Skill appears later, add exact config/version receipts and update the Stack index before using it as runtime evidence.

## Read and write policy

Read current issue/PR bodies, comments, reviews, labels, base/head relations and check executions before claiming state. A branch name, local commit, old comment, skipped workflow or no-runner event does not prove the current PR.

Write operations require an explicit task or admitted delivery loop. Agents may create or update issues/PRs for requested work, but they do not merge, close as completed, delete branches, widen permissions, promote releases or rewrite historical evidence without Human Admit.

Batch related updates. Do not publish every local checkpoint merely to expose progress. Preserve the repository's publication/billing circuit and exact-head evidence rules.

## Cross-repository work

A `skills-shared` procedure PR and a Bettor consumer-binding PR are separate repository subjects. They may have a semantic dependency, but Git cannot make them one atomic stacked PR. Record exact external commit/release identities and block consumer promotion until the dependency is admitted.

Within one repository:

- independent path-disjoint tasks are siblings;
- a true child consumes unmerged parent bytes;
- one terminal leaf delivers one reviewable behavior plus eval/evidence;
- shared indexes, generated locks and final acceptance belong to a convergence leaf.

The four-repository documentation siblings are merged. `bettor-arena#38` is their convergence owner. Current topology is indexed in [`../traceability/STACK_PR_INDEX.md`](../traceability/STACK_PR_INDEX.md).

## Generated contracts and convergence

Generated files such as:

```text
.arena/locks/bettor-arena.lock.json
.arena/contexts.lock.json
data/context-capsules/driver-parity.json
data/module-proof/subjects.lock.json
data/module-proof/release-receipt.json
data/mcp/exposure.json
data/origins/status.json
data/browser/status.json
```

belong in a terminal leaf only when the terminal behavior changes their inputs. Final shared regeneration and exact index updates belong to one convergence owner.

Never hand-edit a digest or accept a focused PASS while the generated composition is stale.

## Traceability

Use this chain:

```text
source / incident / PDF proposal
→ repository decision
→ parent issue
→ molecular slice issue
→ branch and PR
→ evals and planted negatives
→ immutable implementation subject
→ execution receipts
→ convergence index
→ Human Admit
```

A missing link remains explicit. Memory, prose similarity, mutable `main`, package presence or another environment's receipt cannot fill it.

## Stale branch policy

When an old aggregate branch diverges:

1. compare it to current `main`;
2. identify unique load-bearing deltas;
3. extract each into a clean terminal leaf;
4. index the old PR as stale/non-authoritative;
5. preserve history until Human Admit closes or deletes it.

Do not merge a historical aggregate merely because it contains useful files. Current PR #53 is such a subject.

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

A tracker-policy change requires current origin model, publication/permission impact, issue/PR graph impact, negative controls for stale or cross-origin confusion, rollback, exact issue/PR, Stack index update and Human Admit.
