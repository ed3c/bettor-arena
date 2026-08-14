#!/usr/bin/env python3
"""Layer 1 -- source manifest. Where a claim came from, and what it weighs.

Two failures live here, and both are quiet.

The first is a source with no locator acquiring metadata anyway. A path, a
timestamp or a version that nobody read out of the source is a fabrication with
a citation attached, and it reads downstream exactly like a real one.

The second is corroboration counted twice. Three notes files quoting the same
upstream RFC are one piece of evidence, not three -- but a naive count says
three and the confidence ceiling rises on nothing. That is why every source
carries a `dependency_key`: independence is declared and checked, not inferred
from how many rows exist.
"""

from __future__ import annotations

from typing import Any

from kc_common import (
    LOCATOR,
    ContractError,
    exact_object,
    iso_timestamp,
    non_empty_str,
    require,
    sha256_ref,
    validate_notes_subject,
)

SOURCE_KEYS = {
    "source_id",
    "kind",
    "locator",
    "dependency_key",
    "byte_digest",
    "recorded_at",
    "declared_version",
}

SOURCE_KINDS = {"NOTE", "TRANSCRIPT", "DIAGRAM", "SOURCE_CODE", "EXTERNAL_DOC"}

MANIFEST_KEYS = {"schema_version", "notes_subject", "sources", "compiler_identity"}


def validate_source(value: Any, label: str) -> dict[str, Any]:
    source = exact_object(value, SOURCE_KEYS, label)
    non_empty_str(source["source_id"], f"{label}.source_id")
    if source["kind"] not in SOURCE_KINDS:
        raise ContractError(
            f"{label}.kind must be one of {sorted(SOURCE_KINDS)}, got "
            f"{source['kind']!r}"
        )

    locator = source["locator"]
    if locator is not None and (
        not isinstance(locator, str) or LOCATOR.fullmatch(locator) is None
    ):
        raise ContractError(
            f"{label}.locator must be <path>#L<start>[-L<end>] or null; a source "
            "named without a position cannot be checked by anyone else"
        )

    # The control the issue names: no locator, yet metadata appears. If nobody
    # can point at where in the source it was read, it was not read.
    if locator is None:
        for field in ("byte_digest", "recorded_at", "declared_version"):
            if source[field] is not None:
                raise ContractError(
                    f"{label} has no locator but carries {field}={source[field]!r}; "
                    "metadata attached to an unlocatable source is fabricated, and "
                    "downstream it is indistinguishable from metadata that was read"
                )
    else:
        sha256_ref(source["byte_digest"], f"{label}.byte_digest")
        iso_timestamp(source["recorded_at"], f"{label}.recorded_at")
        non_empty_str(source["declared_version"], f"{label}.declared_version")

    non_empty_str(source["dependency_key"], f"{label}.dependency_key")
    return source


def validate_manifest(value: Any) -> dict[str, Any]:
    manifest = exact_object(value, MANIFEST_KEYS, "source manifest")
    require(
        manifest["schema_version"] == "loopx/knowledge-source-manifest/v1",
        "source manifest schema version drifted",
    )
    validate_notes_subject(manifest["notes_subject"])
    non_empty_str(manifest["compiler_identity"], "source manifest.compiler_identity")

    sources = manifest["sources"]
    if not isinstance(sources, list) or not sources:
        raise ContractError("source manifest.sources must be a non-empty list")

    seen: set[str] = set()
    for index, source in enumerate(sources):
        validated = validate_source(source, f"sources[{index}]")
        if validated["source_id"] in seen:
            raise ContractError(
                f"duplicate source_id {validated['source_id']!r}; the same source "
                "listed twice is the cheapest way to double a confidence count"
            )
        seen.add(validated["source_id"])

    if sources != sorted(sources, key=lambda s: s["source_id"]):
        raise ContractError(
            "source manifest.sources must be sorted by source_id; unsorted input "
            "makes two identical manifests digest differently"
        )
    return manifest


def independent_support(sources: list[dict[str, Any]]) -> list[str]:
    """Distinct dependency keys, sorted.

    This is the answer to "how many independent sources back this?" -- not
    `len(sources)`. Two notes quoting one upstream document share a dependency
    key and count once.
    """
    return sorted({source["dependency_key"] for source in sources})


def corroboration_count(sources: list[dict[str, Any]]) -> int:
    return len(independent_support(sources))
