---
type: Architecture
title: MCP surface — declarations, context-pack server, production engine
description: The three portable MCP server declarations for both hosts, the read-only repo-context-pack AST server, and the profile-driven mcp/production migration engine with chained receipts and human gates.
tags: [mcp, host-loop, context-pack]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: 2c36ddf
covers: [mcp-declarations, context-pack, mcp-production-migration]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# MCP surface — declarations, context-pack server, production engine

The MCP surface landed as S10 (issue #12, commit 3bfd114): portable declarations for two hosts plus the adapter layer under `mcp/` (src: ARCHITECTURE.md:26, 31). Approval is always human-owned — [bootstrap](bootstrap.md) prints the steps and never performs them (src: bootstrap.sh:50-58).

## The three declarations (the "三件套")

Both host files declare the same three stdio servers — `grepai`, `repo-context-pack`, `serena`:

- **Claude Code**: `.mcp.json` (src: .mcp.json:2-30). Enabling project MCP is a human admit (src: CLAUDE.md:6).
- **Codex**: `.codex/config.toml`, loaded only after the repo is trusted; it ships ONLY the portable MCP payload — permission profiles, network policy, unix-socket allowlists and plugin toggles are "HOST SECTIONS PENDING (human-owned, never automated)", added by hand per host (src: .codex/config.toml:1-9). It additionally pins per-server timeouts and `enabled_tools` allowlists (src: .codex/config.toml:19-27, 36-42, 50-64).

Every launcher begins `repo_root="$(git rev-parse --show-toplevel)" || exit 1; cd "$repo_root"` before exec, so sessions started in nested directories cannot bind a different root — the declarations are portable to any clone (src: .mcp.json:8, .codex/config.toml:2-4). Serena is pinned to an exact upstream commit in the `uvx --from git+…@32308a87…` URL for both hosts (src: .mcp.json:26, .codex/config.toml:48), differing only in `--context claude-code` vs `--context codex`.

## mcp/context-pack — read-only Python AST evidence server

A repository-bound MCP server for building evidence-budget Python context packs, deliberately narrower than code search or LSP: "GrepAI and Serena find candidate files and symbols; repo-context-pack re-opens the selected source under the configured repository root" (src: mcp/context-pack/README.md:5-9). Guarantees:

- Rejects absolute paths, traversal, symlink escapes, unsupported languages, oversized files, and files that change while being read (src: mcp/context-pack/README.md:10-11).
- Every result is bound to the source bytes with SHA-256 and reports partial completeness; signature and unresolved dynamic-call evidence is mandatory, lower-priority facts are dropped when the explicit byte budget runs out (src: mcp/context-pack/README.md:12-14).
- Budget bounds are hard constants: `MIN_BUDGET_BYTES = 1_024`, `MAX_BUDGET_BYTES = 65_536`, default max source 2 MiB; all failures raise the fail-closed `ContextPackError` (src: mcp/context-pack/src/context_pack_mcp/engine.py:15-23).
- Exactly two tools: `build_python_context_pack(relative_path, symbol, max_bytes)` and `context_pack_status()`; only repository-relative `.py` paths — "TypeScript support is not implied" (src: mcp/context-pack/README.md:34-38).
- An explicitly disclaimed non-claim: it does NOT claim local memory alignment controls remote prompt caching; cache hits must be measured at the API boundary (src: mcp/context-pack/README.md:15-16).

Bootstrap/verify commands (uv-locked project, unittest suite, extractor benchmark) are in its README (src: mcp/context-pack/README.md:18-26); the benchmark's frozen receipt is `mcp/context-pack/benchmarks/receipts/m1-pro-2026-07-29.json`, pinned by `mcp/context-pack/tests/test_benchmark_receipt.py`.

Engine internals that carry the guarantees (src: mcp/context-pack/src/context_pack_mcp/engine.py):

- `_read_source` opens the file with a component-wise `O_RDONLY|O_NOFOLLOW` (+`O_DIRECTORY` for dirs) fd walk from the repository root — symlinks anywhere in the path fail the open; traversal/empty components and non-`.py` suffixes are rejected up front; an OS without `O_NOFOLLOW`/`O_DIRECTORY` refuses entirely rather than degrading (src: engine.py:228-254). The `(dev, ino, size, mtime_ns)` identity is compared before and after the read, so "files that change while being read" fail with "retry with a fresh snapshot" (src: engine.py:259-275).
- Evidence is classified by `_SemanticCollector` (guards, raises, mutations, calls, returns, decorators) with signatures and `unresolved_dynamic_call` marked MANDATORY (src: engine.py:90-174). Budget assembly is a fixed-point: `_stabilize_size` iterates until `context_bytes` equals the encoded size; mandatory evidence exceeding `max_bytes` is a hard error ("increase the budget"), then optional items are admitted in priority order (guard < raise < mutation < call < return < decorator) only while they fit, with `truncated`/`omitted_evidence_count` reported honestly (src: engine.py:176-193, 355-398).
- Results are cached by `(path, source_sha256, symbol, max_bytes)` with deep-copy on BOTH store and hit — a caller mutating a returned pack can never poison the cache — and LRU eviction (src: engine.py:208, 298, 399-403). Signatures and `unresolved_dynamic_call` records are mandatory because they are exactly the facts a budget cut must never hide: the callable's contract, and the call edges static analysis could not resolve — dropping either silently would make a truncated pack read as complete evidence.
- `server.py` is the stdio surface: it resolves the repository root from `REPO_CONTEXT_ROOT` when set (which must be absolute, else it refuses) and otherwise from the launcher's working directory — the `.mcp.json`/`.codex` launchers `cd` to the git toplevel before exec, which is what binds the server to the active clone (src: mcp/context-pack/src/context_pack_mcp/server.py:13-17; .mcp.json:17).
- Named focused tests: `test_rejects_absolute_traversal_and_symlink_escape`, `test_mandatory_signature_is_never_silently_truncated`, `test_budget_retains_mandatory_facts_and_reports_truncation`, `test_hash_and_cache_change_with_source_bytes` (src: mcp/context-pack/tests/test_engine.py:54, 85, 96, 115), plus the stdio-surface suite `mcp/context-pack/tests/test_server.py`.

## mcp/production — profile-driven config migration engine

`mcp/production/migrate.py` is the shared migration mechanism for three local repositories; it owns mechanics only — each repo owns its profile and host config (src: mcp/production/README.md:1-10). Design points:

- stdlib-only; refuses path traversal, symlink destinations, protected-branch mutation, dirty destination overwrite, literal secrets, and resident payload claims for heavy executors (src: mcp/production/README.md:17-20). Secret refusal is regex-driven (`SECRET_KEY`, `TEXT_SECRET_ASSIGNMENT/ARGUMENT`) with an escape hatch only for env-var REFERENCES (`SAFE_SECRET_REFERENCE`) (src: mcp/production/migrate.py:26-38).
- Commands: `plan` / `apply` / `verify --receipt` / `rollback` / `check-receipts`, always with `--repo-root` and `--profile` (src: mcp/production/README.md:26-43). `apply` supports only profile-declared mirrors and writes a recovery backup plus an append-only receipt; `rollback` requires the exact apply receipt and refuses targets changed after apply (src: mcp/production/README.md:20-23).
- `verify` records hashes, not command output, "so a receipt cannot become a credential or prompt dump"; receipts are chained by SHA-256 of the preceding receipt and `check-receipts` validates the chain (src: mcp/production/README.md:45-47). The receipt trail lives in `mcp/production/receipts/`.
- Admission boundary: a technically passing probe reports `technical_pass_human_pending` whenever the profile declares human gates; the engine "never clicks Claude/Codex project approval" (src: mcp/production/README.md:49-55). Host permission profiles are intentionally not mirrored — e.g. the source repo's `.codex/config.toml` OrbStack socket and sandbox policy are host/session config, not portable payload (src: mcp/production/README.md:12-16).
- The profile schema (`profile.schema.json`) requires `engine_sha256` among other fields, binding a profile to the exact engine bytes (src: mcp/production/migrate.py:40-49; the tampered-profile RED is driven in tests/test_mcp_surface.sh).
- **The verify lane has two halves.** `migrate.py verify` executes the PROFILE-DECLARED probes (`probes` is in `PROFILE_REQUIRED`; this repo declares the production unittest discovery and the context-pack suite under uv, src: mcp/production/profile.json) via `_run_probe` (src: migrate.py:656), then RE-validates managed files, mirror plan, forbidden paths, and the receipt chain AFTER the probes ran — a probe that mutates a managed mirror flips the verdict (src: migrate.py:699-751; test `test_verify_rejects_probe_that_mutates_a_managed_mirror`). The status lattice: `not_run` when declared probes were skipped (skipping is never a pass — test `test_skipping_declared_probes_is_not_a_pass`), `fail` on probe or post-probe drift, `technical_pass_human_pending` when human gates are declared (test `test_verify_passes_technical_checks_but_keeps_human_gate_pending`), `technical_pass` only otherwise (src: migrate.py:758-766). The standalone `probe_stdio.py` probes one Codex-configured stdio MCP over the REAL JSON-RPC transport (`PROTOCOL_VERSION = "2025-06-18"`, fail-closed `ProbeError`), with its own test `tests/test_probe_stdio.py` (src: mcp/production/probe_stdio.py:1-24).
- **Transaction and receipt mechanics.** `apply_plan` detects drift via `build_plan`, whose per-mirror judgement is the `_equivalent(source, target, comparison)` helper — semantic JSON/TOML comparison, so formatting alone is not drift (src: migrate.py:260, 284). It asserts clean destinations and a non-protected branch, backs up every before-image under `.mcp-production/backups/<run-id>/`, and restores ALL prior targets when a later write or the receipt write fails (src: migrate.py:509-560; test `test_apply_restores_prior_targets_when_a_later_write_fails`). Receipts are published by `_exclusive_write`: write to an `O_EXCL` temp name, fsync, re-assert the parent-directory identity via fstat (`_assert_parent_binding`, symlink-safe fd walk in `_open_parent_dir`), then `os.link` the temp to the final name — a hardlink onto an existing name raises "append-only receipt collision", making append-only physical, not conventional (src: migrate.py:394-451). Each receipt records `previous_receipt_sha256`, and `check_receipt_chain` walks the chain rejecting any link whose recorded predecessor hash mismatches — "broken receipt chain at <name>" (src: migrate.py:479, 488-502; tests `test_receipts_form_hash_chain_without_overwrite`, `test_receipt_chain_rejects_tampering`). `rollback` accepts only an apply receipt that is in-chain, profile-sha-matched, and whose targets still carry the after-sha (src: migrate.py:785; test `test_rollback_rejects_apply_shaped_file_outside_receipt_chain`).
- **The mirror chain has a direction.** `profile.json` declares `mcp/production/templates/claude-mcp.json → .mcp.json` as a mirror: the template is the SOURCE and `.mcp.json` its derived copy, so the correct entry point for changing the Claude MCP declarations is the template followed by `migrate.py apply` — editing `.mcp.json` directly creates drift that `verify` flags (src: mcp/production/profile.json mirrors; migrate.py build_plan).
- The two declared human gates — Claude project MCP approval and a fresh-chat config reload — ride every verify report as `pending`/non-automatable (src: mcp/production/profile.json human_gates; migrate.py:750-757).

## Focused test

`tests/test_mcp_surface.sh` covers the seam: `.mcp.json` parses and declares exactly the three servers; the production engine's `--help` runs and its profile binds to THIS repo; the engine-hash check is driven RED on a tampered profile; bootstrap's WARNs are driven to fire and to clear (src: tests/test_mcp_surface.sh:1-18). Cleanup hardening for the tampered profile came with commit 57f6809.
