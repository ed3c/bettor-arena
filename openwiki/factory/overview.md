---
type: Architecture
title: Seed-repo factory — overview and workflow
description: The bounded micro-loop that turns one admitted source packet into a standalone seed repo — eight bases, ownership boundary, the F0→H1 stateful workflow, source-kind routing, and the v2 execution plan pointer.
tags: [factory, micro-loop, workflow]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: 2c36ddf
covers: [seed-factory, eight-bases, stateful-workflow, source-kinds]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# Seed-repo factory — overview and workflow

`loop_wiki/evolve-perfect-seed-repo-factory/` is the repo's micro-loop factory: it accepts one admitted physical source packet of kind `dr`, `gcr`, `repo`, or `grill-me` and materializes a standalone repo whose local operator skill executes exactly twenty dependency-valid reasoning functions for an explicit task (src: loop_wiki/evolve-perfect-seed-repo-factory/PROMPT.md:3-7). It was migrated in as S3 via the S2 engine (commit b7983da). It is deterministic: `run.sh` is a one-shot dispatch with no iteration logic; a failed packet/build surfaces to the caller for packet or code repair — "it does not ask an LLM to self-repair or self-admit" (src: loop_wiki/evolve-perfect-seed-repo-factory/AGENTS.md:24-27).

## Eight bases

The sandbox owns all eight harness bases itself (src: loop_wiki/evolve-perfect-seed-repo-factory/AGENTS.md:12-23): passive context = its own `AGENTS.md`/`CLAUDE.md`; settings/authorization = local-only Bun commands, no network or shell-bearing packet fields; lifecycle evidence = `_engine-run/` + `PLAN.md`; routes and specialized skill = `ROUTES.md`, `.agents/agents/seed-factory-router.md`, `.agents/skills/perfect-seed-domain/SKILL.md`; independent verifier = fast-quality receipt, `verify.sh`, `selftest.sh`, generated-repo validator; target contract = `PROMPT.md`; state ledger = `PLAN.md`.

## Ownership boundary

Three layers, strictly separated (src: loop_wiki/evolve-perfect-seed-repo-factory/AGENTS.md:29-37):

- The **macro loop** owns orchestration, cross-loop comparison, and human admission.
- **This loop** owns one packet's validation, reduced IR, repo materialization, twenty-call local execution, route result, baseline/trend, and failure surface.
- The **generated repo** owns its local operator skill and local data; it does not own the factory's governance or sibling-loop routing. Its product contract is [generated-repo](generated-repo.md).

"Perfect" is an optimization target; legal machine states are candidate, validated, failed, human-required (src: loop_wiki/evolve-perfect-seed-repo-factory/AGENTS.md:36-37).

## Stateful workflow (ROUTES.md)

| node | actor | validator | pass edge | failure edge |
|---|---|---|---|---|
| F0 FAST-PREFLIGHT | mechanical script | lineage/format/lint/type receipt | M0 | preflight-repair |
| M0 MATCH | `seed-factory-router` | `src/contracts.ts` | G1 | packet-repair |
| G1 GENERATE-IR | mechanical script | nonzero evidence + hash binding | V1 | source-intake |
| V1 VALIDATE-IR | mechanical script | public behavior tests | G2 | implementation-repair |
| G2 GENERATE-REPO | mechanical script | generated repo tests | V2 | discard-partial-output |
| V2 VALIDATE-REPO | mechanical script | fast quality + full repo verifier | R1 | repo-repair |
| R1 RECORD-OBSERVE | mechanical script | baseline/trend gates | H1 | drift-review |
| H1 ADMIT | human | human judgment | admitted/rejected | return to named node |

(src: loop_wiki/evolve-perfect-seed-repo-factory/ROUTES.md:5-14). The actor boundary is explicit: `main-session` owns integration and human-facing synthesis; `mechanical-script` owns schemas, hashes, counts, DAG execution, and tests; the router agent "returns one route only"; the domain skill owns local terminology; external research/judgment is not performed by this loop; the human owns lifecycle seed admission and architecture replacement (src: loop_wiki/evolve-perfect-seed-repo-factory/ROUTES.md:26-32).

## Source kinds and bounded interpretations

Each source kind gets a bounded interpretation and NO extra authority (src: loop_wiki/evolve-perfect-seed-repo-factory/ROUTES.md:17-23): `dr` = source-linked research narrative (external facts remain candidate); `gcr` = conversation intent and proposed mechanisms (speaker claims are not truth by default); `repo` = read-only bounded file manifest and excerpts (no mutation; bounded to 200 non-ignored files and 128 KiB excerpts per file, src: loop_wiki/evolve-perfect-seed-repo-factory/modules/architecture.md:24-25); `grill-me` = explicit questions/answers/constraints/taste signals (no claim the interview is complete).

## The modules/ SSOTs

Four context/format documents own their domains; the packet contract makes one of them load-bearing:

- `modules/architecture.md` — the reduced-IR record table (what entropy each record removes and what information it preserves), the code-SSOT boundary, and the gate order chain ending in "future asynchronous Code Quality + Production Use axes → human admit" (src: loop_wiki/evolve-perfect-seed-repo-factory/modules/architecture.md:3-40).
- `modules/exchange-formats.md` — packet/result schema semantics; see [packet contract](packet-contract.md).
- `modules/production-readiness.md` — must be read before claiming reusable-seed status (src: loop_wiki/evolve-perfect-seed-repo-factory/AGENTS.md:9).
- `modules/semantic-truth-context.md` — a HARD packet requirement: `readInputPacket` rejects any packet whose `fixed_prompt_context` does not include it (src: loop_wiki/evolve-perfect-seed-repo-factory/src/contracts.ts:127-130).

## Governance rule

"Never edit tests, baselines, or packet state merely to make a target pass. Baseline changes require a reviewed/admitted baseline-update packet" (src: loop_wiki/evolve-perfect-seed-repo-factory/AGENTS.md:47-48) — see [verification](verification.md) for the governed baseline mechanism.

## v2 execution plan

The factory carries its own admitted evolution contract under `plans/perfect-seed-v2/` — a canonical, machine-readable plan for evolving `perfect-seed-repo@1.1.0` to a standalone `@2.0.0`. It is a plan, not implementation evidence, with its own truth-layer discipline: [v2 plan](v2-plan.md).

## Entry commands

```sh
sh verify.sh                                        # T0 chain
sh selftest.sh                                      # good/hollow control
sh trigger.sh packets/inbox/dr-example.json /absolute/output/path
```

(src: loop_wiki/evolve-perfect-seed-repo-factory/AGENTS.md:40-45). The full pipeline is [build-pipeline](build-pipeline.md).
