#!/usr/bin/env python3
"""Workspace leases: one owner, an expiry, and a state revision it was granted at.

A lease is the fabric's whole isolation story at the coordination layer. Two
Workers holding the same lease is not a race to be tuned -- it is two processes
believing they own one directory, and whichever writes second wins silently.

Time is passed in rather than read. A lease check that calls the clock cannot be
tested for the boundary it exists to enforce, and every expiry control would
have to sleep.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fabric_common import (
    ContractError,
    exact_object,
    iso_timestamp,
    non_empty_str,
    require,
    validate_subject,
)

LEASE_KEYS = {
    "schema_version",
    "lease_id",
    "owner",
    "subject",
    "granted_at",
    "expires_at",
    "expected_state_revision",
    "workspace_root",
    "provider_id",
}


def _parse(value: str, label: str) -> datetime:
    iso_timestamp(value, label)
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def validate_lease(value: Any) -> dict[str, Any]:
    lease = exact_object(value, LEASE_KEYS, "lease")
    require(
        lease["schema_version"] == "loopx/runtime-lease/v1",
        "lease schema version drifted",
    )
    non_empty_str(lease["lease_id"], "lease.lease_id")
    non_empty_str(lease["owner"], "lease.owner")
    non_empty_str(lease["provider_id"], "lease.provider_id")
    non_empty_str(lease["workspace_root"], "lease.workspace_root")
    validate_subject(lease["subject"], "lease.subject")

    granted = _parse(lease["granted_at"], "lease.granted_at")
    expires = _parse(lease["expires_at"], "lease.expires_at")
    if expires <= granted:
        raise ContractError(
            "lease.expires_at must be after granted_at; a lease that expires when "
            "it is granted is not a lease"
        )

    revision = lease["expected_state_revision"]
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        raise ContractError(
            "lease.expected_state_revision must be a non-negative integer"
        )
    return lease


def admit_lease(
    lease: dict[str, Any],
    now: str,
    current_state_revision: int,
    held_lease_ids: set[str] | None = None,
) -> dict[str, Any]:
    """May this lease be used to execute, right now, against this state?"""
    validate_lease(lease)
    moment = _parse(now, "now")

    if moment >= _parse(lease["expires_at"], "lease.expires_at"):
        raise ContractError(
            f"lease {lease['lease_id']} expired at {lease['expires_at']}; executing "
            "under an expired lease means the workspace may already be reclaimed"
        )
    if moment < _parse(lease["granted_at"], "lease.granted_at"):
        raise ContractError(
            "lease is not yet valid; a lease granted in the future is a clock fault, "
            "not a grant"
        )
    if lease["expected_state_revision"] != current_state_revision:
        raise ContractError(
            f"lease was granted at revision {lease['expected_state_revision']} but the "
            f"task is at {current_state_revision}; the workload it authorises is not "
            "the workload now being asked for"
        )
    if held_lease_ids is not None and lease["lease_id"] in held_lease_ids:
        raise ContractError(
            f"lease {lease['lease_id']} is already held; two Workers on one lease "
            "both believe they own the workspace and the second write wins silently"
        )
    return {
        "admitted": True,
        "lease_id": lease["lease_id"],
        "owner": lease["owner"],
        "provider_id": lease["provider_id"],
        "at_revision": current_state_revision,
    }


def gc_candidates(leases: list[dict[str, Any]], now: str) -> list[dict[str, Any]]:
    """Leases whose workspaces may be reclaimed.

    Orphan recovery is the reason this exists: a Worker killed between
    LEASE_GRANTED and LEASE_RELEASED leaves a directory nobody will ever release,
    and without a sweep the disk fills with workspaces that look live.
    """
    moment = _parse(now, "now")
    out = []
    for lease in leases:
        validate_lease(lease)
        if moment >= _parse(lease["expires_at"], "lease.expires_at"):
            out.append(
                {
                    "lease_id": lease["lease_id"],
                    "workspace_root": lease["workspace_root"],
                    "expired_at": lease["expires_at"],
                    "reason": "EXPIRED",
                }
            )
    return sorted(out, key=lambda item: item["lease_id"])
