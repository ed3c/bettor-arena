---
type: Reference
title: Data and receipt ledgers
description: The repo-wide receipt-landing map — tracked frozen evidence vs gitignored runtime receipts, the migration ledgers, MCP receipt chains, and the receipt immutability discipline with its single exception.
tags: [receipts, data, evidence]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: 2c36ddf
covers: [receipt-discipline, data-ledgers, frozen-evidence]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# Data and receipt ledgers

A **receipt** is machine-verifiable execution evidence; success and failure both land. Historical receipts are frozen evidence — "rewriting evidence is forging evidence" — with exactly one explicit exception: the migration engine's `--force-receipt`, where rerun intent must be stated and the default is collision refusal (src: CONTEXT.md:10-13). This page maps every receipt landing site in the repo.

## data/migration/ — the migration ledger

- `manifest.json` — the declarative migration surface, not a receipt ([engine](migration/engine.md)).
- `report-<source-commit-7>-<component-set>.json` — per-run apply receipts, append-only, collision-refused (exit 64) unless `--force-receipt` (src: scripts/migrate/migrate_seed.py:17-21, 407-436). Currently one: `report-f3776cb-agents-skills.json`.
- `last-migration-report.json` — a COPY of the latest run kept for existing readers, regenerated at execution time (src: ARCHITECTURE.md:37; scripts/migrate/migrate_seed.py:441-450). The S3/S4 applies predate the per-run mechanism; their receipts exist only as git-history versions of `last-migration-report.json` (src: ARCHITECTURE.md:37).

## data/receipts/ — host-loop receipts, tracked and untracked

**Tracked (frozen evidence)**:

- `driver-smoke.json` — one real round-trip per CLI driver lane (`claude -p` and direct `codex exec`, never the Claude host plugin), schema `bettor-arena-driver-smoke@1.0.0`, exit codes + truncated output heads, no absolute paths (src: tests/tools/driver_smoke.sh:2-10; S11, commit c38b1d5).
- `molecular-corpus-parity.json` — the original-vs-rebuilt validator parity measurement; frozen under the OLD Intent-Slice vocabulary per ADR 0001 (src: docs/adr/0001-molecular-slice-vocabulary.md:25-26); reruns write elsewhere (commit 579771c).
- `molecular-gate-smoke.json` / `molecular-gate-tdd-red.json` — the molecular gate's construction evidence: the smoke pass and the TDD red that preceded it (S8).

**Gitignored (runtime)**: `post-commit-<sha>.json` stage-request receipts written by the [post-commit hook](host-loop/git-hooks.md) on every commit (src: .githooks/post-commit:6-13; .gitignore:4, commit 05d831e).

## mcp/production/receipts/ — chained MCP verification

Append-only `\<timestamp\>-verify-\<hash\>.json` and integration receipts (seven verify + one integration as of 2c36ddf). `verify` records hashes rather than command output "so a receipt cannot become a credential or prompt dump"; receipts are chained by the SHA-256 of the preceding receipt and `check-receipts` validates the whole chain (src: mcp/production/README.md:45-47). See [MCP surface](host-loop/mcp-surface.md).

## mcp/context-pack/benchmarks/receipts/

Frozen benchmark measurement (`m1-pro-2026-07-29.json`), pinned by `mcp/context-pack/tests/test_benchmark_receipt.py` so the recorded numbers and the benchmark code cannot drift apart silently.

## Factory _engine-run/ — sandbox runtime evidence (gitignored)

`fast-quality.<epoch>.<pid>.receipt.json` (the [fast-quality](gates/fast-quality.md) receipt schema, factory mount), `build.<packet_id>.{out,err}`, `exchange-context.<packet_id>.md`, `portability-receipt.json`, and migration-era `s3-*.log` files ([verification](factory/verification.md)). Note the deliberate split: the fast-quality receipt "never lands in data/receipts/" (src: scripts/gates/fast_quality.sh:34-35) — hook-mount receipts go to stdout, factory-mount receipts stay in the sandbox.

## Route results — packets/outbox/

The factory's `route-result.<packet_id>.json` files are receipts of a triggered build (four stage exit codes + refs status + the mandatory human gate) and live beside the packets, not under `data/` (src: loop_wiki/evolve-perfect-seed-repo-factory/trigger.sh:66-81).

## The evidence allowlist as a ledger

`scripts/gates/root_coupling_allowlist.txt` is itself an accounting surface: each entry declares "this file carries historical absolute paths as evidence identity" and is standing debt (src: CONTEXT.md:14-15). The [migration engine](migration/engine.md) appends to it on apply; the [root-coupling gate](gates/structure-gates.md) reads it on every run.
