---
type: Verification
title: Repo-level seam tests and measurement tools
description: The tests/ suite — CLI-exit-code seam tests with red-first controls for bootstrap, fast quality, host config, MCP surface, and the molecular gate — plus the driver-smoke and corpus-parity measurement tools.
tags: [tests, seams, tools]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: 2c36ddf
covers: [seam-tests, driver-smoke, corpus-parity]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# Repo-level seam tests and measurement tools

`tests/` holds repo-level tests that hit the gate CLI exit-code seam (src: ARCHITECTURE.md:36) — the only seam iron law 1 allows (src: ARCHITECTURE.md:43-44). The house style across every file: isolated fixture copies (`mktemp -d` + trap cleanup), both directions exercised, and reds demonstrated before greens are trusted. Run any file directly: `sh tests/<name>.sh`.

## The six seam tests

- **test_bootstrap.sh** — bootstrap CLI exit codes + resulting git config on an isolated copy: relative hooksPath set, idempotent rerun, unconditional `.githooks/` copy so a missing tracked-hooks dir fails rather than being masked (src: tests/test_bootstrap.sh:2-21). See [bootstrap](host-loop/bootstrap.md).
- **test_fast_quality.sh** — `fast_quality.sh` CLI + the REAL pre-commit's behavior in a fixture repo. Controls: per-lane negative controls (TS type error, Python format violation, shell syntax error), clean positive control, fail-fast `not_run` assertion, ruff-absent FATAL 64, hook self-integrity block, budget-overrun FATAL, <5s wall bound — "every green here was first seen red while this file predated the implementation" (src: tests/test_fast_quality.sh:2-11). Since commit 2c36ddf, one EXIT trap owns tagged-orphan cleanup so every failure path sweeps watchdog survivors off the host (proved red first with an escaping setsid grandchild). See [fast quality](gates/fast-quality.md).
- **test_host_config.sh** — host config files + rm_guard CLI: settings.json validity, `$CLAUDE_PROJECT_DIR` usage, PreToolUse registration present, and the guard blocking an escape (2) while passing an inside delete (0) — "or its green proves nothing" (src: tests/test_host_config.sh:2-20). See [Claude host](host-loop/claude-host.md).
- **test_mcp_surface.sh** — `.mcp.json` declares exactly the three servers; production engine `--help` runs and its profile binds to THIS repo; the engine-hash check is driven RED on a tampered profile; bootstrap doctor WARNs are driven to fire and to clear; mid-test failure cannot leave the tampered profile behind (src: tests/test_mcp_surface.sh:2-18). See [MCP surface](host-loop/mcp-surface.md).
- **test_molecular_gate.sh** — the ACTIVE commit-msg/post-commit hooks: armed hooks must be live AND executable ("an armed hook would be silently ignored"), the validator's single-file/node-builtins-only charter is checked, and real commit behavior runs in a fixture where the hooks are activated — activation in this repo itself remains a separate human admit (src: tests/test_molecular_gate.sh:2-20). See [molecular messages](host-loop/molecular-messages.md).
- **test_replay_corpus_parity.sh** — pins the parity tool's precondition exits only: every missing precondition (bun absent from PATH, missing repo/validator) dies FATAL 64 with a diagnostic, never a bare traceback (src: tests/test_replay_corpus_parity.sh:2-21; commit 35a0ca2).

## tests/tools/ — measurement, not pass/fail

- **driver_smoke.sh** — proves the S11 driver-alignment contract physically: the claude lane is a fresh `claude -p <prompt> --max-turns 1`, the codex lane a direct `codex exec` (never the Claude host plugin), missing tool FATAL 64 naming itself. A real run writes `data/receipts/driver-smoke.json` (exit codes + truncated output summaries, no absolute paths). Exit: 0 both lanes round-tripped · 2 a lane ran but failed · 64 tool absent · 1 selftest red; `CLAUDE_BIN`/`CODEX_BIN` override as the selftest seam (src: tests/tools/driver_smoke.sh:2-18).
- **replay_corpus_parity.py** — re-measures original-vs-rebuilt molecular-validator parity over the last N commit messages of a `--source-repo`, in message-only mode (empty `--changed-paths-file`). "Mismatches are expected by design … This script measures the gap; it does not judge it" (src: tests/tools/replay_corpus_parity.py:4-15). Its frozen output is `data/receipts/molecular-corpus-parity.json` ([data ledgers](data-ledgers.md)); reruns must not overwrite it (commit 579771c).

## Where the other test suites live

This directory deliberately covers only the repo-level seams. The factory's tests live in the sandbox (`loop_wiki/evolve-perfect-seed-repo-factory/tests/seed_factory.test.ts` plus each generated repo's `tests/operator.test.ts` — [factory verification](factory/verification.md)); the MCP servers' suites live in their projects (`mcp/context-pack/tests/`, `mcp/production/tests/` — run via the profile-declared probes, [MCP surface](host-loop/mcp-surface.md)); the gates' selftests live inside the gates themselves ([structure gates](gates/structure-gates.md)); kb-ingest's proofs are its module gate and `port/test_relocation.sh` ([kb-ingest](kb-ingest/overview.md)).
