# Molecular Stack PR index

## Authority and freshness

GitHub issue/PR base, head, state, mergeability, checks and main reachability are current authority. This Markdown and [`../git/stack-prs.index.json`](../git/stack-prs.index.json) are reviewed snapshots.

```text
observed_at: 2026-08-14T09:33:48Z
current main: 10380005fa485d6035539589c01b9f740acff15d
repository profile: ../git/REPO_PROFILE.md
```

Refresh the snapshot whenever an affected base, head, state, check, reachability or path lease changes.

## Git Town status

```text
.git-town.toml                         ABSENT
.git-town                              ABSENT
git-town-stacked-pr-worker selected    ABSENT / NOT_SELECTED
repository molecular-delivery policy   IMPLEMENTED
Git Town binary/version/checksum       ABSENT
license/SBOM/legal                     NOT_REVIEWED
local sync/publication                 NOT_EXERCISED
```

The repository uses molecular delivery semantics without claiming an admitted Git Town executable.

## Four-repository documentation convergence

Historical merged route leaves retained for compatibility and traceability:

```text
bettor-arena#37
skills-shared#85
runtime-env#30
agent-shield-monorepo#78
bettor-arena#38
integration/pdf-harness-convergence-v1
```

Their current contract flow remains:

```text
skills-shared procedure
+ runtime-env secret-free runtime contract
→ bettor-arena integration/acceptance
→ agent-shield-monorepo reference product/canaries
→ Human promotion or rollback
```

## Modular platform implementation spine

The landed mainline spine includes module catalog, path ownership, closure-scoped proof subjects, Context Capsules, default-deny stateless MCP, transactional project bootstrap, logical origins/browser contracts and documentation convergence. Exact current truth is read from module manifests, `loopctl/contract.json`, locks and receipts rather than this prose.

## Skill, host execution and provider spine

```text
bettor-arena#43 repo-agent-native binding
→ bettor-arena#48 portable Skill compatibility
→ bettor-arena#50 host-owned execution/assertion runner
→ bettor-arena#51 provider-neutral query/memory contracts
→ bettor-arena#53 historical aggregate
→ bettor-arena#56 provider-evaluation lane
```

A merged child or focused fixture PASS cannot establish current-main or live-provider integration by itself.

## Open terminal leaves required by the PDF target

```text
bettor-arena#24 immutable Agent Shield reference-consumer acceptance
LoopX program issues #61–#72
LoopX implementation PRs #74–#81
```

These compatibility headings and tokens preserve the prior PDF audit route. They do not override the current Stack graph below.

## Canonical shared Git Town method

```text
repository: ed3c/skills-shared
commit: c5750720d960a228a0d9419f28125c09d064e3e1
blob: eb2d915bca3e8a3938625f7d33a10fae95a15769
path: skills/git-town-stacked-pr-worker/SKILL.md
```

Bettor owns the repository profile, task packet, path lease, Stack index, evals and Human policy. It does not copy or shadow the shared Skill.

## Relation vocabulary

```text
sibling      path-disjoint independent leaf
true child   consumes unmerged parent bytes
terminal     one behavior plus positive/control/mutation evidence
convergence  shared selection/index/live/release owner
merged-to-parent
             child entered feature parent but is not reachable from main
```

## Documentation and Git governance Stack

```text
main @ 10380005fa485d6035539589c01b9f740acff15d
└─ PR #60 feat/pdf-loopx-modular-verifier-v1
   head ffbcd91a9eae1f6171fc7c42f0300bb83fac1b90
   OPEN / MERGEABLE / exact-head checks PASS
   └─ PR #81 feat/git-town-stack-governance-v1
      issue #80
      TRUE_CHILD documentation/governance terminal
      OPEN / READY FOR REVIEW / UNMERGED
      rollback ffbcd91a9eae1f6171fc7c42f0300bb83fac1b90
```

Issue #80 changes the same routed root documentation as PR #60, so it is a true child rather than a path-overlapping sibling.

## LoopX completion program

Parent: issue #61.  
Final convergence owner: issue #68.

```text
main @ 10380005fa485d6035539589c01b9f740acff15d
└─ PR #74 feat/loopx-contract-v1
   issue #62
   head 2fd05408f585f6b8999a7922d4995d8379795eb2
   OPEN / MERGEABLE / exact-head checks PASS
   │
   ├─ PR #75 feat/loopx-ledger-v1
   │  issue #63
   │  MERGED_TO_PARENT at PR #74 feature head
   │  NOT_ON_MAIN
   │
   ├─ PR #76 feat/loopx-worker-gateway-v1
   │  issue #64
   │  head 60caac70f75b1f214b2ce05f2c37a5f2b85a9268
   │  OPEN / NON_MERGEABLE metadata / focused checks PASS
   │
   ├─ PR #77 feat/loopx-worker-gateway-terminal-v1
   │  issue #64
   │  head 8778b3dd16dceccc7d3904f954a2ade249fce468
   │  OPEN / NON_MERGEABLE metadata / focused checks PASS
   │
   ├─ PR #78 feat/loopx-decision-memory-v1
   │  issue #42
   │  head 166e0ee4ca69690f9e7da46b14d5452bc25df4b8
   │  OPEN / NON_MERGEABLE metadata / focused checks PASS
   │
   └─ PR #79 feat/loopx-code-truth-graph-v2
      issue #69
      head 371083a4baeda129434aea2ebad538dde8004f07
      OPEN / NON_MERGEABLE metadata / focused checks PASS
```

## Blocking conflict: Worker Gateway duplicate terminal

PR #76 and PR #77 are not parallel-safe:

```text
same issue: #64
same parent: feat/loopx-contract-v1
overlap:
  .arena/modules/loopx-worker-gateway/**
  loop_wiki/loopx-worker-gateway/**
  loopctl/workflow.lock
state: BLOCKED_DUPLICATE_TERMINAL
authority: Human
```

Focused green checks do not choose a winner. Human options are to select one, extract unique delta, sequence one as a true child, mark one superseded or close one.

## Program leaf ledger

| Issue / PR | Terminal behavior | Relation | Current state |
|---|---|---|---|
| #62 / #74 | Objective/Todo/Gate/Evidence/Quota contracts | root terminal | `OPEN CANDIDATE` |
| #63 / #75 | append-only ledger/reducer | true child | `MERGED_TO_PARENT`, not main |
| #64 / #76/#77 | six-host Worker Gateway | duplicate child terminals | `BLOCKED_DUPLICATE_TERMINAL` |
| #65 | Strategy Graph + HITL | planned terminal | `PR ABSENT` |
| #42 / #78 | Decision Memory admission | sibling terminal | `OPEN CANDIDATE` |
| #66 | Runtime Fabric/local-cloud parity | planned terminal | `PR ABSENT` |
| #69 / #79 | Code Truth Graph v2 | sibling terminal | `OPEN CANDIDATE` |
| #70 | Notes Repo → Scaffold | planned terminal | `PR ABSENT` |
| #71 | Code → Knowledge fold-back | planned terminal | `PR ABSENT` |
| #72 | Skill/Prompt evolution | planned terminal | `PR ABSENT` |
| #67 | Observability/signed HITL | planned terminal | `PR ABSENT` |
| #68 | final shared convergence | convergence | `BLOCKED_BY_TERMINALS` |

Only issue #68 may select all settled terminal modules in the shared composition, regenerate final indexes, run the live matrix and record promotion/rollback.

## Provider and historical lanes

### Provider admission

```text
PR #56
head 770b0c8990843e958f7c1a345c3359a2d71eeb82
focused provider evaluator PASS
Knowledge provider contracts FAIL
Modular contracts FAIL
state: BLOCKED
```

Fixture evidence cannot establish live provider health or superiority.

### Historical portable-Skill aggregate

```text
PR #53
head ac9d08fd9cf1e8925f628c6508d495fdeca7d3a2
state: SUPERSEDED_CANDIDATE / historical aggregate
```

Extract unique delta before any Human merge or close decision.

### Other separate lanes

PR #58 remains a runtime-env / Agent Shield documentation audit. PR #73 remains a Skill measurement lane. Neither enters the LoopX implementation parent chain automatically.

## Current issue #80 task packet and path lease

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
  - executable/license/legal admission
  - semantic conflict resolution
  - PR retargeting
  - merge/ship/close/delete
  - promotion and rollback
```

## Required receipt chain

```text
source proposal or incident
→ architecture decision
→ parent issue
→ terminal issue
→ task packet + path lease
→ branch / PR / exact head
→ positive + control + mutation
→ generated projections
→ runtime/host receipt where applicable
→ convergence index
→ Human Admit
```

## Git Town State Machine boundary

Future admitted Git Town use:

```text
profile
→ executable/license/SBOM/legal admission
→ config candidate
→ linked worktree/branch/path lease
→ dry run
→ local sync candidate
→ evals
→ GitHub exact-head publication checks
→ Human Admit
```

Git Town does not own semantic conflict resolution, remote publication, merge/ship/close/delete, production promotion or rollback.

## Update protocol

When Stack topology changes, update together:

- root `README.md`;
- `AGENTS.md` / `CLAUDE.md` when routing changes;
- [`../git/STACKED_PRS.md`](../git/STACKED_PRS.md);
- [`../git/stack-prs.index.json`](../git/stack-prs.index.json);
- this file;
- directory/state maps when ownership changes;
- deterministic verifier fixtures and exact-head checks.

Do not merge, ship, close, delete, promote or rollback without Human Admit.
