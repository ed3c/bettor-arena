---
type: Component
title: Claude host config — settings.json and rm_guard
description: The versioned Claude Code host layer — the PreToolUse hook registration and the fail-closed rm_guard.py deletion boundary with its parser design and two-direction selftest.
tags: [claude-code, host-config, deletion-boundary]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: 2c36ddf
covers: [rm-guard, pretooluse-hook, fail-closed]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# Claude host config — settings.json and rm_guard

`.claude/` is the versioned Claude Code host configuration (src: ARCHITECTURE.md:24). It carries three things: `settings.json` (hook registration), `hooks/rm_guard.py` (the deletion boundary), and `skills/` (twenty symlinks into the host-neutral content homes — see [skills surface](../skills-surface.md)). Enabling the hook and the project MCP is a human admit (src: CLAUDE.md:6). Registered as versioned host config in S6 (commit d69f2bd, issue #8).

## settings.json

A single PreToolUse hook on the `Bash` matcher runs `python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/rm_guard.py"` with status message "checking deletion boundary" (src: .claude/settings.json:3-14). `$CLAUDE_PROJECT_DIR` keeps the registration machine-independent; `tests/test_host_config.sh` asserts both that the variable is used and that a PreToolUse Bash hook registering rm_guard actually exists in the parsed JSON (src: tests/test_host_config.sh:14-20).

## rm_guard.py — the deletion boundary

Contract: stdin receives the PreToolUse payload; exit 0 = no deletion or every target provably inside the repo; exit 2 = BLOCK (src: .claude/hooks/rm_guard.py:11-14). It closes a verified hole: a global auto-approve hook blocked `rm -rf`/`rm -f` patterns but let a plain `rm <path>` — just as irreversible — run anywhere (verified 2026-08-05 in the source repo; src: .claude/hooks/rm_guard.py:4-9).

**Fails CLOSED.** An unparseable command, an unexpanded `$VAR`, an unreadable payload — each is "cannot prove the target is inside", which is a block, not a pass: "A gate that treats 'I could not tell' as allow is not a gate" (src: .claude/hooks/rm_guard.py:16-19).

**Boundary derivation.** `REPO_ROOT = Path(__file__).resolve().parents[2]` — the repo root comes from the guard's own location, so no machine path is baked in and re-cloning re-points the boundary (src: .claude/hooks/rm_guard.py:21-24, 35).

### Parser design (each choice has a recorded reason)

- Deleters: `rm`, `rmdir`, `unlink`, recognized by basename anywhere in a segment — `find . -exec rm {} +` hides the deleter mid-stream (src: .claude/hooks/rm_guard.py:37-38, 73-78).
- Command segmentation uses a quote-aware `shlex` lexer with `punctuation_chars`, never a regex split of the raw string: a regex split cut inside quotes, so `grep 'a|b' f` came apart mid-pattern and read as an unparseable delete (src: .claude/hooks/rm_guard.py:39-43, 57-69).
- Any `$(` or backtick ANYWHERE blocks — a substitution can hide the deleter itself (`echo $(rm ../x)`); parsing into it would be a guess (src: .claude/hooks/rm_guard.py:44-46, 123-125).
- Per-target `[$\`]` check is SEPARATE from the substitution check so `grep 'def .*rm' "$F"` — a deleter named inside a search pattern, never invoked — is not blocked: "a gate that cries wolf on ordinary greps is a gate someone switches off" (src: .claude/hooks/rm_guard.py:47-53). Known accepted cost, marked in-source: `rm "$SCRATCH/f"` blocks even when `$SCRATCH` is inside the repo (src: .claude/hooks/rm_guard.py:51-53).
- Targets resolve through symlinks and `..` on purpose — "textual containment is not containment" (src: .claude/hooks/rm_guard.py:20-21, 106-112). Globs are expanded; a glob matching nothing still requires the pattern's own directory to be inside, "or a later-created file would" escape (src: .claude/hooks/rm_guard.py:96-104).
- One code path: `violations()` serves both `main()` and `selftest()`, "so the assertions test what actually runs rather than a parallel reimplementation" (src: .claude/hooks/rm_guard.py:115-120).

### Selftest — both directions

`--selftest` asserts allowed shapes (inside deletes, chains, `..` that stays inside, deleter words in grep patterns and quoted phrases — including the exact regression shape that blocked a plain grep on 2026-08-05) AND blocked shapes (plain rm outside, `..`/tilde escapes, chains, unexpandable variables, substitutions, unbalanced quotes, `find -exec`, `--`-separated paths, escaping globs, rmdir/unlink, and a repo-inside symlink pointing out) (src: .claude/hooks/rm_guard.py:158-199). Header thesis: "A gate only proved to pass is not proved to be a gate" (src: .claude/hooks/rm_guard.py:159).

`tests/test_host_config.sh` drives the guard's CLI seam in both directions too — a block (2) on an escape and a pass (0) on an inside delete, "or its green proves nothing" (src: tests/test_host_config.sh:2-4).
