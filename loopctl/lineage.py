#!/usr/bin/env python3
"""Workflow lineage: sense a touched workflow, stamp it, and replay it.

    lineage.py trailer <repo> <lock>          the trailer this commit should carry (empty if untouched)
    lineage.py check   <repo> <lock> <msgfile> 0 ok · 2 a workflow file is staged and unstamped
    lineage.py resolve <repo> <ref>            print the workflow commit a ref names, with its tags
    lineage.py --selftest

Why a trailer rather than a rule people remember: the workflow is 60 files spread
over five directories, and "did I touch the workflow?" is not a question anyone
answers reliably by eye. workflow.lock knows, so the hook asks it and writes the
answer into the message.

What the trailer says, and why each part is load-bearing:

    Workflow-Lineage: <commit>            the workflow this change descends from
    Workflow-Version: <tag>               present only when that commit carries one
    Workflow-Touched: <kind>:<loop>:<path>   one line per file, kind first

Kind first because "the workflow changed" cannot be acted on: a harness line means
the mechanism moved and the proofs must be re-stamped, a context line means the
document the model reads moved and the openwiki lane's output may shift, an
artifact line means a terminus moved. They are repaired differently.

The lineage commit is the one the CURRENT lock was built at, not HEAD: that is the
version being descended from, and it is what `replay` can check out and run.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

TRAILER = "Workflow-Lineage:"
VERSION_TRAILER = "Workflow-Version:"
TOUCHED_TRAILER = "Workflow-Touched:"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    ).stdout.strip()


def load_lock(lock: Path) -> dict:
    if not lock.is_file():
        print(
            f"lineage FATAL: no workflow lock at {lock}. Without it nothing knows which "
            "files belong to the workflow, and every commit would pass by covering nothing. "
            "Build it with `sh loopctl/loopctl.sh workflow lock`.",
            file=sys.stderr,
        )
        raise SystemExit(64)
    return json.loads(lock.read_text(encoding="utf-8"))


def staged(repo: Path) -> list[str]:
    out = git(repo, "diff", "--cached", "--name-only", "--diff-filter=ACMR")
    return [line for line in out.splitlines() if line.strip()]


def touched(lock: dict, paths: list[str]) -> list[tuple[str, str, str]]:
    return sorted(
        (lock["files"][p]["kind"], lock["files"][p]["loop"], p)
        for p in paths
        if p in lock["files"]
    )


def trailer_lines(lock: dict, hits: list[tuple[str, str, str]]) -> list[str]:
    if not hits:
        return []
    lines = [f"{TRAILER} {lock['workflow_commit']}"]
    for tag in lock.get("workflow_tags") or []:
        lines.append(f"{VERSION_TRAILER} {tag}")
    lines += [f"{TOUCHED_TRAILER} {kind}:{loop}:{path}" for kind, loop, path in hits]
    return lines


def has_trailer(message: str) -> bool:
    return any(line.startswith(TRAILER) for line in message.splitlines())


def resolve(repo: Path, ref: str) -> dict:
    commit = git(repo, "rev-parse", f"{ref}^{{commit}}")
    if not commit:
        print(
            f"lineage FATAL: {ref!r} does not resolve to a commit here", file=sys.stderr
        )
        raise SystemExit(64)
    return {
        "ref": ref,
        "commit": commit,
        "tags": git(repo, "tag", "--points-at", commit).split(),
        "subject": git(repo, "log", "-1", "--format=%s", commit),
    }


def main(argv: list[str]) -> int:
    if argv[:1] == ["--selftest"]:
        return _selftest()
    if len(argv) < 3:
        print(__doc__.strip(), file=sys.stderr)
        return 64
    cmd, repo = argv[0], Path(argv[1])
    if cmd == "resolve":
        print(json.dumps(resolve(repo, argv[2]), indent=2))
        return 0

    lock = load_lock(Path(argv[2]))
    hits = touched(lock, staged(repo))
    if cmd == "trailer":
        for line in trailer_lines(lock, hits):
            print(line)
        return 0
    if cmd == "check":
        if not hits:
            return 0
        message = Path(argv[3]).read_text(encoding="utf-8")
        if has_trailer(message):
            return 0
        print(
            "lineage FAIL: this commit stages workflow files and carries no "
            f"{TRAILER} trailer, so nothing records which workflow it descends from:",
            file=sys.stderr,
        )
        for kind, loop, path in hits:
            print(f"  {kind}:{loop}:{path}", file=sys.stderr)
        print(
            "  The prepare-commit-msg hook writes this automatically; if you cleared it, "
            "put it back with `sh loopctl/loopctl.sh workflow trailer`.",
            file=sys.stderr,
        )
        return 2
    print(__doc__.strip(), file=sys.stderr)
    return 64


# ---------------------------------------------------------------- selftest


def _selftest() -> int:
    red = 0

    def case(name: str, got, want) -> None:
        nonlocal red
        if got != want:
            print(
                f"SELFTEST case failed — {name}: got {got!r}, want {want!r}",
                file=sys.stderr,
            )
            red = 1

    lock = {
        "workflow_commit": "a" * 40,
        "workflow_tags": ["v1.0"],
        "files": {
            "p/harness.sh": {"kind": "harness", "loop": "macro", "sha256": "x"},
            "p/prompt.md": {"kind": "context", "loop": "openwiki", "sha256": "y"},
        },
    }
    case(
        "untouched-emits-nothing", trailer_lines(lock, touched(lock, ["other.txt"])), []
    )

    hits = touched(lock, ["p/prompt.md", "other.txt", "p/harness.sh"])
    lines = trailer_lines(lock, hits)
    case("lineage-first", lines[0], f"{TRAILER} {'a' * 40}")
    case("version-from-tag", lines[1], f"{VERSION_TRAILER} v1.0")
    # Kind leads each touched line: a moved mechanism and a moved prompt are
    # repaired differently, and a flat path list cannot say which this was.
    case(
        "kind-and-loop-lead-each-line",
        lines[2:],
        [
            f"{TOUCHED_TRAILER} context:openwiki:p/prompt.md",
            f"{TOUCHED_TRAILER} harness:macro:p/harness.sh",
        ],
    )
    # A tagless workflow must still stamp its commit; the version line is the
    # optional part, not the trailer itself.
    case(
        "tagless-still-stamps",
        trailer_lines({**lock, "workflow_tags": []}, hits)[0],
        f"{TRAILER} {'a' * 40}",
    )
    case("trailer-detected", has_trailer(f"subject\n\n{TRAILER} abc\n"), True)
    case("absent-trailer-detected", has_trailer("subject\n\nbody only\n"), False)
    # The trailer must be recognised as a trailer, not as any line mentioning it.
    case(
        "mention-in-prose-is-not-a-trailer",
        has_trailer("we discuss Workflow-Lineage here\n"),
        False,
    )

    print("SELFTEST " + ("GREEN" if not red else "RED"))
    return red


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
