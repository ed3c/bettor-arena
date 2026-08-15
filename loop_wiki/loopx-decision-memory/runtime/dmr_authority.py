#!/usr/bin/env python3
"""The authority ladder. Memory is the lowest rung, and that is the whole point.

A memory says what was true when someone wrote it down. The repository says what
is true now. When they disagree, the repository wins -- not because memory is
unreliable, but because memory is *old by construction* and source is not.

    SOURCE      the code as it is
    TEST        an executed check
    ADR         a recorded decision
    RECEIPT     an admitted evidence artifact
    MEMORY      what someone concluded, at some point, about some tree

The failure this prevents is quiet and expensive: a memory recorded six months
ago says "the retry interval is fixed", the code now does exponential backoff,
and an agent reading memory first acts on the memory. Nothing in the output says
which one it used.

So `resolve` never returns just an answer. It returns the answer, the rung it
came from, and -- when a lower rung disagreed -- what it disagreed with. A caller
that wants to ignore the higher rung has to do so visibly.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from memory import ContractError  # noqa: E402

# Highest authority first. Position in this tuple is the rung.
LADDER = ("SOURCE", "TEST", "ADR", "RECEIPT", "MEMORY")

RANK = {name: index for index, name in enumerate(LADDER)}

CLAIM_KEYS = {"rung", "statement", "ref", "observed_at"}


def validate_claim(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != CLAIM_KEYS:
        raise ContractError(f"{label} fields drifted")
    if value["rung"] not in RANK:
        raise ContractError(f"{label}.rung must be one of {list(LADDER)}")
    for field in ("statement", "ref"):
        if not isinstance(value[field], str) or not value[field].strip():
            raise ContractError(f"{label}.{field} must be a non-empty string")
    return value


def outranks(left: str, right: str) -> bool:
    """Does a claim on rung `left` outrank one on rung `right`?"""
    if left not in RANK or right not in RANK:
        raise ContractError(f"unknown rung in {left!r} vs {right!r}")
    return RANK[left] < RANK[right]


def resolve(claims: list[dict[str, Any]]) -> dict[str, Any]:
    """Which claim holds, and what it overrode. Never returns a bare answer."""
    if not claims:
        raise ContractError("resolve needs at least one claim")
    for index, claim in enumerate(claims):
        validate_claim(claim, f"claims[{index}]")

    ordered = sorted(claims, key=lambda claim: (RANK[claim["rung"]], claim["ref"]))
    winner = ordered[0]
    overridden = [
        claim for claim in ordered[1:] if claim["statement"] != winner["statement"]
    ]
    return {
        "answer": winner["statement"],
        "rung": winner["rung"],
        "ref": winner["ref"],
        # Named, not dropped. A resolution that silently discarded the losing
        # claims reads as though there was never a disagreement.
        "overridden": [
            {
                "rung": claim["rung"],
                "ref": claim["ref"],
                "statement": claim["statement"],
            }
            for claim in overridden
        ],
        "memory_was_overridden": any(claim["rung"] == "MEMORY" for claim in overridden),
    }


def invalidation_proposals(
    resolution: dict[str, Any], memory_id: str
) -> list[dict[str, Any]]:
    """A memory the repository contradicted gets a proposal, not a deletion.

    Automatic invalidation would delete a memory because today's code disagrees,
    and today's code is sometimes the thing that is wrong. The memory is flagged
    for a human; nothing is removed.
    """
    if not resolution["memory_was_overridden"]:
        return []
    return [
        {
            "memory_id": memory_id,
            "proposed_state": "CONTESTED",
            "contradicted_by": {
                "rung": resolution["rung"],
                "ref": resolution["ref"],
                "statement": resolution["answer"],
            },
            "requires_human": True,
            "reason": (
                "a higher rung disagrees with this memory. It is contested rather "
                "than invalidated: today's code is sometimes the thing that is wrong, "
                "and deleting the memory would remove the only record that anyone "
                "ever concluded otherwise"
            ),
        }
    ]
