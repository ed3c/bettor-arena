#!/usr/bin/env python3
"""Memory as a ledger event. Append-only, reducer-owned, replay-stable.

This runtime sits on the contracts already in this module. `validate_proposal`,
`validate_decision`, `stable_id` and the private-reasoning scanner are imported
rather than rewritten -- a second copy of a secret scanner is a second copy that
will drift, and the one that drifts is the one that stops catching things.

What is new here is durability. A proposal that a human admitted becomes a typed
ledger event written by the reducer, and everything after that is an append.
Three properties hold it together:

**Identity is derived.** An event id is a digest of the memory's canonical key,
the revision it carries and the decision that produced it. Replaying an admitted
decision produces the same id, so the append is a no-op rather than a duplicate.

**Revisions advance and never repeat.** Superseding appends a new revision that
names the event it replaces; the old claim stays readable at its own revision.
The obvious check -- counting events whose state is ACTIVE -- asks the wrong
question of an append-only log, because the admission that made revision 1
active still says ACTIVE forever. What can actually go wrong is two events at
one revision, and a reader replaying the log then gets whichever it saw last.

**The writer is the reducer.** Every event names it. A memory event written by
anything else is a durable fact nobody admitted.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from memory import (  # noqa: E402
    FORBIDDEN_TEXT,
    ContractError,
    canonical_bytes,
    digest,
    stable_id,
    timestamp,
    validate_decision,
    validate_proposal,
    validate_subject,
)

EVENT_SCHEMA = "loopx/memory-event/v1"

EVENT_KINDS = (
    "MEMORY_ADMITTED",
    "MEMORY_REVALIDATED",
    "MEMORY_SUPERSEDED",
    "MEMORY_EXPIRED",
    "MEMORY_CONTESTED",
    "MEMORY_REJECTED",
    "MEMORY_TOMBSTONED",
)

# The states a memory can be in after an event. ACTIVE is the only one a reader
# may act on, and the only one that can be superseded.
MEMORY_STATES = (
    "ACTIVE",
    "SUPERSEDED",
    "EXPIRED",
    "CONTESTED",
    "TOMBSTONED",
    "REJECTED",
)

TERMINAL_STATES = {"TOMBSTONED", "REJECTED"}

EVENT_KEYS = {
    "schema_version",
    "event_id",
    "kind",
    "memory_id",
    "canonical_key",
    "revision",
    "state",
    "subject",
    "content",
    "evidence_refs",
    "falsifier",
    "validity_scope",
    "expires_at",
    "supersedes_event_id",
    "admitted_by",
    "admitted_at",
    "origin_digest",
    "writer",
}

WRITER = "LOOPX_LEDGER_REDUCER"


def event_id(payload: dict[str, Any]) -> str:
    """Derived from what produced the event, not from where it landed.

    `revision` is included -- unlike the fold-back module, where it was a
    position -- because here a revision *is* content: revision 2 of a memory is
    a different claim from revision 1, and two of them must not collide.
    `origin_digest` names the decision, so replaying one admission is a no-op
    while two separate admissions reaching the same wording stay distinct.
    """
    return (
        "mev-"
        + digest(
            {
                "origin_digest": payload["origin_digest"],
                "canonical_key": payload["canonical_key"],
                "revision": payload["revision"],
                "kind": payload["kind"],
                "content": payload["content"],
                "state": payload["state"],
            }
        )[7:23]
    )


def scan_for_leakage(value: Any, label: str) -> None:
    """Refuse anything that looks like private reasoning or a secret.

    Run over the serialised object rather than over named fields: the field a
    secret arrives in is never the field anyone wrote a rule for.
    """
    blob = canonical_bytes(value).decode("utf-8")
    match = FORBIDDEN_TEXT.search(blob)
    if match:
        raise ContractError(
            f"{label} contains {match.group(0)[:32]!r}, which reads as private "
            "reasoning or a secret. Durable memory is read back by every later "
            "session, so anything persisted here is persisted everywhere"
        )


def build_event(
    proposal: dict[str, Any],
    decision: dict[str, Any],
    kind: str,
    state: str,
    revision: int,
    supersedes: str | None = None,
) -> dict[str, Any]:
    """Turn an admitted decision into a ledger event. Never writes anything."""
    validate_proposal(proposal)
    validate_decision(decision, proposal)
    if kind not in EVENT_KINDS:
        raise ContractError(f"unknown event kind {kind!r}")
    if state not in MEMORY_STATES:
        raise ContractError(f"unknown memory state {state!r}")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        raise ContractError("revision must be a positive integer")

    if kind == "MEMORY_ADMITTED" and decision["decision"] != "ADMIT":
        raise ContractError(
            f"a {decision['decision']} decision cannot produce MEMORY_ADMITTED; a "
            "rejected proposal that reaches durable state was admitted by the code "
            "rather than by a person"
        )
    if kind == "MEMORY_SUPERSEDED" and not supersedes:
        raise ContractError(
            "a supersession must name the event it replaces, or the claim it "
            "replaces becomes unreachable"
        )

    scan_for_leakage(proposal, "proposal")

    # Field names come from the contracts already in this module, read rather
    # than assumed: the proposal carries `statement`, `epistemic.falsifier` and
    # `scope`, and the decision carries `authority` and `created_at`. An earlier
    # draft of this file invented `content`, `falsifier` and `decided_by`, and
    # every one of them would have failed only at runtime.
    # The admission authority is not re-checked here. `validate_decision`, called
    # above, already refuses anything but a HUMAN signer -- a second check would
    # be a branch no input can reach, and an unreachable guard is worse than none:
    # it reads as protection while testing nothing.
    canonical_key = proposal["canonical_key"]
    authority = decision["authority"]
    payload = {
        "schema_version": EVENT_SCHEMA,
        "kind": kind,
        "memory_id": stable_id(canonical_key),
        "canonical_key": canonical_key,
        "revision": revision,
        "state": state,
        "subject": proposal["subject"],
        "content": proposal["statement"],
        # Evidence refs are objects, sorted by their own id so two events
        # carrying the same evidence in a different order still digest alike.
        "evidence_refs": sorted(
            proposal["evidence_refs"], key=lambda ref: ref["evidence_id"]
        ),
        "falsifier": proposal["epistemic"]["falsifier"],
        "validity_scope": proposal["scope"],
        "expires_at": proposal["retention"]["expires_at"],
        "supersedes_event_id": supersedes,
        "admitted_by": authority["signer_id"],
        "admitted_at": decision["created_at"],
        # What makes a replay a replay: the decision this event came from.
        "origin_digest": digest(decision),
        "writer": WRITER,
    }
    payload["event_id"] = event_id(payload)
    return payload


def validate_event(value: Any, label: str = "event") -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != EVENT_KEYS:
        missing = sorted(EVENT_KEYS - set(value or {}))
        extra = sorted(set(value or {}) - EVENT_KEYS)
        raise ContractError(f"{label} fields drifted; missing={missing}, extra={extra}")
    if value["schema_version"] != EVENT_SCHEMA:
        raise ContractError(f"{label} schema version drifted")
    if value["kind"] not in EVENT_KINDS:
        raise ContractError(f"{label}.kind is unknown")
    if value["state"] not in MEMORY_STATES:
        raise ContractError(f"{label}.state is unknown")
    if value["writer"] != WRITER:
        raise ContractError(
            f"{label} was written by {value['writer']!r}; a memory event written by "
            "anything but the reducer is a durable fact nobody admitted"
        )
    if value["memory_id"] != stable_id(value["canonical_key"]):
        raise ContractError(
            f"{label}.memory_id does not derive from its canonical key; an allocated "
            "id changes on replay and every reference to it silently retargets"
        )
    if value["event_id"] != event_id(value):
        raise ContractError(
            f"{label}.event_id does not derive from its content; replaying an "
            "admission would append a second copy of one decision"
        )
    validate_subject(value["subject"])
    timestamp(value["admitted_at"], f"{label}.admitted_at")
    timestamp(value["expires_at"], f"{label}.expires_at")
    scan_for_leakage(value, label)
    return value


def append(
    log: list[dict[str, Any]], events: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[str]]:
    """Append events, skipping ones already present. Returns (log, appended ids)."""
    for index, event in enumerate(log):
        validate_event(event, f"log[{index}]")
    existing = {event["event_id"] for event in log}
    out = list(log)
    appended = []
    for event in events:
        validate_event(event, f"appended {event.get('event_id')!r}")
        if event["event_id"] in existing:
            continue
        out.append(event)
        existing.add(event["event_id"])
        appended.append(event["event_id"])
    check_single_active(out)
    return out, appended


def check_single_active(log: list[dict[str, Any]]) -> None:
    """Revisions advance, and no revision of a memory appears twice.

    The obvious check -- "count the events whose state is ACTIVE" -- asks the
    wrong question of an append-only log. An event is never edited, so the
    admission that made revision 1 active still says ACTIVE forever; what makes
    it no longer current is a *later* event. Counting ACTIVE events therefore
    reports every superseded memory as doubly active.

    What can actually go wrong is the revision sequence: the same revision
    appended twice, or a revision that goes backwards. Either means two events
    claim to be the same point in a memory's history, and a reader replaying the
    log gets whichever it saw last.
    """
    seen: dict[str, set[int]] = {}
    highest: dict[str, int] = {}
    for event in log:
        key = event["canonical_key"]
        revision = event["revision"]
        if revision in seen.get(key, set()):
            raise ContractError(
                f"memory {key!r} has two events at revision {revision}; two events "
                "claiming the same point in a memory's history means a reader "
                "replaying the log gets whichever it saw last"
            )
        seen.setdefault(key, set()).add(revision)
        if revision < highest.get(key, 0):
            raise ContractError(
                f"memory {key!r} goes from revision {highest[key]} back to {revision}; "
                "history that moves backwards has been rewritten rather than appended to"
            )
        highest[key] = revision


def current(log: list[dict[str, Any]], canonical_key: str) -> dict[str, Any] | None:
    """The ACTIVE revision of a memory, or None. Tombstoned memories are gone."""
    latest = None
    for event in log:
        if event["canonical_key"] != canonical_key:
            continue
        if event["state"] == "ACTIVE":
            latest = event
        elif event["state"] in {"SUPERSEDED", "EXPIRED", "TOMBSTONED", "REJECTED"}:
            latest = None
    return latest
