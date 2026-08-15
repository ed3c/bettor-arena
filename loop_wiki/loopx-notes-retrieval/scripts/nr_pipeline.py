#!/usr/bin/env python3
"""The retrieval pass, in the order #105 names.

    NOTES_REPO_COMMIT_TREE_PINNED
    -> SOURCE_MANIFEST_AND_RELEASE_SELECTED
    -> STATIC_OPENWIKI_PROJECTION_BUILT
    -> VECTOR_GRAPH_IDENTITIES_PINNED_OR_ABSENT
    -> CHUNK_EMBED_INDEX_POLICY_APPLIED
    -> COVERAGE_FRESHNESS_RECEIPT
    -> MACRO_READ_AND_MICRO_QUERY_CANARIES
    -> SOURCE_READBACK
    -> DELETE_REBUILD_RESIDUE_CHECK
    -> RETRIEVAL_RELEASE_CANDIDATE

The OpenWiki projection is built whether or not a vector provider exists. Macro
structure is the part that always works: it is generated Markdown over cards,
and it needs no model, no store and no network. A missing provider costs the
micro queries and nothing else, which is why the states are separate.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nr_common import ContractError, ProviderAbsent, digest
from nr_index import build_chunks, build_subject, check_freshness, coverage
from nr_openwiki import build_projection, validate_projection
from nr_query import micro_query, source_readback, to_claim, validate_result

STATES = [
    "NOTES_REPO_COMMIT_TREE_PINNED",
    "SOURCE_MANIFEST_AND_RELEASE_SELECTED",
    "STATIC_OPENWIKI_PROJECTION_BUILT",
    "VECTOR_GRAPH_IDENTITIES_PINNED_OR_ABSENT",
    "CHUNK_EMBED_INDEX_POLICY_APPLIED",
    "COVERAGE_FRESHNESS_RECEIPT",
    "MACRO_READ_AND_MICRO_QUERY_CANARIES",
    "SOURCE_READBACK",
    "DELETE_REBUILD_RESIDUE_CHECK",
    "RETRIEVAL_RELEASE_CANDIDATE",
]


def build(
    repository: str,
    commit: str,
    tree: str,
    manifest_digest: str,
    policy: dict[str, Any],
    cards: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    texts: dict[str, str],
    provider_present: bool,
) -> dict[str, Any]:
    """Build both projections. The static one does not need a provider."""
    trace = ["NOTES_REPO_COMMIT_TREE_PINNED", "SOURCE_MANIFEST_AND_RELEASE_SELECTED"]

    evidence_by_card: dict[str, list[dict[str, Any]]] = {}
    for record in evidence:
        key = record.get("card_key")
        if key:
            evidence_by_card.setdefault(key, []).append(record)
    openwiki = validate_projection(build_projection(cards, evidence_by_card))
    trace.append("STATIC_OPENWIKI_PROJECTION_BUILT")

    subject = build_subject(repository, commit, tree, manifest_digest, policy)
    trace.append("VECTOR_GRAPH_IDENTITIES_PINNED_OR_ABSENT")

    chunks = build_chunks(evidence, texts, policy) if provider_present else []
    trace.append("CHUNK_EMBED_INDEX_POLICY_APPLIED")

    report = coverage(chunks, evidence)
    trace.append("COVERAGE_FRESHNESS_RECEIPT")

    return {
        "state_trace": trace,
        "index_subject": subject,
        "openwiki": openwiki,
        "chunks": chunks,
        "coverage": report,
        # Named, so a caller does not read an empty chunk list as empty notes.
        "vector_provider": "PRESENT" if provider_present else "ABSENT",
        "build_digest": digest(
            {
                "subject": subject,
                "openwiki": openwiki["projection_digest"],
                "coverage": report["content_digest"],
            }
        ),
    }


def query(
    built: dict[str, Any],
    current_subject: dict[str, Any],
    term: str,
    root: Path,
) -> dict[str, Any]:
    """Macro read plus one micro query, with readback on every hit."""
    trace = list(STATES[:6])

    freshness = check_freshness(built["index_subject"], current_subject)
    provider_present = built["vector_provider"] == "PRESENT"

    macro = {
        "navigation": built["openwiki"]["navigation"],
        "page_count": built["openwiki"]["page_count"],
        # The macro read works with no provider at all. Saying so here keeps a
        # missing store from reading as a missing wiki.
        "requires_provider": False,
    }

    try:
        micro = micro_query(built["chunks"], term, freshness, provider_present)
        provider_state = "PRESENT"
    except ProviderAbsent as exc:
        micro = {
            "state": "PROVIDER_ABSENT",
            "hits": [],
            "reason": str(exc),
            "absence_proof": "NONE",
            "authority": "CURRENT_SOURCE_AND_EVIDENCE",
            "index_freshness": freshness["state"],
        }
        provider_state = "ABSENT"
    validate_result(micro)
    trace.append("MACRO_READ_AND_MICRO_QUERY_CANARIES")

    readbacks = [source_readback(hit, root) for hit in micro["hits"]]
    drifted = [entry for entry in readbacks if entry["state"] != "CONFIRMED"]
    trace.append("SOURCE_READBACK")

    if drifted:
        raise ContractError(
            f"{len(drifted)} hit(s) failed source readback: {drifted[0]['reason']}. A "
            "chunk whose text is no longer in the file it names cites a version that "
            "is gone, and the citation looks perfect"
        )
    trace.append("DELETE_REBUILD_RESIDUE_CHECK")
    trace.append("RETRIEVAL_RELEASE_CANDIDATE")

    return {
        "state_trace": trace,
        "freshness": freshness,
        "vector_provider": provider_state,
        "macro": macro,
        "micro": micro,
        "readbacks": readbacks,
        "claim": to_claim(micro),
    }
