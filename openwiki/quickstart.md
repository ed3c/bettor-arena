---
type: Quickstart
title: bettor-arena wiki quickstart
description: Entry point to the bettor-arena as-built wiki — high-level map, navigation guide, and the task-routing table from change intent to owning files, focused tests, and minimal validation.
tags: [quickstart, navigation]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: 2c36ddf
covers: [quickstart, task-routing]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# bettor-arena wiki quickstart

bettor-arena is the migrated home of four subtrees from `ts-skill-bettor`: a governance-heavy engineering repo where a **macro loop** (git hooks + host config on the commit path) and a **micro loop** (a deterministic seed-repo factory) meet at exactly one seam — CLI exit codes and receipts — with a human admit as every terminal edge (src: ARCHITECTURE.md:41-55). Design facts have a single SSOT (`ARCHITECTURE.md`); this wiki documents the as-built system with file anchors valid at commit 2c36ddf.

## High-level map

- **[Architecture and governance](architecture.md)** — the SSOT/derivation model, §2 placement contract, the seven iron laws and their enforcement mechanisms, the admit glossary, ADR 0001.
- **Macro-loop host layer** — [bootstrap](host-loop/bootstrap.md) (activation + doctor) · [git hooks](host-loop/git-hooks.md) (pre-commit / commit-msg / post-commit) · [molecular messages](host-loop/molecular-messages.md) (the protected-surface commit contract) · [Claude host](host-loop/claude-host.md) (settings + rm_guard deletion boundary) · [MCP surface](host-loop/mcp-surface.md) (three declarations, context-pack server, production migration engine).
- **Gates** — [fast quality](gates/fast-quality.md) (one definition, two mounts, receipt with claim boundary) · [structure gates](gates/structure-gates.md) (root coupling, placement, skill pointers).
- **Micro-loop factory** — [overview](factory/overview.md) (eight bases, F0→H1 workflow) · [packet contract](factory/packet-contract.md) (schema + refs tri-state) · [build pipeline](factory/build-pipeline.md) (trigger → build → three validators → route result) · [generated repo](factory/generated-repo.md) (the product contract, 20-call operator) · [verification](factory/verification.md) (T0, hollow control, portability, baselines) · [v2 plan](factory/v2-plan.md) (the evolution contract).
- **kb-ingest** — [overview](kb-ingest/overview.md) (module boundary, tri-exit gate, host profiles, mastery ladder) · [official port](kb-ingest/official-port.md) (verbatim prompts, deterministic passes, isolated subagents, honest gaps).
- **Migration** — [engine](migration/engine.md) (manifest-declared, receipt-atomic) · [history](migration/history.md) (S1–S11 + fix waves, commit-anchored).
- **Cross-cutting** — [data ledgers](data-ledgers.md) (every receipt landing site) · [testing](testing.md) (seam tests + measurement tools) · [skills surface](skills-surface.md) (single home + pointers).

## Task-routing table

| Change intent | Read first | Owning files | Focused test | Minimal validation |
|---|---|---|---|---|
| Add/move a root-level file or dir | [architecture](architecture.md) | ARCHITECTURE.md §2, scripts/gates/check_placement.py | check_placement `--selftest` | `python3 scripts/gates/check_placement.py` |
| Edit a hook or gate (protected surface) | [git hooks](host-loop/git-hooks.md), [molecular messages](host-loop/molecular-messages.md) | .githooks/, scripts/gates/ | tests/test_fast_quality.sh, tests/test_molecular_gate.sh | stage everything on the surface, molecular message with Intent-Slice, dry-run validator first |
| Change the fast-quality checks | [fast quality](gates/fast-quality.md) | scripts/gates/fast_quality.sh (both mounts follow) | tests/test_fast_quality.sh | run the gate on a sample list; check receipt gate_inputs |
| Touch tracked-path hygiene / allowlist | [structure gates](gates/structure-gates.md) | check_root_coupling.py, root_coupling_allowlist.txt | check_root_coupling `--selftest` | `python3 scripts/gates/check_root_coupling.py` |
| Add or relink a skill | [skills surface](skills-surface.md) | .agents/skills/, .claude/skills/ | check_skill_pointers `--selftest` | `python3 scripts/gates/check_skill_pointers.py` |
| Change the packet schema or refs semantics | [packet contract](factory/packet-contract.md) | loop_wiki/…/src/contracts.ts, modules/exchange-formats.md | tests/seed_factory.test.ts | `sh verify.sh` in the factory |
| Change the generated-repo product | [generated repo](factory/generated-repo.md) | templates/repo/, src/materialize.ts, src/verify_generated_repo.ts | generated tests/operator.test.ts via verify.sh | `sh selftest.sh` (good/hollow) |
| Run a build from a packet | [build pipeline](factory/build-pipeline.md) | trigger.sh, run.sh, src/cli.ts | route-result exits | `sh trigger.sh <packet> <abs-output>` |
| Change factory baselines | [verification](factory/verification.md) | baselines/seed-stats.json via baseline-update packet ONLY | verify.sh cmp gate | admitted baseline-update packet, never a hand edit |
| Change MCP declarations | [MCP surface](host-loop/mcp-surface.md) | mcp/production/templates/claude-mcp.json (the source of .mcp.json), .codex/config.toml | tests/test_mcp_surface.sh | `migrate.py plan` → `apply` → `verify --receipt`; human approval |
| Change the deletion boundary | [Claude host](host-loop/claude-host.md) | .claude/hooks/rm_guard.py | rm_guard `--selftest` | tests/test_host_config.sh |
| Migrate a subtree between repos | [migration engine](migration/engine.md) | scripts/migrate/migrate_seed.py, data/migration/manifest.json | migrate_seed `--selftest` | dry-run first; `--apply`; target gate must return green |
| Regenerate or update this wiki | [kb-ingest overview](kb-ingest/overview.md) | kb-ingest/ (module), openwiki/ (output) | kb-ingest/port/test_relocation.sh | `python3 kb-ingest/check_repo_wiki_converge.py` then the official update flow |
| Bootstrap a fresh clone | [bootstrap](host-loop/bootstrap.md) | bootstrap.sh | tests/test_bootstrap.sh | `sh bootstrap.sh` (exit 0, WARNs named) |

## Reading conventions

Every substantive claim carries a `(src: path:line)` anchor, repo-relative, pinned at commit 2c36ddf — verify with `git show 2c36ddf:<path>`. Exit codes repo-wide follow one convention: 0 pass · 2 check failed · 64 (or kb-ingest's 3) "cannot tell / precondition" — absence is never green (src: ARCHITECTURE.md:53-54). "Candidate" always means all mechanical gates green AND awaiting human admit; no gate output ever constitutes an admit (src: CONTEXT.md:8, 16).
