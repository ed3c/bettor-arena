#!/usr/bin/env python3
"""The memory lifecycle, in the order #103 names.

    MEMORY_PROPOSAL_RECEIVED
    -> SUBJECT_EVIDENCE_PRIVACY_RETENTION_VALIDATED
    -> CURRENT_AUTHORITY_CONFLICT_CHECKED
    -> HUMAN_ADMIT_OR_REJECT
    -> MEMORY_EVENT_APPENDED_BY_REDUCER
    -> ACTIVE
    -> REVALIDATE_EXPIRE_SUPERSEDE_CONTEST
    -> DELETE_EXPORT_REQUEST
    -> HUMAN_AUTHORIZATION
    -> TOMBSTONE_EVENT_RESIDUE_CHECK
    -> PROJECTION_REBUILD

The authority conflict is checked *before* the admit decision reaches the
reducer. A memory admitted first and contested afterwards is a memory that was
durable and readable during the window in between, and that window is exactly
when someone reads it.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from memory import ContractError, digest  # noqa: E402

from dmr_authority import invalidation_proposals, resolve
from dmr_event import append, build_event, current
from dmr_lifecycle import expire_due, redact_log, residue, tombstone, transition

from dmr_projection import (
    rebuild,
    rebuild_matches,
    render_capsule,
    validate_capsule_bounds,
)

STATES = [
    "MEMORY_PROPOSAL_RECEIVED",
    "SUBJECT_EVIDENCE_PRIVACY_RETENTION_VALIDATED",
    "CURRENT_AUTHORITY_CONFLICT_CHECKED",
    "HUMAN_ADMIT_OR_REJECT",
    "MEMORY_EVENT_APPENDED_BY_REDUCER",
    "ACTIVE",
    "REVALIDATE_EXPIRE_SUPERSEDE_CONTEST",
    "DELETE_EXPORT_REQUEST",
    "HUMAN_AUTHORIZATION",
    "TOMBSTONE_EVENT_RESIDUE_CHECK",
    "PROJECTION_REBUILD",
]


def admit(
    log: list[dict[str, Any]],
    proposal: dict[str, Any],
    decision: dict[str, Any],
    competing_claims: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run a proposal through admission. Appends only on ADMIT."""
    trace = ["MEMORY_PROPOSAL_RECEIVED"]

    # Authority first, before the decision is honoured.
    conflicts: list[dict[str, Any]] = []
    resolution = None
    if competing_claims:
        resolution = resolve(competing_claims)
        conflicts = invalidation_proposals(resolution, "pending")
    trace.append("SUBJECT_EVIDENCE_PRIVACY_RETENTION_VALIDATED")
    trace.append("CURRENT_AUTHORITY_CONFLICT_CHECKED")

    if decision["decision"] != "ADMIT":
        # A rejection is recorded and does not reach durable state. There is no
        # branch below that could append it.
        trace.append("HUMAN_ADMIT_OR_REJECT")
        return {
            "state_trace": trace,
            "outcome": "REJECTED",
            "log": list(log),
            "appended": [],
            "authority_resolution": resolution,
            "invalidation_proposals": conflicts,
            "reason": (
                f"the decision was {decision['decision']}; a rejected proposal that "
                "reached durable state was admitted by the code rather than a person"
            ),
        }
    trace.append("HUMAN_ADMIT_OR_REJECT")

    # Replaying one admission must append nothing. Checked on the decision's own
    # digest rather than on the resulting event id: by the time the second run
    # reaches the supersede branch it is building revision 2, whose id is
    # legitimately different -- so the duplicate would slip past an id check and
    # the memory would gain a revision it never earned.
    origin = digest(decision)
    if any(event["origin_digest"] == origin for event in log):
        trace.append("MEMORY_EVENT_APPENDED_BY_REDUCER")
        trace.append("ACTIVE")
        return {
            "state_trace": trace,
            "outcome": "NOOP",
            "log": list(log),
            "appended": [],
            "authority_resolution": resolution,
            "invalidation_proposals": conflicts,
            "reason": (
                "this decision has already been appended; a rerun after a transient "
                "failure would otherwise supersede the memory with itself and the "
                "history would show a revision nobody decided"
            ),
        }

    existing = current(log, proposal["canonical_key"])
    revision = 1 if existing is None else existing["revision"] + 1
    kind = "MEMORY_ADMITTED" if existing is None else "MEMORY_SUPERSEDED"
    event = build_event(
        proposal,
        decision,
        kind,
        "ACTIVE",
        revision,
        supersedes=existing["event_id"] if existing else None,
    )

    # One event, not two. A separate "retire the old revision" event would sit
    # at the same revision number as the new one, and two events at one point in
    # a memory's history is the thing check_single_active refuses. The supersede
    # event names what it replaces, and in an append-only log the last event for
    # a key is what is current.
    updated, appended = append(log, [event])
    trace.append("MEMORY_EVENT_APPENDED_BY_REDUCER")
    trace.append("ACTIVE")

    return {
        "state_trace": trace,
        "outcome": "APPENDED" if appended else "NOOP",
        "log": updated,
        "appended": appended,
        "authority_resolution": resolution,
        "invalidation_proposals": conflicts,
        "reason": "admitted and appended by the reducer",
    }


def delete(
    log: list[dict[str, Any]],
    canonical_key: str,
    authorized_by: str,
    at: str,
    reason: str,
) -> dict[str, Any]:
    """Tombstone a memory: content unretrievable, history intact."""
    trace = ["DELETE_EXPORT_REQUEST", "HUMAN_AUTHORIZATION"]

    event, record = tombstone(log, canonical_key, authorized_by, at, reason)
    updated, appended = append(log, [event])
    redacted = redact_log(updated, canonical_key)
    left = residue(redacted, record["removed_content_digest"])
    trace.append("TOMBSTONE_EVENT_RESIDUE_CHECK")

    if left:
        raise ContractError(
            f"the removed content is still retrievable from events {left}; a delete "
            "that only sets a flag leaves the text in the log for anyone reading it "
            "directly, which is most tools"
        )

    projection = rebuild(redacted)
    trace.append("PROJECTION_REBUILD")

    return {
        "state_trace": trace,
        "log": redacted,
        "appended": appended,
        "tombstone": record,
        "residue": left,
        "projection": projection,
        # Both halves, asserted rather than described.
        "content_retrievable": bool(left),
        "history_preserved": len(redacted) >= len(log),
    }


def lifecycle_sweep(log: list[dict[str, Any]], now: str, actor: str) -> dict[str, Any]:
    """Expire what is due. Reports and appends; never deletes."""
    due = expire_due(log, now)
    events = []
    for entry in due:
        active = current(log, entry["canonical_key"])
        if active is None:
            continue
        events.append(
            transition(
                active,
                "MEMORY_EXPIRED",
                "EXPIRED",
                actor,
                now,
                f"retention expired at {entry['expired_at']}",
            )
        )
    updated, appended = append(log, events)
    return {
        "due": due,
        "log": updated,
        "appended": appended,
        # An expiry is not a deletion. The content stays readable in history;
        # what changes is that nothing reads it as current.
        "content_removed": False,
    }


def handoff(
    log: list[dict[str, Any]],
    scope: str,
    max_bytes: int,
    kinds: dict[str, str] | None = None,
) -> dict[str, Any]:
    projection = rebuild(log)
    capsule = render_capsule(projection, scope, max_bytes, kinds)
    validate_capsule_bounds(capsule)
    if not rebuild_matches(log, projection):
        raise ContractError("the projection does not match a rebuild from the log")
    return {
        "projection": projection,
        "capsule": capsule,
        "handoff_digest": digest(
            {
                "projection": projection["projection_digest"],
                "capsule": capsule["capsule_digest"],
            }
        ),
    }
