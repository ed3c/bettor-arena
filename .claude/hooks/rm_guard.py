#!/usr/bin/env python3
"""PreToolUse/Bash gate — deletion may not reach outside this repo.

Closes the hole a global auto-approve hook leaves open: force/recursive-only
RM patterns (`rm -rf`, `rm -f`) let a plain `rm <path>` — just as
irreversible — fall through to the classifier and run anywhere on the
filesystem (verified 2026-08-05 in the source repo: the force form blocked,
the plain form ran).

Contract:
    stdin   PreToolUse hook payload (JSON)
    exit 0  no deletion, or every target resolves inside the repo
    exit 2  BLOCK — a target resolves outside, or the command cannot be proved safe

Fails CLOSED. An unparseable command, an unexpanded $VAR, a payload this script
cannot read: each is "cannot prove the target is inside", which is a block, not a
pass. A gate that treats "I could not tell" as allow is not a gate.

Targets resolve through symlinks and `..` on purpose — textual containment is not
containment. The repo root is derived at runtime from this file's own location
(.claude/hooks/ is always two levels below root), so no machine path is baked in
and moving or re-cloning the repo re-points the boundary automatically.

Usage: registered as a PreToolUse hook on Bash; `--selftest` runs the assertions.
"""

import glob
import json
import os
import re
import shlex
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DELETERS = {"rm", "rmdir", "unlink"}
DELETER_WORD = re.compile(r"\b(rm|rmdir|unlink)\b")
# Ends one simple command, begins the next: `mv x y && rm ../z` is two commands.
# Recognised as TOKENS from a quote-aware lexer, never by splitting the raw string:
# a regex split cuts inside quotes too, so `grep 'a|b' f` came apart mid-pattern and
# left an unbalanced quote that read as an unparseable delete.
OPERATORS = {";", "&", "&&", "|", "||", "(", ")", "{", "}", "\n"}
# A substitution can hide the deleter itself — `echo $(rm ../x)` — so its mere
# presence anywhere in the command is a block: parsing into it would be a guess.
SUBSTITUTION = re.compile(r"\$\(|`")
# A value only the shell knows, checked per target token. Kept separate from
# SUBSTITUTION so that `grep 'def .*rm' "$F"` — which names a deleter inside a
# search pattern and never invokes one — is not blocked for containing a $.
# A gate that cries wolf on ordinary greps is a gate someone switches off.
# ponytail: still blocks `rm "$SCRATCH/f"` where $SCRATCH is in fact inside the
# repo. Expand the variable at the call site if that ever gets annoying.
UNRESOLVABLE = re.compile(r"[$`]")
GLOB_CHARS = re.compile(r"[*?\[]")


def segments(command: str) -> list[list[str]]:
    """The command's simple commands, as token lists. ValueError if unparseable."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True  # keep paths whole; only quotes and operators split
    out, current = [], []
    for token in lexer:  # raises ValueError on an unbalanced quote
        if token in OPERATORS:
            out.append(current)
            current = []
        else:
            current.append(token)
    out.append(current)
    return out


def targets_of(tokens: list[str]) -> list[str]:
    """Deletion targets in one simple command, or [] if it deletes nothing.

    `find . -exec rm {} +` hides the deleter mid-stream, so the scan looks for a
    deleter anywhere in the segment rather than only at position 0.
    """
    start = next((i for i, t in enumerate(tokens) if Path(t).name in DELETERS), None)
    if start is None:
        return []

    out, only_paths = [], False
    for tok in tokens[start + 1:]:
        if tok == "--":
            only_paths = True
        elif not only_paths and tok.startswith("-"):
            continue  # a flag, not a path
        elif tok in {"{}", "+", ";", "\\;"}:
            continue  # find -exec plumbing, not a path
        else:
            out.append(tok)
    return out


def escapes(target: str, cwd: Path) -> str | None:
    """Reason this target is not provably inside the repo, or None if it is."""
    if GLOB_CHARS.search(target):
        pattern = target if os.path.isabs(target) else str(cwd / target)
        matches = glob.glob(os.path.expanduser(pattern))
        if not matches:
            # Nothing matched, so nothing gets deleted — but the pattern's own
            # directory still has to be inside, or a later-created file would.
            return escapes(os.path.dirname(target) or ".", cwd)
        return next((r for m in matches if (r := escapes(m, cwd))), None)

    resolved = Path(os.path.expanduser(target))
    if not resolved.is_absolute():
        resolved = cwd / resolved
    resolved = resolved.resolve()  # follows symlinks; collapses ..
    if resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
        return None
    return f"{target!r} resolves to {resolved}, outside {REPO_ROOT}"


def violations(command: str, cwd: Path) -> list[str]:
    """Every reason this command may delete outside the repo. Empty = allowed.

    The one code path. main() and selftest() both go through here, so the
    assertions test what actually runs rather than a parallel reimplementation.
    """
    if not DELETER_WORD.search(command):
        return []  # cheap exit: no deleter word, no work to do
    if SUBSTITUTION.search(command):
        return [f"{command!r} may delete through a substitution; what it expands "
                "to is unknown until the shell runs"]
    try:
        parsed = segments(command)
    except ValueError as e:  # unbalanced quote — any reading of it is a guess
        return [f"cannot parse {command!r} ({e}); refusing to guess its targets"]
    out = []
    for segment in parsed:
        for t in targets_of(segment):
            if UNRESOLVABLE.search(t):
                out.append(f"{t!r} is a deletion target the shell resolves; "
                           "its real path is unknown here")
            elif r := escapes(t, cwd):
                out.append(r)
    return out


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        payload = None
        reasons = [f"unreadable hook payload ({e})"]
    if payload is not None:
        if payload.get("tool_name") != "Bash":
            return 0
        cwd = Path(payload.get("cwd") or os.getcwd()).resolve()
        reasons = violations(payload.get("tool_input", {}).get("command") or "", cwd)
    if reasons:
        print(f"BLOCKED by .claude/hooks/rm_guard.py: {reasons[0]}", file=sys.stderr)
        return 2
    return 0


def selftest() -> int:
    """Both directions. A gate only proved to pass is not proved to be a gate."""
    outside = REPO_ROOT.parent
    v = lambda cmd: violations(cmd, REPO_ROOT)

    # Allowed: every target inside the repo.
    assert not v("rm foo.txt"), "plain relative delete inside must pass"
    assert not v(f"rm -rf {REPO_ROOT}/loop_wiki/tmp"), "absolute inside must pass"
    assert not v("rm -f a.txt b.txt"), "multiple inside targets must pass"
    assert not v("touch a && rm b"), "chain, both inside, must pass"
    assert not v("ls -la"), "a command with no deleter must pass"
    assert not v("echo rmdir"), "a bare word, not an invocation, must pass"
    assert not v("rm ./sub/../foo"), ".. that stays inside must pass"
    # Regression: naming a deleter inside a search pattern is not invoking one.
    # This shape blocked a plain grep on 2026-08-05, which is how it was found.
    assert not v("""grep -n 'def .*rm|tier1' "$F" """), "deleter named in a pattern must pass"
    assert not v("""ls -la "$F" """), "a $ with no deleter at all must pass"
    assert not v("echo 'rm is a word here'"), "a quoted phrase must not read as a call"

    # Blocked: the plain form the global hook misses, in every escape shape.
    assert v(f"rm {outside}/x"), "plain rm outside must block"
    assert v("rm ../escape.txt"), "..-escape must block"
    assert v("rm ~/.zshrc"), "tilde-escape must block"
    assert v("touch a && rm ../b"), "second command in a chain must block"
    assert v("rm $TARGET"), "unexpandable variable must block"
    assert v("rm `which python3`"), "command substitution must block"
    assert v("echo $(rm ../x)"), "deleter hidden inside a substitution must block"
    assert v('rm "unbalanced'), "unparseable command must block"
    assert v("find . -name x -exec rm ../y {} +"), "find -exec must block"
    assert v("rm -- ../dashed"), "path after -- must block"
    assert v("rm ../*.txt"), "glob escaping the repo must block"
    assert v("rmdir ../d"), "rmdir must block"
    assert v("unlink ../f"), "unlink must block"

    # A symlink inside the repo pointing out is an escape, not a local delete.
    link = REPO_ROOT / ".rm-guard-selftest-link"
    link.unlink(missing_ok=True)
    link.symlink_to(outside)
    try:
        assert v(f"rm {link}/x"), "symlink out of the repo must block"
    finally:
        link.unlink(missing_ok=True)

    print(f"selftest OK — boundary = {REPO_ROOT}")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
