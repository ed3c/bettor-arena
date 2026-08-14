#!/usr/bin/env python3
"""What must still be true after something ran, whatever ran.

Git Town is not installed here, so nothing in this file claims anything about
Git Town's behaviour. What it does claim is checkable without it: these are the
guard rails, and a guard rail is only worth anything if it holds around a
program nobody has read.

The invariants are taken before and after, and compared:

  * every remote ref is byte-identical. `--no-push` is a flag on a program; this
    is a fact about the remote, and the two are not the same kind of statement;
  * protected and perennial branches point where they pointed;
  * nothing outside the lease changed;
  * the tree was clean before, and is clean after -- no conflict markers, no
    `.orig`/`.rej` residue, no lock files left behind;
  * the rollback subject still resolves to what it named.

`snapshot` reads a real repository. Nothing is simulated.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from gt_common import ContractError, InputError, digest, find_conflict_markers

# Files a half-finished merge or rebase leaves behind. Named, because "the tree
# is clean" is a `git status` question and these do not always answer it.
RESIDUE_GLOBS = ("*.orig", "*.rej", "*.BACKUP.*", "*.BASE.*", "*.LOCAL.*", "*.REMOTE.*")

# Directories git creates while an operation is in flight. Present afterwards
# means the operation stopped in the middle, which is the state a `--continue`
# would be offered for.
IN_FLIGHT = (
    "rebase-merge",
    "rebase-apply",
    "MERGE_HEAD",
    "CHERRY_PICK_HEAD",
    "REVERT_HEAD",
)


def git(repo: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )
    if done.returncode != 0:
        raise InputError(
            f"git {' '.join(args)} failed in {repo}: {done.stderr.strip()}"
        )
    return done.stdout.strip()


def refs(repo: Path, pattern: str) -> dict[str, str]:
    out = git(repo, "for-each-ref", "--format=%(refname) %(objectname)", pattern)
    entries = {}
    for line in out.splitlines():
        if line.strip():
            name, sha = line.rsplit(" ", 1)
            entries[name.strip()] = sha
    return entries


def snapshot(repo: Path, remote: Path | None, lease: list[str]) -> dict[str, Any]:
    """Everything that must not change, read from a real repository."""
    if not (repo / ".git").exists() and not (repo / "HEAD").exists():
        raise InputError(f"{repo} is not a git repository")

    tracked = git(repo, "ls-files").splitlines()
    in_lease = sorted(
        p for p in tracked if any(p.startswith(prefix) for prefix in lease)
    )
    out_of_lease = sorted(set(tracked) - set(in_lease))

    return {
        "head": git(repo, "rev-parse", "HEAD"),
        "branch": git(repo, "rev-parse", "--abbrev-ref", "HEAD"),
        "local_refs": refs(repo, "refs/heads"),
        # Read from the remote repository itself, not from the local
        # remote-tracking refs. A local ref that did not move is evidence about a
        # local cache; the question is whether the remote moved.
        "remote_refs": refs(remote, "refs/heads") if remote else {},
        "dirty": bool(git(repo, "status", "--porcelain")),
        "residue": residue(repo),
        "in_flight": in_flight(repo),
        "conflict_markers": conflicted_files(repo, tracked),
        # A digest over the out-of-lease files' content, so a change anywhere
        # outside the lease shows up as one number moving.
        "out_of_lease_digest": digest(
            {path: git(repo, "hash-object", path) for path in out_of_lease}
        ),
        "out_of_lease_count": len(out_of_lease),
    }


def residue(repo: Path) -> list[str]:
    found: list[str] = []
    for pattern in RESIDUE_GLOBS:
        found.extend(
            str(p.relative_to(repo))
            for p in repo.rglob(pattern)
            if ".git" not in p.parts
        )
    return sorted(found)


def in_flight(repo: Path) -> list[str]:
    git_dir = repo / ".git"
    if git_dir.is_file():  # a worktree; .git is a pointer file
        git_dir = Path(git(repo, "rev-parse", "--absolute-git-dir"))
    return sorted(name for name in IN_FLIGHT if (git_dir / name).exists())


def conflicted_files(repo: Path, tracked: list[str]) -> list[str]:
    """Files carrying conflict markers, whether or not git thinks it is merging.

    The interesting case is the one where the operation finished: git reports a
    clean tree and the markers are in the file, committed, looking like code.
    """
    found = []
    for rel in tracked:
        path = repo / rel
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if find_conflict_markers(text):
            found.append(rel)
    return sorted(found)


def compare(
    before: dict[str, Any], after: dict[str, Any], lease: list[str]
) -> dict[str, Any]:
    """Every invariant, with the reason each one exists attached to its violation."""
    violations: list[dict[str, str]] = []

    def fail(rule: str, detail: str) -> None:
        violations.append({"rule": rule, "detail": detail})

    if before["remote_refs"] != after["remote_refs"]:
        moved = sorted(
            name
            for name in set(before["remote_refs"]) | set(after["remote_refs"])
            if before["remote_refs"].get(name) != after["remote_refs"].get(name)
        )
        fail(
            "REMOTE_REF_MOVED",
            f"remote refs {moved} moved. --no-push is a flag on a program; this is a fact "
            "about the remote, and only the second one is evidence",
        )

    for name, sha in before["local_refs"].items():
        if name not in after["local_refs"]:
            fail("PROTECTED_REF_DELETED", f"{name} is gone")
        elif after["local_refs"][name] != sha and name in protected(before, lease):
            fail(
                "PROTECTED_REF_MOVED",
                f"{name} moved {sha[:12]} -> {after['local_refs'][name][:12]}",
            )

    if after["dirty"] and not before["dirty"]:
        fail("TREE_LEFT_DIRTY", "the tree was clean before and is not now")

    if after["residue"]:
        fail(
            "RESIDUE_LEFT",
            f"{after['residue']} remain. `git status` can report a clean tree with these "
            "on disk, which is a half-finished merge that looks finished",
        )

    if after["in_flight"]:
        fail(
            "OPERATION_IN_FLIGHT",
            f"{after['in_flight']} present: the operation stopped in the middle, which is "
            "exactly the state a --continue would be offered for",
        )

    if after["conflict_markers"]:
        fail(
            "SILENT_CONFLICT_MARKERS",
            f"{after['conflict_markers']} carry conflict markers. The dangerous case is "
            "the one where the operation finished: git reports clean and the markers are "
            "in the file, looking like code",
        )

    if before["out_of_lease_digest"] != after["out_of_lease_digest"]:
        fail(
            "OUT_OF_LEASE_DIFF",
            f"{after['out_of_lease_count']} file(s) outside {lease} changed",
        )

    return {
        "held": not violations,
        "violations": violations,
        "checked": [
            "REMOTE_REF_MOVED",
            "PROTECTED_REF_MOVED",
            "TREE_LEFT_DIRTY",
            "RESIDUE_LEFT",
            "OPERATION_IN_FLIGHT",
            "SILENT_CONFLICT_MARKERS",
            "OUT_OF_LEASE_DIFF",
        ],
    }


def protected(snapshot_before: dict[str, Any], lease: list[str]) -> set[str]:
    """Refs a bounded sync may not move: main and anything perennial."""
    return {
        name
        for name in snapshot_before["local_refs"]
        if name.endswith(("/main", "/master")) or "/perennial/" in name
    }


def require_held(result: dict[str, Any]) -> None:
    if not result["held"]:
        detail = "; ".join(f"{v['rule']}: {v['detail']}" for v in result["violations"])
        raise ContractError(f"the bounded-sync invariants did not hold -- {detail}")


def rollback_subject(
    repo: Path, remote: Path | None, lease: list[str]
) -> dict[str, Any]:
    """What an undo would return to, pinned by SHA rather than by name.

    A rollback target named by branch drifts the moment the branch moves, and the
    rollback then restores something nobody chose. The name is kept for reading;
    the SHA is what it means.
    """
    state = snapshot(repo, remote, lease)
    return {
        "branch": state["branch"],
        "commit": state["head"],
        "refs": state["local_refs"],
        "subject_digest": digest({"head": state["head"], "refs": state["local_refs"]}),
    }


def require_rollback_intact(
    before: dict[str, Any], repo: Path, remote: Path | None, lease: list[str]
) -> None:
    """The rollback target can still be rolled back to.

    Not "the branch has not moved". A branch moving forward is what a sync does,
    and a rollback to the pre-sync commit is still available -- that is the point.
    Drift is the commit becoming *unreachable* from the branch it was recorded on,
    which is what a reset or a force-push does, and after which the rollback
    restores something nobody chose.
    """
    head = before["branch"]
    if not commit_exists(repo, before["commit"]):
        raise ContractError(
            f"the rollback subject named {before['commit'][:12]} and that commit is no "
            "longer in the repository; a rollback target named by branch restores "
            "something nobody chose"
        )
    if f"refs/heads/{head}" not in refs(repo, "refs/heads"):
        raise ContractError(
            f"the rollback subject was recorded on {head}, which no longer exists; a "
            "rollback target named by branch restores something nobody chose"
        )
    if not is_ancestor(repo, before["commit"], head):
        raise ContractError(
            f"the rollback subject {before['commit'][:12]} is no longer reachable from "
            f"{head}. The branch was reset or force-pushed past it, and a rollback target "
            "named by branch restores something nobody chose"
        )


def commit_exists(repo: Path, commit: str) -> bool:
    done = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{commit}^{{commit}}"],
        capture_output=True,
        check=False,
    )
    return done.returncode == 0


def is_ancestor(repo: Path, commit: str, branch: str) -> bool:
    done = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", commit, branch],
        capture_output=True,
        check=False,
    )
    return done.returncode == 0
