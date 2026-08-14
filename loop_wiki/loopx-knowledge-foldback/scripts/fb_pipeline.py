#!/usr/bin/env python3
"""The reverse pass. Verified change in, admitted revision history out.

The state machine #71 names, in order:

    BEFORE/AFTER SUBJECTS PINNED
    -> DIFF + SYMBOL/EDGE DELTA
    -> TEST/RUNTIME EVIDENCE JOIN
    -> AFFECTED KNOWLEDGE LOCATED
    -> PATCH CANDIDATES COMPILED
    -> CONTRADICTIONS_UNKNOWNS_PRESERVED
    -> IDENTITY_DEPENDENCY_LOCATOR_GATES
    -> CANDIDATE_FOLD_BACK_BUNDLE
    -> HUMAN_ADMIT
    -> REVISION_HISTORY_APPENDED

`fold_back` stops at CANDIDATE_FOLD_BACK_BUNDLE. `admit_bundle` is a separate
call that takes explicit human decisions -- separate because a single function
that compiled and admitted in one pass would make the boundary a matter of which
arguments happened to be present.
"""

from __future__ import annotations

from typing import Any

from fb_bundle import admit, build_bundle
from fb_common import ContractError, digest
from fb_delta import validate_delta
from fb_history import append, validate_history

STATES = [
    "BEFORE_AFTER_SUBJECTS_PINNED",
    "DIFF_SYMBOL_EDGE_DELTA",
    "TEST_RUNTIME_EVIDENCE_JOIN",
    "AFFECTED_KNOWLEDGE_LOCATED",
    "PATCH_CANDIDATES_COMPILED",
    "CONTRADICTIONS_UNKNOWNS_PRESERVED",
    "IDENTITY_DEPENDENCY_LOCATOR_GATES",
    "CANDIDATE_FOLD_BACK_BUNDLE",
]


def fold_back(
    delta: dict[str, Any],
    cards: list[dict[str, Any]],
    patches: list[dict[str, Any]],
    similarity: dict[str, float],
    history: dict[str, Any],
    anchor_states: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compile a candidate bundle. Deterministic given its inputs."""
    trace = ["BEFORE_AFTER_SUBJECTS_PINNED"]

    delta = validate_delta(delta)
    trace.append("DIFF_SYMBOL_EDGE_DELTA")
    trace.append("TEST_RUNTIME_EVIDENCE_JOIN")

    validate_history(history)
    bundle = build_bundle(delta, cards, patches, similarity, history, anchor_states)
    trace.append("AFFECTED_KNOWLEDGE_LOCATED")
    trace.append("PATCH_CANDIDATES_COMPILED")

    preserved = sorted(
        patch["canonical_key"]
        for patch in bundle["patches"]
        if patch["kind"] in {"CONFLICT", "UNKNOWN"}
    )
    trace.append("CONTRADICTIONS_UNKNOWNS_PRESERVED")
    trace.append("IDENTITY_DEPENDENCY_LOCATOR_GATES")
    trace.append("CANDIDATE_FOLD_BACK_BUNDLE")

    return {
        "state_trace": trace,
        "bundle": bundle,
        "preserved_open": preserved,
        # The idempotence handle: a rerun over the same inputs produces this
        # same value, and a rerun over the same history appends nothing.
        "fold_digest": digest(
            {
                "bundle": bundle["bundle_digest"],
                "history_head": [r["revision_id"] for r in history["revisions"]],
            }
        ),
    }


def admit_bundle(
    bundle: dict[str, Any],
    history: dict[str, Any],
    decisions: list[dict[str, Any]],
    cards: list[dict[str, Any]],
) -> dict[str, Any]:
    """Apply human decisions and append. Returns the new history and the receipt."""
    entries, receipt = admit(bundle, history, decisions, cards)
    updated, appended = append(history, entries["entries"])
    return {
        "state_trace": [*STATES, "HUMAN_ADMIT", "REVISION_HISTORY_APPENDED"],
        "history": updated,
        "receipt": receipt,
        "appended_revision_ids": appended,
        # A rerun appends nothing and says so, rather than reporting success
        # over an empty change -- the two look identical from the outside.
        "outcome": "APPENDED" if appended else "NOOP",
    }


def rerun_is_noop(first: dict[str, Any], second: dict[str, Any]) -> None:
    """The idempotence check, stated as its own function so it can be called twice."""
    if second["outcome"] != "NOOP":
        raise ContractError(
            f"re-admitting the same bundle appended {second['appended_revision_ids']}; "
            "a rerun after a transient failure would double every revision, and the "
            "history would then show a claim that changed twice when it changed once"
        )
    if second["history"] != first["history"]:
        raise ContractError("a NOOP rerun still changed the history")
