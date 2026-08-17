# Molecular Stack PR index

## Authority and freshness

GitHub issue/PR base, head, state, mergeability, checks and main reachability are current authority. This Markdown, [`../git/stack-prs.index.json`](../git/stack-prs.index.json) and [`../git/pdf-terminal-sequence.json`](../git/pdf-terminal-sequence.json) are reviewed snapshots.

```text
observed GitHub main: ad0fdde3e46aa6ab6c59ced145bead7fa4fc72d3
program: #61
queue index task: #102
current active item: #140 (order 13; HUMAN_ADMIT_REQUIRED)
final convergence: #68
repository profile: ../git/REPO_PROFILE.md
```

Refresh the ordered queue whenever an affected issue, branch, PR, exact head, path lease, check, main reachability or policy-waiver receipt changes.

## Git Town status

```text
.git-town.toml                         ABSENT
.git-town                              ABSENT
git-town-stacked-pr-worker selected    NOT_SELECTED
repository molecular-delivery policy   IMPLEMENTED
Git Town binary/version/checksum       ABSENT
license/SBOM/legal                     NOT_REVIEWED
local no-push sync/publication         NOT_EXERCISED
typed controller/13 physical controls  IMPLEMENTED / PASS
```

The repository uses the shared Skill's molecular-delivery semantics without claiming an admitted Git Town executable.

## Canonical shared Git Town method

```text
repository: ed3c/skills-shared
commit: c5750720d960a228a0d9419f28125c09d064e3e1
blob: eb2d915bca3e8a3938625f7d33a10fae95a15769
path: skills/git-town-stacked-pr-worker/SKILL.md
```

Bettor owns repository profile, queue, task packet, path lease, Stack index, evals, receipts and automated-admission policy. It does not copy or shadow the shared Skill.

The current Bettor binding source `skills-shared@b3c722da1c40301b0a12e0ef99848d884bfc720b` contains the same blob at the same path. This is exact byte-equivalence evidence; the Skill remains `NOT_SELECTED`.

The current Bettor binding source `skills-shared@b3c722da1c40301b0a12e0ef99848d884bfc720b` contains the same blob at the same path. This is exact byte-equivalence evidence; the Skill remains `NOT_SELECTED`.

## Ordered PDF terminal completion queue

Human view: [`../git/PDF_TERMINAL_SEQUENCE.md`](../git/PDF_TERMINAL_SEQUENCE.md)  
Machine queue: [`../git/pdf-terminal-sequence.json`](../git/pdf-terminal-sequence.json)  
Canonical repository paths: `docs/git/PDF_TERMINAL_SEQUENCE.md` and `docs/git/pdf-terminal-sequence.json`.

```text
order 00  #82       Worker Gateway residual-file disposition       COMPLETE
order 01  #90       current-main LoopX foundation validation       COMPLETE
order 02  #65       Strategy Graph + HITL                          COMPLETE
order 03  #67       Observability + signed HITL projection         COMPLETE
order 04  #66       Runtime Fabric + local/cloud parity            COMPLETE
order 05  #94       Herdr/tmux-compatible Worker Fleet             COMPLETE
order 06  #97       resource retention and GC                      COMPLETE
order 07  #96       worktree-aware LSP Pool                        COMPLETE
order 08  #103      canonical Decision Memory runtime              COMPLETE
order 09  #93       Mem0 rebuildable projection                    COMPLETE
order 10  #104      YT/PDF/Notes source ingest                     COMPLETE
order 11  #105      OpenWiki + vector/graph Notes retrieval        COMPLETE
order 12  #92       Serena/GrepAI live canaries                    COMPLETE
order 13  #140      Blindspots + Tech Lead + Code-Graph-RAG retirement ACTIVE / HUMAN_ADMIT_REQUIRED
order 14  #70       Notes Repo → Scaffold                          BLOCKED_BY_PREDECESSOR
order 15  #71       Code → Knowledge fold-back                     BLOCKED_BY_PREDECESSOR
order 16  #95       prompt-cache-stable Context Assembly          BLOCKED_BY_PREDECESSOR
order 17  #72       Skill/Prompt evolution + sealed holdout        BLOCKED_BY_PREDECESSOR
order 18  #98       local/GitHub CI parity                         BLOCKED_BY_PREDECESSOR
order 19  #91       six-host live matrix                           BLOCKED_BY_PREDECESSOR
order 20  #45       Codex/Claude paired A/B                        BLOCKED_BY_PREDECESSOR
order 21  #46/#56   provider evaluation convergence               BLOCKED_BY_PREDECESSOR
order 22  #99       Harness Console                                BLOCKED_BY_PREDECESSOR
order 23  #100      profile-scoped Harness benchmarks              BLOCKED_BY_PREDECESSOR
order 24  #101      Git Town runtime admission                     BLOCKED_BY_PREDECESSOR
order 25  #68       final convergence/release/rollback             FINAL_CONVERGENCE
```

Only one item may be `ACTIVE`. Queue order serializes completion, while branch ancestry follows actual byte dependency. A future implementation branch is not created before activation unless the automated-admission controller records a scoped policy waiver.

## Terminal implementation PR reachability

This mapping is independent of ordered acceptance. A later merged PR remains blocked in the queue until its predecessors settle.

| Orders | Issues | Implementation PRs on main | Queue interpretation |
|---|---|---|---|
| foundation | #62/#63/#64/#42/#69 | #74/#75/#76/#78/#79 | consumed by order 1 |
| 0–4 | #82/#90/#65/#67/#66 | #76/#77, #109, #106, #116, #117 | orders 0–4 complete; #77 superseded |
| 5–11 | #94/#97/#96/#103/#93/#104/#105 | #122/#123/#124/#125/#126/#127/#128 | orders 5–11 complete |
| 12–13 | #92/#140 | #153/#155/#156/#157 | #92 complete; #140 deterministic leaves merged, Human Admit pending |
| 14–18 | #70/#71/#95/#72/#98 | #118/#119/#129/#120/#130 | bytes merged; acceptance blocked |
| 19–21 | #91/#45/#46/#56 | #56 evaluator only | live/A-B/convergence blocked |
| 22–24 | #99/#100/#101 | #131/#134, #132/#135, #133 | bytes/mechanisms merged; acceptance blocked |
| 25 | #68 | none | final convergence |

## Terminal implementation PR reachability

This mapping is independent of ordered acceptance. A later merged PR remains blocked in the queue until its predecessors settle.

| Orders | Issues | Implementation PRs on main | Queue interpretation |
|---|---|---|---|
| foundation | #62/#63/#64/#42/#69 | #74/#75/#76/#78/#79 | consumed by order 1 |
| 0–4 | #82/#90/#65/#67/#66 | #76/#77, #109, #106, #116, #117 | orders 0–4 complete; #77 superseded |
| 5–11 | #94/#97/#96/#103/#93/#104/#105 | #122/#123/#124/#125/#126/#127/#128 | orders 5–11 complete |
| 12–13 | #92/#41 | none | active then blocked |
| 14–18 | #70/#71/#95/#72/#98 | #118/#119/#129/#120/#130 | bytes merged; acceptance blocked |
| 19–21 | #91/#45/#46/#56 | #56 evaluator only | live/A-B/convergence blocked |
| 22–24 | #99/#100/#101 | #131/#134, #132/#135, #133 | bytes/mechanisms merged; acceptance blocked |
| 25 | #68 | none | final convergence |

## Current-main LoopX foundation

```text
PR #74  LoopX Contract v1              MERGED_TO_MAIN
├─ PR #75  append-only Ledger/reducer  MERGED_TO_MAIN through #74
├─ PR #76  Worker Gateway              MERGED_TO_MAIN through #74
├─ PR #78  Decision Memory contracts   MERGED_TO_MAIN through #74
└─ PR #79  Code Truth Graph v2         MERGED_TO_MAIN through #74
```

Reachability proves those bytes are on current `main`; it does not prove final composition selection, live host/provider execution, cloud isolation or production promotion.

## Resolved duplicate terminal

```text
PR #76  admitted Worker Gateway implementation
PR #77  closed SUPERSEDED_CANDIDATE
issue #64 implemented twice over overlapping paths
state: RESOLVED_BY_HUMAN
residual action: issue #82 completed the eight-file disposition
```

Do not delete the record. A resolved duplicate must remain distinguishable from a Stack that never noticed the conflict.

## Documentation and governance lineage

```text
PR #60  PDF/LoopX executable traceability       MERGED_TO_MAIN
PR #81  Git Town governance                     MERGED_TO_MAIN
issue #80 governance terminal                   COMPLETED
PR #107/#121 ordered queue and derived-head gate MERGED_TO_MAIN
issue #102 ordered queue documentation leaf      CLOSED
```

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

Their contract flow remains:

```text
skills-shared procedure
+ runtime-env secret-free runtime contract
→ bettor-arena integration/acceptance
→ agent-shield-monorepo reference product/canaries
→ automated promotion or rollback
```

## Modular platform implementation spine

The mainline foundation includes module catalog, path ownership, closure-scoped proof subjects, Context Capsules, default-deny MCP, transactional bootstrap, origins/browser contracts and documentation convergence. Current truth comes from manifests, public contracts, locks and receipts rather than this prose.

## Skill, host execution and provider spine

```text
bettor-arena#43 repo-agent-native binding
→ bettor-arena#48 portable Skill compatibility
→ bettor-arena#50 host-owned execution/assertion runner
→ bettor-arena#51 provider-neutral query/memory contracts
→ bettor-arena#53 historical aggregate
→ bettor-arena#56 provider-evaluation lane
```

A focused fixture PASS cannot establish live-provider health, current-main reachability or final release.

## Open terminal leaves required by the PDF target

```text
bettor-arena#24 immutable Agent Shield reference-consumer acceptance
LoopX program issue #61
active ordered issue #140; remaining #45/#68/#91 and later acceptance states
final convergence #68
```

These compatibility tokens preserve earlier audit routes. The current order is defined only by `pdf-terminal-sequence.json`.

## Historical provider and aggregate lanes

```text
PR #56  provider evaluation bytes on main; live convergence still issue #46/#56
PR #53  CLOSED historical aggregate
PR #58  runtime-env / Agent Shield documentation audit, separate lane
PR #73  Skill measurement lane, separate evidence subject
```

Extract unique delta before any reuse of a superseded aggregate.

## Relation vocabulary

```text
ROOT
  first active branch from admitted main

ROOT_AFTER_PREDECESSOR
  path-disjoint terminal created from the new main after its predecessor completes

TRUE_CHILD
  consumes unmerged parent bytes

CONVERGENCE
  owns shared selection, locks, indexes, live acceptance and release

MERGED_TO_PARENT
  child entered a feature parent but was not yet reachable from main

MERGED_TO_MAIN
  current-main reachability is proven
```

Global completion order does not require a 26-deep true-child chain.

## Required receipt chain

```text
source proposal or incident
→ architecture decision
→ program issue #61
→ active terminal issue/task packet
→ branch relation + path lease
→ implementation PR / exact head
→ positive + independent control + planted mutation
→ generated projections where required
→ runtime/host/provider receipt where applicable
→ queue advancement receipt
→ issue #68 convergence
→ automated admission
```

## Automation-owned operations

Agents and background Workers may invoke these operations only through the named
exact-subject controller. They must not:

- guess semantic conflicts or run Git Town continue, skip or undo outside policy;
- create future terminal branches before activation or a scoped waiver;
- use raw push, merge, ship, close or delete paths;
- change remotes, credentials or permissions;
- activate providers, models, runtimes or secrets without the required manifest and receipt;
- admit unscoped exceptions or destructive cleanup;
- promote or roll back production outside the release controller.

## Update protocol

When queue or Stack topology changes, update together:

- root `README.md`;
- `AGENTS.md` when active item or routing changes;
- [`../git/PDF_TERMINAL_SEQUENCE.md`](../git/PDF_TERMINAL_SEQUENCE.md);
- [`../git/pdf-terminal-sequence.json`](../git/pdf-terminal-sequence.json);
- [`../git/STACKED_PRS.md`](../git/STACKED_PRS.md);
- this file;
- relevant directory/State-Machine maps;
- deterministic verifier fixtures and exact-head checks.

Merge, ship, close, delete, promote and roll back only through the exact-subject automated-admission controller.
