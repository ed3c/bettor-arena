---
type: History
title: Migration history — S1 to S11 and the fix waves
description: The commit-anchored story of how bettor-arena was built — the numbered migration slices, the staged-then-armed hook activation, and every hardening fix wave with its commit.
tags: [migration, history, commits]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: 2c36ddf
covers: [migration-slices, activation-waves, fix-waves]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# Migration history — S1 to S11 and the fix waves

bettor-arena was assembled as numbered slices (S-prefixed subjects in `git log`), each anchored to a ts-skill-bettor tracker issue (see [ADR 0001](../architecture.md)). All commit hashes below are from this repo's history at 2c36ddf; `git show <hash>` reproduces each.

## The numbered slices

| Slice | Commit | What landed |
|---|---|---|
| S1 | 08b2fdf | Skeleton: root-coupling gate, idempotent bootstrap, placement contract |
| S2 | 5473211 | Migration engine v2 — manifest-declared, root-decoupled, selftested (issue #4; [engine](engine.md)) |
| S3 | b7983da | The loop-factory sandbox migrated in VIA the S2 engine ([factory](../factory/overview.md)) |
| S4 | 550a44a | kb-ingest lands; `nonofficial/` becomes `port/`; the gate stops naming machines ([kb-ingest](../kb-ingest/overview.md)) |
| S5 | ae3a2db | Skill content gets one home; host entries become pointers ([skills surface](../skills-surface.md)) |
| S6 | d69f2bd | Deletion boundary registered as versioned host config (issue #8; [Claude host](../host-loop/claude-host.md)) |
| S7 | c435d42 | One fast-quality definition, mounted at pre-commit reach ([fast quality](../gates/fast-quality.md)) |
| S8 | 99fa15d | Molecular commit-msg gate rebuilt inside its legislated charter ([molecular messages](../host-loop/molecular-messages.md)) |
| S10 | 3bfd114 | MCP surface carried over, profile rebound to this repo (issue #12; [MCP surface](../host-loop/mcp-surface.md)) |
| S11 | c38b1d5 | The codex driver lane stands on its own feet (driver_smoke lanes; [testing](../testing.md)) |

(No commit carries an S9 subject in this history; the slice numbering runs the tracker, not this repo, and the tracker is the SSOT for what S9 was — src: ARCHITECTURE.md:4-5.)

## Hook activation — staged, then armed by human admit (#14)

The hooks landed inert as `.staged` files and were armed in explicit activation-admit waves (the glossary's first admit sense, src: CONTEXT.md:4-5):

1. 9db3984 prep(#14): ruff-clean gates, structure gates wired into pre-commit, `ISSUE-<n>` slice vocabulary adopted.
2. fd164bd fix(#14): fixture proves the hook calls the structure gates it now wires — the wiring got its red before its green.
3. 9c401d1 activate(#14 stage 1): pre-commit and post-commit armed.
4. a61e9be fix(#14): post-commit needed its executable bit to fire.
5. 38e4251 activate(#14 stage 2): commit-msg molecular gate armed (2026-08-06, human admit; src: .githooks/commit-msg:2-4).
6. 0d01497 / 07e0a20: the seam tests retargeted to judge the ACTIVATED hooks they test.

## Fix waves (each wave = one class of defect, swept across its instances)

**Root-decoupling and gate honesty**: 7e52b8e (bootstrap asserts tracked hooks exist before claiming OK) · 42c92e1 (gate names the scanned root up front; selftest exit 1 documented) · 50392c0 (gates anchor the scan on the script's own location, not cwd) · e0f017b (receipts allowlist narrowed from prefix to per-file) · 760669b (rewrite assertion made falsifiable; red-gate branch actually fired) · 4d9f279 (HEAD-red coupling literal cleared; example packet grounded in a real anchor).

**Evidence and receipts**: 579771c (test reruns stop overwriting tracked evidence; parity replay tool added) · 73fe3a5 (apply receipts become per-run files; the latest is only a copy) · 8fe5c12 (issue #19: per-run receipt collisions refused instead of silently rewriting history) · 05d831e (runtime stage-request receipts and serena state ignored) · 65eda5a (glossary receipt entry admits its one explicit exception).

**Gate strictness and process control**: bd294c5 (staged bytes judged with the factory's strictness) · 6f8cd13 (Python lane judges with local ruff or refuses — never fetches) · 186f175 (budget watchdog kills the gate's whole process group) · dc37c1c (one shared spine for gate scripts; staged tree gains full-index context) · 35a0ca2 (parity tool dies FATAL 64 when bun is absent, never a bare traceback).

**Contract evolution**: 568f5d7 (source_refs: every packet carries its provenance chain) · c329882 (issue #20: refs grounding becomes a tri-state so the human gate cannot misread it) · 2c36ddf (issue #22: stale receipts get their own state — audited-then-broken distinguishable from never-audited, typed ReceiptCheckError to exit 2, one EXIT trap for orphan cleanup in the fast-quality seam test, atomic O_EXCL receipt claim in the migration engine — [packet contract](../factory/packet-contract.md)) · 6f06881 (§2 admits module-owned skill symlinks) · 9f5f497 (rule text kept in the SSOT only; derived files become pointers) · 28cc5c4 / 8c1c898 (kb-ingest naming and docstring accuracy) · 57f6809 (ollama probe URL parameterized; mcp-surface test cleanup hardened) · 68f333b (.mcp.json/.gitignore slots declared; pycache ignored) · 75cc24b (the §2 placement contract mechanized).

The recurring pattern across every wave: a defect found once was swept across all instances of its class (shared gate spine, pattern assembly in two engines, anchoring control in every gate selftest), and every green kept the red that proves it can fail.
