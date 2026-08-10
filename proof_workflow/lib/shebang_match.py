#!/usr/bin/env python3
"""No proof or control may run a bash-shebang script with `sh`.

    shebang_match.py            scan the repo, exit 2 on any mismatch
    shebang_match.py --selftest

It works right up until the exercised path uses bash-only syntax, and then it
fails as a syntax error inside a step that is about something else entirely. That
is how it presented here: a new selftest case used process substitution, and the
openwiki proof went red with `syntax error near unexpected token '('` against a
worker whose shebang had said bash all along. Six sibling scripts were invoked
the same way and were fine only because they really are `#!/bin/sh`.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    """The tree containing THIS FILE, never the caller's cwd.

    Anchored on __file__ because the answer changes with the tree: run from a
    worktree that lacks a fix, the same scan reports the mismatch the fix
    removed, and comparing that against a proof run in the main tree compares
    two different trees while looking like one measurement. That is how it
    surfaced — a live scan said exit 2 next to a harness proof saying 0.

    The env scrub is the second half and is not hypothetical: git exports
    GIT_DIR / GIT_WORK_TREE / GIT_PREFIX to hooks, and a relative GIT_WORK_TREE
    ("." is common) is reinterpreted after `git -C`, making a file under
    proof_workflow/lib believe that directory is the root. Same shape and same
    reason as scripts/gates/_gate_common.py, kept local rather than imported:
    proof_workflow/ owns its own lib, and reaching into scripts/gates/ would
    make two modules depend on each other to resolve a path.
    """
    env = os.environ.copy()
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_PREFIX"):
        env.pop(name, None)
    return Path(
        subprocess.run(
            [
                "git",
                "-C",
                str(Path(__file__).resolve().parent),
                "rev-parse",
                "--show-toplevel",
            ],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        ).stdout.strip()
    )


# `sh path/to/x.sh` but not `bash path/to/x.sh` — the negative lookbehind is the
# whole point, since "sh " is a suffix of "bash ".
# The lookbehind must exclude `.` and `/` as well as `-` and word characters, or
# the `sh` ending `worker.sh` reads as the `sh` command and every line that
# passes an argument after a script path becomes a hit.
INVOKE = re.compile(r"(?<![-\w./])sh\s+(?:\"?\$?[\w{}/.\"-]*?)([\w.-]+\.sh)")

# `sh "$SOME_VAR"` — the target is a variable, so no basename can be resolved and
# the check above simply does not apply. Reported rather than passed over: a
# blind spot nobody can see is worse than one that announces itself every run.
UNRESOLVED = re.compile(r"(?<![-\w./])sh\s+\"?\$[\w{]")

# `docker run --entrypoint sh <image>` is sh being made the container's entry
# point, not sh being handed a host script. Named specifically rather than
# widening the patterns, which would blind them to the real shape.
ENTRYPOINT = re.compile(r"--entrypoint\s+sh\b")


def bash_scripts(root: Path) -> set[str]:
    out = subprocess.run(
        ["git", "-C", str(root), "ls-files", "*.sh"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    named = set()
    for rel in out:
        p = root / rel
        try:
            first = p.read_text(encoding="utf-8", errors="replace").splitlines()[0]
        except (OSError, IndexError):
            continue
        if "bash" in first:
            named.add(Path(rel).name)
    return named


def scan(root: Path) -> tuple[list[str], list[str]]:
    bash = bash_scripts(root)
    if not bash:
        # Measured, not imagined: stubbing the resolver to return an empty set
        # made the whole scan report zero mismatches and exit 0. A checker that
        # resolved nothing and returned success is indistinguishable from one
        # that checked everything and found nothing, and this is the one shape
        # this repo refuses everywhere else. 64 = cannot tell, never 0 or 2.
        raise SystemExit(
            "shebang FATAL: no bash-shebang script found anywhere in %s. Either "
            "this tree really has none, or the resolver is broken — and a pass "
            "that covered nothing looks exactly like a pass that covered "
            "everything." % root
        )
    bad, unresolved = [], []
    for caller in sorted((root / "proof_workflow").glob("*.sh")):
        for n, line in enumerate(caller.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("#") or ENTRYPOINT.search(line):
                continue
            hits = list(INVOKE.finditer(line))
            for hit in hits:
                if hit.group(1) in bash:
                    bad.append(
                        "%s:%d runs %s (a bash script) with sh"
                        % (caller.relative_to(root), n, hit.group(1))
                    )
            # Only when nothing WAS resolvable: `sh "$ROOT/loopctl/x.sh"` carries
            # a literal basename after the variable and is fully checkable, so
            # reporting it as unchecked would bury the genuine blind spots.
            if not hits and UNRESOLVED.search(line):
                unresolved.append(
                    "%s:%d runs a VARIABLE target with sh — not checkable here"
                    % (caller.relative_to(root), n)
                )
    return bad, unresolved


def _selftest() -> int:
    red = 0

    def case(name, got, want):
        nonlocal red
        if got == want:
            print("  [ok]   %s" % name)
        else:
            print("  [RED]  %s — got %r, want %r" % (name, got, want), file=sys.stderr)
            red = 1

    # The regex is the whole mechanism, so it is what gets planted against.
    case(
        "plain-sh-invocation-is-caught",
        bool(INVOKE.search("  -- sh kb/worker.sh --selftest")),
        True,
    )
    case(
        "bash-invocation-is-not-caught",
        bool(INVOKE.search("  -- bash kb/worker.sh --selftest")),
        False,
    )
    # A variable target cannot be resolved to a basename, so it is REPORTED
    # instead of checked. The first version asserted the opposite and went red
    # against its own mechanism — the fix was to state the limit, not loosen it.
    case(
        "variable-target-is-reported-not-checked",
        (
            bool(INVOKE.search('capture x -- sh "$WT/$WORKER"')),
            bool(UNRESOLVED.search('capture x -- sh "$WT/$WORKER"')),
        ),
        (False, True),
    )
    case(
        "literal-target-is-not-reported-as-unresolved",
        bool(UNRESOLVED.search("  -- sh kb/worker.sh")),
        False,
    )
    # Three shapes that each produced a false positive in the live scan.
    case(
        "script-path-argument-is-not-an-sh-command",
        bool(INVOKE.search('-- bash port/worker.sh "$REQUEST" --dry-run')),
        False,
    )
    case(
        "entrypoint-sh-is-a-container-entry-not-a-script",
        bool(ENTRYPOINT.search('docker run --rm --entrypoint sh "$IMAGE" -c ...')),
        True,
    )
    m2 = INVOKE.search('capture x -- sh "$ROOT/loopctl/container-run.sh" serve')
    case(
        "variable-prefix-with-literal-basename-is-still-checkable",
        m2.group(1) if m2 else None,
        "container-run.sh",
    )
    m = INVOKE.search("  -- sh proof_workflow/lib/prove.sh --selftest")
    case("basename-is-extracted", m.group(1) if m else None, "prove.sh")
    # `sh` inside a word must not fire, or every mention of a *.sh path would.
    case(
        "dash-sh-suffix-is-not-a-match",
        bool(INVOKE.search("use --dry-run-sh worker.sh")),
        False,
    )

    # The vacuous-pass guard, driven rather than trusted: with the resolver
    # returning nothing the scan used to report zero mismatches and exit 0.
    import tempfile

    with tempfile.TemporaryDirectory() as t:
        fake = Path(t)
        (fake / "proof_workflow").mkdir()
        (fake / "proof_workflow" / "prove_x.sh").write_text(
            "-- sh a/worker.sh\n", encoding="utf-8"
        )
        real = globals()["bash_scripts"]
        globals()["bash_scripts"] = lambda _r: set()
        try:
            scan(fake)
            case("empty-resolver-is-fatal-not-a-pass", "returned", "SystemExit")
        except SystemExit as exc:
            case(
                "empty-resolver-is-fatal-not-a-pass",
                "covered nothing" in str(exc),
                True,
            )
        finally:
            globals()["bash_scripts"] = real

    # Anchoring, driven rather than asserted: invoked as a subprocess from a
    # FOREIGN repo's cwd, the scan must still report its OWN tree. It resolved
    # from cwd until this case existed, so running it from a worktree scanned
    # the worktree — and the answer differs per tree, which is the whole reason
    # this matters. scripts/gates/check_placement.py carries the identical case
    # under the identical name; two anchoring conventions in one repo is how a
    # reader learns the wrong one.
    with tempfile.TemporaryDirectory() as t:
        foreign = Path(t) / "foreign"
        foreign.mkdir()
        subprocess.run(["git", "-C", str(foreign), "init", "-q"], check=True)
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve())],
            cwd=str(foreign),
            capture_output=True,
            text=True,
        )
        first = (proc.stdout or "<no output>").splitlines()[0]
        own = str(repo_root())
        case(
            "external-cwd-scans-own-repo",
            (own in first, str(foreign) in first),
            (True, False),
        )
        if own not in first:
            print("  detail — own=%s first=%s" % (own, first), file=sys.stderr)

    if red == 0:
        print("SELFTEST GREEN")
        return 0
    print("SELFTEST RED", file=sys.stderr)
    return 2


if __name__ == "__main__":
    if sys.argv[1:2] == ["--selftest"]:
        sys.exit(_selftest())
    root = repo_root()
    # Which tree answered, printed FIRST. Without it a red here and a green in a
    # proof read as a contradiction rather than as two trees.
    print("shebang: scanning repo root %s" % root)
    problems, unresolved = scan(root)
    for p in problems:
        print("shebang-mismatch: %s" % p, file=sys.stderr)
    for u in unresolved:
        print("shebang-unchecked: %s" % u)
    if problems:
        sys.exit(2)
    print(
        "no proof or control runs a bash script with sh (%d variable target(s) not checkable)"
        % len(unresolved)
    )
