#!/usr/bin/env python3
"""The Mem0 projection: an index built from admitted events, and nothing else.

Mem0 is a cache with a query language. It is not canonical memory, not
repository authority, and not a writeback channel. Everything in this file
follows from that:

`build` takes the LoopX event log and a redaction policy. It does not take a
previous projection, so a projection can never be built from itself and drift
away from the events. `rebuild_equivalent` compares a fresh build against a
stored one on **relations**, not on bytes: a vector store legitimately assigns
different internal ids on each build, and a byte comparison would report every
correct rebuild as a mismatch until someone disabled the check.

The retrieval path returns provenance with every hit and refuses to answer at
all when the provider is unavailable -- an empty result list from a store that
is down looks exactly like an empty result list from a store with nothing to
say.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "runtime"))

from memory import ContractError, digest  # noqa: E402

from dmr_event import validate_event  # noqa: E402
from mem0_identity import provider_state, validate_identity

PROJECTION_SCHEMA = "loopx/mem0-projection/v1"

# Fields a projected record may carry. `content` is here; raw source blobs,
# page bodies and reasoning traces are not, and there is no field for them.
PROJECTED_FIELDS = (
    "memory_id",
    "canonical_key",
    "content",
    "evidence_refs",
    "expires_at",
    "source_event_id",
)


def redact(record: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    """Apply the pinned redaction policy. Drops only; never adds."""
    dropped = sorted(set(policy.get("drop_fields", [])) & set(record))
    out = {k: v for k, v in record.items() if k not in dropped}
    return out


def build(
    log: list[dict[str, Any]],
    identity: dict[str, Any],
    policy: dict[str, Any],
    now: str,
) -> dict[str, Any]:
    """Build the projection from admitted events. Takes no prior projection."""
    validate_identity(identity)
    if not isinstance(policy, dict) or "policy_digest" not in policy:
        raise ContractError(
            "the redaction policy must carry its own digest; a projection built under "
            "an unrecorded policy cannot be compared with one built under another"
        )

    for index, event in enumerate(log):
        validate_event(event, f"log[{index}]")

    active: dict[str, dict[str, Any]] = {}
    for event in log:
        key = event["canonical_key"]
        if event["state"] == "ACTIVE":
            active[key] = event
        else:
            active.pop(key, None)

    records = []
    for key, event in sorted(active.items()):
        record = {field: event.get(field) for field in PROJECTED_FIELDS}
        record["canonical_key"] = key
        record["source_event_id"] = event["event_id"]
        records.append(redact(record, policy))

    projection = {
        "schema_version": PROJECTION_SCHEMA,
        "identity": identity,
        "policy_digest": policy["policy_digest"],
        "namespace": identity["namespace"],
        "records": records,
        "record_count": len(records),
        "source_event_digests": sorted(event["event_id"] for event in log),
        "built_at": now,
        # Said where it is read.
        "canonical": False,
        "canonical_source": "LOOPX_LEDGER_EVENTS",
        "authority": "PROJECTION_ONLY",
    }
    projection["relation_digest"] = relation_digest(projection)
    return projection


def relation_digest(projection: dict[str, Any]) -> str:
    """A digest over what the projection *means*, not over how it was stored.

    Internal ids, insertion order and vector layout are excluded deliberately.
    A vector store assigns different internal ids on each build, so a digest
    over them would report every correct rebuild as a mismatch -- and the first
    fix anyone reaches for is to stop checking.
    """
    return digest(
        {
            "namespace": projection["namespace"],
            "policy_digest": projection["policy_digest"],
            "records": sorted(
                (
                    {
                        "canonical_key": record["canonical_key"],
                        "content": record.get("content"),
                        "source_event_id": record.get("source_event_id"),
                    }
                    for record in projection["records"]
                ),
                key=lambda entry: entry["canonical_key"],
            ),
        }
    )


def validate_projection(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema_version") != PROJECTION_SCHEMA:
        raise ContractError("projection schema version drifted")
    if value.get("canonical") is not False:
        raise ContractError(
            "the Mem0 projection claims to be canonical; it is an index over events a "
            "human admitted, and promoting it makes the vector store the record"
        )
    if value.get("authority") != "PROJECTION_ONLY":
        raise ContractError("projection authority drifted")
    if value.get("canonical_source") != "LOOPX_LEDGER_EVENTS":
        raise ContractError("projection canonical source drifted from the ledger")
    if value.get("relation_digest") != relation_digest(value):
        raise ContractError("the relation digest does not match the records")
    validate_identity(value.get("identity", {}))
    return value


def rebuild_equivalent(
    log: list[dict[str, Any]],
    stored: dict[str, Any],
    policy: dict[str, Any],
    now: str,
) -> dict[str, Any]:
    """Rebuild from events and compare relations. Reports, never repairs."""
    validate_projection(stored)
    fresh = build(log, stored["identity"], policy, now)
    same = fresh["relation_digest"] == stored["relation_digest"]
    return {
        "equivalent": same,
        "stored_relation_digest": stored["relation_digest"],
        "rebuilt_relation_digest": fresh["relation_digest"],
        "comparison": "RELATION_EQUIVALENT",
        # Stated so a reader does not conclude the bytes matched.
        "note": (
            "compared on relations rather than bytes: a vector store assigns "
            "different internal ids on each build, and a byte comparison would fail "
            "on every correct rebuild"
        ),
    }


def query(
    projection: dict[str, Any],
    term: str,
    availability: str,
) -> dict[str, Any]:
    """Read-only retrieval. Refuses to answer when the provider is unavailable."""
    validate_projection(projection)
    provider_state(availability, "provider availability")

    if availability != "AVAILABLE":
        # Not an empty result. An empty list from a store that is down looks
        # exactly like an empty list from a store with nothing to say.
        return {
            "state": "PROVIDER_UNAVAILABLE",
            "hits": [],
            "reason": (
                f"the provider is {availability}; a query that never reached the index "
                "found nothing because it did not look, which is not the same as the "
                "index having nothing"
            ),
            "authority": "PROJECTION_ONLY",
        }

    hits = [
        {
            "canonical_key": record["canonical_key"],
            "content": record.get("content"),
            "provenance": {
                "namespace": projection["namespace"],
                "source_event_id": record.get("source_event_id"),
                "built_at": projection["built_at"],
                "policy_digest": projection["policy_digest"],
                "mode": projection["identity"]["mode"],
            },
        }
        for record in projection["records"]
        if term.lower() in str(record.get("content", "")).lower()
    ]
    return {
        "state": "ANSWERED",
        "hits": sorted(hits, key=lambda hit: hit["canonical_key"]),
        "reason": f"{len(hits)} hit(s) in namespace {projection['namespace']}",
        # On every answer, because this is where someone forms the impression.
        "authority": "PROJECTION_ONLY",
    }
