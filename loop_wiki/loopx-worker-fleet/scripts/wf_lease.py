#!/usr/bin/env python3
"""Branch, worktree and path leases. One Worker, one branch, one tree, one path set.

A lease here covers four things at once because they fail together: two Workers
on one branch produce commits nobody ordered, two on one worktree produce a tree
neither wrote alone, and two on overlapping paths produce the same thing more
slowly. Splitting them into separate ledgers would let a Worker hold three of the
four and look admitted.

The `owner_checkout` field is the one that looks like configuration and is
actually a safety property: a worktree path inside the owner's live checkout
means a Worker editing the developer's working tree while they are in it.
"""

from __future__ import annotations

from typing import Any

from wf_common import (
    ContractError,
    exact_object,
    glob_root,
    iso_timestamp,
    non_empty_str,
    normalise_path,
    parse_time,
    paths_overlap,
)

LEASE_KEYS = {
    "lease_id",
    "worker_id",
    "task_id",
    "branch",
    "worktree_path",
    "path_globs",
    "granted_at",
    "expires_at",
    "heartbeat_interval_s",
    "state",
}

# REQUESTED is separate from GRANTED because leasing happens at dispatch, not at
# queue time. Without it, a lease defined alongside its queue item already counts
# as held, and every task collides with its own reservation.
LEASE_STATES = ("REQUESTED", "GRANTED", "ACTIVE", "RELEASED", "EXPIRED", "REVOKED")

# The states in which a lease occupies its branch, worktree and paths.
HOLDING_STATES = {"GRANTED", "ACTIVE"}


def validate_lease(value: Any, label: str) -> dict[str, Any]:
    lease = exact_object(value, LEASE_KEYS, label)
    for field in ("lease_id", "worker_id", "task_id", "branch"):
        non_empty_str(lease[field], f"{label}.{field}")
    if lease["state"] not in LEASE_STATES:
        raise ContractError(f"{label}.state must be one of {list(LEASE_STATES)}")

    normalise_path(lease["worktree_path"], f"{label}.worktree_path")

    globs = lease["path_globs"]
    if not isinstance(globs, list) or not globs or globs != sorted(globs):
        raise ContractError(f"{label}.path_globs must be a sorted non-empty list")
    roots = [glob_root(pattern) for pattern in globs]
    for index, root in enumerate(roots):
        normalise_path(root, f"{label}.path_globs[{index}]")
    # A lease that overlaps itself is a lease whose author did not look. It is
    # harmless on its own and it makes every later overlap report ambiguous.
    for i, left in enumerate(roots):
        for right in roots[i + 1 :]:
            if paths_overlap(left, right):
                raise ContractError(
                    f"{label} leases {left!r} and {right!r}, which nest; a lease that "
                    "overlaps itself makes every later collision report ambiguous"
                )

    granted = parse_time(lease["granted_at"], f"{label}.granted_at")
    expires = parse_time(lease["expires_at"], f"{label}.expires_at")
    if expires <= granted:
        raise ContractError(
            f"{label}.expires_at is not after granted_at; a lease that expires when "
            "it is granted cannot be held"
        )
    interval = lease["heartbeat_interval_s"]
    if not isinstance(interval, int) or isinstance(interval, bool) or interval < 1:
        raise ContractError(f"{label}.heartbeat_interval_s must be a positive integer")
    if interval >= (expires - granted).total_seconds():
        raise ContractError(
            f"{label}.heartbeat_interval_s is not shorter than the lease; a Worker "
            "that dies is only detected by a missed heartbeat, and one that cannot "
            "miss a heartbeat before expiry is detected by nothing"
        )
    return lease


def conflicts(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    """Every reason these two leases cannot both be held.

    All of them, not the first: reporting one conflict at a time turns fixing a
    collision into a loop of re-runs, and the second reason is usually the one
    that explains the first.
    """
    found = []
    if left["branch"] == right["branch"]:
        found.append(f"same branch {left['branch']!r}")
    if left["worktree_path"] == right["worktree_path"]:
        found.append(f"same worktree {left['worktree_path']!r}")
    for a in (glob_root(p) for p in left["path_globs"]):
        for b in (glob_root(p) for p in right["path_globs"]):
            if paths_overlap(a, b):
                found.append(f"overlapping paths {a!r} and {b!r}")
    return sorted(set(found))


def admit(
    lease: dict[str, Any],
    held: list[dict[str, Any]],
    now: str,
    owner_checkout: str,
) -> dict[str, Any]:
    """May this lease be granted right now, against these held leases?"""
    validate_lease(lease, f"lease {lease.get('lease_id')!r}")
    moment = parse_time(iso_timestamp(now, "now"), "now")

    if moment >= parse_time(lease["expires_at"], "lease.expires_at"):
        raise ContractError(
            f"lease {lease['lease_id']} expired at {lease['expires_at']}; a Worker "
            "running under an expired lease holds a workspace the fleet believes is "
            "free, and the next grant will hand it to someone else"
        )

    # The worktree must not be inside the owner's live checkout.
    worktree = str(normalise_path(lease["worktree_path"], "lease.worktree_path"))
    checkout = str(normalise_path(owner_checkout, "owner_checkout"))
    if paths_overlap(worktree, checkout):
        raise ContractError(
            f"lease {lease['lease_id']} places its worktree at {worktree!r}, inside "
            f"the owner live checkout {checkout!r}; a Worker there edits the "
            "developer's working tree while they are in it"
        )

    for other in held:
        if other["lease_id"] == lease["lease_id"]:
            raise ContractError(
                f"lease {lease['lease_id']} is already held; two Workers on one lease "
                "both believe they own the workspace and the second write wins"
            )
        if other["state"] not in HOLDING_STATES:
            continue
        reasons = conflicts(lease, other)
        if reasons:
            raise ContractError(
                f"lease {lease['lease_id']} collides with held lease "
                f"{other['lease_id']}: {'; '.join(reasons)}"
            )
    return {
        "admitted": True,
        "lease_id": lease["lease_id"],
        "worker_id": lease["worker_id"],
        "task_id": lease["task_id"],
        "at": now,
    }


def expired(leases: list[dict[str, Any]], now: str) -> list[dict[str, Any]]:
    """Leases past their expiry, with the reason recorded rather than implied."""
    moment = parse_time(iso_timestamp(now, "now"), "now")
    out = []
    for lease in leases:
        if lease["state"] in {"RELEASED", "REVOKED"}:
            continue
        if moment >= parse_time(lease["expires_at"], "lease.expires_at"):
            out.append(
                {
                    "lease_id": lease["lease_id"],
                    "worker_id": lease["worker_id"],
                    "worktree_path": lease["worktree_path"],
                    "expired_at": lease["expires_at"],
                    "reason": "EXPIRED",
                }
            )
    return sorted(out, key=lambda entry: entry["lease_id"])


def stale_heartbeat(
    leases: list[dict[str, Any]], heartbeats: dict[str, str], now: str
) -> list[dict[str, Any]]:
    """Leases whose Worker has stopped reporting.

    Separate from `expired`, and reported separately: a lease that is still
    within its window but whose Worker went silent is a crashed Worker, while an
    expired one may simply have taken too long. Recovering them the same way
    would kill slow work.
    """
    moment = parse_time(iso_timestamp(now, "now"), "now")
    out = []
    for lease in leases:
        if lease["state"] not in HOLDING_STATES:
            continue
        last = heartbeats.get(lease["lease_id"])
        if last is None:
            out.append(
                {
                    "lease_id": lease["lease_id"],
                    "worker_id": lease["worker_id"],
                    "reason": "NO_HEARTBEAT_RECORDED",
                    "silent_for_s": None,
                }
            )
            continue
        silent = (moment - parse_time(last, "heartbeat")).total_seconds()
        # Two missed intervals, not one: a single missed beat is as likely to be
        # a slow tick as a dead Worker, and killing on it makes the fleet flap.
        if silent > lease["heartbeat_interval_s"] * 2:
            out.append(
                {
                    "lease_id": lease["lease_id"],
                    "worker_id": lease["worker_id"],
                    "reason": "HEARTBEAT_STALE",
                    "silent_for_s": int(silent),
                }
            )
    return sorted(out, key=lambda entry: entry["lease_id"])
