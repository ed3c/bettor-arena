#!/usr/bin/env python3
"""Index subject, chunk provenance, and the freshness that is not a timer.

An index subject is four things together: the Notes Repo commit, its tree, the
digest of the source manifest it was built from, and the compiler policy that
built it. Any one of them moving invalidates the index, and each moves for a
different reason -- so a subject missing one of them is an index that will keep
answering after the thing it describes has changed.

The embedding identity is inside the policy for the same reason. An index built
with a 384-dimension model and queried with a 768-dimension one does not error;
it returns neighbours, and they are meaningless. That is the quietest failure in
this module, so `check_freshness` compares the policy digest and reports
`STALE_POLICY` separately from `STALE_SUBJECT`: one means the notes moved, the
other means the way we read them did.

Every chunk carries the source id, evidence id, card key and locator it came
from. A chunk without them is a paragraph with a similarity score, and the thing
downstream needs is not the paragraph.
"""

from __future__ import annotations

from typing import Any

from nr_common import (
    FRESHNESS_STATES,
    SHA40,
    ContractError,
    digest,
    exact_object,
    non_empty_str,
    positive_int,
    sha256_ref,
    text_digest,
)

SUBJECT_KEYS = {
    "repository",
    "commit",
    "tree",
    "ref_kind",
    "source_manifest_digest",
    "policy_digest",
}

POLICY_KEYS = {
    "chunk_max_chars",
    "chunk_overlap_chars",
    "embedding_model",
    "embedding_dimensions",
    "provider_id",
    "provider_version",
}

CHUNK_KEYS = {
    "chunk_id",
    "text",
    "source_id",
    "evidence_id",
    "card_key",
    "locator",
    "ordinal",
}


def validate_policy(value: Any, label: str = "policy") -> dict[str, Any]:
    policy = exact_object(value, POLICY_KEYS, label)
    positive_int(policy["chunk_max_chars"], f"{label}.chunk_max_chars")
    overlap = policy["chunk_overlap_chars"]
    if not isinstance(overlap, int) or isinstance(overlap, bool) or overlap < 0:
        raise ContractError(f"{label}.chunk_overlap_chars must be non-negative")
    if overlap >= policy["chunk_max_chars"]:
        raise ContractError(
            f"{label}.chunk_overlap_chars is not smaller than the chunk size; chunks "
            "would contain each other and one paragraph would be retrieved as several"
        )
    non_empty_str(policy["embedding_model"], f"{label}.embedding_model")
    non_empty_str(policy["provider_id"], f"{label}.provider_id")
    non_empty_str(policy["provider_version"], f"{label}.provider_version")
    positive_int(policy["embedding_dimensions"], f"{label}.embedding_dimensions")
    return policy


def policy_digest(policy: dict[str, Any]) -> str:
    return digest(validate_policy(policy))


def validate_subject(value: Any, label: str = "index subject") -> dict[str, Any]:
    subject = exact_object(value, SUBJECT_KEYS, label)
    non_empty_str(subject["repository"], f"{label}.repository")
    for field in ("commit", "tree"):
        if SHA40.fullmatch(str(subject[field])) is None:
            raise ContractError(f"{label}.{field} must be a full 40-hex sha")
    if subject["ref_kind"] != "IMMUTABLE_COMMIT":
        raise ContractError(
            f"{label}.ref_kind must be IMMUTABLE_COMMIT; an index pinned to a branch "
            "keeps answering after the notes it describes have moved"
        )
    sha256_ref(subject["source_manifest_digest"], f"{label}.source_manifest_digest")
    sha256_ref(subject["policy_digest"], f"{label}.policy_digest")
    return subject


def build_subject(
    repository: str,
    commit: str,
    tree: str,
    manifest_digest: str,
    policy: dict[str, Any],
) -> dict[str, Any]:
    return validate_subject(
        {
            "repository": repository,
            "commit": commit,
            "tree": tree,
            "ref_kind": "IMMUTABLE_COMMIT",
            "source_manifest_digest": manifest_digest,
            "policy_digest": policy_digest(policy),
        }
    )


def chunk_text(text: str, policy: dict[str, Any]) -> list[str]:
    """Split deterministically. The same text and policy give the same chunks."""
    validate_policy(policy)
    size = policy["chunk_max_chars"]
    overlap = policy["chunk_overlap_chars"]
    step = size - overlap
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + size])
        start += step
    return chunks or [""]


def build_chunks(
    evidence: list[dict[str, Any]],
    texts: dict[str, str],
    policy: dict[str, Any],
) -> list[dict[str, Any]]:
    """Chunks that keep every identity they came from."""
    validate_policy(policy)
    out: list[dict[str, Any]] = []
    for record in sorted(evidence, key=lambda item: item["evidence_id"]):
        text = texts.get(record["evidence_id"], "")
        for ordinal, piece in enumerate(chunk_text(text, policy)):
            out.append(
                {
                    "chunk_id": "ch-"
                    + digest({"ev": record["evidence_id"], "n": ordinal})[7:23],
                    "text": piece,
                    "source_id": record["source_id"],
                    "evidence_id": record["evidence_id"],
                    "card_key": record.get("card_key"),
                    "locator": record["locator"],
                    "ordinal": ordinal,
                }
            )
    return out


def validate_chunk(value: Any, label: str) -> dict[str, Any]:
    chunk = exact_object(value, CHUNK_KEYS, label)
    non_empty_str(chunk["chunk_id"], f"{label}.chunk_id")
    non_empty_str(chunk["source_id"], f"{label}.source_id")
    non_empty_str(chunk["evidence_id"], f"{label}.evidence_id")
    non_empty_str(chunk["locator"], f"{label}.locator")
    if not isinstance(chunk["ordinal"], int) or chunk["ordinal"] < 0:
        raise ContractError(f"{label}.ordinal must be a non-negative integer")
    if not isinstance(chunk["text"], str):
        raise ContractError(f"{label}.text must be a string")
    return chunk


def check_freshness(
    index_subject: dict[str, Any] | None, current_subject: dict[str, Any]
) -> dict[str, Any]:
    """Is this index still about the notes as they are?

    Subject drift and policy drift are reported separately. They are both
    "stale", and they mean different things: one says the notes moved, the other
    says the way we read them did -- and the second is the one that returns
    confident nonsense rather than nothing.
    """
    validate_subject(current_subject)
    if index_subject is None:
        return {"state": "NOT_BUILT", "reason": "no index has been built"}
    validate_subject(index_subject, "stored index subject")

    if (
        index_subject["commit"] != current_subject["commit"]
        or index_subject["tree"] != current_subject["tree"]
        or index_subject["source_manifest_digest"]
        != current_subject["source_manifest_digest"]
    ):
        return {
            "state": "STALE_SUBJECT",
            "reason": (
                f"the index was built at {index_subject['commit'][:8]} and the notes "
                f"are at {current_subject['commit'][:8]}; answers describe the older "
                "tree and nothing in them says so"
            ),
        }
    if index_subject["policy_digest"] != current_subject["policy_digest"]:
        return {
            "state": "STALE_POLICY",
            "reason": (
                "the chunk or embedding policy changed. An index built with one "
                "embedding model and queried with another does not error -- it "
                "returns neighbours, and they are meaningless"
            ),
        }
    return {"state": "CURRENT", "reason": "subject and policy both match"}


def freshness_state(value: str) -> str:
    if value not in FRESHNESS_STATES:
        raise ContractError(f"unknown freshness state {value!r}")
    return value


def coverage(
    chunks: list[dict[str, Any]], evidence: list[dict[str, Any]]
) -> dict[str, Any]:
    """What is in the index, and what is not. Uncovered evidence is UNKNOWN."""
    indexed = {chunk["evidence_id"] for chunk in chunks}
    declared = {record["evidence_id"] for record in evidence}
    uncovered = sorted(declared - indexed)
    return {
        "evidence_declared": len(declared),
        "evidence_indexed": len(indexed & declared),
        "uncovered_evidence_ids": uncovered,
        # Named rather than implied. A query about uncovered evidence returns
        # nothing, and without this field that reads as the notes being silent.
        "uncovered_state": "UNKNOWN",
        "chunk_count": len(chunks),
        "content_digest": text_digest(
            "".join(sorted(chunk["chunk_id"] for chunk in chunks)).encode("utf-8")
        ),
    }
