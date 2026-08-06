---
type: Component
title: kb-ingest — the repo-wiki module
description: The repo-wiki-converge module — its official/port directory boundary, the tri-exit perception gate, host profiles, workspace conventions, and the mastery ladder that positions it as L1.
tags: [kb-ingest, repo-wiki, module-gate]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: 2c36ddf
covers: [kb-ingest-module, host-profile, mastery-ladder, module-gate]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# kb-ingest — the repo-wiki module

`kb-ingest/` is the host-native port of langchain-ai/openwiki's official code-mode init/update procedure: official prompts verbatim, the three official review subagents as hard-isolated child processes, and the official deterministic post-processing rebuilt in stdlib Python — with inference running in the host CLI's own subscription session, no Node, no provider key (src: kb-ingest/skill/SKILL.md:3-7, 17-19). It landed as S4 (commit 550a44a, which also renamed `nonofficial/` to `port/`). This wiki itself was produced by it.

## The directory boundary is physical, not annotational

| Directory | Rule |
|---|---|
| `kb-ingest/openwiki/` | upstream bytes ONLY — seven machine-generated assets wrapped in `OPENWIKI-OFFICIAL:BEGIN/END`; nothing hand-written, nothing skill-bettor-invented (src: kb-ingest/port/README.md:5-7) |
| `kb-ingest/port/` | everything local: generators, host adapters, reimplementations of upstream's code-owned behavior, appendices (src: kb-ingest/port/README.md:8) |
| `kb-ingest/` root | the module's own entry points and installation declaration: the gate, `host-profile.json`, setup scripts, and the two ledgers (`mastery-ladder.md`, `engine-baseline.md`) (src: kb-ingest/port/README.md:9) |

Adding behavior means adding a file in `port/`, never editing `../openwiki/`; the three legal moves when an official asset seems to need a change are: extend `sync_prompts.py` and regenerate, write a new appendix, or upgrade the upstream checkout and regenerate (src: kb-ingest/port/README.md:102-109). Purity is verifiable at any time with `python3 kb-ingest/port/sync_prompts.py <openwiki_repo> --check` (src: kb-ingest/port/README.md:11-17). Details of every port asset: [official port](official-port.md).

## check_repo_wiki_converge.py — the perception gate

"It proves the skill's claims are backed by runnable local assets rather than prose": official assets exist and are machine-generated, the deterministic post-processing runs (selftests), the three subagents' read boundaries actually hold, and — where declared — the RepoDoc lane still accepts a wiki (src: kb-ingest/check_repo_wiki_converge.py:3-8).

**Tri-exit contract**: 0 pass · 1 fail · 3 FATAL "cannot tell" (src: kb-ingest/check_repo_wiki_converge.py:10-11). Exit 3 is NOT a worse 1: it means the gate could not establish what it was supposed to check (no host declaration, unparseable declaration, unknown profile name, no git worktree) — "a forgotten configuration would otherwise read as 'this host legitimately has no such profile' and the check would disappear while the banner stayed green" (src: check_repo_wiki_converge.py:19-24). This is the module-level instance of iron law 6's absence≠green (src: ARCHITECTURE.md:53-54).

**Two roots, deliberately distinct**: `MODULE_ROOT` (this directory — self-provable checks resolve from it so the module survives being copied to another repo under another name at another depth) vs `HOST_ROOT` (the enclosing checkout — only host-profile checks may touch it). "Collapsing the two … is what pinned this lane to one repo at one depth" (src: check_repo_wiki_converge.py:13-18).

**What the gate actually runs**: asset presence and provenance-marker checks over the seven prompt assets (`DO NOT EDIT BY HAND` + `OPENWIKI-OFFICIAL` needles, no unresolved `{PLACEHOLDER}` in system prompts, src: check_repo_wiki_converge.py:375-382); directory-boundary purity of `openwiki/` — exactly the generated assets, nothing hand-added (`check_official_purity`, src: check_repo_wiki_converge.py:353); the `--selftest` of both port scripts (`sync_prompts.py`, `openwiki_post.py`); the three subagent read boundaries proven physically under `OPENWIKI_DRY_RUN` against a committed-wiki fixture — finder must not see `openwiki/`, verifier must not see source, and no worktree may leak (`check_subagent_boundaries`); and a stale-root scan (`foreign_home_paths`) derived from `ALLOWED_ROOTS` — the host root plus the `--git-common-dir` parent, so a linked worktree stays legal — rather than a hardcoded machine list (src: check_repo_wiki_converge.py:126-141, 138-151). Declared host profiles add their text-contract needles per `PROFILE_TEXT` (src: check_repo_wiki_converge.py:330-349).

## host-profile.json — declared host facts

The declaration file MUST exist; missing/unparseable/unknown-name are all FATAL 3 (src: kb-ingest/host-profile.json:10-15). Known profiles: `repodoc` (the indexing/KB sink), `host-skill-links` (the host exposes the skill as a symlink into the module, not a copy), `skill-bettor-layout` (source-repo directory conventions) (src: host-profile.json:16-20). bettor-arena declares ONLY `host-skill-links`: it has no indexing/ KB sink and does not carry the repo//prototype/ conventions — "declaring either here would make the gate assert host facts that are false in this checkout" (src: host-profile.json:21-24). Consequence: the SKILL's S5 snapshot+KB-ingest step is skipped on this host; the wiki itself is the complete artifact (src: kb-ingest/skill/SKILL.md:114-117).

## Workspace conventions

- `setup-repo.sh <name> <url>` clones FULL history (never `--depth 1`; shallow breaks the git-history evidence path) into `<host_root>/repo/<name>/<name>` with artifacts landing in `<host_root>/repo/<name>/` — gitignored, durable, never `/tmp`; overridable via `SKILL_BETTOR_REPO_ROOT` (src: kb-ingest/setup-repo.sh:2-11, 25-27).
- `setup-prototype.sh <plan> <repo> [--mvp]` scaffolds a feasibility prototype (venv + NOTES.md + independent git, throwaway) or, with `--mvp`, a full eight-base sandbox that graduates; the flag exists because an earlier version overclaimed "八大基座 scaffolder" while only building a venv (Fable-5 review 2026-07-11, src: kb-ingest/setup-prototype.sh:2-17).

## Position in the mastery ladder

`mastery-ladder.md` is the layered-escalation SSOT shared with `repo-agent-native`: L1 understanding (this module, gate = official three subagents + zero broken links + human admit) → L2 invariants (`repo-agent-native`) → L3 mastery+specs — "wiki 收斂 ≠ repo 掌握"; the funnel is never inverted, source code is SSOT for every layer, and wiki prose is never a fact source for L2 (src: kb-ingest/mastery-ladder.md:3-6, 13-17, 28-31). Since 2026-08-04, L1 runs the official-openwiki engine and layer escalation is demand-pull, not judge-triggered (src: kb-ingest/mastery-ladder.md:7-10). `engine-baseline.md` is the RETIRED predecessor engine's cost ledger, kept because its measured hypothesis failures (anchoring cost squeezing coverage; Flash fabricating concrete values like "100k files") are the only evidence for those conclusions (src: kb-ingest/engine-baseline.md:1-6) — see [official port](official-port.md) for the retirement ledger.
