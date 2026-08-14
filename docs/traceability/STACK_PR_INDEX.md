# Molecular Stack PR index

## Authority and freshness

GitHub issue/PR base, head, state, mergeability, checks and main reachability are current authority. This document records the relationship and last observed immutable subjects.

```text
observed_at: 2026-08-14T09:33:48Z
current main: 10380005fa485d6035539589c01b9f740acff15d
machine snapshot: ../git/stack-prs.index.json
repository profile: ../git/REPO_PROFILE.md
```

Refresh this index whenever any affected GitHub field changes.

## Canonical shared Git Town method

```text
repository: ed3c/skills-shared
commit: c5750720d960a228a0d9419f28125c09d064e3e1
blob: eb2d915bca3e8a3938625f7d33a10fae95a15769
path: skills/git-town-stacked-pr-worker/SKILL.md
```

Bettor owns the profile, work packet, path lease, Stack index, evals and Human policy. It does not copy the shared Skill.

Current admission:

```text
shared Skill reference            PINNED
consumer binding selection        NOT_SELECTED
.git-town.toml                    ABSENT
Git Town binary/version/checksum  ABSENT
license/SBOM/legal                NOT_REVIEWED
live sync/publication             NOT_EXERCISED
```

## Relation vocabulary

```text
sibling      path-disjoint independent leaf
true child   consumes unmerged parent bytes
terminal     one behavior plus eval/evidence
convergence  shared selection/index/live/release owner
merged-to-parent
             child entered feature parent, not current main
```

## Documentation and governance Stack

```text
main @ 10380005fa485d6035539589c01b9f740acff15d
└─ PR #60 feat/pdf-loopx-modular-verifier-v1
   head ffbcd91a9eae1f6171fc7c42f0300bb83fac1b90
   OPEN / MERGEABLE
   exact-head checks PASS:
     Modular contracts
     PDF Harness integration audit
     LoopX PDF modular integration
     repo-agent-native Bettor Binding
   └─ PR #81 feat/git-town-stack-governance-v1
      issue #80; true-child documentation/governance terminal
      observed head 857b6239b5faaff12910b37b73c32e5121b4f291
      OPEN DRAFT / MERGEABLE
      Modular contracts PASS; focused Git Town job skipped while Draft
      rollback ffbcd91a9eae1f6171fc7c42f0300bb83fac1b90
```

Issue #80 is a child because it changes the same root routing documents as #60.

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
   │  MERGED_TO_PARENT at #74 head
   │  NOT_ON_MAIN
   │
   ├─ PR #76 feat/loopx-worker-gateway-v1
   │  issue #64
   │  head 60caac70f75b1f214b2ce05f2c37a5f2b85a9268
   │  OPEN / NON_MERGEABLE
   │  focused + Modular + PDF checks PASS
   │
   ├─ PR #77 feat/loopx-worker-gateway-terminal-v1
   │  issue #64
   │  head 8778b3dd16dceccc7d3904f954a2ade249fce468
   │  OPEN / NON_MERGEABLE
   │  Modular + PDF checks PASS
   │
   ├─ PR #78 feat/loopx-decision-memory-v1
   │  issue #42
   │  head 166e0ee4ca69690f9e7da46b14d5452bc25df4b8
   │  OPEN / NON_MERGEABLE
   │  Decision-Memory + Modular + PDF checks PASS
   │
   └─ PR #79 feat/loopx-code-truth-graph-v2
      issue #69
      head 371083a4baeda129434aea2ebad538dde8004f07
      OPEN / NON_MERGEABLE
      CTG-v2 + Modular + PDF checks PASS
```

## Blocking conflict: Worker Gateway duplicate terminal

PR #76 and PR #77:

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

The two PRs are not sibling-safe. Focused green checks do not choose a winner.

## Program leaf ledger

| Issue / PR | Terminal behavior | Relation | Current state |
|---|---|---|---|
| #62 / #74 | LoopX Objective/Todo/Gate/Evidence/Quota contracts | root terminal | `OPEN CANDIDATE` |
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

## Provider and Skill lanes

### Provider admission

```text
PR #56
head 770b0c8990843e958f7c1a345c3359a2d71eeb82
focused provider evaluator PASS
Knowledge provider contracts FAIL
Modular contracts FAIL
state: BLOCKED
```

Fixture evidence cannot establish live provider health.

### Historical portable-Skill aggregate

```text
PR #53
head ac9d08fd9cf1e8925f628c6508d495fdeca7d3a2
state: SUPERSEDED_CANDIDATE / historical aggregate
```

Extract unique delta before any Human close or merge decision.

### Skill measurement

PR #73 remains a separate measurement lane. Its universal protocol conformance does not promote the measured Skill and does not enter the LoopX implementation parent chain.

## Runtime-env / Agent Shield documentation lane

PR #58 remains a separate documentation audit. It must not be used to prove runtime pin freshness, live host/provider execution or product completion.

## Current issue #80 path lease

```text
parent: PR #60
base: feat/pdf-loopx-modular-verifier-v1
head: feat/git-town-stack-governance-v1
class: true-child terminal

allowed:
  README.md
  AGENTS.md
  CLAUDE.md
  docs/git/**
  docs/README.md
  docs/INDEX.md
  docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md
  docs/architecture/STATE_MACHINES.md
  docs/architecture/agent-entrypoints.contract.json
  docs/traceability/STACK_PR_INDEX.md
  .arena/contexts/macro.json
  scripts/gates/check_git_town_stack_docs.py
  tests/test_git_town_stack_docs.py
  .github/workflows/git-town-stack-docs.yml
  generated modular projections through workflow

excluded:
  LoopX implementation directories
  loopctl public surface
  MCP policy
  provider credentials/live receipts
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
→ runtime/host receipt when applicable
→ convergence index
→ Human Admit
```

## Git Town State Machine boundary

Future admitted Git Town use:

```text
profile
→ executable/legal admission
→ config candidate
→ linked worktree/branch/path lease
→ dry run
→ local sync candidate
→ evals
→ GitHub publication checks
→ Human Admit
```

Git Town does not own:

```text
semantic conflict resolution
remote publication
merge / ship / close / delete
production promotion
rollback
```

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
