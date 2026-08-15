#!/usr/bin/env python3
"""The evidence manifest, and the identity that keeps a repost from counting twice.

An evidence id is derived from the artifact digest and the *position inside it*
-- not from the URL it arrived through. A mirror, a repost with a new address,
the same recording uploaded twice: all of them collapse to one record, because
the bytes and the offset are the same. Keying on the URL would have let each
repost become a second source, and two copies of one upload look like
corroboration.

The manifest is pinned to a Notes Repo commit and tree. That is the immutable
compilation subject: everything downstream cites this manifest, and a manifest
whose subject was a branch would describe a different tree tomorrow.
"""

from __future__ import annotations

from typing import Any

from si_capture import bears_evidence, gaps
from si_common import (
    SHA40,
    ADMISSIBLE_ORIGIN,
    ContractError,
    require_read_origin,
    digest,
    exact_object,
    iso_timestamp,
    non_empty_str,
    require,
    sha256_ref,
    SOURCE_TYPES,
)

MANIFEST_SCHEMA = "loopx/source-evidence-manifest/v1"

SUBJECT_KEYS = {"repository", "commit", "tree", "ref_kind"}

EVIDENCE_KEYS = {
    "evidence_id",
    "source_id",
    "source_type",
    "artifact_digest",
    "locator",
    "locator_origin",
    "dependency_key",
    "quote_digest",
}


def locator_fragment(locator: str) -> str:
    """The part of a locator that says *where in the artifact*.

    Split from the origin deliberately. The same recording reposted to a mirror
    has a different URL and identical bytes, and it is one piece of evidence --
    so identity is the artifact plus the position inside it, and the full
    locator is kept alongside to say where this copy was obtained.
    """
    return locator.split("#", 1)[1] if "#" in locator else ""


def evidence_id(artifact_digest: str, locator: str) -> str:
    """Derived, so the same bytes at the same place are one piece of evidence.

    Keyed on the artifact digest and the position inside it, not on the URL: a
    repost with a new address is the same evidence, and counting it twice raises
    a confidence ceiling on one upload.
    """
    return (
        "ev-"
        + digest({"artifact": artifact_digest, "at": locator_fragment(locator)})[7:23]
    )


def validate_subject(value: Any) -> dict[str, Any]:
    subject = exact_object(value, SUBJECT_KEYS, "notes subject")
    non_empty_str(subject["repository"], "subject.repository")
    for field in ("commit", "tree"):
        if SHA40.fullmatch(str(subject[field])) is None:
            raise ContractError(f"subject.{field} must be a full 40-hex sha")
    if subject["ref_kind"] != "IMMUTABLE_COMMIT":
        raise ContractError(
            "subject.ref_kind must be IMMUTABLE_COMMIT; a manifest pinned to a branch "
            "describes a different tree tomorrow, and everything citing it moves with it"
        )
    return subject


def build_evidence(
    capture: dict[str, Any], locator: str, quote: str, origin: str
) -> dict[str, Any]:
    """One evidence record. Refuses without captured bytes or a read locator."""
    if not bears_evidence(capture):
        raise ContractError(
            f"source {capture['source_id']} is {capture['state']} and carries no bytes; "
            f"an evidence record built on it would cite something nobody captured "
            f"({capture['reason']})"
        )
    # The shared check, rather than a second copy of the same rule. There were
    # two: one here and one in si_common, and only this one was ever called --
    # so the other was a rule nobody could reach and nobody would notice going
    # stale.
    require_read_origin(origin, "evidence locator_origin")
    non_empty_str(locator, "locator")
    non_empty_str(quote, "quote")
    if capture["source_type"] not in SOURCE_TYPES:
        raise ContractError(f"unknown source type {capture['source_type']!r}")

    return {
        "evidence_id": evidence_id(capture["artifact_digest"], locator),
        "source_id": capture["source_id"],
        "source_type": capture["source_type"],
        "artifact_digest": capture["artifact_digest"],
        "locator": locator,
        "locator_origin": origin,
        "dependency_key": capture["dependency_key"],
        # The quote is digested rather than stored: the manifest cites, and the
        # artifact holds the text. Two copies of a quote drift.
        "quote_digest": digest(quote),
    }


def build_manifest(
    subject: dict[str, Any],
    captures: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    injection_findings: dict[str, list[dict[str, Any]]],
    at: str,
) -> dict[str, Any]:
    validate_subject(subject)
    iso_timestamp(at, "manifest.at")

    seen: dict[str, dict[str, Any]] = {}
    duplicates = []
    for index, record in enumerate(evidence):
        checked = exact_object(record, EVIDENCE_KEYS, f"evidence[{index}]")
        sha256_ref(checked["artifact_digest"], f"evidence[{index}].artifact_digest")
        existing = seen.get(checked["evidence_id"])
        if existing is not None:
            # Same bytes, same locator: one piece of evidence that arrived twice.
            # Counted once and recorded as a duplicate rather than dropped, so a
            # reader can see the repost happened.
            duplicates.append(
                {
                    "evidence_id": checked["evidence_id"],
                    "source_ids": sorted({existing["source_id"], checked["source_id"]}),
                    "dependency_key": checked["dependency_key"],
                }
            )
            continue
        seen[checked["evidence_id"]] = checked

    unique = sorted(seen.values(), key=lambda record: record["evidence_id"])

    # Independent support is counted by dependency key, never by record count.
    keys = sorted({record["dependency_key"] for record in unique})

    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "notes_subject": subject,
        "evidence": unique,
        "evidence_count": len(unique),
        "duplicates": sorted(duplicates, key=lambda entry: entry["evidence_id"]),
        "independent_dependency_keys": keys,
        "independent_source_count": len(keys),
        "gaps": gaps(captures),
        "injection_findings": {
            source_id: findings
            for source_id, findings in sorted(injection_findings.items())
            if findings
        },
        "compiled_at": at,
        "state": "READY_FOR_KNOWLEDGE_COMPILATION" if unique else "NO_EVIDENCE",
        "authority": "EVIDENCE_INVENTORY_ONLY",
    }
    manifest["manifest_digest"] = digest(
        {k: v for k, v in manifest.items() if k != "manifest_digest"}
    )
    require(True, "")
    return manifest


def validate_manifest(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema_version") != MANIFEST_SCHEMA:
        raise ContractError("manifest schema version drifted")
    validate_subject(value.get("notes_subject", {}))
    if value.get("authority") != "EVIDENCE_INVENTORY_ONLY":
        raise ContractError(
            "the manifest claims more than an inventory; it lists what was captured "
            "and where, and it decides nothing about what any of it means"
        )

    ids = [record["evidence_id"] for record in value.get("evidence", [])]
    if len(ids) != len(set(ids)):
        raise ContractError(
            "the manifest carries duplicate evidence ids; the same bytes at the same "
            "locator counted twice raises a confidence ceiling on one artifact"
        )
    for record in value.get("evidence", []):
        expected = evidence_id(record["artifact_digest"], record["locator"])
        if record["evidence_id"] != expected:
            raise ContractError(
                f"evidence {record['evidence_id']!r} does not derive from its artifact "
                "and locator; an allocated id lets a repost become a second source"
            )
        if record["locator_origin"] != ADMISSIBLE_ORIGIN:
            raise ContractError(
                f"evidence {record['evidence_id']!r} has a {record['locator_origin']} "
                "locator in the manifest"
            )

    recomputed = digest({k: v for k, v in value.items() if k != "manifest_digest"})
    if value.get("manifest_digest") != recomputed:
        raise ContractError("manifest digest does not match its content")
    return value
