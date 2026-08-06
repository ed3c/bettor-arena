---
type: Verification
title: Factory verification — T0 chain, hollow control, portability, baselines
description: The factory's verifier topology — verify.sh's full T0 chain, the selftest good/hollow anti-placebo pair, the git-archive portability proof with negative controls, governed baselines, and the PLAN.md iteration ledger.
tags: [factory, verification, baselines]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: 2c36ddf
covers: [t0-verify, hollow-control, portability, governed-baseline]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# Factory verification — T0 chain, hollow control, portability, baselines

The verifier topology is declared in the state ledger (src: loop_wiki/evolve-perfect-seed-repo-factory/PLAN.md:5-27) and implemented by three scripts plus the baseline/trend gates.

## verify.sh — the T0 chain

Ordered stages (src: loop_wiki/evolve-perfect-seed-repo-factory/verify.sh:1-32):

1. Required-file presence for the whole eight-base surface (passive context, modules, scripts) (src: verify.sh:7-9).
2. `bun run quality:fast` — the F0 physical minimum-lineage/format/lint/typecheck receipt (mount 2 of [the single fast-quality definition](../gates/fast-quality.md); src: verify.sh:11, PLAN.md:7-9).
3. `bun test tests/seed_factory.test.ts` — the factory behavior suite (20 tests / 225 assertions at iteration 7; src: loop_wiki/evolve-perfect-seed-repo-factory/PLAN.md:40).
4. `src/stats.ts --check` and `src/check_template_lifecycle.ts` (template lifecycle governance, see [generated-repo](generated-repo.md)) (src: verify.sh:13-14).
5. Schema replay: migrate `packets/inbox/legacy-dr-example.json` to a temp file, then `cli.ts validate` it (src: verify.sh:16-19).
6. A REAL build into a temp dir, then the same three post-trigger validators as production: generated fast quality, the generated repo's own `scripts/plan.ts` run, `bun test` of the generated `tests/operator.test.ts`, and `verify_generated_repo.ts` (src: verify.sh:20-24).
7. Trend recording: `src/record_trend.ts` must produce exactly one line (src: verify.sh:25-26).
8. Governed baseline: `src/update_baseline.ts` applied to `packets/outbox/baseline-update-example.json` must reproduce `baselines/seed-stats.json` byte-identically (`cmp -s`), else "governed baseline output drift" (src: verify.sh:27-28).
9. Governance greps: the baseline-update packet must declare `packet_kind: baseline-update`, the behavior-eval packet must preserve `human_gate: required_before_seed_admit` (src: verify.sh:30-31).

Baseline changes never happen by editing the file: "Baseline changes require a reviewed/admitted baseline-update packet" (src: loop_wiki/evolve-perfect-seed-repo-factory/AGENTS.md:47-48).

## selftest.sh — the anti-placebo pair

Positive control: build a good repo, run its operator, validate it. Hollow control: copy the good repo, rename away its `seed-repo-operator/SKILL.md`, and REQUIRE `verify_generated_repo.ts` to fail — "PASS: good repo passed and hollow repo failed" (src: loop_wiki/evolve-perfect-seed-repo-factory/selftest.sh:9-19). This is the §1 rule (every green needs a demonstrated red) applied to the product validator itself.

## portability.sh — relocation proof with negative controls

Extracts `HEAD:<this loop>` with `git archive` into a directory OUTSIDE the repository, installs from the committed lockfile, and requires its own T0 to pass there. Two negative controls: the archive must not ship `node_modules` and must FAIL `verify.sh` before install ("otherwise the green is not bought by the clean install"), and removing one `verify.sh` required file must return exit 2 ("otherwise the instrument is not demonstrably capable of going red"). It refuses a dirty subtree because `git archive` reads HEAD "and a green result would then describe a commit nobody is looking at" (src: loop_wiki/evolve-perfect-seed-repo-factory/PLAN.md:12-20). It is deliberately OUTSIDE verify.sh — verify.sh is the per-iteration hot path and this pays for a real `bun install`; execution is an explicit human/CI act with the receipt landing in `_engine-run/portability-receipt.json`. Claim boundary: "relocatability of HEAD, not of the working tree" (src: PLAN.md:20-26).

## PLAN.md — the iteration ledger

STATUS: candidate (src: loop_wiki/evolve-perfect-seed-repo-factory/PLAN.md:3). The trajectory table records eight iterations of alternating RED/GREEN with concrete evidence per row — e.g. iteration 0: "public CLI tests failed because src/cli.ts did not exist"; iteration 4: the generated-repo fast gate exposed 11 format drifts + 2 strict lint defects and the factory lanes 14 more; iterations 6–7: the source_refs feature landed red-first then green with the NOT_RUN and sentinel semantics (src: PLAN.md:29-40). Remaining human gates are ledgered too: whether the seed complements or replaces the plan-truth mother loop, whether a future carrier may turn the twenty local calls into external LLM/MCP calls ("this implementation does not authorize that boundary"), and the async CQ/PU promotion gates that keep fast quality preflight-only until built (src: PLAN.md:42-49).

## _engine-run/ — the evidence yard

Gitignored runtime evidence: `fast-quality.*.receipt.json` receipts, `build.<packet_id>.{out,err}` logs, `exchange-context.<packet_id>.md` files, `s3-selftest.log`/`s3-verify.log` migration-era logs, and `portability-receipt.json` (src: loop_wiki/evolve-perfect-seed-repo-factory/ROUTES.md:38-39; AGENTS.md:18). See [data ledgers](../data-ledgers.md) for the repo-wide receipt map.
