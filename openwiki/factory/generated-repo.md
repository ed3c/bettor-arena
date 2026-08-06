---
type: Contract
title: Generated seed repo — the product contract
description: What a factory-generated repo must contain and prove — the 13-file requirement set, the 20-call operator runtime invariants, the shared minimum-lineage module, template lifecycle governance, and the local operator skill.
tags: [factory, generated-repo, operator]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: 2c36ddf
covers: [generated-repo-contract, twenty-call-operator, minimum-lineage, template-lifecycle]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# Generated seed repo — the product contract

The factory's product is itself a repo with a contract. This page documents what every generated repo must contain, what its operator runtime guarantees, and which validators enforce each piece. The template SSOT is `templates/repo/`; "generated repos are versioned products" (src: loop_wiki/evolve-perfect-seed-repo-factory/modules/architecture.md:19-20).

## Required content — the 13-file set

`src/verify_generated_repo.ts` hard-requires (src: loop_wiki/evolve-perfect-seed-repo-factory/src/verify_generated_repo.ts:11-26): `AGENTS.md`, `.agents/skills/seed-repo-operator/SKILL.md`, `scripts/plan.ts`, and ten `data/` records — `source.json` (source kind, packet/task hashes, gate), `evidence.jsonl` (stable ids, refs, hashes, excerpts), `claims.jsonl` (claim→evidence bindings and grounding), `unknowns.json` (KK/KU/UK/UU rows), `decisions.jsonl` (state, decision, evidence, grounding), `lineage.json` (packet/template/task/manifest/file hashes), `artifact-manifest.json`, `build-receipt.json`, `call-plan.json` (exact task and dependency order), `call-results.jsonl` (input/output hashes per call). The per-record semantics — what entropy each removes, what information it preserves — are the reduced-IR table (src: loop_wiki/evolve-perfect-seed-repo-factory/modules/architecture.md:5-15).

Beyond presence, the validator asserts consistency (src: verify_generated_repo.ts:27-67): both `source.json.human_gate` and `lineage.json.terminal_human_gate` must still read `required_before_seed_admit` ("generated repo lost human admit gate"); `source_refs` are shape-valid in both files AND byte-identical between them; `refs_status` agrees between them and is consistent with the refs shape (sentinel refs force `sentinel`; otherwise `declared`/`resolved`/`stale` are the legal values, src: verify_generated_repo.ts:38-42); exactly 20 call records exist in both plan and results with unique ids and strictly earlier-indexed dependencies; `plan.task_sha256` matches the task bytes; every result's `output_sha256` re-hashes correctly; and the FINAL call must be `F20` with `output.admit_edge === "human_required"` ("final call must surface human_required").

## Operator runtime — templates/repo/src/operator.ts

`runOperator` enforces at run time (src: loop_wiki/evolve-perfect-seed-repo-factory/templates/repo/src/operator.ts:12-53): the capability registry contains exactly 20 calls with no duplicate call_ids; every dependency of a call was already executed; a handler exists for every function name; each call's input (task + source packet sha + dependency output hashes) and output are sha256 hash-bound; and the run writes `data/call-plan.json` (`perfect-seed-call-plan@1.0.0`) plus `data/call-results.jsonl`. The registry itself is `templates/repo/src/capabilities.ts`: F01 `load_task_context` … F20 `synthesize_next_action`, a fixed dependency DAG (src: loop_wiki/evolve-perfect-seed-repo-factory/templates/repo/src/capabilities.ts:3-24). The CLI wrapper `scripts/plan.ts --task <task>` prints `{"status":"candidate-human-admit-required", call_count, final_call}` and exits 64 on usage, 1 on failure (src: loop_wiki/evolve-perfect-seed-repo-factory/templates/repo/scripts/plan.ts:1-24).

## Minimum lineage — a deliberate template↔factory shared module

`templates/repo/scripts/check_minimum_lineage.ts` is the IMPLEMENTATION: it pins its own required-manifest path list (including itself) and hash-verifies manifest entries (src: loop_wiki/evolve-perfect-seed-repo-factory/templates/repo/scripts/check_minimum_lineage.ts:5-16). The factory-side `src/minimum_lineage.ts` is a one-line re-export of it (src: loop_wiki/evolve-perfect-seed-repo-factory/src/minimum_lineage.ts:1) — a deliberate cross-boundary dependency: the factory verifier and every generated repo judge lineage with the same bytes, so the check cannot drift between producer and product. `verify_generated_repo.ts` calls `verifyMinimumLineage(root)` first (src: verify_generated_repo.ts:4-10), and the factory's own F0 preflight runs `src/check_factory_minimum_lineage.ts` (src: loop_wiki/evolve-perfect-seed-repo-factory/verify.sh:7).

## Template lifecycle governance

`templates/template-metadata.json` (`perfect-seed-template-lifecycle@1.0.0`) currently declares `template_version: perfect-seed-repo@1.1.0`, `lifecycle_state: validated`, `human_admit: false`, promotion evidence `tests/seed_factory.test.ts` + `verify.sh` (src: loop_wiki/evolve-perfect-seed-repo-factory/templates/template-metadata.json:1-7). `src/check_template_lifecycle.ts` validates: known schema; state ∈ {draft, validated, seed, deprecated, retired}; **state `seed` requires `human_admit: true`**; and every promotion-evidence path must exist (src: loop_wiki/evolve-perfect-seed-repo-factory/src/check_template_lifecycle.ts:5-16). `materialize.ts` stamps the same `TEMPLATE_VERSION` constant into lineage (src: loop_wiki/evolve-perfect-seed-repo-factory/src/materialize.ts:6), so a product always names the template that made it.

## The local operator skill

Each generated repo carries `.agents/skills/seed-repo-operator/` — role: "turn one explicit task into exactly twenty local function calls … it does not claim semantic perfection, external research, or independent model consensus"; workflow Match→Generate→Validate→Record→Observe→Admit with "never auto-admit the seed or a repo mutation" as the terminal rule (src: loop_wiki/evolve-perfect-seed-repo-factory/templates/repo/.agents/skills/seed-repo-operator/SKILL.md:9-24). `cases.json` (`seed-repo-operator-cases@1.0.0`) ships positive/negative trigger cases with expectation `twenty-local-calls` (src: loop_wiki/evolve-perfect-seed-repo-factory/templates/repo/.agents/skills/seed-repo-operator/cases.json:1-19). Ownership: the generated repo owns this skill and its local data, not the factory's governance (src: loop_wiki/evolve-perfect-seed-repo-factory/AGENTS.md:32-33).

## How the contract is exercised

Live in three places: per-trigger by the [build pipeline](build-pipeline.md)'s validator stage; per-`verify.sh` run against a fresh temp build including `bun test` of the generated repo's own `tests/operator.test.ts` (src: loop_wiki/evolve-perfect-seed-repo-factory/verify.sh:20-24); and by the anti-placebo hollow control that removes the operator skill and requires failure (src: loop_wiki/evolve-perfect-seed-repo-factory/selftest.sh:13-18) — see [verification](verification.md). The validator's own reds are named tests in `tests/seed_factory.test.ts`: "generated repo verifier rejects a lineage stripped of source_refs" (:534), "generated repo verifier rejects a source.json whose refs_status diverges from lineage" (:495), and "minimum-lineage gate accepts a fresh repo and rejects one-byte template drift" (:184).
