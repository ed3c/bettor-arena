# Bettor Arena molecular Stacked PR topology

## Authority

GitHub base/head/state/check metadata is publication truth. This document is a snapshot and must be refreshed whenever a PR base, head, state, mergeability, check or reachability changes.

```text
observed_at: 2026-08-14T09:33:48Z
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
   └─ PR #81 feat/git-town-stack-governance-v1
      issue #80; true-child terminal
      observed head 857b6239b5faaff12910b37b73c32e5121b4f291
      OPEN DRAFT / MERGEABLE
      Modular contracts PASS; focused Git Town job skipped while Draft
```

Issue #80 changes the same routed root documentation introduced by #60, so it is a true child rather than a path-overlapping sibling.

## LoopX Contract and terminal candidate Stack

```text
main @ ea8c4a101bcf44ffe54c78ef53da583afa9efad2
└─ PR #74 feat/loopx-contract-v1
   issue #62
   head 0731b667d0832c49b7844d7a2788c435518a654f
   MERGED_TO_MAIN at d194df1ad7a9e114dab1952d2be57fdf86b7b44d
   checks at that head:
     Modular contracts                  PASS
     PDF Harness integration audit      PASS
     LoopX Contract v1                  PASS
     LoopX Ledger v1                    PASS
     knowledge-provider gates           PASS
   │
   ├─ PR #75 feat/loopx-ledger-v1
   │  issue #63
   │  head 8fa52730754c49da3128474423ddbc75007c5ae4
   │  MERGED_TO_MAIN via #74
   │
   ├─ PR #76 feat/loopx-worker-gateway-v1
   │  issue #64
   │  head 4ebdfdfb0e20b9177b2e11834c49af41b3bbd228
   │  MERGED_TO_MAIN via #74
   │
   ├─ PR #77 feat/loopx-worker-gateway-terminal-v1
   │  issue #64
   │  head fa2c120ee573c1991ef60e0b8ac3dee3c645f92e
   │  SUPERSEDED_CANDIDATE — closed unmerged; see the duplicate record below
   │
   ├─ PR #78 feat/loopx-decision-memory-v1
   │  issue #42
   │  head 1f0eb3acef73b9b22bf71f886a28b5363a09cc9c
   │  MERGED_TO_MAIN via #74
   │
   └─ PR #79 feat/loopx-code-truth-graph-v2
      issue #69
      head 966e74fa11fac99b4a0eeb5cf8c7d80aeaa8d10c
      MERGED_TO_MAIN via #74
```

Every child here landed into `feat/loopx-contract-v1` first and reached `main`
only when #74 itself merged. A child reporting `merged=true` against a feature
parent stays `NOT_ON_MAIN` until that parent lands; the two states were
genuinely different for several hours on 2026-08-14.

## Resolved duplicate terminal

PR #76 and PR #77 were not parallel-safe:

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
  RESOLVED_BY_HUMAN on 2026-08-14
```

Green focused checks did not resolve duplicate authority; the owner did. The
options were:

```text
select one leaf
extract unique delta into a new path-disjoint leaf
rebase one as an explicit child
mark one superseded
close one
```

What was chosen: #76, the 82-file implementation, was admitted and reached
`main`; #77, a separate 19-file implementation of the same module, was closed as
`SUPERSEDED_CANDIDATE`. Merging both would have left the module with two
`module.json` declarations (`aggregate` versus `provider`) and two selftest
entrypoints. The 8 files that exist only on #77 — the host-descriptor schema and
registry, `gateway_engine.py`, `gateway_selftest.py`, `check_contracts.py` and
three fixtures — are tracked in issue #82 rather than discarded.

The record stays after resolution on purpose: an index that simply dropped the
conflict would be indistinguishable from one that never detected it.

No Agent may choose or execute the resolution.

## Remaining LoopX program leaves

Parent program: issue #61.

| Order | Issue | Terminal behavior | Current publication state |
|---:|---:|---|---|
| 1 | #62 / PR #74 | LoopX task contracts | `MERGED_TO_MAIN` |
| 2 | #63 / PR #75 | append-only ledger/reducer | `MERGED_TO_MAIN` via #74 |
| 3 | #64 / PRs #76/#77 | six-host Worker Gateway | #76 `MERGED_TO_MAIN`; #77 `SUPERSEDED_CANDIDATE`, delta in #82 |
| 4 | #65 | Strategy Graph + HITL | `PR ABSENT` |
| 5 | #42 / PR #78 | decision-memory admission | `MERGED_TO_MAIN` via #74 |
| 6 | #66 | runtime fabric/local-cloud parity | `PR ABSENT` |
| 7 | #69 / PR #79 | Code Truth Graph v2 | `MERGED_TO_MAIN` via #74 |
| 8 | #70 | Notes Repo → Scaffold | `PR ABSENT` |
| 9 | #71 | Code → Knowledge fold-back | `PR ABSENT` |
| 10 | #72 | Skill/prompt evolution | `PR ABSENT` |
| 11 | #67 | observability/signed HITL projection | `PR ABSENT` |
| 12 | #68 | final convergence | `BLOCKED_BY_TERMINALS` |

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
  unique delta must be extracted before any Human merge decision

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

## Publication state machine

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
