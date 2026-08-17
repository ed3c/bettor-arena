# Git Town Stacked-PR governance

## Role

This directory is the **repository-owned adoption and queue layer** for the canonical shared `git-town-stacked-pr-worker` method.

```text
shared Skill
  = reusable Git Town / stacked-PR procedure and eval contract

docs/git/
  = Bettor repository profile, ordered queue, task/path-lease policy,
    historical Stack snapshots and runtime admission state

Git Town
  = optional admitted local branch hierarchy and no-push synchronization engine

GitHub
  = publication/base/head/check authority

LoopX
  = canonical task-state authority

Automated admission controller
  = exact-subject push, merge/ship, queue, provider activation, promotion and rollback authority
```

Bettor does not copy a local `skills/git-town-stacked-pr-worker/SKILL.md`.

## Canonical shared method subject

```text
repository: ed3c/skills-shared
commit:     c5750720d960a228a0d9419f28125c09d064e3e1
blob:       eb2d915bca3e8a3938625f7d33a10fae95a15769
path:       skills/git-town-stacked-pr-worker/SKILL.md
```

Current consumer selection: `NOT_SELECTED`.

The current Bettor binding source `skills-shared@b3c722da1c40301b0a12e0ef99848d884bfc720b` resolves this path to the same blob. That proves byte-equivalent source availability, not selection into Bettor's runtime closure.

## Directory map

| File | Owner | Purpose | Authority |
|---|---|---|---|
| [`README.md`](README.md) | repository Git governance | route, State Machine and data flow | navigation |
| [`REPO_PROFILE.md`](REPO_PROFILE.md) | repository owner | branches, remotes, policies, receipts and automation boundaries | repository policy |
| [`PDF_TERMINAL_SEQUENCE.md`](PDF_TERMINAL_SEQUENCE.md) | #61/#102 queue owner | full ordered PDF completion queue and directory/data-flow map | human queue view |
| [`pdf-terminal-sequence.schema.json`](pdf-terminal-sequence.schema.json) | queue contract owner | closed shape for orders 0–25 | machine contract |
| [`pdf-terminal-sequence.json`](pdf-terminal-sequence.json) | queue owner | active item, prerequisites, paths, branches, acceptance and automation bounds | current reviewed queue |
| [`STACKED_PRS.md`](STACKED_PRS.md) | Stack topology owner | dependency-driven branch graph and expected branches | human topology view |
| [`WORKER_PROTOCOL.md`](WORKER_PROTOCOL.md) | task/lease owner | one Worker/worktree/branch/path lease | execution contract |
| [`GIT_TOWN_ADMISSION.md`](GIT_TOWN_ADMISSION.md) | trusted operator | executable/config/license/SBOM/legal/live gates | mutable admission ledger |
| [`stack-prs.index.schema.json`](stack-prs.index.schema.json) | historical snapshot contract | machine shape for observed PR graph | machine contract |
| [`stack-prs.index.json`](stack-prs.index.json) | generated/reviewed historical snapshot | observed GitHub graph and lineage | snapshot only |

Full historical human index: [`../traceability/STACK_PR_INDEX.md`](../traceability/STACK_PR_INDEX.md).

## State Machine

### Ordered completion

```text
PDF GAP INVENTORY
→ EXISTING ISSUE/PR SUBJECTS RESOLVED
→ MISSING TERMINALS CREATED
→ STRICT GLOBAL COMPLETION ORDER DECLARED
→ ONE ACTIVE TERMINAL
→ TASK PACKET + PATH LEASE
→ IMPLEMENT / CONTROL / MUTATION / CLEANUP
→ EXACT-HEAD PUBLICATION CANDIDATE
→ AUTOMATED ADMISSION
→ QUEUE ADVANCE
→ FINAL CONVERGENCE #68
```

Current stopping point:

```text
program                        #61
queue index task               #102
completed prefix               orders 0–11
active order                   12
active issue                   #92
final convergence              #68
```

Queue order and ancestry are separate. Global completion is serial; branch topology follows real byte dependency. A true child consumes unmerged parent bytes. Path-disjoint work starts from the updated `main` after its predecessor lands.

### Git Town runtime

```text
SHARED_METHOD_PINNED
→ REPO_PROFILE_VALIDATED
→ EXECUTABLE / LICENSE / SBOM / CONFIG ADMISSION
→ ISOLATED STACK FIXTURE
→ DRY-RUN NO-PUSH
→ LIVE LOCAL NO-PUSH
→ REPOSITORY EVALS
→ GITHUB PUBLICATION GATE
→ AUTOMATED ADMISSION
→ MERGE / SHIP / ROLLBACK
```

Current runtime state:

```text
SHARED_METHOD_PINNED       PASS
REPO_PROFILE_VALIDATED     IMPLEMENTED
ORDERED_QUEUE_INDEXED      IMPLEMENTED; active order derived from machine queue
CONTROLLER_MECHANISM       IMPLEMENTED by PR #133
PHYSICAL_CONTROLS          PASS: 13 real-repository controls
GIT_TOWN_EXECUTABLE        ABSENT
GIT_TOWN_CONFIG            ABSENT
LOCAL_NO_PUSH_SYNC         NOT_EXERCISED
PUBLICATION                NOT_EXERCISED
AUTOMATION_POLICY          ADMITTED; exact runtime operation remains subject-bound
admission mechanism owner  issue #101 / PR #133; executable activation unresolved
```

## Inputs and outputs

| Stage | Inputs | Output | Failure state |
|---|---|---|---|
| Method pin | exact repository/commit/path/blob | immutable method reference | `ABSENT` / `DRIFT` |
| Repo profile | repository identity + policies | closed profile | `PROFILE_INVALID` |
| Ordered queue | PDF gaps + issue/PR facts | orders 0–25 | `GAP`, `DUPLICATE`, `ORDER_INVALID` |
| Task packet | active order, issue, paths, evals, rollback | accepted work packet | `PACKET_INVALID` |
| Branch graph | current main + byte dependencies | root/sibling/true-child/convergence relation | `STALE`, `UNKNOWN_PARENT`, `PATH_OVERLAP` |
| Lease | linked worktree + branch + path allowlist | exclusive Worker lease | `LEASE_CONFLICT` |
| Terminal eval | positive + control + mutation + cleanup | candidate receipt | `FAIL` |
| Publication | exact head + GitHub checks | review candidate | `BLOCKED`, `NOT_EXERCISED` |
| Automation edge | evidence + conflict policy + exact-head readback | merge/reject/rollback/waiver receipt | `BLOCKED_POLICY` |

## Data flow

```text
PDF source proposal + current GitHub/repository facts
        ↓
program #61 + machine queue
        ↓
active issue/task packet + path lease
        ↓
dependency-driven branch relation
        ↓
linked worktree and single writer
        ↓
implementation + positive/control/mutation
        ↓
bounded artifacts + cleanup + rollback receipt
        ↓
exact-head GitHub publication checks
        ↓
queue advancement candidate
        ↓
automated admission
        ↓
next active terminal
        ↓
#68 final composition/release
```

Git Town never replaces GitHub publication admission, module proof, LoopX state authority or the automated-admission controller.

## Stable outcomes

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
MERGED_TO_MAIN
MERGED_TO_PARENT
ACTIVE
BLOCKED_BY_PREDECESSOR
FINAL_CONVERGENCE
SUPERSEDED_CANDIDATE
NOT_CREATED
```

## Resolved duplicate and current head

PR #76 and PR #77 both implemented issue #64 over overlapping Worker Gateway paths. The owner admitted #76 and closed #77 as `SUPERSEDED_CANDIDATE`.

The conflict remains recorded as `RESOLVED_BY_HUMAN`. Issue #82 and queue order 0 are `COMPLETE`; the active head is issue #92 at order 12. Keeping the #76/#77 record prevents later success from erasing evidence that duplicate writers once existed.

## Public call surfaces

Ordered queue gate:

```sh
python3 scripts/gates/check_pdf_terminal_sequence.py
python3 scripts/gates/check_pdf_terminal_sequence.py --selftest
python3 -m unittest -q tests/test_pdf_terminal_sequence.py
```

Historical governance gate:

```sh
python3 scripts/gates/check_git_town_stack_docs.py
python3 scripts/gates/check_git_town_stack_docs.py --selftest
python3 -m unittest -q tests/test_git_town_stack_docs.py
```

Neither gate executes Git Town.

The repository-owned runtime controller has a separate executable gate:

```sh
sh tests/git-town/run-all.sh
```

It verifies the typed controller, fail-closed absence lane and 13 physical controls without claiming a Git Town execution.

## Evidence and receipts

Current evidence:

```text
GitHub base/head/state/check and reachability metadata
repository bytes
ordered queue and historical Stack snapshots
zero-network verifiers
planted mutations
typed Git Town controller contracts and 13 physical controls
```

Not yet available:

```text
Git Town executable version/checksum/license/SBOM receipt
admitted .git-town.toml
dry-run/live local no-push receipt
publication canary
runtime rollback receipt
```

## Allowed changes

- repository profile and Stack/queue policy;
- issue/PR snapshot refresh;
- deterministic verifier and planted controls;
- Agent/document/Context routes;
- current active terminal bytes under its declared path lease;
- generated modular projections through admitted workflows.

## Forbidden changes

- local copy or shadow of the shared Skill;
- future terminal branch before queue activation;
- `.git-town.toml` before admission;
- raw shell or arbitrary Git command execution;
- semantic conflict resolution without a deterministic winner declared by policy;
- raw push/merge/ship/close/delete outside the admitted controller;
- remote, credential or permission mutation;
- provider/runtime/model activation outside its typed policy boundary;
- production promotion or rollback outside its exact-subject controller;
- rewriting historical evidence.

## Automated admission boundary

The typed automated-admission controller owns:

```text
Git Town executable and legal admission
machine-resolvable conflict handling with a declared deterministic winner
bounded continue / skip / undo declared by the controller contract
remote publication
PR retargeting
merge / ship / close / delete
provider/model/runtime/credential activation
scoped queue waiver
promotion
rollback
```

Every operation binds an exact subject, emits a durable receipt and performs remote
readback. Missing inputs produce `BLOCKED_POLICY`; the Agent does not request a
routine confirmation prompt. See [`AUTOMATED_ADMISSION.md`](AUTOMATED_ADMISSION.md).

Current queue base is recorded in [`pdf-terminal-sequence.json`](pdf-terminal-sequence.json); GitHub remains current-state authority.
