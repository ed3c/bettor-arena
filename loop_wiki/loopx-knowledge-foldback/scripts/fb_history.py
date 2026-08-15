#!/usr/bin/env python3
"""Revision history. Append-only, content-addressed, and it keeps the rejections.

Three properties, and each answers a failure that would otherwise be invisible
because the thing it destroys is the thing that would have shown it:

**Append-only.** A revision is never edited or removed. `SUPERSEDE` appends a new
revision and marks the old one superseded; the old claim stays readable. Rollback
appends a reversal rather than deleting -- a rollback that erased the revision
would also erase the evidence that justified it, and the next person would find a
card that had simply never changed.

**Rejections are recorded.** A patch a human declined becomes a `REJECTED`
revision. Dropping it loses the fact that the question was asked and answered,
and the same patch gets proposed again next month with nothing to say it was
already considered.

**Idempotent.** A revision id is the digest of its content, so re-running the
same fold-back against the same history appends nothing and reports NOOP. Without
this, a rerun after a transient failure quietly doubles every revision, and the
history then shows a claim that changed twice when it changed once.
"""

from __future__ import annotations

from typing import Any

from fb_common import (
    ContractError,
    digest,
    exact_object,
    iso_timestamp,
    non_empty_str,
    require,
)

REVISION_KEYS = {
    "revision_id",
    "canonical_key",
    "revision",
    "patch_kind",
    "claim",
    "state",
    "supersedes_revision_id",
    "admitted_by",
    "admitted_at",
    "evidence_class",
    "supporting_anchor_ids",
    "origin_digest",
}

REVISION_STATES = ("ADMITTED", "REJECTED", "SUPERSEDED", "ROLLED_BACK")

HISTORY_KEYS = {"schema_version", "revisions"}


def revision_id(payload: dict[str, Any]) -> str:
    """Content-addressed on what produced the revision, not on where it landed.

    `revision` and `supersedes_revision_id` are deliberately excluded. Both are
    positions in a history that has already moved by the time a rerun happens, so
    including them would give the same fold-back a different id on every retry --
    and the retry would append a second copy of a change that happened once.

    `origin_digest` is what makes two revisions the same revision: the bundle and
    decision set they came from. Two genuinely separate fold-backs that reach the
    same wording still get distinct ids, because they came from distinct bundles.
    """
    return (
        "rev-"
        + digest(
            {
                "origin_digest": payload["origin_digest"],
                "canonical_key": payload["canonical_key"],
                "patch_kind": payload["patch_kind"],
                "claim": payload["claim"],
                "state": payload["state"],
                "supporting_anchor_ids": sorted(payload["supporting_anchor_ids"]),
            }
        )[7:23]
    )


def validate_revision(value: Any, label: str) -> dict[str, Any]:
    revision = exact_object(value, REVISION_KEYS, label)
    non_empty_str(revision["canonical_key"], f"{label}.canonical_key")
    non_empty_str(revision["claim"], f"{label}.claim")
    non_empty_str(revision["admitted_by"], f"{label}.admitted_by")
    non_empty_str(revision["origin_digest"], f"{label}.origin_digest")
    iso_timestamp(revision["admitted_at"], f"{label}.admitted_at")

    if revision["state"] not in REVISION_STATES:
        raise ContractError(f"{label}.state must be one of {list(REVISION_STATES)}")
    if not isinstance(revision["revision"], int) or revision["revision"] < 1:
        raise ContractError(f"{label}.revision must be a positive integer")

    expected = revision_id(revision)
    if revision["revision_id"] != expected:
        raise ContractError(
            f"{label}.revision_id is {revision['revision_id']!r} but its content "
            f"derives {expected!r}; an allocated id lets the same revision be "
            "appended twice and the history then shows two changes where there was one"
        )
    if revision["patch_kind"] == "SUPERSEDE" and not revision["supersedes_revision_id"]:
        raise ContractError(
            f"{label} is a SUPERSEDE naming nothing it supersedes; the claim it "
            "replaces would be unreachable"
        )
    return revision


def validate_history(value: Any) -> dict[str, Any]:
    history = exact_object(value, HISTORY_KEYS, "revision history")
    require(
        history["schema_version"] == "loopx/foldback-revision-history/v1",
        "revision history schema version drifted",
    )
    revisions = history["revisions"]
    if not isinstance(revisions, list):
        raise ContractError("revision history.revisions must be a list")

    seen: set[str] = set()
    highest: dict[str, int] = {}
    for index, value_ in enumerate(revisions):
        revision = validate_revision(value_, f"revisions[{index}]")
        if revision["revision_id"] in seen:
            raise ContractError(
                f"duplicate revision {revision['revision_id']!r}; a rerun appended a "
                "revision that was already there"
            )
        seen.add(revision["revision_id"])

        key = revision["canonical_key"]
        # Rejected revisions do not advance the card. They are recorded so the
        # question is not asked again from scratch, not so the claim moves.
        if revision["state"] != "REJECTED":
            if revision["revision"] <= highest.get(key, 0):
                raise ContractError(
                    f"revisions[{index}] for {key!r} is revision "
                    f"{revision['revision']}, not after {highest[key]}; history that "
                    "goes backwards has been rewritten rather than appended to"
                )
            highest[key] = revision["revision"]

        if revision["supersedes_revision_id"] and (
            revision["supersedes_revision_id"] not in seen
        ):
            raise ContractError(
                f"revisions[{index}] supersedes {revision['supersedes_revision_id']!r}, "
                "which is not earlier in this history"
            )
    return history


def current_revision(history: dict[str, Any], canonical_key: str) -> int:
    return max(
        (
            r["revision"]
            for r in history["revisions"]
            if r["canonical_key"] == canonical_key and r["state"] != "REJECTED"
        ),
        default=0,
    )


def append(
    history: dict[str, Any], entries: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[str]]:
    """Append revisions, skipping any already present. Returns (history, appended).

    The skip is what makes a rerun a NOOP, and it is decided on the content
    digest rather than on a timestamp or a sequence number -- both of which would
    differ on a rerun that changed nothing.
    """
    existing = {r["revision_id"] for r in history["revisions"]}
    revisions = list(history["revisions"])
    appended = []
    for entry in entries:
        validate_revision(entry, f"appended revision {entry.get('revision_id')!r}")
        if entry["revision_id"] in existing:
            continue
        revisions.append(entry)
        existing.add(entry["revision_id"])
        appended.append(entry["revision_id"])
    updated = {"schema_version": history["schema_version"], "revisions": revisions}
    validate_history(updated)
    return updated, appended


def rollback(
    history: dict[str, Any], revision_id_to_reverse: str, actor: str, at: str
) -> dict[str, Any]:
    """Append a reversal. Nothing is deleted, including the evidence."""
    target = next(
        (r for r in history["revisions"] if r["revision_id"] == revision_id_to_reverse),
        None,
    )
    if target is None:
        raise ContractError(
            f"cannot roll back {revision_id_to_reverse!r}: it is not in this history"
        )
    restored = next(
        (
            r
            for r in reversed(history["revisions"])
            if r["canonical_key"] == target["canonical_key"]
            and r["revision"] < target["revision"]
            and r["state"] != "REJECTED"
        ),
        None,
    )
    entry = {
        "canonical_key": target["canonical_key"],
        "revision": current_revision(history, target["canonical_key"]) + 1,
        "patch_kind": "SUPERSEDE",
        "claim": restored["claim"] if restored else target["claim"],
        "state": "ADMITTED",
        "supersedes_revision_id": target["revision_id"],
        "admitted_by": actor,
        "admitted_at": at,
        "evidence_class": target["evidence_class"],
        "supporting_anchor_ids": target["supporting_anchor_ids"],
        # A rollback's origin is the revision it reverses, so rolling the same
        # revision back twice is the same rollback and appends once.
        "origin_digest": f"rollback:{target['revision_id']}",
    }
    entry["revision_id"] = revision_id(entry)
    updated, _ = append(history, [entry])
    return updated
