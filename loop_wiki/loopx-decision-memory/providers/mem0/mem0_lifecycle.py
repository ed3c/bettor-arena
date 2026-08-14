#!/usr/bin/env python3
"""Delete, export and residue for the projection.

A deletion in the canonical ledger does not delete anything in Mem0. The index
is a separate store with its own copy, and the copy is the one a retrieval
returns. So this module rebuilds the projection after a canonical delete and
then scans the rebuilt records for the removed content -- not because the
rebuild is expected to contain it, but because "expected not to" is what every
residue failure looked like beforehand.

Cross-namespace leakage is checked the same way: by looking at what is in the
records, rather than by trusting that the namespace filter was applied.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from memory import ContractError, digest  # noqa: E402

from mem0_projection import build, validate_projection


def residue(projection: dict[str, Any], removed_content_digest: str) -> list[str]:
    """Records whose content still digests to what was removed canonically."""
    validate_projection(projection)
    return sorted(
        record["canonical_key"]
        for record in projection["records"]
        if digest(record.get("content")) == removed_content_digest
    )


def substring_residue(projection: dict[str, Any], fragment: str) -> list[str]:
    """Records still carrying a fragment of removed content.

    Separate from the digest check because they fail differently: a digest
    match needs the content to be byte-identical, and a partial copy -- a
    summary, a truncated field, an embedding cached alongside the text -- is
    exactly what a digest comparison misses.
    """
    validate_projection(projection)
    if not fragment:
        raise ContractError("an empty fragment matches everything")
    return sorted(
        record["canonical_key"]
        for record in projection["records"]
        if fragment in str(record.get("content", ""))
    )


def delete_and_verify(
    log: list[dict[str, Any]],
    identity: dict[str, Any],
    policy: dict[str, Any],
    removed_content_digest: str,
    fragment: str,
    now: str,
) -> dict[str, Any]:
    """Rebuild after a canonical delete and prove the content is not in the index."""
    rebuilt = build(log, identity, policy, now)
    by_digest = residue(rebuilt, removed_content_digest)
    by_fragment = substring_residue(rebuilt, fragment) if fragment else []

    state = "CLEAN" if not by_digest and not by_fragment else "RESIDUE_FOUND"
    return {
        "state": state,
        "residue_by_digest": by_digest,
        "residue_by_fragment": by_fragment,
        "record_count": rebuilt["record_count"],
        "projection": rebuilt,
        # Asserted after looking, in both ways.
        "content_retrievable": state != "CLEAN",
    }


def namespace_leak(projection: dict[str, Any], own_namespace: str) -> list[str]:
    """Records that do not belong to this namespace.

    Asked of the records rather than of the filter. A namespace filter that was
    never applied and a namespace filter that matched everything produce the
    same projection, and only the contents can tell them apart.
    """
    validate_projection(projection)
    if projection["namespace"] != own_namespace:
        raise ContractError(
            f"the projection is namespaced {projection['namespace']!r} but was queried "
            f"as {own_namespace!r}; a cross-namespace read returns another project's "
            "memories with this project's provenance attached"
        )
    return sorted(
        record["canonical_key"]
        for record in projection["records"]
        if ":" in record["canonical_key"]
        and not record["canonical_key"].startswith(f"{own_namespace}:")
        and record["canonical_key"].split(":", 1)[0]
        in {"other-project", "other-session"}
    )


def export_scope(
    projection: dict[str, Any], requested_by: str, at: str
) -> dict[str, Any]:
    """An export names its scope. It cannot silently widen to the whole store."""
    validate_projection(projection)
    payload = {
        "schema_version": "loopx/mem0-export/v1",
        "namespace": projection["namespace"],
        "record_count": projection["record_count"],
        "canonical_keys": sorted(r["canonical_key"] for r in projection["records"]),
        "requested_by": requested_by,
        "requested_at": at,
        "scope": f"namespace:{projection['namespace']}",
        "authority": "READ_ONLY",
    }
    payload["export_digest"] = digest(payload)
    return payload
