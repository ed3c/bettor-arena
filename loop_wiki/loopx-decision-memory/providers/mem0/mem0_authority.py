#!/usr/bin/env python3
"""The four-rung authority law from #93, and the writeback that is only a proposal.

    current source / tests / ADR / CONTEXT / LoopX ledger
      > Human-admitted memory event
      > Mem0 projection result
      > model summary

The runtime module already has a ladder ending at MEMORY. This extends it
downward by two rungs, and the two additions are the ones that get inverted in
practice: a retrieval result reads as authoritative because it came back from a
system, and a model summary reads as authoritative because it is fluent.

`writeback_proposal` is the other half. Mem0 may index and retrieve; it may not
turn a retrieval into durable memory. So the only thing this module can produce
in that direction is a proposal addressed to the runtime's admission path, and
`validate_writeback` refuses anything that claims to have written.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "runtime"))

from memory import ContractError, digest  # noqa: E402

from dmr_authority import LADDER as RUNTIME_LADDER  # noqa: E402

# The runtime ladder, extended downward. MEMORY keeps its place; the projection
# and the model sit below it.
LADDER = (*RUNTIME_LADDER, "MEM0_PROJECTION", "MODEL_SUMMARY")

RANK = {name: index for index, name in enumerate(LADDER)}

WRITEBACK_KEYS = {
    "proposal_id",
    "canonical_key",
    "statement",
    "derived_from_hits",
    "state",
    "requires_human_admit",
    "written",
    "target",
}


def outranks(left: str, right: str) -> bool:
    if left not in RANK or right not in RANK:
        raise ContractError(f"unknown rung in {left!r} vs {right!r}")
    return RANK[left] < RANK[right]


def resolve(claims: list[dict[str, Any]]) -> dict[str, Any]:
    """Which claim holds, and everything it outranked."""
    if not claims:
        raise ContractError("resolve needs at least one claim")
    for index, claim in enumerate(claims):
        if claim.get("rung") not in RANK:
            raise ContractError(f"claims[{index}].rung must be one of {list(LADDER)}")

    ordered = sorted(
        claims, key=lambda claim: (RANK[claim["rung"]], claim.get("ref", ""))
    )
    winner = ordered[0]
    overridden = [
        c for c in ordered[1:] if c.get("statement") != winner.get("statement")
    ]
    return {
        "answer": winner.get("statement"),
        "rung": winner["rung"],
        "overridden": [
            {"rung": c["rung"], "statement": c.get("statement"), "ref": c.get("ref")}
            for c in overridden
        ],
        "projection_was_overridden": any(
            c["rung"] == "MEM0_PROJECTION" for c in overridden
        ),
        "model_summary_was_overridden": any(
            c["rung"] == "MODEL_SUMMARY" for c in overridden
        ),
    }


def writeback_proposal(
    hits: list[dict[str, Any]], canonical_key: str, statement: str
) -> dict[str, Any]:
    """Turn retrieval into a *proposal*. There is no function that writes."""
    if not hits:
        raise ContractError(
            "a writeback proposal with no supporting hits is a model summary wearing "
            "a retrieval's clothes"
        )
    if not isinstance(statement, str) or not statement.strip():
        raise ContractError("a writeback proposal needs a statement")
    return {
        "proposal_id": "wb-"
        + digest({"key": canonical_key, "statement": statement})[7:19],
        "canonical_key": canonical_key,
        "statement": statement,
        "derived_from_hits": sorted(hit["canonical_key"] for hit in hits),
        "state": "PROPOSED",
        "requires_human_admit": True,
        # Recorded as a fact about what this module did, so a reader does not
        # have to infer it from the absence of a write.
        "written": False,
        "target": "LOOPX_MEMORY_ADMISSION",
    }


def validate_writeback(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != WRITEBACK_KEYS:
        raise ContractError("writeback proposal fields drifted")
    if value["state"] != "PROPOSED":
        raise ContractError(
            f"a writeback in state {value['state']!r}; Mem0 may index and retrieve, and "
            "turning a retrieval into durable memory is the admission path's decision"
        )
    if value["requires_human_admit"] is not True:
        raise ContractError("a writeback proposal that does not require admission")
    if value["written"] is not False:
        raise ContractError(
            "the writeback reports itself written; an automatic writeback makes the "
            "vector store an author, and the next session reads its output as "
            "something a person decided"
        )
    if value["target"] != "LOOPX_MEMORY_ADMISSION":
        raise ContractError("a writeback aimed somewhere other than the admission path")
    return value
