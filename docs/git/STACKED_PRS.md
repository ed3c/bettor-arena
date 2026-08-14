# Bettor Arena molecular Stacked PR topology

## Authority

GitHub base/head/state/check metadata is publication truth. This document is a snapshot and must be refreshed whenever a PR base, head, state, mergeability, check or reachability changes.

```text
observed_at: 2026-08-14T08:44:56Z
main: 10380005fa485d6035539589c01b9f740acff15d
canonical shared method:
  ed3c/skills-shared@c5750720d960a228a0d9419f28125c09d064e3e1
  skills/git-town-stacked-pr-worker/SKILL.md
```

No Git Town executable or `.git-town.toml` is admitted. The graph below is derived from GitHub metadata, not `git town` output.

## Relation vocabulary

```text
sibling
  independent, path-disjoint leaves based on the same settled subject

true child
  consumes unmerged parent bytes and targets the parent branch

terminal
  one reviewable behavior plus positive/control/mutation evidence

convergence
  owns shared composition, generated indexes, live matrix and final acceptance

merged-to-parent
  child bytes entered a feature parent but are not reachable from main

superseded candidate
  historical or duplicate implementation that must not be merged as-is
```

## Documentation and Git governance Stack

```text
main @ 10380005fa485d6035539589c01b9f740acff15d
└─ PR #60 feat/pdf-loopx-modular-verifier-v1
   head ffbcd91a9eae1f6171fc7c42f0300bb83fac1b90
   OPEN / mergeable / exact-head checks PASS
   └─ issue #80 feat/git-town-stack-governance-v1
      true-child terminal
      PR NOT_CREATED at this snapshot
```

Issue #80 changes the same routed root documentation introduced by #60, so it is a true child rather than a path-overlapping sibling.

## LoopX Contract and terminal candidate Stack

```text
main @ 10380005fa485d6035539589c01b9f740acff15d
└─ PR #74 feat/loopx-contract-v1
   issue #62
   head 2fd05408f585f6b8999a7922d4995d8379795eb2
   OPEN / mergeable
   checks:
     Modular contracts                  PASS
     PDF Harness integration audit      PASS
     LoopX Contract v1                  PASS
     LoopX Ledger v1                    PASS
     knowledge-provider gates           PASS
   │
   ├─ PR #75 feat/loopx-ledger-v1
   │  issue #63
   │  MERGED_TO_PARENT at 2fd05408f585f6b8999a7922d4995d8379795eb2
   │  NOT_REACHABLE_FROM_MAIN
   │
   ├─ PR #76 feat/loopx-worker-gateway-v1
   │  issue #64
   │  head 60caac70f75b1f214b2ce05f2c37a5f2b85a9268
   │  OPEN / non-mergeable metadata
   │  exact-head Worker/Modular/PDF checks PASS
   │
   ├─ PR #77 feat/loopx-worker-gateway-terminal-v1
   │  issue #64
   │  head 8778b3dd16dceccc7d3904f954a2ade249fce468
   │  OPEN / non-mergeable metadata
   │  exact-head Modular/PDF checks PASS
   │
   ├─ PR #78 feat/loopx-decision-memory-v1
   │  issue #42
   │  head 166e0ee4ca69690f9e7da46b14d5452bc25df4b8
   │  OPEN / non-mergeable metadata
   │  exact-head Decision-Memory/Modular/PDF checks PASS
   │
   └─ PR #79 feat/loopx-code-truth-graph-v2
      issue #69
      head 371083a4baeda129434aea2ebad538dde8004f07
      OPEN / non-mergeable metadata
      exact-head CTG-v2/Modular/PDF checks PASS
```

## Blocking duplicate terminal

PR #76 and PR #77 are not parallel-safe:

```text
same owner issue:
  #64

same parent:
  feat/loopx-contract-v1

overlapping paths:
  .arena/modules/loopx-worker-gateway/**
  loop_wiki/loopx-worker-gateway/**
  generated modular projections
  loopctl/workflow.lock

state:
  BLOCKED_DUPLICATE_TERMINAL
```

Green focused checks do not resolve duplicate authority. Human options are:

```text
select one leaf
extract unique delta into a new path-disjoint leaf
rebase one as an explicit child
mark one superseded
close one
```

No Agent may choose or execute the resolution.

## Remaining LoopX program leaves

Parent program: issue #61.

| Order | Issue | Terminal behavior | Current publication state |
|---:|---:|---|---|
| 1 | #62 / PR #74 | LoopX task contracts | `OPEN CANDIDATE` |
| 2 | #63 / PR #75 | append-only ledger/reducer | `MERGED_TO_PARENT`, not main |
| 3 | #64 / PRs #76/#77 | six-host Worker Gateway | `BLOCKED_DUPLICATE_TERMINAL` |
| 4 | #65 | Strategy Graph + HITL | `PR ABSENT` |
| 5 | #42 / PR #78 | decision-memory admission | `OPEN CANDIDATE` |
| 6 | #66 | runtime fabric/local-cloud parity | `PR ABSENT` |
| 7 | #69 / PR #79 | Code Truth Graph v2 | `OPEN CANDIDATE` |
| 8 | #70 | Notes Repo → Scaffold | `PR ABSENT` |
| 9 | #71 | Code → Knowledge fold-back | `PR ABSENT` |
| 10 | #72 | Skill/prompt evolution | `PR ABSENT` |
| 11 | #67 | observability/signed HITL projection | `PR ABSENT` |
| 12 | #68 | final shared convergence | `BLOCKED_BY_TERMINALS` |

Only #68 may select all settled terminal modules in the shared composition, regenerate final shared indexes, run the required live matrix and record Human promotion/rollback.

## Separate provider and historical lanes

```text
PR #56
  provider admission evaluation
  separate from LoopX terminal Stack
  fixture results cannot prove live provider health

PR #53
  historical portable-Skill aggregate
  not current integration authority
  unique delta must be extracted before any Human close or merge decision

PR #58
  runtime-env / Agent Shield documentation audit
  separate documentation lane
```

These lanes must not be silently inserted into the LoopX parent chain.

## Work packet for issue #80

```yaml
parent_issue: 61
terminal_issue: 80
base_branch: feat/pdf-loopx-modular-verifier-v1
parent_branch: feat/pdf-loopx-modular-verifier-v1
head_branch: feat/git-town-stack-governance-v1
class: true-child terminal
allowed_paths:
  - README.md
  - AGENTS.md
  - CLAUDE.md
  - docs/git/**
  - docs/README.md
  - docs/INDEX.md
  - docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md
  - docs/architecture/STATE_MACHINES.md
  - docs/architecture/agent-entrypoints.contract.json
  - docs/traceability/STACK_PR_INDEX.md
  - .arena/contexts/macro.json
  - scripts/gates/check_git_town_stack_docs.py
  - tests/test_git_town_stack_docs.py
  - .github/workflows/git-town-stack-docs.yml
  - workflow-generated modular projections
non_goals:
  - Git Town installation/configuration
  - sync/push/merge/ship
  - semantic conflict resolution
  - LoopX/runtime/provider code changes
rollback_subject: ffbcd91a9eae1f6171fc7c42f0300bb83fac1b90
human_owned:
  - conflict resolution
  - PR retargeting
  - merge/ship/close/delete
  - executable/legal admission
  - promotion and rollback
```

## Publication State Machine

```text
ISSUE + TASK PACKET
→ BRANCH GRAPH VALIDATION
→ LINKED WORKTREE / BRANCH / PATH LEASE
→ TERMINAL IMPLEMENTATION
→ POSITIVE + CONTROL + MUTATION
→ EXACT-HEAD GITHUB CHECKS
→ OPTIONAL PARENT RESTACK
→ CONVERGENCE LEAF
→ HUMAN ADMIT
→ MERGE / SHIP / ROLLBACK
```

A future admitted Git Town executable may automate local hierarchy synchronization only. It cannot own GitHub publication or Human decisions.

## Required evidence chain

```text
source proposal or incident
→ architecture decision
→ parent issue
→ terminal issue
→ task packet and path lease
→ branch / PR / exact head
→ positive + control + mutation
→ generated locks/indexes
→ runtime/host receipt where applicable
→ convergence index
→ Human Admit
```

Missing links remain `ABSENT`.

## Refresh protocol

When a Stack fact changes:

1. fetch current `main`;
2. fetch every affected PR base/head/state/mergeability;
3. check main reachability for merged children;
4. fetch exact-head workflow conclusions;
5. recompute active path overlap;
6. update this document;
7. update [`stack-prs.index.json`](stack-prs.index.json);
8. update [`../traceability/STACK_PR_INDEX.md`](../traceability/STACK_PR_INDEX.md);
9. rerun the deterministic gate;
10. do not merge or ship without Human Admit.
