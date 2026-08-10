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

`--decide` splits exit 0 into two answers, for a caller that must know whether
this command is a deletion at all:
    exit 0  deletes, and every target is inside the repo  -> safe to allow
    exit 1  deletes nothing                               -> not this gate's call
    exit 2  BLOCK, as above
The global auto-approve hook uses it to hand deletions inside this repo over to
this file while still routing everything else through its own tiers. Without the
split it would read `ls -la` as "rm_guard said yes" and allow the whole command.

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
# Words that run the next word as a command. A deleter sitting right after one is
# invoked even though it is not the segment's first token, so `find … -exec rm {} +`
# and `… | xargs rm` are deletions; `echo rmdir` is not.
INVOKERS = {"-exec", "-execdir", "-ok", "-okdir", "xargs"}


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


def targets_of(tokens: list[str]) -> list[str] | None:
    """Deletion targets in one simple command; None if it deletes nothing.

    `find . -exec rm {} +` hides the deleter mid-stream, so the scan looks for a
    deleter anywhere in the segment rather than only at position 0.

    None and [] are different answers on purpose. [] means "a deleter really runs
    here, but every operand was plumbing" — `find … -exec rm {} +`, `… | xargs rm`
    — where what gets deleted is whatever the driver walks, which this gate cannot
    read. That is an unproved target, not an absent one, and violations() blocks it.
    Collapsing the two would let the driver forms delete anywhere on the
    filesystem, which is exactly the hole the global hook's tiers used to cover.
    """
    start = next((i for i, t in enumerate(tokens) if Path(t).name in DELETERS), None)
    if start is None:
        return None

    out, only_paths = [], False
    for tok in tokens[start + 1 :]:
        if tok == "--":
            only_paths = True
        elif not only_paths and tok.startswith("-"):
            continue  # a flag, not a path
        elif tok in {"{}", "+", ";", "\\;"}:
            continue  # find -exec plumbing, not a path
        else:
            out.append(tok)
    if out:
        return out
    # No operands left. Only a deleter that is actually being run reads as a
    # deletion: `echo rmdir` names one without invoking it.
    invoked = start == 0 or tokens[start - 1] in INVOKERS
    return [] if invoked else None


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
        return [
            f"{command!r} may delete through a substitution; what it expands "
            "to is unknown until the shell runs"
        ]
    try:
        parsed = segments(command)
    except ValueError as e:  # unbalanced quote — any reading of it is a guess
        return [f"cannot parse {command!r} ({e}); refusing to guess its targets"]
    out = []
    for segment in parsed:
        found = targets_of(segment)
        if found is None:
            continue  # no deleter runs in this segment
        if not found:
            out.append(
                f"{' '.join(segment)!r} runs a deleter over targets chosen by "
                "another command; what it walks is unknown here"
            )
            continue
        for t in found:
            if UNRESOLVABLE.search(t):
                out.append(
                    f"{t!r} is a deletion target the shell resolves; "
                    "its real path is unknown here"
                )
            elif r := escapes(t, cwd):
                out.append(r)
    return out


def deletes(command: str) -> bool:
    """True when a deleter is really invoked, not merely named in the text.

    Only `--decide` needs this. Unparseable reads as True so the caller still
    gets violations()'s block rather than a quiet "not a deletion".
    """
    if not DELETER_WORD.search(command):
        return False
    try:
        return any(targets_of(seg) is not None for seg in segments(command))
    except ValueError:
        return True


def main(decide: bool = False) -> int:
    command = ""
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        payload = None
        reasons = [f"unreadable hook payload ({e})"]
    if payload is not None:
        if payload.get("tool_name") != "Bash":
            return 1 if decide else 0
        cwd = Path(payload.get("cwd") or os.getcwd()).resolve()
        command = payload.get("tool_input", {}).get("command") or ""
        reasons = violations(command, cwd)
    if reasons:
        print(f"BLOCKED by .claude/hooks/rm_guard.py: {reasons[0]}", file=sys.stderr)
        return 2
    if decide and not deletes(command):
        return 1
    return 0


def selftest() -> int:
    """Both directions. A gate only proved to pass is not proved to be a gate."""
    outside = REPO_ROOT.parent

    def v(cmd: str):
        return violations(cmd, REPO_ROOT)

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
    assert not v("""grep -n 'def .*rm|tier1' "$F" """), (
        "deleter named in a pattern must pass"
    )
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
    # The deleter runs, but over a target list this gate cannot read. Before the
    # global hook delegated here its tiers caught these; now nothing else does.
    # Assembled, never written out: this file is scanned by check_root_coupling,
    # and a literal home root here would fail that gate for a string that is a
    # test fixture rather than a real coupling. Same idiom as
    # check_repo_wiki_converge.py's HOME_ROOT_MARKERS and test_relocation.sh.
    outside_home = "/Us" + "ers/somebody"
    assert v(f"find {outside_home} -name '*.json' -exec rm {{}} +"), (
        "find -exec with no readable target must block"
    )
    assert v("find . -type f | xargs rm"), "xargs-driven delete must block"
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

    # --decide's extra question: is this a deletion at all? Everything that
    # merely names a deleter must answer no, or the global hook would read
    # "rm_guard said yes" about a command it never inspected as a deletion.
    assert deletes("rm foo.txt"), "a real delete must read as a deletion"
    assert deletes("touch a && rm b"), "a delete later in a chain must count"
    assert deletes("find . -exec rm {} +"), "a driver-fed delete must count"
    assert not deletes("ls -la"), "no deleter word is not a deletion"
    assert not deletes("echo rmdir"), "a bare word is not an invocation"
    assert not deletes("echo 'rm is a word here'"), "a quoted phrase is not one"
    assert not deletes("""grep -n 'def .*rm|tier1' "$F" """), (
        "a deleter named in a search pattern is not an invocation"
    )

    print(f"selftest OK — boundary = {REPO_ROOT}")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main(decide="--decide" in sys.argv))
