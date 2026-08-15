# PDF Harness architecture integration audit

## Purpose

This document answers one narrow question:

> Does the current `bettor-arena` repository modularly integrate the architecture proposed in the attached 41-page PDF, **LLM 泛化：模型權重與 Harness**?

The PDF is a **source proposal**, not repository truth. It proposes an Agent-agnostic LoopX kernel with Objective, Todos, Gates, Evidence and Quota; a deterministic state-transition engine; LangGraph HITL; white-box and gray-box workers; hot/cold memory; OpenWiki and vector/graph retrieval; worktree fleets; cloud/local separation; and observability. Its examples also include direct `.loopx/state.json` writes, `shell=True`, `force_skip`, raw Thought Stream transfer, and performance claims. Those examples are not treated as admitted Bettor mechanisms.

Current correction measured on 2026-08-16:

```text
LoopX terminal mechanisms       IMPLEMENTED across current-main directories
ordered acceptance              COMPLETE through order 11; issue #92 active
selected release composition    14 base modules; LoopX terminals excluded
aggregate module evidence       NOT_EXERCISED
full PDF release                not admitted; issue #68 pending
```

The detailed mapping below records the original audit baseline and source-to-target gap decomposition. Where it calls a mechanism `NOT_IMPLEMENTED`, use the current correction plus [`modular-integration-status.md`](modular-integration-status.md), [`DIRECTORY_STATE_MACHINE_MAP.md`](DIRECTORY_STATE_MACHINE_MAP.md) and the machine queue for present state. It remains useful for requirements; it is no longer a live implementation inventory.

Historical audit baseline:

```text
repository: ed3c/bettor-arena
main commit: d291523856988cfa54316dba967fea8470194b72
main tree:   71d7b874dfd181e15d6b614cd6d3bf7fb47d8c43
source:      attached PDF, 41 pages, not copied into Git
```

The machine-readable companion is
[`pdf-harness-integration.matrix.json`](pdf-harness-integration.matrix.json).
The executable gate is:

```sh
python3 scripts/gates/check_pdf_harness_integration.py
python3 scripts/gates/check_pdf_harness_integration.py --selftest
```

## Verdict

```text
Modular control-plane foundation                 IMPLEMENTED
Hard gates, receipts, controls and mutations     IMPLEMENTED
Portable Skill proposal → host-owned execution   IMPLEMENTED
Context Capsules and immutable projections       IMPLEMENTED
OpenWiki and Code Truth Graph mechanisms         IMPLEMENTED
Provider-neutral knowledge contracts             IMPLEMENTED

LoopX kernel/Ledger/Strategy/HITL mechanisms      IMPLEMENTED
Runtime/Fleet/Memory/Notes/Console mechanisms     IMPLEMENTED
LoopX modules selected into release composition   ABSENT
Six-host live worker matrix                       NOT_EXERCISED
Serena/GrepAI live provider canaries              NOT_EXERCISED
Code-Graph-RAG live admission                     NOT_EXERCISED
Cloud/local equivalent execution                  NOT_EXERCISED
External observability backend/live Console       NOT_EXERCISED
Git Town repository configuration                 ABSENT
```

Therefore the truthful repository-level conclusion is:

> **Bettor has modularly integrated a large part of the supporting Harness and has now landed most component mechanisms, but it has not selected, live-verified or released them as the PDF's complete LoopX architecture.**

`loopctl` is a stable public command surface; it is **not** proof that a LoopX state kernel exists. `.arena` is a module/composition/context control plane; it is **not** the PDF's Objective/Todos/Gates/Evidence/Quota task ledger.

## Source proposal → historical audit mapping

| PDF concept | Current Bettor mapping | State | What is still missing |
|---|---|---|---|
| Agent-agnostic control plane | `.arena/`, `loopctl/`, module contracts | `IMPLEMENTED` foundation | One canonical task-state kernel and reducer |
| Objective and Todos | typed loop/task packets and command contracts | `PARTIAL` | canonical Objective/Todo schema, lifecycle and single writer |
| Gates | Skill assertions, proof/control/mutation, repository gates | `IMPLEMENTED` | aggregation into one LoopX task transition |
| Evidence | `data/proof-workflow/`, `data/module-proof/`, execution receipts | `IMPLEMENTED` mechanism | event-ledger linkage to every task transition |
| Quota | isolated time/output limits in individual runners | `PARTIAL` | canonical retry/token/cost quota and terminal state |
| `.loopx/state.json` | no equivalent path | `NOT_IMPLEMENTED` | event ledger, derived snapshot, reducer and lease |
| deterministic transition engine | `loopctl` dispatch and independent gates | `PARTIAL` | one reducer that alone commits task state |
| LangGraph DAG/Mesh | no admitted module | `NOT_IMPLEMENTED` | strategy-command port, checkpoint projection, cycle/termination policy |
| HITL interrupt/resume | Human Admit is documented | `PARTIAL` | machine interrupt, resume and exception receipts |
| white-box monolithic worker | Grok Build is documented as a source-visible reference | `NOT_EXERCISED` | pinned executable/adapter/index and live canary receipt |
| gray-box workers | Codex/Claude Skill/context projections | `IMPLEMENTED` contract | current live Codex/Claude receipts |
| OpenCode, Pi and Ante | compatibility documentation in `harness-wiki` | `IMPLEMENTED` contract | live adapter canaries and trace-completeness evidence |
| hot/cold episodic memory | provider-neutral memory proposals | `PARTIAL` | evidence-bound capsule ledger, expiry, supersession and admit |
| OpenWiki | `kb-ingest/`, `openwiki/`, OpenWiki module | `IMPLEMENTED` mechanism | current full probabilistic run remains subject-specific |
| AST/LSP/Code Truth | Code Truth Graph and Serena contract | `PARTIAL` | unified source-provenance graph and live Serena canary |
| semantic retrieval | GrepAI candidate provider contract | `PARTIAL` | current index identity/freshness and paired live eval |
| Code-Graph-RAG | candidate manifest only | `NOT_IMPLEMENTED` runtime | read-only adapter, isolated stores, coverage and freshness receipts |
| Mem0 | candidate memory proposal contract only | `NOT_IMPLEMENTED` runtime | storage/model/embedding/retention/delete/writeback admission |
| herdr/tmux fleet | no admitted configuration | `NOT_IMPLEMENTED` | worker queue, leases, worktree cleanup and resource quotas |
| cloud/local separation | `runtime-env`, origins/browser contracts | `IMPLEMENTED` contract | same-workload local/cloud canary and rollback |
| Langfuse/OTel | no admitted module | `NOT_IMPLEMENTED` | trace schema, redaction, exporter and retention |
| Web UI | no admitted app | `NOT_IMPLEMENTED` | event/evidence projection and signed HITL actions |

`PARTIAL` in this human table means that an enabling mechanism exists but the PDF component's complete state machine does not. It is not an additional machine evidence state.

## Rejected source shortcuts

The following PDF examples must not be copied as production contracts:

| Source example | Bettor decision |
|---|---|
| `subprocess.run(command, shell=True)` | use typed executable + `argv[]`; raw shell is rejected |
| Agent or Worker edits `.loopx/state.json` | only a host-owned reducer may commit canonical state |
| `force_skip` string | require a scoped, reasoned, expiring Human exception receipt |
| LangGraph checkpoint as canonical state | checkpoint is a projection of the canonical ledger, not a second authority |
| raw Thought Stream handoff | store externalized observations, dead ends, decisions and evidence refs; never private chain of thought |
| Provider output marks `TESTED` or PASS | provider output remains candidate-only until independent readback and hard gates |
| performance, RAM, cost or certainty numbers | remain `SOURCE_PROPOSAL` until a pinned workload produces receipts |
| automatic OpenWiki update after any edit | update only through a typed request, bounded path policy and independent verification |

## Current modular integration graph

```text
skills-shared release
        │ requirements-filtered binding
        ▼
.agents/ + .skill-bindings/
        │
runtime-env release ───────────────┐
        │ secret-free projection   │
        ▼                          ▼
.runtime-env/                 .arena/compositions/
                                   │ resolve
                                   ▼
                              composition lock
                                   │
                  ┌────────────────┼─────────────────┐
                  ▼                ▼                 ▼
             Context Caps      module subjects   MCP projection
                  │                │                 │
                  ▼                ▼                 ▼
         host Worker proposal  proof/control/    loopctl public port
                  │            mutation receipts    │
                  └────────────────┬─────────────────┘
                                   ▼
                         Human Admit / release
```

This graph is implemented as modular infrastructure. The following proposed control loop is not:

```text
Objective + Todos + Quota
        ↓
single-writer LoopX event ledger
        ↓
strategy graph proposes command
        ↓
worker executes in isolated workspace
        ↓
hard gates observe artifacts
        ↓
LoopX reducer commits transition
        ↓
memory distiller proposes capsule
        ↓
HITL interrupt/resume or next task
```

## Exact drift found at audit start

At the baseline `main` subject:

- `.arena/compositions/bettor-arena.requirements.json` selects `knowledge-providers`;
- `.arena/modules/knowledge-providers/module.json` exists;
- the checked `.arena/locks/bettor-arena.lock.json` omits that module;
- `data/module-proof/release-receipt.json` also omits it.

That was a **stale generated-projection failure**, not a documentation preference. The current requirements, lock and release receipt now agree on 14 base modules; their aggregate evidence is still `NOT_EXERCISED`, and LoopX terminal modules remain unselected.

The current active provider terminal is issue #92 and is indexed in
[`../traceability/STACK_PR_INDEX.md`](../traceability/STACK_PR_INDEX.md).
Its fixture evaluator check can pass while modular integration remains red. Those outcomes are different subjects and must not proxy one another.

## Required state-machine leaves (historical decomposition)

The audit decomposed the following leaves. Most mechanism leaves have since landed; their current acceptance state is the ordered queue:

1. **LoopX contract leaf**
   - Objective/Todo/Gate/Evidence/Quota schemas;
   - event, command and snapshot schemas;
   - named terminal states and reducer invariants.

2. **Single-writer ledger leaf**
   - append-only event store;
   - hash chain and writer lease;
   - snapshot projector;
   - replay, corruption and split-brain controls.

3. **Worker gateway leaf**
   - one adapter contract for Grok Build, OpenCode, Pi, Codex, Claude and Ante;
   - capability probing and trace-completeness;
   - no state or gate authority.

4. **Strategy/HITL leaf**
   - graph proposes typed commands only;
   - LoopX validates and commits;
   - interrupt/resume/exception receipts;
   - no checkpoint split-brain.

5. **Memory leaf**
   - evidence-bound decision-memory capsule;
   - validity scope, expiry, supersession and conflict;
   - privacy, delete/export and Human Admit.

6. **Runtime fabric leaf**
   - disposable worktree/container adapters;
   - resource quotas, process-group kill, network policy and cleanup;
   - local/cloud same-workload receipt.

7. **Observability/UI leaf**
   - redacted event projection;
   - OTel/Langfuse adapter;
   - evidence inspector and signed HITL control;
   - no UI-owned state transition.

8. **Convergence leaf**
   - generated locks and receipts agree;
   - all module/interface/path owners agree;
   - fresh host canaries are separate;
   - Human Admit decides merge/promotion.

## Completion criteria

The complete PDF architecture cannot be marked integrated until all of the following are true:

```text
requirements module set == composition-lock module set
composition-lock module set == release-receipt module set
every selected module has one owner, manifest and README
LoopX ledger/reducer/schema exists and passes split-brain controls
workers cannot write task state or gate verdicts
all hard-gate results bind exact subject and artifacts
quota exhaustion has a named HITL interrupt state
resume and exception actions have immutable receipts
memory capsules are evidence-bound, scoped and removable
six host adapters have current canary receipts
provider indexes have exact subject/freshness/coverage
local/cloud same-workload canary exists
observability is redacted and rebuildable
every terminal PR is indexed and one convergence owner remains
Human Admit is explicit
```

## Related routes

- [`DIRECTORY_STATE_MACHINE_MAP.md`](DIRECTORY_STATE_MACHINE_MAP.md)
- [`STATE_MACHINES.md`](STATE_MACHINES.md)
- [`modular-integration-requirements.md`](modular-integration-requirements.md)
- [`modular-integration-status.md`](modular-integration-status.md)
- [`../integration/CROSS_REPO_INTEGRATION.md`](../integration/CROSS_REPO_INTEGRATION.md)
- [`../traceability/STACK_PR_INDEX.md`](../traceability/STACK_PR_INDEX.md)
- [`../../.arena/README.md`](../../.arena/README.md)
