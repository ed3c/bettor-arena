#!/usr/bin/env python3
"""Cleanup and orphan recovery. Fail closed, and delete nothing by default.

Orphan recovery is the one component here that can destroy work, so it is built
inside out: `inventory` finds candidates and classifies them, and `plan`
produces actions — but every action that removes anything starts as
`PROPOSED_REQUIRES_HUMAN`. `execute` runs only the actions a human admitted, and
re-checks each one against the filesystem immediately before acting, because an
inventory taken five minutes ago describes a tree that may have gained a Worker
since.

Three things are never auto-removable, and the reasons differ:

    a worktree with an active lease   someone is using it
    a worktree with uncommitted work  the work exists nowhere else
    a worktree we could not read      absence of evidence, and a GC that treats
                                      "cannot tell" as "safe to delete" is a GC
                                      that deletes exactly what it cannot see

The third is the one that gets left out. A scan error on one directory is easy
to skip past, and skipping past it means the directory is classified as having
no reason to keep it.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from wf_common import (
    ContractError,
    non_empty_str,
    normalise_path,
    paths_overlap,
)

DISPOSITIONS = (
    "AUTO_REMOVABLE",
    "PROPOSED_REQUIRES_HUMAN",
    "KEEP_ACTIVE_LEASE",
    "KEEP_DIRTY",
    "KEEP_UNREADABLE",
)

# Only this one may ever be executed without a human decision, and only for a
# workspace that is both leaseless and empty of uncommitted work.
AUTO_DISPOSITION = "AUTO_REMOVABLE"


def _dirty(path: Path) -> bool | None:
    """Does this workspace hold work that exists nowhere else?

    Returns None when it cannot be determined. None is not False: the caller
    must be able to tell "clean" from "could not look", because they lead to
    opposite decisions.
    """
    marker = path / ".worker-dirty"
    try:
        if marker.exists():
            return True
        entries = list(path.iterdir())
    except OSError:
        return None
    # A workspace with any file outside the known scaffold counts as dirty here.
    # Deliberately conservative: over-keeping costs disk, under-keeping costs
    # the only copy of someone's work.
    return any(entry.name not in {".lease", ".worker-scaffold"} for entry in entries)


def inventory(
    root: Path, held_leases: list[dict[str, Any]], owner_checkout: str
) -> list[dict[str, Any]]:
    """Every workspace under root, classified. Reports; never removes."""
    non_empty_str(owner_checkout, "owner_checkout")
    leased_paths = {
        lease["worktree_path"]
        for lease in held_leases
        if lease["state"] in {"GRANTED", "ACTIVE"}
    }

    found: list[dict[str, Any]] = []
    try:
        candidates = sorted(p for p in root.iterdir() if p.is_dir())
    except OSError as exc:
        raise ContractError(f"cannot inventory {root}: {exc}") from exc

    for path in candidates:
        relative = path.name
        dirty = _dirty(path)
        leased = any(
            paths_overlap(relative, str(normalise_path(leased, "leased")))
            for leased in leased_paths
        )
        if leased:
            disposition, reason = "KEEP_ACTIVE_LEASE", "a live lease names this path"
        elif dirty is None:
            disposition, reason = (
                "KEEP_UNREADABLE",
                "the workspace could not be read; a GC that treats 'cannot tell' as "
                "'safe to delete' deletes exactly what it cannot see",
            )
        elif dirty:
            disposition, reason = (
                "KEEP_DIRTY",
                "uncommitted work is present and exists nowhere else",
            )
        else:
            disposition, reason = (
                "PROPOSED_REQUIRES_HUMAN",
                "leaseless and clean; removal is still a human decision by default",
            )
        found.append(
            {
                "path": relative,
                "absolute": str(path),
                "leased": leased,
                "dirty": dirty,
                "disposition": disposition,
                "reason": reason,
            }
        )
    return found


def plan(
    entries: list[dict[str, Any]], destructive_admitted: list[str] | None = None
) -> dict[str, Any]:
    """Turn an inventory into actions. Nothing becomes removable without a name.

    `destructive_admitted` is the list of paths a human explicitly admitted.
    Passing None -- the default -- yields a plan that removes nothing at all,
    which is what a scheduled GC run should look like.
    """
    admitted = set(destructive_admitted or [])
    actions = []
    for entry in entries:
        disposition = entry["disposition"]
        if disposition not in DISPOSITIONS:
            raise ContractError(f"unknown disposition {disposition!r}")
        if disposition == "PROPOSED_REQUIRES_HUMAN" and entry["path"] in admitted:
            actions.append({**entry, "disposition": AUTO_DISPOSITION})
            continue
        if disposition in {"KEEP_ACTIVE_LEASE", "KEEP_DIRTY", "KEEP_UNREADABLE"} and (
            entry["path"] in admitted
        ):
            # A human may admit removing a leaseless clean workspace. They may
            # not admit away the reason a workspace is being kept -- that is a
            # different decision, and it needs the lease released or the work
            # committed first.
            raise ContractError(
                f"{entry['path']!r} is {disposition} and cannot be admitted for "
                f"removal: {entry['reason']}. Release the lease or commit the work "
                "first; admitting past this makes the check decorative"
            )
        actions.append(dict(entry))

    removable = [a for a in actions if a["disposition"] == AUTO_DISPOSITION]
    return {
        "actions": sorted(actions, key=lambda a: a["path"]),
        "removable_count": len(removable),
        "kept_count": len(actions) - len(removable),
        "default_is_destructive": False,
    }


def execute(plan_value: dict[str, Any], apply: bool = False) -> dict[str, Any]:
    """Remove only what the plan marked removable, re-checking each one first."""
    removed, skipped = [], []
    for action in plan_value["actions"]:
        if action["disposition"] != AUTO_DISPOSITION:
            skipped.append({"path": action["path"], "reason": action["reason"]})
            continue
        path = Path(action["absolute"])
        # Re-checked here, immediately before acting. An inventory taken five
        # minutes ago describes a tree that may have gained a Worker since.
        current = _dirty(path)
        if current is None:
            skipped.append(
                {"path": action["path"], "reason": "became unreadable since inventory"}
            )
            continue
        if current:
            skipped.append(
                {"path": action["path"], "reason": "became dirty since inventory"}
            )
            continue
        if not apply:
            skipped.append({"path": action["path"], "reason": "dry run"})
            continue
        shutil.rmtree(path, ignore_errors=True)
        removed.append({"path": action["path"], "gone": not path.exists()})

    for entry in removed:
        if not entry["gone"]:
            raise ContractError(
                f"{entry['path']!r} was reported removed but is still on disk; a "
                "cleanup that prints success without looking is the failure this "
                "whole file is arranged around"
            )
    return {
        "removed": sorted(removed, key=lambda e: e["path"]),
        "skipped": sorted(skipped, key=lambda e: e["path"]),
        "applied": apply,
    }


def descendants_alive(pgid: int) -> bool:
    """Is anything still running in this process group?

    A timeout that kills the Worker and leaves its children is the failure that
    shows up half an hour later as a machine with no free CPU, and the fleet's
    own records will say the task ended.
    """
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # The group exists and belongs to someone else. Reporting False here
        # would be reporting "nothing is running" on the basis of not being
        # allowed to ask.
        return True
    return True
