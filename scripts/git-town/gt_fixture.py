#!/usr/bin/env python3
"""A real stack in a real repository with a real remote.

Not a mock. The invariants in gt_invariants read refs, files and git-dir state
off disk, and a fixture that only pretends to be a repository would let every one
of them pass while checking nothing.

The remote is a bare repository on the filesystem. That is what makes
`REMOTE_REF_MOVED` a real check: a push here genuinely moves refs in another
repository, and the invariant reads them from that repository rather than from
the local remote-tracking cache -- which is the thing that does not move when
somebody pushes from somewhere else, and does move when nobody pushed at all.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from gt_common import InputError

# The stack this fixture builds: main, then two branches each on top of the last.
STACK = ("feature-a", "feature-b")

# Environment that makes every run byte-identical. Timestamps and identities in
# the environment would make two fixtures differ in their commit SHAs, and a
# fixture whose SHAs move cannot be compared against a recorded receipt.
FIXED_ENV = {
    "GIT_AUTHOR_NAME": "fixture",
    "GIT_AUTHOR_EMAIL": "fixture@invalid",
    "GIT_COMMITTER_NAME": "fixture",
    "GIT_COMMITTER_EMAIL": "fixture@invalid",
    "GIT_AUTHOR_DATE": "2020-01-01T00:00:00+00:00",
    "GIT_COMMITTER_DATE": "2020-01-01T00:00:00+00:00",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
}


def run(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    import os

    merged = {**os.environ, **FIXED_ENV, **(env or {})}
    done = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )
    if done.returncode != 0:
        raise InputError(f"git {' '.join(args)} failed: {done.stderr.strip()}")
    return done.stdout.strip()


def build(root: Path) -> dict[str, Any]:
    """A bare remote, a clone, and a two-deep stack on top of main."""
    remote = root / "remote.git"
    repo = root / "work"
    remote.mkdir(parents=True)
    subprocess.run(
        ["git", "init", "--bare", "--initial-branch=main", str(remote)],
        capture_output=True,
        check=True,
    )

    subprocess.run(
        ["git", "clone", str(remote), str(repo)], capture_output=True, check=True
    )
    run(repo, "config", "user.name", "fixture")
    run(repo, "config", "user.email", "fixture@invalid")
    run(repo, "config", "commit.gpgsign", "false")

    (repo / "leased").mkdir()
    (repo / "leased" / "one.txt").write_text("one\n", encoding="utf-8")
    (repo / "outside.txt").write_text("outside the lease\n", encoding="utf-8")
    run(repo, "add", "-A")
    run(repo, "commit", "-m", "main: initial")
    run(repo, "push", "-u", "origin", "main")

    for index, branch in enumerate(STACK, start=1):
        run(repo, "checkout", "-b", branch)
        (repo / "leased" / f"{branch}.txt").write_text(
            f"{branch} content\n", encoding="utf-8"
        )
        run(repo, "add", "-A")
        run(repo, "commit", "-m", f"{branch}: add {index}")
        run(repo, "push", "-u", "origin", branch)

    run(repo, "checkout", STACK[-1])
    return {
        "root": root,
        "remote": remote,
        "repo": repo,
        "stack": list(STACK),
        "lease": ["leased/"],
    }
