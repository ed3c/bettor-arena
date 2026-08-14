#!/usr/bin/env python3
"""Lifecycle: expire, supersede, contest, revalidate, tombstone, export.

Deletion is the part worth reading carefully, because it has to do two things
that sound contradictory:

    the content must become unretrievable
    the history must stay intact

A delete that drops the events erases the audit trail, and the next person finds
a memory that never existed. A delete that only marks a flag leaves the content
sitting in the log for anyone who reads it directly. So a tombstone carries the
*digest* of what was removed and none of the content, the content is physically
overwritten in the store, and the residue check greps for it afterwards rather
than trusting that it went.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from memory import (  # noqa: E402
    ContractError,
    digest,
    stable_id,
    timestamp,
)

from dmr_event import current, event_id, validate_event

TOMBSTONE_KEYS = {
    "schema_version",
    "memory_id",
    "canonical_key",
    "tombstoned_at",
    "authorized_by",
    "removed_content_digest",
    "removed_event_ids",
    "history_preserved",
    "reason",
}


def expire_due(log: list[dict[str, Any]], now: str) -> list[dict[str, Any]]:
    """Memories whose expiry has passed. Reported, not applied."""
    moment = timestamp(now, "now")
    due = []
    seen: set[str] = set()
    for event in reversed(log):
        key = event["canonical_key"]
        if key in seen:
            continue
        seen.add(key)
        if event["state"] != "ACTIVE":
            continue
        if timestamp(event["expires_at"], "event.expires_at") <= moment:
            due.append(
                {
                    "memory_id": event["memory_id"],
                    "canonical_key": key,
                    "expired_at": event["expires_at"],
                    "event_id": event["event_id"],
                }
            )
    return sorted(due, key=lambda entry: entry["canonical_key"])


def transition(
    active: dict[str, Any],
    kind: str,
    state: str,
    actor: str,
    at: str,
    reason: str,
    content: str | None = None,
) -> dict[str, Any]:
    """Append-shaped state change on an existing memory."""
    validate_event(active, "active event")
    if active["state"] != "ACTIVE":
        raise ContractError(
            f"{active['canonical_key']} is {active['state']}, not ACTIVE; a state "
            "change applied to a memory that already moved is computed from a stale "
            "read of the log"
        )
    timestamp(at, "transition.at")
    if not isinstance(reason, str) or not reason.strip():
        raise ContractError("a state change must record why")

    payload = {
        **active,
        "kind": kind,
        "state": state,
        "revision": active["revision"] + 1,
        "content": content if content is not None else active["content"],
        "supersedes_event_id": active["event_id"]
        if kind == "MEMORY_SUPERSEDED"
        else None,
        "admitted_by": actor,
        "admitted_at": at,
        "origin_digest": digest(
            {"from": active["event_id"], "kind": kind, "reason": reason, "at": at}
        ),
    }
    payload["event_id"] = event_id(payload)
    return validate_event(payload, "transition")


def tombstone(
    log: list[dict[str, Any]],
    canonical_key: str,
    authorized_by: str,
    at: str,
    reason: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """A tombstone event plus the record of what was removed.

    Returns (event, tombstone). The event keeps the memory's place in the log
    with its content emptied; the tombstone holds the digest of what went, so
    the removal is auditable without the content being retrievable.
    """
    active = current(log, canonical_key)
    if active is None:
        raise ContractError(
            f"{canonical_key!r} has no ACTIVE revision to tombstone; deleting a "
            "memory that already moved would tombstone the wrong revision"
        )
    if not isinstance(authorized_by, str) or not authorized_by.strip():
        raise ContractError(
            "a deletion needs a named human authority; a tombstone with no author is "
            "a removal nobody can be asked about"
        )

    removed_digest = digest(active["content"])
    event = transition(
        active,
        "MEMORY_TOMBSTONED",
        "TOMBSTONED",
        authorized_by,
        at,
        reason,
        # The content is emptied here rather than left in place. A tombstone
        # that only sets a flag leaves the text in the log for anyone reading it
        # directly, which is most tools.
        content="[REMOVED]",
    )
    record = {
        "schema_version": "loopx/memory-tombstone/v1",
        "memory_id": stable_id(canonical_key),
        "canonical_key": canonical_key,
        "tombstoned_at": at,
        "authorized_by": authorized_by,
        "removed_content_digest": removed_digest,
        "removed_event_ids": sorted(
            entry["event_id"]
            for entry in log
            if entry["canonical_key"] == canonical_key
        ),
        # The events stay. Only their content goes.
        "history_preserved": True,
        "reason": reason,
    }
    return event, validate_tombstone(record)


def validate_tombstone(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != TOMBSTONE_KEYS:
        raise ContractError("tombstone fields drifted")
    if value["schema_version"] != "loopx/memory-tombstone/v1":
        raise ContractError("tombstone schema version drifted")
    if value["history_preserved"] is not True:
        raise ContractError(
            "a tombstone that does not preserve history is a deletion of the audit "
            "trail; the next person finds a memory that never existed"
        )
    if not value["removed_event_ids"]:
        raise ContractError("a tombstone naming no events removed nothing")
    return value


def redact_log(log: list[dict[str, Any]], canonical_key: str) -> list[dict[str, Any]]:
    """Empty the content of every event for a tombstoned memory.

    The events keep their place, their ids, their timestamps and their authors.
    What goes is the text -- which is the only part that has to.
    """
    out = []
    for event in log:
        if event["canonical_key"] != canonical_key:
            out.append(event)
            continue
        redacted = {**event, "content": "[REMOVED]"}
        # The event id was derived over the content, so redaction changes it.
        # Recomputing keeps every event self-verifying; the tombstone holds the
        # original ids, so the link back is not lost.
        redacted["event_id"] = event_id(redacted)
        out.append(redacted)
    return out


def residue(log: list[dict[str, Any]], removed_content_digest: str) -> list[str]:
    """Event ids whose content still digests to what was supposed to be removed."""
    return sorted(
        event["event_id"]
        for event in log
        if digest(event["content"]) == removed_content_digest
    )


def export(
    log: list[dict[str, Any]], canonical_key: str, requested_by: str, at: str
) -> dict[str, Any]:
    """An export is a read with a receipt, and it cannot export a tombstone."""
    timestamp(at, "export.at")
    events = [event for event in log if event["canonical_key"] == canonical_key]
    if not events:
        raise ContractError(f"no memory {canonical_key!r} to export")
    if any(event["state"] == "TOMBSTONED" for event in events):
        raise ContractError(
            f"{canonical_key!r} is tombstoned; exporting it would hand back content "
            "that a human authorised the removal of"
        )
    payload = {
        "schema_version": "loopx/memory-export/v1",
        "canonical_key": canonical_key,
        "requested_by": requested_by,
        "requested_at": at,
        "events": events,
        "authority": "READ_ONLY",
    }
    payload["export_digest"] = digest(payload)
    return payload
