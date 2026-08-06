---
type: Component
title: fast_quality.sh — one definition, two mounts
description: The single fast-quality check definition (format/lint/type/shell-syntax), its per-extension lanes, fail-fast stage machinery, hash-bound receipt, and the preflight-only claim boundary.
tags: [gates, fast-quality, receipt]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: 2c36ddf
covers: [fast-quality, claim-boundary, gate-inputs]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# fast_quality.sh — one definition, two mounts

`scripts/gates/fast_quality.sh` is the single fast-quality check definition for the repo, realizing ARCHITECTURE §3.5's "same definition, different scope" (src: scripts/gates/fast_quality.sh:2-5). Landed as S7 (commit c435d42). Two mounts, neither redefining the checks:

- **Mount 1 — staged/preflight**: the armed [pre-commit hook](../host-loop/git-hooks.md) feeds it the staged file list from a checkout-index temp tree; any caller may feed any list (src: scripts/gates/fast_quality.sh:6-8).
- **Mount 2 — factory full scope**: `loop_wiki/evolve-perfect-seed-repo-factory/verify.sh` → `bun run quality:fast` (`src/run_fast_quality.ts`), same toolchain + configs over the whole sandbox (src: scripts/gates/fast_quality.sh:8-12).

## Input and lanes

Input is file paths as arguments or newline-separated stdin (src: scripts/gates/fast_quality.sh:13-14). Relative paths are anchored to `$PWD` immediately because lanes `cd` elsewhere; a missing input file is FATAL — "deleted paths must be filtered out by the caller" (src: scripts/gates/fast_quality.sh:67-68). Lanes by extension (src: scripts/gates/fast_quality.sh:14-31):

| Lane | Extensions | Tools | Notes |
|---|---|---|---|
| TS | `.ts .tsx .mts .cts` | factory `node_modules/.bin` prettier --check → eslint → tsc --noEmit | Runs from the factory dir (`in_factory`, src: scripts/gates/fast_quality.sh:122). TS files OUTSIDE the factory ride the same lane: eslint skips files outside its base path (warning, not a lying green — the receipt still records the stage), and tsc mirrors the factory tsconfig's compilerOptions as CLI flags because `--project` cannot take a file list (src: scripts/gates/fast_quality.sh:17-25, 131-137; strictness alignment by commit bd294c5) |
| Python | `.py` | `ruff format --check` + `ruff check --quiet` | ruff absent = FATAL 64 with install guidance, NO network fallback: "the gate judges with the locally pinned tool or refuses, it never fetches one" (src: scripts/gates/fast_quality.sh:25-28, 78-81; commit 6f8cd13) |
| Shell | `.sh .bash` | `bash -n` (`sh -n` when bash absent) | syntax only (src: scripts/gates/fast_quality.sh:28-29, 88-89) |

Cheap lanes run first "so a cheap red spares the expensive TS toolchain spin-up" (src: scripts/gates/fast_quality.sh:124-125).

## Fail-fast stage machinery

The first failing stage blocks all later stages, which are recorded as `not_run` (src: scripts/gates/fast_quality.sh:30-31, 104-120). No tests are run and no network is touched (src: scripts/gates/fast_quality.sh:31).

## Receipt and claim boundary

The JSON receipt (stdout, or `--receipt <path>`; "Never lands in data/receipts/") carries schema `bettor-arena-fast-quality-receipt@1.0.0`, per-lane counts, per-stage status/exit, and `gate_inputs` — sha256 of every involved config file plus the script itself, so config drift is visible in the receipt (src: scripts/gates/fast_quality.sh:33-36, 139-164). Its `claim_boundary` is hard-coded `preflight-only-not-code-quality-axis`: "green here is a preflight pass only, never a CQ/PU code-quality-axis claim" (src: scripts/gates/fast_quality.sh:36-38, 161) — iron law 5 (src: ARCHITECTURE.md:51-53). Factory-side receipts of this shape accumulate under `loop_wiki/evolve-perfect-seed-repo-factory/_engine-run/fast-quality.*.receipt.json`.

Exit codes: 0 pass · 2 check failed · 64 FATAL (usage, missing file, missing tool). `FAST_QUALITY_FACTORY` overrides the factory path as a test seam (src: scripts/gates/fast_quality.sh:39-40).

## Focused test

`tests/test_fast_quality.sh` carries a negative control per lane (TS type error, Python format violation, shell syntax error), a clean positive control, a fail-fast `not_run` assertion, a ruff-absent FATAL 64, plus the pre-commit-side controls (self-integrity block, budget FATAL, <5s bound) — "every green here was first seen red while this file predated the implementation" (src: tests/test_fast_quality.sh:2-11). The seam test was retargeted to the ACTIVATED hook when #14 stage 1 armed it (commit 0d01497). Mount 2 has its own named coverage in the factory suite: "factory fast gate writes a preflight-only receipt in fail-fast order" (src: loop_wiki/evolve-perfect-seed-repo-factory/tests/seed_factory.test.ts:271), "generated repo exposes a local fail-fast quality gate" (:208), and "generated quality gate detects format, lint, and type defects at their physical stages" (:225) — the stage-attribution proof that a format, lint, and type defect each fails at its OWN stage, not a merged one.
