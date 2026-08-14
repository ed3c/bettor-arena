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

Human
  = semantic conflict, merge/ship, provider activation, promotion and rollback authority
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

## Directory map

| File | Owner | Purpose | Authority |
|---|---|---|---|
| [`README.md`](README.md) | repository Git governance | route, State Machine and data flow | navigation |
| [`REPO_PROFILE.md`](REPO_PROFILE.md) | repository owner | branches, remotes, policies, receipts and Human boundaries | repository policy |
| [`PDF_TERMINAL_SEQUENCE.md`](PDF_TERMINAL_SEQUENCE.md) | #61/#102 queue owner | full ordered PDF completion queue and directory/data-flow map | human queue view |
| [`pdf-terminal-sequence.schema.json`](pdf-terminal-sequence.schema.json) | queue contract owner | closed shape for orders 0–25 | machine contract |
| [`pdf-terminal-sequence.json`](pdf-terminal-sequence.json) | queue owner | active item, prerequisites, paths, branches, acceptance and Human bounds | current reviewed queue |
| [`STACKED_PRS.md`](STACKED_PRS.md) | Stack topology owner | dependency-driven branch graph and expected branches | human topology view |
| [`WORKER_PROTOCOL.md`](WORKER_PROTOCOL.md) | task/lease owner | one Worker/worktree/branch/path lease | execution contract |
| [`GIT_TOWN_ADMISSION.md`](GIT_TOWN_ADMISSION.md) | trusted operator | executable/config/license/SBOM/legal/live gates | mutable admission ledger |
| [`stack-prs.index.schema.json`](stack-prs.index.schema.json) | historical snapshot contract | machine shape for observed PR graph | machine contract |
| [`stack-prs.index.json`](stack-prs.index.json) | generated/reviewed historical snapshot | observed GitHub graph and lineage | snapshot only |

Full historical human index: [`../traceability/STACK_PR_INDEX.md`](../traceability/STACK_PR_INDEX.md).

## Ordered completion State Machine

```text
PDF GAP INVENTORY
→ EXISTING ISSUE/PR SUBJECTS RESOLVED
→ MISSING TERMINALS CREATED
→ STRICT GLOBAL COMPLETION ORDER DECLARED
→ ONE ACTIVE TERMINAL
→ TASK PACKET + PATH LEASE
→ IMPLEMENT / CONTROL / MUTATION / CLEANUP
→ EXACT-HEAD PUBLICATION CANDIDATE
→ HUMAN REVIEW
→ QUEUE ADVANCE
→ FINAL CONVERGENCE #68
```

Current stopping point:

```text
program                        #61
queue index task               #102
active order                   0
active issue                   #82
future implementation branches NOT_CREATED until activation
final convergence              #68
```

Queue order and ancestry are separate. Global completion is serial; branch topology follows real byte dependency. A true child consumes unmerged parent bytes. Path-disjoint work starts from the updated `main` after its predecessor lands.

## Git Town runtime State Machine

```text
SHARED_METHOD_PINNED
→ REPO_PROFILE_VALIDATED
→ EXECUTABLE / LICENSE / SBOM / CONFIG ADMISSION
→ ISOLATED STACK FIXTURE
→ DRY-RUN NO-PUSH
→ LIVE LOCAL NO-PUSH
→ REPOSITORY EVALS
→ GITHUB PUBLICATION GATE
→ HUMAN ADMIT
→ MERGE / SHIP / ROLLBACK
```

Current runtime state:

```text
SHARED_METHOD_PINNED       PASS
REPO_PROFILE_VALIDATED     IMPLEMENTED
ORDERED_QUEUE_INDEXED      candidate in issue #102
GIT_TOWN_EXECUTABLE        ABSENT
GIT_TOWN_CONFIG            ABSENT
LOCAL_NO_PUSH_SYNC         NOT_EXERCISED
PUBLICATION                NOT_EXERCISED
HUMAN_ADMIT                NOT_PERFORMED
runtime admission owner    issue #101
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
| Human edge | evidence + conflict + review | merge/reject/rollback/waiver | `PENDING` |

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
Human review
        ↓
next active terminal
        ↓
#68 final composition/release
```

Git Town never replaces GitHub publication admission, module proof, LoopX state authority or Human governance.

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

## Resolved duplicate and active residue

PR #76 and PR #77 both implemented issue #64 over overlapping Worker Gateway paths. The owner admitted #76 and closed #77 as `SUPERSEDED_CANDIDATE`.

The conflict remains recorded as `RESOLVED_BY_HUMAN`. Issue #82 is now active and must compare the eight PR #77-only files by execution, then fold or reject each with a reason.

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

## Evidence and receipts

Current evidence:

```text
GitHub base/head/state/check and reachability metadata
repository bytes
ordered queue and historical Stack snapshots
zero-network verifiers
planted mutations
```

Not yet available:

```text
Git Town version/checksum/license/SBOM receipt
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
- automatic semantic conflict resolution;
- push/merge/ship/close/delete;
- remote, credential or permission mutation;
- provider/runtime/model activation outside its Human boundary;
- production promotion or rollback;
- rewriting historical evidence.

## Human Admit boundary

Human or trusted operator owns:

```text
Git Town executable and legal admission
semantic conflict resolution
continue / skip / undo
remote publication
PR retargeting
merge / ship / close / delete
provider/model/runtime/credential activation
scoped queue waiver
promotion
rollback
```

Current queue base is recorded in [`pdf-terminal-sequence.json`](pdf-terminal-sequence.json); GitHub remains current-state authority.
