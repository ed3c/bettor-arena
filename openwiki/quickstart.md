---
type: Quickstart
title: bettor-arena wiki quickstart
description: Entry point to the bettor-arena as-built wiki — high-level map, navigation guide, and the task-routing table from change intent to owning files, focused tests, and minimal validation.
tags: [quickstart, navigation]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: ca72a92
covers: [quickstart, task-routing]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# bettor-arena wiki quickstart

bettor-arena is the migrated home of four subtrees from `ts-skill-bettor`: a governance-heavy engineering repo where a **macro loop** (git hooks + host config on the commit path) and a **micro loop** (a deterministic seed-repo factory) meet at exactly one seam — CLI exit codes and receipts — with a human admit as every terminal edge (src: ARCHITECTURE.md:45-59). Design facts have a single SSOT (`ARCHITECTURE.md`); this wiki documents the as-built system with file anchors valid at commit 2c36ddf, updated through ca72a92. Since ISSUE-23, the two loops also meet at a second seam: a successful factory delivery emits a typed wiki-update request that a digestion station (`kb-ingest/port/wiki_update_worker.sh`) consumes to keep this wiki itself current — see [kb-ingest official port](kb-ingest/official-port.md).

## High-level map

- **[Architecture and governance](architecture.md)** — the SSOT/derivation model, §2 placement contract, the seven iron laws and their enforcement mechanisms, the admit glossary, ADR 0001.
- **Macro-loop host layer** — [bootstrap](host-loop/bootstrap.md) (activation + doctor) · [git hooks](host-loop/git-hooks.md) (pre-commit / commit-msg / post-commit) · [molecular messages](host-loop/molecular-messages.md) (the protected-surface commit contract) · [Claude host](host-loop/claude-host.md) (settings + rm_guard deletion boundary) · [MCP surface](host-loop/mcp-surface.md) (three declarations, context-pack server, production migration engine).
- **Gates** — [fast quality](gates/fast-quality.md) (one definition, two mounts, receipt with claim boundary) · [structure gates](gates/structure-gates.md) (root coupling, placement, skill pointers).
- **Micro-loop factory** — [overview](factory/overview.md) (eight bases, F0→H1 workflow) · [packet contract](factory/packet-contract.md) (schema + refs tri-state) · [build pipeline](factory/build-pipeline.md) (trigger → build → three validators → route result) · [generated repo](factory/generated-repo.md) (the product contract, 20-call operator) · [verification](factory/verification.md) (T0, hollow control, portability, baselines) · [v2 plan](factory/v2-plan.md) (the evolution contract).
- **kb-ingest** — [overview](kb-ingest/overview.md) (module boundary, tri-exit gate, host profiles, mastery ladder) · [official port](kb-ingest/official-port.md) (verbatim prompts, deterministic passes, isolated subagents, the wiki-update digestion station, honest gaps).
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
| Digest a factory delivery into a wiki update | [kb-ingest official port](kb-ingest/official-port.md#wiki_update_workersh-digestion-station-for-factory-wiki-update-requests) | kb-ingest/port/wiki_update_worker.sh, data/wiki-update/ | wiki_update_worker.sh `--selftest` | `sh kb-ingest/port/wiki_update_worker.sh <request.json> --dry-run` |
| Bootstrap a fresh clone | [bootstrap](host-loop/bootstrap.md) | bootstrap.sh | tests/test_bootstrap.sh | `sh bootstrap.sh` (exit 0, WARNs named) |

## Reading conventions

Every substantive claim carries a `(src: path:line)` anchor, repo-relative, pinned at the commit recorded in that page's front-matter `commit:` field — verify with `git show <commit>:<path>`. Exit codes repo-wide follow one convention: 0 pass · 2 check failed · 64 (or kb-ingest's 3) "cannot tell / precondition" — absence is never green (src: ARCHITECTURE.md:57-58). "Candidate" always means all mechanical gates green AND awaiting human admit; no gate output ever constitutes an admit (src: CONTEXT.md:8, 16).

## Backlog

- [deferred from poweron-2026-08-06@1e7f3df900094d85b99bd7b91dc6a827f8e583d0] [b1] Q-03 PARTIAL: /openwiki/kb-ingest/official-port.md (§wiki_update_worker.sh review-gates bullet, and the openwiki_subagent.sh section) omits: (1) that the worker takes only the LAST stdout line of `openwiki_subagent.sh` as the review-file path and why (the runner emits diagnostics/progress on stdout before that path); (2) the named failure branch for a finder output containing zero `[Q-NN]` questions — the page documents only the missing-verifier-file and zero-`<result>`-block reds, so a question-less finder run is not shown to fail by name.
- [deferred from poweron-2026-08-06@1e7f3df900094d85b99bd7b91dc6a827f8e583d0] [b2] Q-04 PARTIAL: /openwiki/kb-ingest/official-port.md (§wiki_update_worker.sh, "Post passes" bullet) describes the dry-run live-wiki proof only as "byte-diff the live wiki against a pre-run snapshot": it lacks the named `live-before` copy, the `diff -r` comparator, and the statement that this comparison is asserted before any success line prints. Same page also never states what the dry-run explicitly does NOT cover on a real run (no model turn or write-boundary gate exercise, no real verifier verdicts, no live finalize, no `_plan.md` removal, no `gitHead`-equals-HEAD assert). Also verify the receipt field name: the page calls the skipped-segment field `llm_regenerate`, the source criterion names it `regenerate_state`.
- [deferred from poweron-2026-08-06@1e7f3df900094d85b99bd7b91dc6a827f8e583d0] [b2] Q-05 PARTIAL: /openwiki/kb-ingest/official-port.md and /openwiki/data-ledgers.md#openwikilast-updatejson-the-wiki-freshness-anchor omit: the worker's concrete finalize invocation (`--target "$root" --command update --model claude-code+sonnet --status success --normalize-backlog`) and the explicit statement that `gitHead` is the worker-root target repo's HEAD; the omission mechanics inside `write_last_update` (`check=False`, stderr to DEVNULL, empty stdout drops the key, so a git failure never raises); the exit code the failed assert maps to (named FAIL 2); the position of `pass_backlog_heading` in the ordered finalize chain (mermaid → indexes → links → `.last-update.json` → backlog heading); and why `index.md` must never be hand-written (deterministic regeneration overwrite).
- [deferred from poweron-2026-08-06@1e7f3df900094d85b99bd7b91dc6a827f8e583d0] [b2] Q-06 PARTIAL: /openwiki/factory/build-pipeline.md (step 7 / "Focused tests") lacks the test's pre-clean plus `finally` cleanup of `data/wiki-update/request-*.json`, which is what stops a stale request from masquerading as this delivery's emission. Neither that page nor /openwiki/kb-ingest/official-port.md nor /openwiki/data-ledgers.md states the drift-coupling consequence explicitly: the three-value `delta_status` enum is hard-coded independently in `trigger.sh` and `wiki_update_worker.sh` stage 1 and pinned in `seed_factory.test.ts`, so adding a fourth status requires editing all three.

No known coverage gaps as of commit ca72a92. This heading is also the fixed anchor the wiki-update pipeline's `emergent_prompt_context` lane points at (src: CONTEXT.md:16-18; [kb-ingest official port](kb-ingest/official-port.md#wiki_update_workersh-digestion-station-for-factory-wiki-update-requests)) — emergent observations from a future update run land here, never inside a standards module.
