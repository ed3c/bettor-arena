---
type: Component
title: bootstrap.sh — per-clone activation and doctor
description: The idempotent activation script that registers versioned git hooks, runs a FATAL-64 tool doctor, probes the optional MCP toolchain as WARNs, and prints the human-owned MCP approval steps.
tags: [bootstrap, host-loop, doctor]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: 2c36ddf
covers: [bootstrap-activation, hookspath, doctor-fatal-warn]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# bootstrap.sh — per-clone activation and doctor

`bootstrap.sh` exists because git cannot version `core.hooksPath`, and hook registration must never depend on where the tree was cloned (src: bootstrap.sh:4-6). Everything derives from the script's own location (`ROOT=$(cd "$(dirname "$0")" && pwd)`, src: bootstrap.sh:11); rerunning is always safe. Run it as `sh bootstrap.sh` (src: AGENTS.md:6).

## Exit-code contract

`0` activated · `64` missing tool or precondition — diagnosable, deliberately distinct from any gate's FAIL 2 (src: bootstrap.sh:8-9). The `fatal()` helper prints `bootstrap FATAL: <reason>` and exits 64 (src: bootstrap.sh:13).

## Ordered steps

1. **Work-tree assertion**: `git rev-parse --show-toplevel` must succeed, else FATAL with "clone the repo, then run bootstrap" (src: bootstrap.sh:15-16).
2. **Doctor, required tools**: `git`, `python3` ("gates are Python"), `bun` ("factory toolchain") each FATAL by name when absent — "a missing tool must never be readable as checks passed" (src: bootstrap.sh:18-22).
3. **hooksPath registration with empty-dir assertion**: before configuring, it asserts `.githooks/` exists AND is non-empty, because pointing hooksPath at a missing/empty dir "would print OK while registering nothing" (src: bootstrap.sh:24-29). Only then `git config core.hooksPath .githooks` — a relative value, valid from any checkout location (src: bootstrap.sh:29). The tracked hooks themselves are documented in [git hooks](git-hooks.md).
4. **Instrument verification before trust**: runs `python3 scripts/gates/check_root_coupling.py --selftest` and goes FATAL on red — "do not trust its green" (src: bootstrap.sh:31-32). This is the §1 discipline (a green never seen red is not evidence) applied to bootstrap's own dependency.
5. **Optional MCP toolchain, WARN never FATAL**: MCP is opt-in and a clone without it must still bootstrap (src: bootstrap.sh:35-36). Three probes, each WARN naming the fix, not just the gap:
   - `uv` absent → names the context-pack/serena launchers and the install URL (src: bootstrap.sh:37-38).
   - ollama unreachable on `${OLLAMA_URL:-http://localhost:11434}` → names grepai embeddings and the brew/serve commands (src: bootstrap.sh:39-44). The URL is parameterized via `OLLAMA_URL` (hardened in commit 57f6809, src: git log).
   - `.grepai/index.gob` absent → names `grepai init && grepai watch` (src: bootstrap.sh:45-46).
6. **Success line**: `bootstrap OK: hooksPath=.githooks, doctor green (git/python3/bun)` (src: bootstrap.sh:48).
7. **MCP approval instructions, printed never performed**: "auto-enabling project MCP servers would be self-approval" (src: bootstrap.sh:50-58). The human approves `.mcp.json`'s three servers in Claude Code's project-trust prompt and hand-adds host sections to `.codex/config.toml` — see [MCP surface](mcp-surface.md).

## Focused test

`tests/test_bootstrap.sh` exercises the seam on an isolated copy: first run must set `core.hooksPath` to exactly the relative string `.githooks`, the second run must be idempotent with no drift, and the copy step for `.githooks/` is deliberately unconditional so a missing tracked hooks dir fails the test rather than being masked by a fallback `mkdir` (src: tests/test_bootstrap.sh:2-21). Historical anchor: the tracked-hooks-exist assertion was added in commit 7e52b8e ("assert tracked hooks exist before claiming OK").

## Relationship to the rest of the host loop

bootstrap is the ONLY activation path: nothing else writes `core.hooksPath`, and the hooks it registers are the tracked ones under `.githooks/`. Rollback of an individual hook is a rename to `.staged` (src: .githooks/commit-msg:4), not a bootstrap change.
