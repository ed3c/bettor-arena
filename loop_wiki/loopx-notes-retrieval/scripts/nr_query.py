#!/usr/bin/env python3
"""Macro reads and micro queries, and the readback that makes a hit worth having.

Two retrieval shapes, and they answer different questions:

    macro   the OpenWiki structure -- what exists, how it is organised
    micro   a bounded semantic query -- which chunks are near this text

A macro read is deterministic: the same projection gives the same navigation.
A micro query is not a fact. `to_claim` is the boundary: a hit becomes a
*candidate with provenance*, never a claim and never a gate verdict, and the
field saying so is on every result rather than in a document someone would have
to consult.

`source_readback` is what separates a usable hit from a plausible one. A chunk
carries a locator; readback goes to the source and checks the text is actually
there. A retrieval system that skips it will, sooner or later, return a chunk
whose text no longer matches the file it names -- and the citation will look
perfect.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nr_common import (
    ContractError,
    FINAL_AUTHORITY,
    ProviderAbsent,
    non_empty_str,
    proves_absence,
    retrieval_state,
)

RESULT_KEYS = {
    "state",
    "hits",
    "reason",
    "absence_proof",
    "authority",
    "index_freshness",
}


def micro_query(
    chunks: list[dict[str, Any]],
    term: str,
    freshness: dict[str, Any],
    provider_present: bool,
    limit: int = 5,
) -> dict[str, Any]:
    """A bounded query. Says which of the four kinds of nothing it found."""
    non_empty_str(term, "query term")

    if not provider_present:
        # Raised rather than returned as an empty list: nothing was asked, so
        # nothing can be concluded, and a caller that ignores the exception has
        # to do so deliberately.
        raise ProviderAbsent(
            "no vector provider is present. Nothing was queried, so nothing about "
            "the notes follows -- an empty result here would be a claim about an "
            "index that does not exist"
        )

    if freshness["state"] != "CURRENT":
        return _result(
            "NOT_INDEXED",
            [],
            f"the index is {freshness['state']}: {freshness['reason']}",
            freshness,
        )

    if not chunks:
        return _result(
            "NOT_INDEXED",
            [],
            "the index holds no chunks; a query against an empty index returns "
            "nothing because there is nothing in it, not because the notes are silent",
            freshness,
        )

    needle = term.lower()
    hits = [
        {
            "chunk_id": chunk["chunk_id"],
            "text": chunk["text"],
            # Provenance travels with the hit. A chunk without it is a paragraph
            # with a score, and the paragraph is not what anyone needs.
            "provenance": {
                "source_id": chunk["source_id"],
                "evidence_id": chunk["evidence_id"],
                "card_key": chunk["card_key"],
                "locator": chunk["locator"],
                "ordinal": chunk["ordinal"],
            },
        }
        for chunk in chunks
        if needle in chunk["text"].lower()
    ][:limit]

    if not hits:
        return _result(
            "MISS",
            [],
            "no chunk in this index was near enough to the query. That is a fact "
            "about the index, not about the notes",
            freshness,
        )
    return _result("HIT", hits, f"{len(hits)} candidate chunk(s)", freshness)


def _result(
    state: str, hits: list[dict[str, Any]], reason: str, freshness: dict[str, Any]
) -> dict[str, Any]:
    retrieval_state(state, "result.state")
    return {
        "state": state,
        "hits": hits,
        "reason": reason,
        # On every result, including the hits. No retrieval state proves absence.
        "absence_proof": proves_absence(state),
        "authority": FINAL_AUTHORITY,
        "index_freshness": freshness["state"],
    }


def validate_result(value: Any, label: str = "result") -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != RESULT_KEYS:
        raise ContractError(f"{label} fields drifted; expected {sorted(RESULT_KEYS)}")
    retrieval_state(value["state"], f"{label}.state")
    if value["absence_proof"] != "NONE":
        raise ContractError(
            f"{label} claims its result proves absence. A retrieval says something "
            "about an index and nothing about the world"
        )
    if value["authority"] != FINAL_AUTHORITY:
        raise ContractError(
            f"{label} claims authority {value['authority']!r}; the final authority is "
            "current source and evidence, and a projection is a way of finding it"
        )
    if value["state"] in {"MISS", "NOT_INDEXED", "PROVIDER_ABSENT"} and value["hits"]:
        raise ContractError(f"{label} is {value['state']} and carries hits")
    for index, hit in enumerate(value["hits"]):
        if set(hit) != {"chunk_id", "text", "provenance"}:
            raise ContractError(f"{label}.hits[{index}] fields drifted")
        if set(hit["provenance"]) != {
            "source_id",
            "evidence_id",
            "card_key",
            "locator",
            "ordinal",
        }:
            raise ContractError(
                f"{label}.hits[{index}].provenance is incomplete; a chunk that lost "
                "its locator is a paragraph nobody can check"
            )
    return value


def source_readback(hit: dict[str, Any], root: Path) -> dict[str, Any]:
    """Go to the source and check the chunk text is actually there.

    The check that makes a hit usable. Without it a retrieval will eventually
    return a chunk whose text no longer matches the file it names, and the
    citation will look perfect.
    """
    locator = hit["provenance"]["locator"]
    path = root / locator.split("#", 1)[0]
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {
            "chunk_id": hit["chunk_id"],
            "state": "SOURCE_UNREADABLE",
            "reason": f"cannot read {path}: {exc}",
        }
    if hit["text"] and hit["text"] not in text:
        return {
            "chunk_id": hit["chunk_id"],
            "state": "DRIFTED",
            "reason": (
                "the chunk text is not in the source it cites; the index describes a "
                "version of this file that is no longer there"
            ),
        }
    return {
        "chunk_id": hit["chunk_id"],
        "state": "CONFIRMED",
        "reason": "the chunk text is present in the source it cites",
    }


def to_claim(result: dict[str, Any]) -> dict[str, Any]:
    """What a downstream consumer is handed. A candidate, never a fact."""
    validate_result(result)
    return {
        "admitted_as": "RETRIEVAL_CANDIDATE",
        "state": result["state"],
        "candidates": result["hits"],
        "absence_proof": "NONE",
        # Said at the boundary, because this is where the promotion would happen.
        "is_fact": False,
        "is_gate_verdict": False,
        "authority": FINAL_AUTHORITY,
        "note": (
            "a vector hit is a place to look. Whether the claim holds is settled by "
            "the source and the evidence it cites, not by the similarity that found it"
        ),
    }
