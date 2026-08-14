#!/usr/bin/env python3
"""Locating affected knowledge, and proposing a patch that preserves what was there.

**Locating.** A card is affected because it declares a code anchor that this
delta touched -- not because a similarity score says it looks related. Semantic
similarity is kept, but only as `CANDIDATE_FOR_REVIEW`: it may put a card in
front of a human, and it may not produce a patch. The reason is asymmetric cost.
A missed card is a gap someone notices; an unrelated card silently rewritten
because two paragraphs used the same vocabulary is a wrong fact with a citation
on it, and the citation makes it look checked.

**Patching.** Six kinds, and the choice between two of them is the whole
argument:

    UPDATE      the claim still holds; detail changed
    SUPERSEDE   the conclusion flipped; the old claim stays, marked superseded
    DEPRECATE   the subject is gone
    CONFLICT    the evidence disagrees with the card and neither side wins here
    UNKNOWN     the delta raises a question the evidence does not answer
    NOOP        nothing to fold back

A conclusion that flipped may not be an UPDATE. UPDATE rewrites the card, and
after it nobody can see that the system ever believed the other thing -- which is
precisely the information someone needs when the flip turns out to be wrong.

**Normative sources.** A card whose kind is normative (an ADR, a NORM) is never
UPDATE or SUPERSEDE from a code change. Code diverging from a decision does not
amend the decision; it is a CONFLICT, and a human decides which one moves.
"""

from __future__ import annotations

import hashlib
from typing import Any

from fb_common import (
    ContractError,
    canonical_bytes,
    exact_object,
    non_empty_str,
    require,
    validate_evidence_class,
)
from fb_delta import require_supported

PATCH_KINDS = ("UPDATE", "SUPERSEDE", "DEPRECATE", "CONFLICT", "UNKNOWN", "NOOP")

EPISTEMIC_STATUSES = (
    "SOURCE_STATEMENT",
    "INFERENCE",
    "HYPOTHESIS",
    "NORM",
)

# Cards a code change may not rewrite. A decision record is a record of what was
# decided, not a description of what the code currently does.
NORMATIVE_CARD_KINDS = {"ADR", "NORM", "POLICY"}

MATCH_REASONS = ("EXPLICIT_ANCHOR", "DECLARED_SYMBOL", "SEMANTIC_SIMILARITY")

# The two that may produce a patch. Similarity is deliberately absent.
PATCHABLE_MATCH_REASONS = {"EXPLICIT_ANCHOR", "DECLARED_SYMBOL"}

CARD_KEYS = {
    "canonical_key",
    "card_id",
    "kind",
    "claim",
    "code_anchors",
    "declared_symbols",
    "source_dependency_keys",
    "revision",
}

PATCH_KEYS = {
    "patch_id",
    "canonical_key",
    "card_id",
    "kind",
    "match_reason",
    "claim_before",
    "claim_after",
    "evidence_class",
    "epistemic_status",
    "supporting_anchor_ids",
    "supporting_symbols",
    "source_dependency_keys",
    "unresolved",
    "rollback",
}


def validate_card(value: Any, label: str) -> dict[str, Any]:
    card = exact_object(value, CARD_KEYS, label)
    non_empty_str(card["canonical_key"], f"{label}.canonical_key")
    non_empty_str(card["claim"], f"{label}.claim")
    non_empty_str(card["kind"], f"{label}.kind")
    if not isinstance(card["revision"], int) or card["revision"] < 0:
        raise ContractError(f"{label}.revision must be a non-negative integer")
    for field in ("code_anchors", "declared_symbols", "source_dependency_keys"):
        value_ = card[field]
        if not isinstance(value_, list) or value_ != sorted(value_):
            raise ContractError(f"{label}.{field} must be a sorted list")
    # Card identity is derived from the canonical key, exactly as the forward
    # compiler derives it. A fold-back that minted a fresh id for an existing
    # key would fork the card, and both halves would look current.
    expected = card_id_for(card["canonical_key"])
    if card["card_id"] != expected:
        raise ContractError(
            f"{label}.card_id is {card['card_id']!r} but its canonical key derives "
            f"{expected!r}; a new id for an existing key forks the card, and every "
            "later reference lands on whichever half it happened to see"
        )
    duplicates = [
        key
        for key in set(card["source_dependency_keys"])
        if card["source_dependency_keys"].count(key) > 1
    ]
    if duplicates:
        raise ContractError(
            f"{label} lists source dependency keys {sorted(duplicates)} more than "
            "once; the same source counted twice reads as corroboration"
        )
    return card


def card_id_for(canonical_key: str) -> str:
    return (
        "card-"
        + hashlib.sha256(canonical_bytes({"key": canonical_key})).hexdigest()[:16]
    )


def locate_affected(
    cards: list[dict[str, Any]], delta: dict[str, Any], similarity: dict[str, float]
) -> list[dict[str, Any]]:
    """Which cards this delta touches, and on what grounds.

    Similarity scores are accepted and reported, never acted on.
    """
    touched_anchors = {anchor["anchor_id"] for anchor in delta["anchors"]}
    touched_symbols = {entry["symbol"] for entry in delta["symbol_delta"]}

    located = []
    for card in cards:
        validate_card(card, f"card {card.get('canonical_key')!r}")
        anchors = sorted(set(card["code_anchors"]) & touched_anchors)
        symbols = sorted(set(card["declared_symbols"]) & touched_symbols)
        if anchors:
            reason = "EXPLICIT_ANCHOR"
        elif symbols:
            reason = "DECLARED_SYMBOL"
        elif similarity.get(card["canonical_key"], 0.0) > 0:
            reason = "SEMANTIC_SIMILARITY"
        else:
            continue
        located.append(
            {
                "canonical_key": card["canonical_key"],
                "match_reason": reason,
                "matched_anchor_ids": anchors,
                "matched_symbols": symbols,
                "similarity": similarity.get(card["canonical_key"], 0.0),
                # The field that keeps a score from becoming an edit.
                "patchable": reason in PATCHABLE_MATCH_REASONS,
                "state": (
                    "AFFECTED"
                    if reason in PATCHABLE_MATCH_REASONS
                    else "CANDIDATE_FOR_REVIEW"
                ),
            }
        )
    return sorted(located, key=lambda row: row["canonical_key"])


def validate_patch(
    value: Any,
    label: str,
    cards_by_key: dict[str, dict[str, Any]],
    located_by_key: dict[str, dict[str, Any]],
    delta: dict[str, Any],
) -> dict[str, Any]:
    patch = exact_object(value, PATCH_KEYS, label)
    non_empty_str(patch["patch_id"], f"{label}.patch_id")

    key = patch["canonical_key"]
    if key not in cards_by_key:
        raise ContractError(f"{label} targets unknown card {key!r}")
    card = cards_by_key[key]
    if patch["card_id"] != card["card_id"]:
        raise ContractError(
            f"{label} carries card_id {patch['card_id']!r} for a card whose id is "
            f"{card['card_id']!r}; a patch that renames the card it edits creates a "
            "second card nobody asked for"
        )

    if patch["kind"] not in PATCH_KINDS:
        raise ContractError(f"{label}.kind must be one of {list(PATCH_KINDS)}")
    if patch["match_reason"] not in MATCH_REASONS:
        raise ContractError(
            f"{label}.match_reason must be one of {list(MATCH_REASONS)}"
        )

    located = located_by_key.get(key)
    if located is None:
        raise ContractError(
            f"{label} patches {key!r}, which this delta did not locate as affected"
        )
    if patch["match_reason"] != located["match_reason"]:
        raise ContractError(
            f"{label} claims match_reason {patch['match_reason']!r} but the locator "
            f"found {located['match_reason']!r}"
        )
    # The similarity control. A score may surface a card; it may not edit one.
    if patch["match_reason"] == "SEMANTIC_SIMILARITY":
        raise ContractError(
            f"{label} patches {key!r} on semantic similarity alone. A score can put a "
            "card in front of a human; it cannot rewrite one, because an unrelated "
            "card edited on vocabulary overlap becomes a wrong fact wearing a citation"
        )

    validate_evidence_class(patch["evidence_class"], f"{label}.evidence_class")
    if patch["epistemic_status"] not in EPISTEMIC_STATUSES:
        raise ContractError(
            f"{label}.epistemic_status must be one of {list(EPISTEMIC_STATUSES)}"
        )

    symbols = patch["supporting_symbols"]
    if not isinstance(symbols, list) or symbols != sorted(symbols):
        raise ContractError(f"{label}.supporting_symbols must be a sorted list")

    anchors = patch["supporting_anchor_ids"]
    if not isinstance(anchors, list) or anchors != sorted(anchors):
        raise ContractError(f"{label}.supporting_anchor_ids must be a sorted list")
    known_anchors = {anchor["anchor_id"] for anchor in delta["anchors"]}
    for anchor_id in anchors:
        if anchor_id not in known_anchors:
            raise ContractError(f"{label} cites anchor {anchor_id!r} not in the delta")

    # Normative cards. Code diverging from a decision is a conflict, not an
    # amendment to the decision.
    if card["kind"] in NORMATIVE_CARD_KINDS and patch["kind"] in {
        "UPDATE",
        "SUPERSEDE",
        "DEPRECATE",
    }:
        raise ContractError(
            f"{label} would {patch['kind']} the {card['kind']} card {key!r} from a "
            "code change. Code diverging from a decision record does not amend the "
            "decision; that is a CONFLICT, and which side moves is a human's call"
        )

    if patch["kind"] == "NOOP":
        if patch["claim_after"] != patch["claim_before"]:
            raise ContractError(f"{label} is a NOOP that changes the claim")
        return patch

    if patch["kind"] in {"CONFLICT", "UNKNOWN"}:
        # These record a question, so they do not assert a new claim and are not
        # required to carry evidence strong enough to support one.
        if patch["claim_after"] != patch["claim_before"]:
            raise ContractError(
                f"{label} is a {patch['kind']} but rewrites the claim; recording a "
                "disagreement is not the same as settling it"
            )
        if not patch["unresolved"]:
            raise ContractError(
                f"{label} is a {patch['kind']} with nothing unresolved recorded"
            )
        return patch

    non_empty_str(patch["claim_after"], f"{label}.claim_after")
    if patch["claim_before"] != card["claim"]:
        raise ContractError(
            f"{label}.claim_before does not match the card it patches; a patch built "
            "against a claim the card no longer holds was computed from a stale read"
        )

    # The supersession rule. A flip is not an edit.
    if patch["kind"] == "UPDATE" and _contradicts(
        patch["claim_before"], patch["claim_after"]
    ):
        raise ContractError(
            f"{label} is an UPDATE that reverses the claim. UPDATE rewrites the card, "
            "and afterwards nobody can see the system ever believed the other thing "
            "-- which is exactly what someone needs when the reversal turns out to be "
            "wrong. Use SUPERSEDE"
        )
    if patch["kind"] == "SUPERSEDE" and not _contradicts(
        patch["claim_before"], patch["claim_after"]
    ):
        raise ContractError(
            f"{label} is a SUPERSEDE that does not reverse anything; superseding a "
            "claim that still holds buries a live claim in history"
        )

    if not symbols:
        raise ContractError(
            f"{label} asserts a new claim with no supporting symbol; the change it "
            "folds back cannot be located in the delta"
        )
    for symbol in symbols:
        require_supported(delta, symbol, patch["evidence_class"])

    if not anchors:
        raise ContractError(
            f"{label} asserts a new claim with no anchor; a knowledge revision with "
            "no citation is indistinguishable from one written from memory"
        )

    keys = patch["source_dependency_keys"]
    if not isinstance(keys, list) or keys != sorted(keys):
        raise ContractError(f"{label}.source_dependency_keys must be a sorted list")
    if len(set(keys)) != len(keys):
        raise ContractError(
            f"{label} counts a source dependency more than once; repeated keys read "
            "as independent corroboration and raise a ceiling on nothing"
        )

    rollback = patch["rollback"]
    if not isinstance(rollback, dict) or set(rollback) != {"kind", "restores_revision"}:
        raise ContractError(
            f"{label}.rollback must name a kind and the revision it restores"
        )
    if rollback["kind"] not in {"RESTORE_REVISION", "APPEND_REVERSAL"}:
        raise ContractError(
            f"{label}.rollback.kind must be RESTORE_REVISION or APPEND_REVERSAL; "
            "neither deletes history, because a rollback that erased the revision "
            "would also erase the evidence that justified it"
        )
    if rollback["restores_revision"] != card["revision"]:
        raise ContractError(
            f"{label}.rollback restores revision {rollback['restores_revision']} but "
            f"the card is at {card['revision']}"
        )
    require(True, "")
    return patch


NEGATIONS = (
    (" is ", " is not "),
    (" does ", " does not "),
    (" must ", " must not "),
    (" always ", " never "),
    (" before ", " after "),
)


def _affirms(text: str, positive: str, negative: str) -> bool:
    """Does the text use the positive form, other than inside the negative one?

    Every positive marker here is a substring of its own negation -- " does " is
    inside " does not " -- so a naive membership test reports both forms present
    in any sentence that contains the negation. The negation is removed first, so
    only a genuinely separate affirmative counts.
    """
    return positive in text.replace(negative, " ")


def _contradicts(before: str, after: str) -> bool:
    """Does the new claim reverse the old one?

    A deliberately shallow, declared heuristic over a fixed negation table.
    Anything cleverer would decide supersession by inference, and the decision
    would then be unauditable at exactly the moment it matters. A caller who
    knows better states the kind explicitly and the checks above hold them to it.
    """
    left, right = before.lower(), after.lower()
    for positive, negative in NEGATIONS:
        if _affirms(left, positive, negative) and negative in right:
            return True
        if negative in left and _affirms(right, positive, negative):
            return True
    return False
