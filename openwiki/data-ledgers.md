---
type: Reference
title: Data and receipt ledgers
description: The repo-wide receipt-landing map — tracked frozen evidence vs gitignored runtime receipts, the migration ledgers, MCP receipt chains, and the receipt immutability discipline with its single exception.
tags: [receipts, data, evidence]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: ca72a92
covers: [receipt-discipline, data-ledgers, frozen-evidence]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# Data and receipt ledgers

A **receipt** is machine-verifiable execution evidence; success and failure both land. Historical receipts are frozen evidence — "rewriting evidence is forging evidence" — with exactly one explicit exception: the migration engine's `--force-receipt`, where rerun intent must be stated and the default is collision refusal (src: CONTEXT.md:10-13). This page maps every receipt landing site in the repo.

## data/migration/ — the migration ledger

- `manifest.json` — the declarative migration surface, not a receipt ([engine](migration/engine.md)).
- `report-<source-commit-7>-<component-set>.json` — per-run apply receipts, append-only, collision-refused (exit 64) unless `--force-receipt` (src: scripts/migrate/migrate_seed.py:17-21, 407-436). Currently one: `report-f3776cb-agents-skills.json`.
- `last-migration-report.json` — a COPY of the latest run kept for existing readers, regenerated at execution time (src: ARCHITECTURE.md:41; scripts/migrate/migrate_seed.py:441-450). The S3/S4 applies predate the per-run mechanism; their receipts exist only as git-history versions of `last-migration-report.json` (src: ARCHITECTURE.md:41).

## data/wiki-update/ — the factory-to-wiki delivery ledger (ISSUE-23, gitignored)

Runtime landing site for the second host-loop↔factory seam, gitignored in full (src: .gitignore:5). Producer is the factory's [build pipeline](factory/build-pipeline.md) delivery terminus (`trigger.sh`); consumer is the digestion station documented on [kb-ingest official port](kb-ingest/official-port.md#wiki_update_workersh-digestion-station-for-factory-wiki-update-requests). The request lands HERE rather than in the sandbox's `packets/outbox/` by design, for two stated reasons: the digestion station must "never depend on sandbox layout" (the factory can move, be renamed, or run relocated — its `portability.sh` proof does exactly that), and a standalone extracted tree has no arena ledger at all, which is why emission outside an enclosing git repo is a NAMED skip instead of a write to a path that only sometimes exists (src: loop_wiki/evolve-perfect-seed-repo-factory/trigger.sh:91-108).

- `request-<packet_id>.json` (`bettor-arena-wiki-update-request@1.0.0`) — written once per successful delivery, `request_id` = `<packet_id>@<git_head>`. Three context lanes: `fixed_prompt_context` (pointers to the official update prompts, never copied text), `iteration_auto_context` (a deterministic delta — `delta_status` ∈ `computed`/`no-last-update`/`unresolvable-last-head`, each a named state rather than a silent empty array; in the `computed` case `changed_files` is `git diff --name-only <recorded gitHead> HEAD` over the arena), `emergent_prompt_context` (a pointer to `openwiki/quickstart.md#backlog` — emergent content itself never lands here or in any standards module, src: CONTEXT.md:16-18).
- `receipt-<packet_id>.json` (`bettor-arena-wiki-update-receipt@1.0.0`) — the digestion station's execution evidence, back-linking `request_id`; collision-refused (exit 64, the FATAL evidence-precondition class, not the contract-fail 2) unless `WIKI_UPDATE_FORCE_RECEIPT=1`, which disables exactly the pre-write existence refusal and nothing else — the same frozen-evidence discipline as the migration engine's `--force-receipt` (src: kb-ingest/port/wiki_update_worker.sh:341-343). Because this whole directory is gitignored, git history protects none of it: that collision refusal is the ONLY immutability enforcement these receipts get (src: .gitignore:4-7).
- `regen-<packet_id>.json` — the real-run LLM transcript (`claude -p --output-format json`) for the regeneration turn, written only in a real (non-dry-run) pass (src: kb-ingest/port/wiki_update_worker.sh:190-194).

A tree with no enclosing git repository (the factory's `portability.sh` extracted archive) skips emission by name (`wiki_update_request=skipped-standalone`) rather than silently omitting the artifact — see [build pipeline](factory/build-pipeline.md).

## openwiki/.last-update.json — the wiki freshness anchor

Not under `data/`, but it is a ledger artifact all the same: the single record of the last successful documentation run, and the anchor three independent readers hang decisions on. Its **sole writer** is `openwiki_post.py`'s `write_last_update` (the finalize pass) — the doc agent is explicitly told the CLI records this metadata, and the digestion station's real run asserts rather than writes it (src: kb-ingest/port/openwiki_post.py:518-534). `gitHead` is only emitted when finalize is given `--target` AND `git rev-parse HEAD` in that target actually returns output; a metadata file without `gitHead` is therefore a real state, and each reader treats it distinctly (src: kb-ingest/port/openwiki_post.py:527-532):

- `bootstrap.sh` doctor → an empty/unresolvable `gitHead` is "freshness undecidable", a WARN distinct from "stale" because the anchor itself is unusable (src: bootstrap.sh:56-57).
- `trigger.sh` delta computation → no extractable `gitHead` is `delta_status: no-last-update` with an empty `changed_files`; a `gitHead` that `git cat-file -e` cannot resolve in the arena is `unresolvable-last-head` — two named absences, never a silent empty delta (src: loop_wiki/evolve-perfect-seed-repo-factory/trigger.sh:110-123). The digestion station re-validates that this enum is one of the three named states at parse time (src: kb-ingest/port/wiki_update_worker.sh:76-78).
- `wiki_update_worker.sh` real-run finalize assert → after the post passes rewrite the file, the recorded `gitHead` (strict 40-hex extraction) must equal `git rev-parse HEAD`, and an ABSENT `gitHead` fails that assert by name (`gitHead absent != HEAD`) — the worker reads it back, never trusts the write (src: kb-ingest/port/wiki_update_worker.sh:328-332).
- the official update prompt → "If no prior `gitHead` exists, inspect recent history selectively" (src: kb-ingest/openwiki/update.system.md:187).

Two finalize-stage behaviors are tied to this file's neighborhood: the worker deletes `openwiki/_plan.md` right after finalize, mirroring upstream's middleware which removes the temporary plan file after the run — the plan states INTENT, and leaving it would both let a later verifier mistake intent for content and hand the index generator a control file (src: kb-ingest/port/wiki_update_worker.sh:326-327; kb-ingest/port/openwiki_subagent.sh:90-93). And both worker modes pass `--normalize-backlog` to finalize so quickstart's heading is normalized back to exactly `## Backlog` whenever a run left trailing title text on it (the text survives as the section's first line — mechanics on [kb-ingest official port](kb-ingest/official-port.md#openwiki_postpy-the-code-owned-passes)), which is what keeps the emergent lane's `openwiki/quickstart.md#backlog` pointer (carried in every wiki-update request above) resolvable run over run (src: kb-ingest/port/wiki_update_worker.sh:308-309, 321-322; kb-ingest/port/openwiki_post.py:544-559).

One consistency caveat worth knowing when these readers disagree: `trigger.sh` and `wiki_update_worker.sh` extract `gitHead` with a strict 40-hex `sed` pattern, while `bootstrap.sh` uses a looser `[0-9a-f]*` match — a malformed (short or truncated) `gitHead` therefore reads as `no-last-update` to the factory but as a resolvable-or-undecidable anchor probe to the doctor, so the two can legitimately report different states for the same file (src: trigger.sh:112; wiki_update_worker.sh:330; bootstrap.sh:51-52).

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

The factory's `route-result.<packet_id>.json` files are receipts of a triggered build (four stage exit codes + refs status + the mandatory human gate) and live beside the packets, not under `data/` (src: loop_wiki/evolve-perfect-seed-repo-factory/trigger.sh:70-85). A successful route result is also the trigger for the `data/wiki-update/` request above — the two ledgers are sequential stages of one delivery, not duplicates.

## The evidence allowlist as a ledger

`scripts/gates/root_coupling_allowlist.txt` is itself an accounting surface: each entry declares "this file carries historical absolute paths as evidence identity" and is standing debt (src: CONTEXT.md:14-15). The [migration engine](migration/engine.md) appends to it on apply; the [root-coupling gate](gates/structure-gates.md) reads it on every run.
