# AGENTS.md — Dual-Agent program integration

This file scopes `docs/architecture/dual-agent-program/**`. Repository-root `AGENTS.md` and repository-owned executable contracts remain authoritative outside this directory.

## Required read order

1. this file
2. `README.md`
3. `stack-index.json`
4. `merge-review.md`
5. `local-handoff-queue.md`
6. current GitHub PR, Issue and Actions state named by the index
7. repository-local AGENTS/README/contracts before changing that repository

Never act only from this snapshot. Rebind current branches, heads, trees, checks, reviews, path ownership and Human authority first.

## Mission

Maintain one honest integration view of the local↔cloud Dual-Agent program while preserving repository authority separation and evidence ceilings.

The target product loop is:

```text
local sovereign request
→ durable offline enqueue
→ reconnect and cloud durable execution
→ API-first or admitted browser fallback
→ effect/readback when needed
→ content-addressed results
→ local restart/rebuild
→ user-visible verification
→ cleanup
→ independent evidence closure
→ Human admission/release
```

## Authority map

```text
skills-shared
  portable method and invariants

runtime-env
  runtime wire contracts, transport and identity bindings

bettor-arena workflow
  deterministic workflow proposals and task orchestration

bettor-arena effect ledger
  canonical external-effect admission and reconciliation

agent-shield-monorepo
  provider, route and isolation adapters

truth-verify-loop
  independent evidence/readback and existing closure vocabulary

Human/trusted execution plane
  credentials, terms, target admission, live execution, merge/release/rollback
```

This directory has `canonical_write=NONE` for task, workflow, effect, provider, Human and release state.

## State vocabulary

Use these states precisely:

```text
SOURCE_PROPOSAL
NOT_STARTED
DRAFT_CANDIDATE
DETERMINISTIC_PASS
MERGE_REVIEW_REQUIRED
MERGED_DETERMINISTIC_SUBTREE
SUPERSEDED
ABSORBED_BY_CONVERGENCE
BLOCKED_RESTACK_REQUIRED
NOT_EXERCISED
HUMAN_REQUIRED
NOT_PERFORMED
RELEASED
ROLLED_BACK
```

Do not convert `DRAFT_CANDIDATE` or `DETERMINISTIC_PASS` into `MERGED_DETERMINISTIC_SUBTREE` without exact target-branch readback. Do not convert deterministic or package-presence evidence into live evidence.

## Program State Machine

```text
SOURCE_PROPOSAL_BOUND
→ METHOD_BOUND
→ RUNTIME_CONTRACT_BOUND
→ TRANSPORT_AND_IDENTITY_BOUND
→ WORKFLOW_BOUND
→ EFFECT_BOUND
→ ROUTE_AND_SANDBOX_BOUND
→ INDEPENDENT_VERIFICATION_BOUND
→ PHYSICAL_CANARY_EXECUTED
→ HUMAN_ADMITTED
→ RELEASED | ROLLED_BACK
```

Current deterministic admission has reached:

```text
runtime contracts / transport / identity       MERGED_DETERMINISTIC_SUBTREE
workflow / effect                               MERGED_DETERMINISTIC_SUBTREE
independent technical verification              MERGED_DETERMINISTIC_SUBTREE
route / browser / gVisor                        MERGE_REVIEW_REQUIRED
physical local→cloud→local                      NOT_EXERCISED
Human release                                   NOT_PERFORMED
```

Each transition requires its own exact subject and evidence owner. A later-stage PASS cannot backfill an earlier missing subject.

## Git and Process DAG laws

- Process prerequisites across repositories are represented by exact commit/tree/schema/digest bindings, not fake cross-repository Git ancestry.
- A true child consumes named unmerged parent bytes.
- Path-disjoint leaves remain siblings.
- A convergence PR may absorb exact sibling blobs, but must verify byte identity and rerun the complete denominator.
- After convergence lands, absorbed leaf PRs close as superseded rather than being merged a second time.
- Main movement invalidates old mergeability and old exact-head conclusions until the current subject is reread.
- Never force-push away failed-head history merely to make a Stack look clean.

## Merge-review rules

Before recommending or performing merge:

1. read current PR state, base, head, mergeability and Draft state;
2. read exact-head required checks and distinguish PASS from SKIPPED;
3. inspect unresolved review threads and comments;
4. inspect changed paths for overlapping writer leases;
5. verify the evidence ceiling and all `NOT_EXERCISED` lanes;
6. choose the minimal convergence path to avoid duplicate merging;
7. retarget/restack children only after their exact parent is admitted;
8. rerun checks after every base movement;
9. preserve a rollback subject;
10. update Issues and the Local Handoff Queue after admission.

Do not self-approve an owner-authored PR. A merge request from the repository owner authorizes merge execution, but does not waive exact-subject or CI gates.

## Close rules

Close an implementation issue as `completed` only when its acceptance bytes are on the admitted branch. Close a leaf PR without merge only when an admitted convergence PR contains and verifies its exact bytes. Keep parent Issues open when live, semantic, Human, release or rollback criteria remain.

Historical PRs may close as `superseded`; retain their failed heads/runs in documentation or comments.

## Evidence non-substitution laws

```text
mergeable                       != merged
CI green                        != live runtime
ACK                             != task success
workflow complete               != effect commit
provider observation            != user result
API                             != browser
local sandbox                   != gVisor isolation
hash declaration                != byte readback
technical verifier agreement    != semantic support/refutation
fixture Human record            != Human decision
merged deterministic subtree    != physical product loop
```

## Current merged deterministic planes

### Runtime

```text
ed3c/runtime-env main
baa4ce25d32a9fb4383ea8bc3530f9fd80be9ae7
tree 117901dbd77cc93993ddc388682b7ab26a00d544
```

Contract, local durable transport semantics, NATS adapter contract, identity/policy semantics, README/AGENTS/Stack and Local Handoff are admitted. Physical transport #73 and live identity #83 remain open through parents #58/#59.

### Workflow and Effect

```text
ed3c/bettor-arena main
74d1e75c61589dcd163c7412e1345f726781ffb4
tree 0de94032a3227ad04dde52f138041294ef9cb810
```

Workflow contract/reducer/operational siblings/matrix/docs and Effect contract/reducer/policy/provider-readback/compensation/matrix/docs are admitted. Parent #184/#185 remain open for live engine/effect evidence; #223 remains the reversible live-effect frontier.

### Independent verification

The `truth-verify-loop` deterministic subtree is admitted through PRs #29, #39, #44 and #45. Its technical result remains `UNVERIFIABLE` until the existing semantic plane independently closes the exact claim. Parent `truth-verify-loop#22` remains open for real physical evidence.

## Current merge-review frontier

Only the Agent Shield deterministic families remain in current-main merge review:

```text
route
#162 → #166 → #167
absorb #163/#164/#165

gVisor
#174 → #177 → #178
absorb #175/#176

shared non-promoting candidate
#180
```

Current Agent Shield main is `30e12cc917503b56b002aa7351428811f20fea8e` / tree `6f465f936515d81ed51c5b80595de530593f25fc`.

Historical green checks are preparation evidence only. Restack or retarget each minimal convergence path to current main, rerun exact-head checks, then close absorbed leaves after admission.

Do not merge live placeholder Issues or create ceremonial live branches for:

- physical NATS reconnect;
- workload identity enrollment/revocation;
- live API/browser route;
- real runsc/gVisor isolation;
- external effect/readback;
- live durable-workflow engine;
- physical local→cloud→local canary.

## Shadow stop conditions

Stop and hand off when the next action requires:

- credentials or signed-in browser/session state;
- provider billing, trust-domain enrollment or secret resolution;
- target terms/egress approval;
- real external write or compensation;
- destructive cleanup;
- private-source access;
- Human semantic adjudication;
- production release or rollback.

Use `local-handoff-queue.md` and update the owning Issue with exact input subjects, commands, expected receipts, failure cases and cleanup criteria. Do not self-approve.

## Definition of done for this directory

- README accurately maps directory/state/DAG/data flow;
- Stack index is valid JSON and distinguishes merged/candidate/live/Human states;
- merge-review decisions preserve supersession and failure history;
- Local Handoff queue names one owner per terminal task;
- no document grants itself task/effect/provider/Human/release authority;
- a verifier rejects evidence-ceiling widening and false physical closure.
