# Git Town Stacked-PR governance

## Role

This directory is the **repository-owned adoption layer** for the canonical shared `git-town-stacked-pr-worker` method.

```text
shared Skill
  = reusable procedure and eval contract

docs/git/
  = Bettor repository profile, task/lease policy, Stack index and admission state

Git Town
  = optional branch hierarchy and deterministic local sync engine

GitHub
  = publication/base/head/check authority

Human
  = semantic conflict, merge/ship, promotion and rollback authority
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
| [`REPO_PROFILE.md`](REPO_PROFILE.md) | repository owner | perennial branches, remotes, policies, receipts and Human boundaries | repository policy |
| [`STACKED_PRS.md`](STACKED_PRS.md) | Stack topology owner | sibling/child/terminal/convergence graph and current conflicts | human Stack snapshot |
| [`WORKER_PROTOCOL.md`](WORKER_PROTOCOL.md) | task/lease owner | one Worker/worktree/branch/path lease and stable outcomes | execution contract |
| [`GIT_TOWN_ADMISSION.md`](GIT_TOWN_ADMISSION.md) | trusted operator | executable/config/license/SBOM/legal/live admission gates | mutable admission ledger |
| [`stack-prs.index.schema.json`](stack-prs.index.schema.json) | contract owner | machine shape for the Stack snapshot | machine contract |
| [`stack-prs.index.json`](stack-prs.index.json) | generated/reviewed snapshot | exact observed GitHub graph and blockers | snapshot only |

The historical human index remains [`../traceability/STACK_PR_INDEX.md`](../traceability/STACK_PR_INDEX.md).

## State Machine

```text
SHARED_METHOD_PINNED
→ REPO_PROFILE_VALIDATED
→ TASK_PACKET_ACCEPTED
→ BRANCH_GRAPH_VALIDATED
→ WORKTREE / BRANCH / PATH LEASED
→ DRY_RUN_REQUIRED
→ LOCAL_SYNC_CANDIDATE
→ EVAL_REPLAYED
→ PUBLICATION_CANDIDATE
→ HUMAN_ADMIT
→ MERGE / SHIP / ROLLBACK
```

Current stopping point:

```text
SHARED_METHOD_PINNED       PASS
REPO_PROFILE_VALIDATED     candidate in issue #80
STACK_GRAPH_INDEXED        candidate in issue #80
GIT_TOWN_EXECUTABLE        ABSENT
GIT_TOWN_CONFIG            ABSENT
LOCAL_SYNC                 NOT_EXERCISED
PUBLICATION                NOT_EXERCISED
HUMAN_ADMIT                NOT_PERFORMED
```

## Inputs and outputs

| Stage | Inputs | Output | Failure state |
|---|---|---|---|
| Method pin | exact repository/commit/path/blob | immutable method reference | `ABSENT` / `DRIFT` |
| Repo profile | repository identity + policies | closed profile | `PROFILE_INVALID` |
| Task packet | issue, base/parent/head, paths, evals, rollback | accepted work packet | `PACKET_INVALID` |
| Stack graph | current GitHub PR metadata | DAG + relations | `CYCLE`, `STALE`, `UNKNOWN_PARENT` |
| Lease | linked worktree + branch + path allowlist | exclusive Worker lease | `LEASE_CONFLICT` |
| Dry run | admitted Git Town executable/config | local sync plan | `NOT_EXERCISED`, `CONFLICT` |
| Eval | positive + hollow/mutation + exact subject | candidate receipt | `FAIL` |
| Publication | exact head + GitHub admission | PR/check snapshot | `BLOCKED`, `NOT_EXERCISED` |
| Human edge | conflict/review/evidence | merge/ship/reject/rollback decision | `PENDING` |

## Data flow

```text
issue / architecture decision
        ↓
task packet + path lease
        ↓
Stack graph validation
        ↓
linked worktree and branch ownership
        ↓
Git Town dry-run plan                 [future; not exercised]
        ↓
local sync candidate                  [future; no push]
        ↓
repository evals + mutation controls
        ↓
exact-head GitHub publication checks
        ↓
Stack index + evidence receipt
        ↓
Human Admit
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
BLOCKED_DUPLICATE_TERMINAL
SUPERSEDED_CANDIDATE
NOT_CREATED
```

## Current critical conflict

PR #76 and PR #77 both target `feat/loopx-contract-v1`, claim issue #64 and overlap:

```text
.arena/modules/loopx-worker-gateway/**
loop_wiki/loopx-worker-gateway/**
generated modular projections
```

They are not parallel-safe siblings. Current state is `BLOCKED_DUPLICATE_TERMINAL`; only a Human can select, supersede, extract or close a leaf.

## Public call surface

Current deterministic documentation gate:

```sh
python3 scripts/gates/check_git_town_stack_docs.py
python3 scripts/gates/check_git_town_stack_docs.py --selftest
python3 -m unittest -q tests/test_git_town_stack_docs.py
```

There is no admitted `git town` wrapper in this repository.

## Evidence and receipts

Current evidence:

```text
GitHub base/head/state/check metadata
repository bytes
zero-network document/index verifier
planted mutations
```

Not yet available:

```text
Git Town version/checksum/license/SBOM receipt
git town config receipt
dry-run/sync receipt
conflict-preservation canary
publication canary
rollback receipt
```

## Allowed changes

- repository profile and Stack policy;
- issue/PR snapshot refresh;
- deterministic verifier and planted controls;
- Agent/document routes;
- generated modular projections through the admitted sync workflow.

## Forbidden changes

- local copy of the shared Skill;
- `.git-town.toml` before admission;
- raw shell or arbitrary Git command execution;
- automatic semantic conflict resolution;
- push/merge/ship/close/delete;
- remote or credential mutation;
- permission widening;
- production promotion or rollback;
- rewriting historical evidence.

## Human Admit boundary

Human/trusted operator owns:

```text
Git Town executable and legal admission
semantic conflict resolution
continue / skip / undo
remote publication
PR retargeting
merge / ship / close / delete
promotion
rollback
```

Snapshot observed: `2026-08-14T08:44:56Z`. GitHub is the current-state authority.
