#!/usr/bin/env python3
"""The candidate fold-back bundle, and the receipt that records what was admitted.

The bundle is a proposal. Nothing in this module writes a card, an ADR or a
Notes file; `admit` takes an explicit human decision per patch and emits
revisions from it. A patch nobody admitted produces a REJECTED revision, not
silence -- silence is what makes the same proposal come back next month with
nothing recording that it was already considered.

The receipt is content-addressed over the bundle and the decisions, so two
receipts claiming the same fold-back can be compared as digests rather than read.
"""

from __future__ import annotations

from typing import Any

from fb_anchor import require_fresh
from fb_common import (
    ContractError,
    digest,
    exact_object,
    iso_timestamp,
    non_empty_str,
    require,
)
from fb_history import current_revision, revision_id, validate_history
from fb_patch import locate_affected, validate_card, validate_patch

BUNDLE_SCHEMA = "loopx/foldback-candidate-bundle/v1"
RECEIPT_SCHEMA = "loopx/foldback-receipt/v1"

DECISION_KEYS = {"patch_id", "decision", "actor", "at", "note"}
DECISIONS = {"ADMIT", "REJECT"}


def build_bundle(
    delta: dict[str, Any],
    cards: list[dict[str, Any]],
    patches: list[dict[str, Any]],
    similarity: dict[str, float],
    history: dict[str, Any],
    anchor_states: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compile a candidate bundle. Raises rather than repairing."""
    validate_history(history)
    for card in cards:
        validate_card(card, f"card {card.get('canonical_key')!r}")
    cards_by_key = {card["canonical_key"]: card for card in cards}
    if len(cards_by_key) != len(cards):
        raise ContractError("two cards share a canonical key")

    # Anchors are re-checked against the after tree before anything is proposed.
    # A patch built on a moved anchor cites lines that now say something else.
    if anchor_states is not None:
        require_fresh(anchor_states)

    located = locate_affected(cards, delta, similarity)
    located_by_key = {row["canonical_key"]: row for row in located}

    seen: set[str] = set()
    validated = []
    for index, patch in enumerate(patches):
        checked = validate_patch(
            patch, f"patches[{index}]", cards_by_key, located_by_key, delta
        )
        if checked["patch_id"] in seen:
            raise ContractError(f"duplicate patch_id {checked['patch_id']!r}")
        seen.add(checked["patch_id"])
        # The card must be at the revision the patch was computed against.
        card = cards_by_key[checked["canonical_key"]]
        if card["revision"] != current_revision(history, card["canonical_key"]):
            raise ContractError(
                f"patches[{index}] targets {card['canonical_key']!r} at revision "
                f"{card['revision']}, but the history is at "
                f"{current_revision(history, card['canonical_key'])}; the patch was "
                "computed from a read that is no longer current"
            )
        validated.append(checked)

    review_only = [row for row in located if not row["patchable"]]
    bundle = {
        "schema_version": BUNDLE_SCHEMA,
        "before": delta["before"],
        "after": delta["after"],
        "located": located,
        "patches": sorted(validated, key=lambda p: p["patch_id"]),
        # Named, not dropped. A card surfaced by similarity and then omitted
        # entirely would look like a card nothing pointed at.
        "candidates_for_review": sorted(row["canonical_key"] for row in review_only),
        "state": "CANDIDATE",
        "admit_required": True,
        "authority": "PROPOSES",
    }
    bundle["bundle_digest"] = digest(
        {k: v for k, v in bundle.items() if k != "bundle_digest"}
    )
    return bundle


def validate_bundle(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("bundle must be an object")
    if value.get("schema_version") != BUNDLE_SCHEMA:
        raise ContractError("bundle schema version drifted")
    if value.get("state") != "CANDIDATE" or value.get("admit_required") is not True:
        raise ContractError(
            "a fold-back bundle is a candidate awaiting Human Admit; any other state "
            "would be a knowledge write this module has no authority to make"
        )
    recomputed = digest({k: v for k, v in value.items() if k != "bundle_digest"})
    if value.get("bundle_digest") != recomputed:
        raise ContractError("bundle digest does not match its content")
    return value


def validate_decision(value: Any, label: str) -> dict[str, Any]:
    decision = exact_object(value, DECISION_KEYS, label)
    non_empty_str(decision["patch_id"], f"{label}.patch_id")
    non_empty_str(decision["actor"], f"{label}.actor")
    iso_timestamp(decision["at"], f"{label}.at")
    if decision["decision"] not in DECISIONS:
        raise ContractError(f"{label}.decision must be ADMIT or REJECT")
    if decision["decision"] == "REJECT" and not decision["note"]:
        raise ContractError(
            f"{label} rejects a patch with no note; a rejection nobody explained "
            "will be re-proposed with nothing to say why it was declined before"
        )
    return decision


def admit(
    bundle: dict[str, Any],
    history: dict[str, Any],
    decisions: list[dict[str, Any]],
    cards: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Apply human decisions. Returns (revisions to append, receipt).

    Every patch needs a decision. A patch left undecided is neither admitted nor
    rejected, and emitting a receipt over a partial decision set would record a
    fold-back that a human only partly saw.
    """
    validate_bundle(bundle)
    validate_history(history)
    by_key = {card["canonical_key"]: card for card in cards}

    decided = {}
    for index, value in enumerate(decisions):
        decision = validate_decision(value, f"decisions[{index}]")
        if decision["patch_id"] in decided:
            raise ContractError(f"two decisions for patch {decision['patch_id']!r}")
        decided[decision["patch_id"]] = decision

    patch_ids = {patch["patch_id"] for patch in bundle["patches"]}
    undecided = sorted(patch_ids - set(decided))
    if undecided:
        raise ContractError(
            f"patches {undecided} have no decision; a receipt over a partial decision "
            "set records a fold-back a human only partly saw"
        )
    unknown = sorted(set(decided) - patch_ids)
    if unknown:
        raise ContractError(f"decisions name patches not in this bundle: {unknown}")

    # What makes a rerun a rerun: the bundle plus the decisions taken on it.
    # Two identical bundles decided differently are not the same fold-back.
    origin = digest(
        {
            "bundle": bundle["bundle_digest"],
            "decisions": sorted(
                (d["patch_id"], d["decision"]) for d in decided.values()
            ),
        }
    )

    entries = []
    for patch in bundle["patches"]:
        decision = decided[patch["patch_id"]]
        card = by_key[patch["canonical_key"]]
        admitted = decision["decision"] == "ADMIT"
        if patch["kind"] == "NOOP" and admitted:
            # Nothing changed, so nothing is appended. Recording a revision here
            # would make a rerun look like a change.
            continue
        entry = {
            "canonical_key": patch["canonical_key"],
            "revision": current_revision(history, patch["canonical_key"]) + 1,
            "patch_kind": patch["kind"],
            "claim": patch["claim_after"] if admitted else card["claim"],
            "state": "ADMITTED" if admitted else "REJECTED",
            "supersedes_revision_id": _superseded_id(history, patch, admitted),
            "admitted_by": decision["actor"],
            "admitted_at": decision["at"],
            "evidence_class": patch["evidence_class"],
            "supporting_anchor_ids": patch["supporting_anchor_ids"],
            "origin_digest": origin,
        }
        entry["revision_id"] = revision_id(entry)
        entries.append(entry)

    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "before": bundle["before"],
        "after": bundle["after"],
        "bundle_digest": bundle["bundle_digest"],
        "decisions": sorted(decided.values(), key=lambda d: d["patch_id"]),
        "revisions": [entry["revision_id"] for entry in entries],
        "admitted": sorted(
            e["canonical_key"] for e in entries if e["state"] == "ADMITTED"
        ),
        "rejected": sorted(
            e["canonical_key"] for e in entries if e["state"] == "REJECTED"
        ),
        "candidates_for_review": bundle["candidates_for_review"],
        "authority": "HUMAN_ADMITTED",
    }
    receipt["receipt_digest"] = digest(
        {k: v for k, v in receipt.items() if k != "receipt_digest"}
    )
    require(True, "")
    return {"entries": entries}, receipt


def _superseded_id(
    history: dict[str, Any], patch: dict[str, Any], admitted: bool
) -> str | None:
    if not admitted or patch["kind"] != "SUPERSEDE":
        return None
    previous = [
        r
        for r in history["revisions"]
        if r["canonical_key"] == patch["canonical_key"] and r["state"] == "ADMITTED"
    ]
    if not previous:
        raise ContractError(
            f"patch {patch['patch_id']!r} supersedes a card with no admitted revision "
            "to supersede"
        )
    return previous[-1]["revision_id"]


def validate_receipt(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("receipt must be an object")
    if value.get("schema_version") != RECEIPT_SCHEMA:
        raise ContractError("receipt schema version drifted")
    if value.get("authority") != "HUMAN_ADMITTED":
        raise ContractError(
            "a fold-back receipt records a human decision; any other authority would "
            "mean knowledge was written without one"
        )
    recomputed = digest({k: v for k, v in value.items() if k != "receipt_digest"})
    if value.get("receipt_digest") != recomputed:
        raise ContractError(
            "receipt digest does not match its content; a receipt that is not "
            "content-addressed cannot be compared to another claiming the same "
            "fold-back"
        )
    return value
