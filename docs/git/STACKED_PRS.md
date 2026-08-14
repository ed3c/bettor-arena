# Bettor Arena molecular Stacked PR topology

## Authority

GitHub base/head/state/check metadata is publication truth. This document is a reviewed topology guide. The strict completion order is machine-owned by [`pdf-terminal-sequence.json`](pdf-terminal-sequence.json).

```text
queue base: 844b7121789e57ebe00f1a07a67b27c1542cf05b
program: #61
index task: #102
active: #82
convergence: #68
canonical shared method:
  ed3c/skills-shared@c5750720d960a228a0d9419f28125c09d064e3e1
  skills/git-town-stacked-pr-worker/SKILL.md
```

No Git Town executable or `.git-town.toml` is admitted. The graph is derived from GitHub metadata and repository policy, not `git town` output.

## Relation vocabulary

```text
ROOT
  first active terminal from admitted main

ROOT_AFTER_PREDECESSOR
  path-disjoint work created from the updated main after the previous queue item lands

TRUE_CHILD
  consumes unmerged parent bytes and targets the parent branch

TERMINAL
  one reviewable behavior plus positive/control/mutation evidence

CONVERGENCE
  owns shared composition, generated indexes, live matrix, release and rollback
```

Queue order serializes completion. It does not turn every future branch into a true child.

## Current-main foundation

```text
main
└─ PR #74 LoopX Contract v1                       MERGED_TO_MAIN
   ├─ PR #75 append-only Ledger/reducer           MERGED_TO_MAIN through #74
   ├─ PR #76 host-neutral Worker Gateway          MERGED_TO_MAIN through #74
   ├─ PR #78 Decision Memory contracts            MERGED_TO_MAIN through #74
   └─ PR #79 Code Truth Graph v2                  MERGED_TO_MAIN through #74
```

`MERGED_TO_MAIN` proves byte reachability. It does not prove final composition selection or live runtime/provider acceptance.

## Resolved duplicate terminal

```text
PR #76 selected implementation
PR #77 closed SUPERSEDED_CANDIDATE
same issue #64 and overlapping paths
state: RESOLVED_BY_HUMAN
follow-up: issue #82 compares eight PR #77-only files
```

PR #77 history remains indexed; issue #82 may fold or explicitly reject each unique file after executable comparison.

## Documentation governance lineage

```text
PR #60 PDF/LoopX traceability           MERGED_TO_MAIN
└─ PR #81 Git Town governance           MERGED_TO_MAIN
   issue #80 completed

issue #102 ordered queue docs
└─ branch docs/pdf-terminal-stack-sequence-v1
   documentation/governance terminal; unmerged
```

## Ordered completion topology

Human view: [`PDF_TERMINAL_SEQUENCE.md`](PDF_TERMINAL_SEQUENCE.md)  
Machine queue: [`pdf-terminal-sequence.json`](pdf-terminal-sequence.json)

```text
00 #82  Worker Gateway residue                     ACTIVE
01 #90  current-main foundation validation
02 #65  Strategy Graph + HITL
03 #67  Observability + signed HITL
04 #66  Runtime Fabric + local/cloud parity
05 #94  Worker Fleet / Herdr-tmux boundary
06 #97  Resource GC
07 #96  LSP Pool
08 #103 Decision Memory runtime
09 #93  Mem0 projection
10 #104 source ingest
11 #105 Notes retrieval
12 #92  Serena/GrepAI live canaries
13 #41  Code-Graph-RAG read-only admission
14 #70  Notes → Scaffold
15 #71  Code → Knowledge fold-back
16 #95  Context Assembly
17 #72  Skill/Prompt evolution
18 #98  CI parity
19 #91  six-host live matrix
20 #45  Codex/Claude A/B
21 #46/#56 provider evaluation convergence
22 #99  Harness Console
23 #100 profile-scoped benchmarks
24 #101 Git Town runtime admission
25 #68  final convergence
```

Only order 00 is active. Future implementation branches are `NOT_CREATED` until activation or a Human waiver.

## Branch creation protocol

For the active queue item:

```text
1. pin current main commit/tree
2. read task packet and owner paths
3. classify ROOT / TRUE_CHILD / ROOT_AFTER_PREDECESSOR / CONVERGENCE
4. acquire one worktree, branch writer and path lease
5. implement one behavior
6. run positive, independent control and mutation
7. publish exact head
8. observe generated sync and final exact-head checks
9. Human reviews merge or rejection
10. advance queue snapshot
```

Never create future branches merely to display a complete graph.

## Expected branch names

```text
#82   feat/loopx-worker-gateway-residue-v1
#90   feat/loopx-stage0-validation-v1
#65   feat/loopx-strategy-hitl-v1
#67   feat/loopx-observability-v1
#66   feat/loopx-runtime-fabric-v1
#94   feat/loopx-worker-fleet-v1
#97   feat/loopx-resource-gc-v1
#96   feat/loopx-lsp-pool-v1
#103  feat/loopx-decision-memory-runtime-v1
#93   feat/loopx-mem0-projection-v1
#104  feat/loopx-notes-source-ingest-v1
#105  feat/loopx-notes-retrieval-v1
#92   feat/loopx-code-intelligence-canaries-v1
#41   feat/code-graph-rag-readonly-admission-v1
#70   feat/loopx-notes-scaffold-v1
#71   feat/loopx-code-knowledge-foldback-v1
#95   feat/loopx-context-assembly-v1
#72   feat/loopx-skill-prompt-evolution-v1
#98   feat/loopx-ci-parity-v1
#91   feat/loopx-six-host-live-matrix-v1
#45   feat/loopx-codex-claude-ab-v1
#46   eval/loopx-provider-convergence-v1
#99   feat/loopx-harness-console-v1
#100  feat/loopx-benchmark-v1
#101  feat/git-town-runtime-admission-v1
#68   integration/loopx-harness-convergence-v1
```

Branch names are plans until GitHub reports a real ref. `NOT_CREATED` is not progress or failure.

## Path lease law

- one Worker owns one worktree, branch writer and path lease;
- siblings must be path-disjoint;
- a true child must name unmerged parent bytes it consumes;
- overlapping active terminals are blocked until a Human resolves ownership;
- generated locks, root indexes, public surfaces and release receipts are owned only by #68;
- cleanup and rollback subjects are part of every terminal receipt.

## Git Town runtime boundary

Current state:

```text
shared Skill reference                  PINNED
Skill consumer selection                NOT_SELECTED
Git Town binary/config                  ABSENT
local no-push sync                      NOT_EXERCISED
remote publication                      NOT_EXERCISED
merge/ship/rollback                     HUMAN-OWNED
```

Issue #101 owns future executable/config/no-push admission. Until then, Agents must not run Git Town mutation commands.

## Required evidence before queue advancement

```text
exact commit/tree and branch relation
machine contract
nearest README / State Machine / data flow
positive execution or bounded fixture
independent control
hollow or mutation that turns red
bounded artifact and cleanup receipt
rollback subject
final exact-head checks
Human review for merge or activation
```

## Human boundary

Agents and background Workers must not:

- resolve semantic conflict;
- run continue, skip or undo;
- create later branches before activation;
- push, merge, ship, close or delete branches;
- change remotes, credentials or permissions;
- activate providers, runtimes or models;
- admit scoped exceptions or destructive cleanup;
- promote or roll back production.

## Update contract

When an issue, relation, branch, PR, exact head, path lease or queue state changes, update:

- [`PDF_TERMINAL_SEQUENCE.md`](PDF_TERMINAL_SEQUENCE.md);
- [`pdf-terminal-sequence.json`](pdf-terminal-sequence.json);
- this file;
- [`../traceability/STACK_PR_INDEX.md`](../traceability/STACK_PR_INDEX.md);
- root `README.md` and `AGENTS.md` when active item changes;
- deterministic sequence gate and exact-head checks.
