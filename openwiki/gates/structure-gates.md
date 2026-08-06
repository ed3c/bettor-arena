---
type: Component
title: Structure gates — root coupling, placement, skill pointers
description: The three zero-LLM Python structure gates and their shared spine — pattern-assembled home-root scanning with an evidence allowlist, §2 placement mechanization, and the skills single-home pointer contract.
tags: [gates, root-coupling, placement, skill-pointers]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: 2c36ddf
covers: [root-coupling, evidence-allowlist, placement-gate, skill-pointer-gate, gate-selftest]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# Structure gates — root coupling, placement, skill pointers

`scripts/gates/` holds the repo-level defense scripts, zero LLM involvement (src: ARCHITECTURE.md:33). All three Python gates ride the [pre-commit hook](../host-loop/git-hooks.md) after the quality gate (src: .githooks/pre-commit:68-71) and share the exit contract 0 clean · 2 violation · 64 usage/precondition, with `--selftest` returning 0 green / 1 red on throwaway git fixtures.

## Shared spine — _gate_common.py

`repo_root()` was byte-identical across the three gates and the fixture builder was duplicated; "a fix in one copy silently missed the others", so both were shared once (src: scripts/gates/_gate_common.py:1-9; commit dc37c1c). The gates stay single-file invocable because `sys.path[0]` is the gates directory when run as a script (src: scripts/gates/_gate_common.py:6-9).

All three gates anchor their scan on `Path(__file__).resolve().parent`, NOT cwd — each selftest includes an anchoring control that invokes the gate as a subprocess from a foreign repo's cwd and asserts the gate still scans its OWN repo (src: scripts/gates/check_root_coupling.py:206-224, scripts/gates/check_placement.py:126-144; commit 50392c0). Each gate's first output line names the root it scans (commit 42c92e1).

## check_root_coupling.py — no absolute home roots in tracked files

The open-source contract: "clone anywhere and every gate runs"; absolute home-root prefixes in tracked files silently re-couple the tree to one machine (src: scripts/gates/check_root_coupling.py:4-8). Iron law 2 (src: ARCHITECTURE.md:45-46). Mechanics:

- **Patterns are assembled at runtime from fragments** — the macOS/Linux/Windows per-user prefixes — so the gate's own source never contains a literal match for what it hunts (src: scripts/gates/check_root_coupling.py:26-27, 39-42). The migration engine uses the identical trick (src: scripts/migrate/migrate_seed.py:52-55).
- **Scope**: tracked files only — untracked local state is allowed to be dirty (src: scripts/gates/check_root_coupling.py:8-9). Binary/unreadable files are skipped as "not a text coupling surface" (src: scripts/gates/check_root_coupling.py:88-90).
- **`--staged` (the pre-commit wiring, S7)** scans the git index blobs via `git grep -I -n --cached -F` instead of the worktree, "so what is judged is exactly what is being committed"; the allowlist is then also read from the index (src: scripts/gates/check_root_coupling.py:22-24, 97-128). A git-grep return code other than 0/1 raises "broken instrument" instead of passing (src: scripts/gates/check_root_coupling.py:118-122).
- **Evidence allowlist**: `scripts/gates/root_coupling_allowlist.txt`, one `<path-or-prefix> <reason>` per line; "historical evidence files are declared there, never rewritten: rewriting evidence is forging evidence" (src: scripts/gates/check_root_coupling.py:10-14). Each entry is standing debt (src: CONTEXT.md:14-15). The allowlist was narrowed from prefix to per-file entries in commit e0f017b; the migration engine appends target-side declarations on `--apply` (src: scripts/migrate/migrate_seed.py:298-306).
- **Selftest** covers clean / tracked-violation / allowlisted / untracked-ignored / not-a-repo, plus three `--staged` controls proving judged content comes from the index and not the worktree (worktree drift ignored by `--staged`, seen by the worktree scan) (src: scripts/gates/check_root_coupling.py:157-224).

[bootstrap](../host-loop/bootstrap.md) refuses to complete if this gate's selftest is red (src: bootstrap.sh:31-32).

## check_placement.py — §2 slots vs actual root items

Mechanizes the placement contract: parses the root-level entries of ARCHITECTURE.md's §2 fenced tree (regex `^[├└]──\s+(\S+)`; nested entries under `│` deliberately do not count as root slots) and compares against the root-level items of `git ls-files` (src: scripts/gates/check_placement.py:2-11, 26-52). An undeclared root item fails loud (`UNPLACED <name>`, exit 2, "amend the map first, then land the file"); a declared slot with no files yet stays green (src: scripts/gates/check_placement.py:75-86). ARCHITECTURE.md missing or slotless is 64, not 2 — the contract itself is absent, which must not read as either green or ordinary red (src: scripts/gates/check_placement.py:61-74). Landed in commit 75cc24b.

## check_skill_pointers.py — skill content exists once

Mechanizes the S5 skills-SSOT contract (commit ae3a2db): `.agents/skills/` is the host-neutral single home; `.claude/skills/` holds only symlinks resolving into `.agents/skills/` or the module-owned home `kb-ingest/skill` (src: scripts/gates/check_skill_pointers.py:2-8, 31-33; §2 admission of module-owned symlinks in commit 6f06881). Three invariants (src: scripts/gates/check_skill_pointers.py:8-19):

1. every `.claude/skills/` entry is a symlink resolving inside an allowed content home — no real files, no escapes (`REAL-ENTRY` / `ESCAPED-LINK` violations);
2. no symlink under `.agents/skills/` resolves back into `.claude/` (`BACK-LINK` — content must never live behind a host entry);
3. repo-wide, no two real `SKILL.md` files share the same skill-directory name (`DUPLICATE-SKILL` — a residual copy re-creates the dual-home drift S5 removed), checked against tracked+untracked-visible files (src: scripts/gates/check_skill_pointers.py:101-116).

Selftest builds a fixture with a real skill home, the kb-ingest module home, and both pointer kinds, then injects each violation shape (residual copy, escaped link, back-link, far duplicate, missing surface, not-a-repo) and requires the exact exit code back (src: scripts/gates/check_skill_pointers.py:130-186). See [skills surface](../skills-surface.md) for the content inventory this gate protects.
