# AGENTS.md — bettor-arena Codex / cross-host entry

Engineering SSOT is [`ARCHITECTURE.md`](ARCHITECTURE.md). The complete modular target is [`docs/architecture/modular-integration-requirements.md`](docs/architecture/modular-integration-requirements.md); current implementation truth is [`docs/architecture/modular-integration-status.md`](docs/architecture/modular-integration-status.md). This file owns mandatory Agent routing, trust boundaries and the completion report.

`AGENTS.md` and `CLAUDE.md` are governed projections. Repository-local gates validate their bytes without reading sibling checkouts. Cross-repository generators are promotion-time tools only.

## Mandatory multi-hop read order

For modules, Macro/Micro loops, Skills, runtime-env, proof, MCP, workers, browser, origins, external consumers, Agent Shield, or either PDF architecture:

1. [`README.md`](README.md)
2. [`CONTEXT.md`](CONTEXT.md)
3. [`ARCHITECTURE.md`](ARCHITECTURE.md) §1–§3
4. [`docs/INDEX.md`](docs/INDEX.md)
5. [`docs/architecture/DOCUMENT_ROUTING.md`](docs/architecture/DOCUMENT_ROUTING.md)
6. [`docs/architecture/modular-integration-requirements.md`](docs/architecture/modular-integration-requirements.md)
7. [`docs/architecture/modular-integration-status.md`](docs/architecture/modular-integration-status.md)
8. [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md)
9. [`docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md) when the task references LoopX, Harness, LangGraph, monolithic workers, episodic memory, Notes Repo/OpenWiki, cloud/local separation, Grok Build, Pi, OpenCode or Ante
10. [`docs/architecture/pdf-loopx-harness.integration.json`](docs/architecture/pdf-loopx-harness.integration.json) for the executable LoopX audit state
11. [`docs/architecture/PDF_SKILL_MCP_TRACEABILITY.md`](docs/architecture/PDF_SKILL_MCP_TRACEABILITY.md) when the task references the separate SKILL.md + MCP PDF
12. [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md)
13. [`docs/traceability/TRACEABILITY_INDEX.md`](docs/traceability/TRACEABILITY_INDEX.md)
14. [`docs/agent-runtime-integration.md`](docs/agent-runtime-integration.md)
15. `sh loopctl/loopctl.sh contract`
16. the target module/loop nearest README, Context Capsule, machine manifest/contract, source, tests, proof/control/mutation receipts and exact issue/PR.

A missing owner, route, path, module, issue, parent, eval, receipt or current provider subject is `ABSENT`; do not reconstruct it from chat or memory. A mechanism that exists but has not run for the exact subject remains `NOT_EXERCISED`. A target described only in prose may remain `NOT_IMPLEMENTED`.

After changing passive context, open a fresh Agent session before claiming that a host loaded the new bytes.

## LoopX PDF verification protocol

The source **《LLM 泛化：模型權重與 Harness》** is a 41-page requirement/hypothesis source. It proposes LoopX, hard gates, LangGraph HITL, monolithic workers, episodic memory, OpenWiki/retrieval, worktree orchestration and cloud/local topology. Source examples and product claims are not repository evidence.

Before modifying or declaring this architecture:

```sh
python3 scripts/gates/check_pdf_loopx_harness_integration.py
python3 scripts/gates/check_pdf_loopx_harness_integration.py --selftest
python3 scripts/gates/check_arena_core.py
python3 scripts/gates/check_arena_core.py --selftest
```

The machine contract is:

```text
docs/architecture/pdf-loopx-harness.integration.json
```

Rules:

1. Map every PDF requirement to exact pages, owner module, State Machine, tracked paths, deterministic gates, implementation state and blockers.
2. Treat `IMPLEMENTED`, `PARTIAL`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `NOT_ADOPTED` and `BLOCKED` as distinct.
3. Do not introduce `.loopx/state.json` as a competing authority without a reviewed single-writer reducer/event contract.
4. Workers submit typed requests and observations; they do not write completion, Human Admit, promotion or rollback state.
5. Never execute model-generated raw shell or use `shell=True`; use allowlisted executable + `argv[]`, exact environment, timeout, process-group cleanup and bounded artifacts.
6. Do not accept `force_skip` as authority. An exception needs a subject-bound Human decision receipt with scope, reason, authority, expiry, follow-up and rollback impact.
7. Do not persist raw chain-of-thought. Persist only externally observable, evidence-bound observations, dead ends, quirks, hypotheses with falsifiers, decisions, scope and expiry.
8. LangGraph checkpoints, UI state, vector indexes, code graphs and memory stores are rebuildable projections; none may become a second canonical state authority.
9. Provider installation, source visibility or fixture PASS cannot prove live capability, isolation, superiority or production readiness.
10. Update root `README.md`, this file, `STATE_MACHINES.md`, `PDF_LOOPX_HARNESS_TRACEABILITY.md` and the JSON manifest together when the verdict or Stack topology changes.

Current exact verdict:

```text
modular control plane                    IMPLEMENTED
portable Skill execution                 IMPLEMENTED on current main
LoopX five-part canonical kernel         PARTIAL
single-writer append-only ledger         NOT_IMPLEMENTED
LangGraph interrupt/resume               NOT_IMPLEMENTED
episodic-memory runtime                  PARTIAL
Grok/Pi/OpenCode/Ante live parity         NOT_EXERCISED or ABSENT
physical cloud/local integration         NOT_EXERCISED
```

## Publication and Stack truth

Git Town is optional local stack tooling. **GitHub base/head metadata plus exact-head checks are publication truth.** A child PR may be merged only into a parent branch and still be absent from `main`.

Snapshot at the LoopX audit baseline:

```text
main @ 77267aba27ad94dde85a4dbda7dacc70a3057fb0
├─ #43 repo-agent-native binding                              MERGED TO MAIN
├─ #51 knowledge-provider contracts + current runner bytes    MERGED TO MAIN
├─ #57 first PDF modular traceability                         MERGED TO MAIN
├─ #53 historical portable-Skill convergence                  OPEN / DIVERGED / SUPERSEDED CANDIDATE
├─ #56 provider admission evaluations                         OPEN / RED EXACT HEAD
├─ #58 runtime-env + Agent Shield second-PDF audit             OPEN DRAFT / BASE MAIN
└─ LoopX PDF executable traceability                          THIS WORKSTREAM
```

Portable Skill execution is present on current `main`:

- `.arena/modules/agent-runtime-integration/module.json` selects `portable_skill_execution`;
- the module provides `skill-execution.runner/v1`;
- `loopctl/contract.json` declares `skill-execution` `run/prove/test`;
- `.agents/skills/harness-wiki/scripts/run_portable_skill.py` emits a subject-bound receipt and never writes LoopX state.

Therefore PR #53 is not current integration authority. Treat it as a stale/diverged historical branch until a Human compares unique delta and closes, supersedes or rebuilds it.

PR #56 is not merge-authorized while its exact head is red. Fixture-only provider evaluation cannot prove Serena, GrepAI, Code-Graph-RAG or Mem0 live health. PR #58 is a Draft documentation audit and cannot proxy runtime/product completion.

Whenever GitHub topology changes, refresh the Stack index in root README, both PDF traceability documents and the LoopX JSON manifest.

## Bettor Arena role

```text
Module Host + Loop Runtime + Proof Kernel + Stateless MCP Gateway + Project Bootstrapper
```

The minimum modularity test:

```text
no inbound private-code dependency
+ one owner for every tracked path
+ module-owned verify/selftest
+ public typed port
+ relocation/isolation proof
+ independent control
+ mutation/hollow instrument that turns red
```

## PDF translation boundary

Translate useful architecture ideas into Bettor authorities:

```text
Objective / scope
→ Macro composition requirements

Todos
→ typed bounded Micro task

Gates
→ host-owned deterministic assertions

Evidence
→ subject-bound artifacts and receipts

Quota
→ bounded retry/resource policy with named exits

SKILL.md
→ immutable procedure + consumer binding

MCP
→ public loopctl contract + default-deny projection

worker execution
→ typed request + disposable provider

episodic memory
→ evidence-bound proposal, conflict/expiry controls

HITL
→ Human Admit / exception receipt

release
→ exact subject + proof/control/mutation + Human decision
```

Do not copy PDF example latency, memory usage, market/adoption claims, model behavior, provider availability or license conclusions into repository truth without independent current evidence.

## Shared document-route interface

Bettor implements the same route names consumed by `skills-shared`, `runtime-env` and `agent-shield-monorepo`:

```text
README.md
AGENTS.md
CLAUDE.md
CONTEXT.md
ARCHITECTURE.md
docs/INDEX.md
docs/architecture/DOCUMENT_ROUTING.md
docs/architecture/STATE_MACHINES.md
docs/integration/CROSS_REPO_INTEGRATION.md
docs/traceability/TRACEABILITY_INDEX.md
<governed-directory>/README.md
```

A README explains ownership, State Machine, input/output, evidence and navigation. It never replaces module manifests, schemas, CLI contracts, scripts, tests, receipts or Git history.

## Macro / Micro boundary

| | Macro / Composition | Micro / Task |
|---|---|---|
| Owns | module selection, dependency/conflict resolution, projection, proof matrix, Human Admit, lock, promotion/rollback | typed task, bounded iteration, private module state, typed result, named exits |
| Reads | manifests, public capabilities, locks, receipts | own Context Capsule, source, own private closure |
| Cross-module seam | capability + `loopctl` public port | typed packet → public port → artifact/receipt ref |
| Must not | learn private flags or per-run temp | import another module’s private executable or read another run directory |
| State authority | trusted resolver/reducer/operator | no Human Admit, promotion or production rollback |

The only seam is the public interface, typed packet, artifact reference, exact exit and receipt.

## Internal / external consumption

```text
Symlink       local development projection
Bundle + lock reproducible execution
CLI / MCP     public consumption
```

- Same-module adapters may invoke executables in their own closure.
- Same-repo cross-module use goes through a stable API or `loopctl`.
- External repositories default to immutable Bettor release + stateless MCP.
- Symlinks must not carry cross-repo executables, environments, browser profiles, credentials or cloud dependencies.

## CLI, MCP, and passive context

1. `loopctl/contract.json` is canonical; MCP tools derive from it.
2. Commands default hidden unless both the public command and policy expose them.
3. Every external call pins an immutable subject and runs in a disposable workspace/bundle.
4. Callers cannot provide server-host paths, arbitrary `cwd`, private flags, secrets, sessions or browser profiles.
5. Accept only typed packets, closed inline bundles or content-addressed artifact references.
6. Macro work is packetized (`plan → resolve → verify → status`), not one hidden long-lived call.
7. Human Admit, live-repo apply, promotion, production rollback, secret rotation and permission widening are never model tools.
8. Context materialization preserves root and loop native files; do not flatten them into one ad-hoc prompt.

```text
immutable release
→ root/loop context selected
→ tracked bytes materialized
→ digest frozen
→ allowlisted host driver
→ typed output
→ context/driver receipt
```

## LoopX-compatible hard execution boundary

```text
typed request + exact subject + assertion digest
→ host-owned runner
→ disposable worktree/process group
→ executable + argv[]
→ stdout/stderr/diff/artifact observations
→ independent assertions
→ subject-bound receipt
→ trusted reducer/Human Admit
```

The Worker cannot:

- mark a Todo complete;
- write gate PASS;
- change quota;
- write durable memory directly;
- waive a hard gate;
- promote or roll back a release.

A local process runner cannot claim network/filesystem isolation it did not physically enforce.

## Proof and anti-jitter

Each module needs independent arrival paths:

- `proof`: traversal/artifact claim;
- `control`: execute the real public port;
- `mutation` or hollow: prove a load-bearing guard turns red;
- `consumer-canary`: exercise released adapter from outside its owner checkout;
- `release-receipt`: aggregate one exact composition subject.

`ABSENT`, `FAIL`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, hashed-not-run and `PASS` never proxy one another. Exit codes propagate unchanged. Module proof identity is closure-scoped; an unrelated repository HEAD move does not invalidate an isolated module.

## Conflict, Skills, runtime, providers and memory

- Every tracked path has exactly one module owner or explicit generated/evidence classification.
- Root projections are deterministic; modules do not maintain parallel authority copies.
- `SKILL.md` contains generalized procedure, laws and resource routing. Consumer-specific facts belong in `.skill-bindings/` and nearest READMEs.
- `runtime-env` synchronizes secret-free projections; consumer gates are offline and never auto-sync source.
- Serena, GrepAI, Code-Graph-RAG and Mem0 are capability providers, not truth stores.
- Current source, manifests, tests, runtime receipts and current ADRs outrank provider/memory output.
- Memory mutation is proposal-only until retention, provenance, conflict, privacy and Human Admit gates pass.
- Claude Code, Codex, Grok Build, Pi, OpenCode and Ante are actors/adapters with independent trace completeness and live evidence.
- Signed-in sessions, cookies, profiles and secret values never enter Git, bundles, MCP payloads or receipts.

## Four-repository integration

```text
skills-shared immutable procedural release
+ runtime-env secret-free runtime contract
→ Bettor module/Skill/runtime composition
→ loopctl/MCP/bootstrap release
→ Agent Shield provider/product canaries
→ Bettor external-release acceptance
→ Human promotion or rollback
```

Mutable sibling checkouts, local symlinks and `main` branch names are not release identity.

## Evidence vocabulary

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

`IMPLEMENTED` describes current bytes/contracts; it does not mean a live environment was exercised. Source prose, diagrams, package presence, old SHAs, skipped jobs, another provider or another environment cannot create live PASS.

## Completion contract

Before stopping, report:

```text
audit subject and source class
changed module IDs / interface versions / closure digests
changed document routes and directory owners
directory → State Machine → input/output/evidence delta
affected transitive dependents
changed public CLI / MCP surface
path ownership conflicts
proof / control / mutation-hollow results
LoopX requirement states and blockers
Claude / Codex / Grok / Pi / OpenCode / Ante adapter status
GitHub / Forgejo origin and exact-head status
browser / provider / external-consumer canary status
remaining ABSENT / NOT_IMPLEMENTED / NOT_EXERCISED / SKIPPED_BY_POLICY
Stack PR base/head/merge order
rollback subject
Human Admit boundary
```

Missing an applicable item forbids a claim that modular integration is complete.

## Rule → evidence routing

| Law | Evidence |
|---|---|
| Green depends on arrival path | proof + independent control + external canary remain separate |
| An instrument must turn red | module selftests and mutation/hollow fixtures |
| Absence is not denial | explicit `ABSENT` / `NOT_EXERCISED` states |
| A module does not depend upward | ownership roots, public ports and relocation/isolation controls |
| Worker prose is not verdict | OS/artifact observations + independent assertions |
| A UI/checkpoint is not authority | subject-bound reducer/receipt + Human Admit |
