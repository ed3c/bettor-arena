#!/usr/bin/env python3
"""Layer 3 -- knowledge cards. Stable keys, typed links, and no quiet merges.

A card ID is derived from the card's own content, never allocated. A random or
counter-based ID would change on every rerun, and then a downstream reference
either dangles or -- worse -- lands on a different card that happens to have
taken the number. `compile_cards` is a pure function of the assertions it is
given, which is what makes the whole compile idempotent.

Cards that contradict each other are linked with CONTRADICTS and both survive.
The compiler never picks a winner: doing so deletes evidence and leaves a graph
that looks consistent because the disagreement was removed, not settled.
"""

from __future__ import annotations

import hashlib
from typing import Any

from kc_common import (
    ContractError,
    canonical_bytes,
    exact_object,
    non_empty_str,
    require,
)

LINK_KINDS = {"SUPPORTS", "CONTRADICTS", "REFINES", "DEPENDS_ON"}

CARD_KEYS = {
    "card_id",
    "canonical_key",
    "title",
    "kind",
    "assertion_ids",
    "verification_state",
    "links",
    "unknowns",
}

GRAPH_KEYS = {"schema_version", "notes_subject", "cards"}


def canonical_key(title: str, kind: str) -> str:
    """A human-readable key, normalised so the same card is the same card."""
    slug = "-".join(title.lower().split())
    return f"{kind.lower()}:{slug}"


def card_id(canonical: str, assertion_ids: list[str]) -> str:
    """Derived from content, so a rerun on the same sources reproduces it.

    This is the "unstable random card IDs on rerun" control, answered by
    construction rather than by a test: there is no code path that could
    allocate a different ID for the same content.
    """
    payload = canonical_bytes({"key": canonical, "assertions": sorted(assertion_ids)})
    return "card-" + hashlib.sha256(payload).hexdigest()[:16]


def compile_cards(
    assertions: list[dict[str, Any]],
    contradictions: list[dict[str, Any]],
    grouping: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    """Group assertions into cards. Pure, sorted, and total over its input.

    `grouping` maps assertion_id -> {title, kind}. It is supplied rather than
    inferred: guessing which claims belong together is exactly the step where a
    model's prior knowledge leaks in, and here it is an input the caller has to
    write down and a reader can check.
    """
    by_id = {a["assertion_id"]: a for a in assertions}
    for assertion_id in grouping:
        if assertion_id not in by_id:
            raise ContractError(f"grouping names unknown assertion {assertion_id!r}")
    ungrouped = sorted(set(by_id) - set(grouping))
    if ungrouped:
        raise ContractError(
            f"assertions {ungrouped} were not assigned to a card; a claim dropped "
            "between layers disappears without ever being contradicted"
        )

    buckets: dict[str, dict[str, Any]] = {}
    for assertion_id, spec in sorted(grouping.items()):
        key = canonical_key(spec["title"], spec["kind"])
        bucket = buckets.setdefault(
            key,
            {"title": spec["title"], "kind": spec["kind"], "assertion_ids": []},
        )
        if bucket["title"] != spec["title"] or bucket["kind"] != spec["kind"]:
            raise ContractError(
                f"canonical key {key!r} is claimed by two different card definitions"
            )
        bucket["assertion_ids"].append(assertion_id)

    contradicted_pairs: set[tuple[str, str]] = set()
    for entry in contradictions:
        ids = entry["assertion_ids"]
        for left in ids:
            for right in ids:
                if left != right:
                    contradicted_pairs.add((left, right))

    key_of_assertion = {
        assertion_id: canonical_key(spec["title"], spec["kind"])
        for assertion_id, spec in grouping.items()
    }

    cards = []
    for key, bucket in sorted(buckets.items()):
        assertion_ids = sorted(bucket["assertion_ids"])
        members = [by_id[a] for a in assertion_ids]
        states = {a["verification_state"] for a in members}

        # A card is only as verified as its weakest member. A card holding one
        # verified and one unknown claim is not verified, and rendering it that
        # way is how an unknown becomes an assumption downstream.
        if "CONTRADICTED" in states:
            state = "CONTRADICTED"
        elif "UNKNOWN" in states:
            state = "PARTIALLY_UNKNOWN"
        elif states == {"VERIFIED_BY_EXECUTION"}:
            state = "VERIFIED_BY_EXECUTION"
        elif states <= {"VERIFIED_BY_EXECUTION", "CORROBORATED", "ADMITTED_BY_HUMAN"}:
            state = "CORROBORATED"
        else:
            state = "UNVERIFIED"

        links = []
        for assertion_id in assertion_ids:
            for other_id, other_key in sorted(key_of_assertion.items()):
                if other_key == key:
                    continue
                if (assertion_id, other_id) in contradicted_pairs:
                    links.append({"kind": "CONTRADICTS", "target": other_key})
        unique_links = sorted({(link["kind"], link["target"]) for link in links})

        cards.append(
            {
                "card_id": card_id(key, assertion_ids),
                "canonical_key": key,
                "title": bucket["title"],
                "kind": bucket["kind"],
                "assertion_ids": assertion_ids,
                "verification_state": state,
                "links": [{"kind": k, "target": t} for k, t in unique_links],
                "unknowns": sorted(
                    a["assertion_id"]
                    for a in members
                    if a["verification_state"] == "UNKNOWN"
                ),
            }
        )
    return cards


def validate_card_graph(value: Any) -> dict[str, Any]:
    graph = exact_object(value, GRAPH_KEYS, "card graph")
    require(
        graph["schema_version"] == "loopx/knowledge-card-graph/v1",
        "card graph schema version drifted",
    )
    cards = graph["cards"]
    if not isinstance(cards, list) or not cards:
        raise ContractError("card graph.cards must be a non-empty list")

    keys = set()
    for index, value_ in enumerate(cards):
        label = f"cards[{index}]"
        card = exact_object(value_, CARD_KEYS, label)
        non_empty_str(card["title"], f"{label}.title")
        non_empty_str(card["kind"], f"{label}.kind")

        expected_key = canonical_key(card["title"], card["kind"])
        if card["canonical_key"] != expected_key:
            raise ContractError(
                f"{label}.canonical_key is {card['canonical_key']!r} but its title and "
                f"kind derive {expected_key!r}; a key that is not a function of the "
                "card cannot be recomputed by anyone checking it"
            )
        expected_id = card_id(expected_key, card["assertion_ids"])
        if card["card_id"] != expected_id:
            raise ContractError(
                f"{label}.card_id is {card['card_id']!r} but its content derives "
                f"{expected_id!r}; an allocated id changes on rerun and every "
                "reference to it silently retargets"
            )
        if card["canonical_key"] in keys:
            raise ContractError(f"duplicate canonical_key {card['canonical_key']!r}")
        keys.add(card["canonical_key"])

        for link in card["links"]:
            exact_object(link, {"kind", "target"}, f"{label}.links[]")
            if link["kind"] not in LINK_KINDS:
                raise ContractError(
                    f"{label} link kind {link['kind']!r} is not one of "
                    f"{sorted(LINK_KINDS)}"
                )

    # Links must resolve. A CONTRADICTS pointing at a key that is not in the
    # graph is how a contradiction gets "resolved": delete the other card and
    # the disagreement stops being visible.
    for card in cards:
        for link in card["links"]:
            if link["target"] not in keys:
                raise ContractError(
                    f"card {card['canonical_key']!r} links to {link['target']!r}, "
                    "which is not in the graph; the other side of this relation was "
                    "dropped rather than settled"
                )

    if [c["canonical_key"] for c in cards] != sorted(c["canonical_key"] for c in cards):
        raise ContractError("card graph.cards must be sorted by canonical_key")
    return graph
