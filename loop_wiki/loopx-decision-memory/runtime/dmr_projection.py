#!/usr/bin/env python3
"""Projections rebuilt from the ledger, and a capsule with a bounded size.

A projection is a cache. Deleting one costs a rebuild; treating one as canonical
costs the ability to say what was actually admitted. So `rebuild` takes only the
event log, `project` never accepts a projection as an input to itself, and every
projection carries `canonical: false` where a reader will see it.

Mem0 is not imported, referenced or required. A projection built here is a plain
dictionary; whether anyone loads it into a vector store later is that leaf's
problem, and this module works with none.

The capsule is bounded because an unbounded handoff is the shape that quietly
consumes the context window it was meant to save. When the budget runs out the
capsule says how many memories it dropped -- a truncated capsule that looked
complete would let a reader conclude a memory does not exist.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from memory import ContractError, digest  # noqa: E402

from dmr_event import validate_event

PROJECTION_SCHEMA = "loopx/memory-projection/v1"
CAPSULE_SCHEMA = "loopx/memory-handoff-capsule/v1"

# Ordered so the same log always yields the same capsule.
CLASS_PRIORITY = ("INCIDENT_POINTER", "DECISION", "DEAD_END", "QUIRK", "HYPOTHESIS")


def rebuild(log: list[dict[str, Any]]) -> dict[str, Any]:
    """The active memory set, derived from events alone."""
    for index, event in enumerate(log):
        validate_event(event, f"log[{index}]")

    active: dict[str, dict[str, Any]] = {}
    for event in log:
        key = event["canonical_key"]
        if event["state"] == "ACTIVE":
            active[key] = event
        else:
            active.pop(key, None)

    entries = [
        {
            "memory_id": event["memory_id"],
            "canonical_key": key,
            "revision": event["revision"],
            "content": event["content"],
            "evidence_refs": event["evidence_refs"],
            "falsifier": event["falsifier"],
            "validity_scope": event["validity_scope"],
            "expires_at": event["expires_at"],
            "source_event_id": event["event_id"],
        }
        for key, event in sorted(active.items())
    ]
    projection = {
        "schema_version": PROJECTION_SCHEMA,
        "entries": entries,
        "entry_count": len(entries),
        "source_event_count": len(log),
        # Where a reader sees it, not in a document they would have to consult.
        "canonical": False,
        "canonical_source": "LOOPX_LEDGER_EVENTS",
        "rebuildable": True,
    }
    projection["projection_digest"] = digest(
        {k: v for k, v in projection.items() if k != "projection_digest"}
    )
    return projection


def validate_projection(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("projection must be an object")
    if value.get("schema_version") != PROJECTION_SCHEMA:
        raise ContractError("projection schema version drifted")
    if value.get("canonical") is not False:
        raise ContractError(
            "a projection claiming to be canonical is a cache that has been promoted "
            "to a source of truth; deleting it would then destroy something instead "
            "of costing a rebuild"
        )
    if value.get("canonical_source") != "LOOPX_LEDGER_EVENTS":
        raise ContractError("projection canonical source drifted from the ledger")
    recomputed = digest({k: v for k, v in value.items() if k != "projection_digest"})
    if value.get("projection_digest") != recomputed:
        raise ContractError("projection digest does not match its content")
    return value


def rebuild_matches(log: list[dict[str, Any]], stored: dict[str, Any]) -> bool:
    """Does the stored projection match one rebuilt from the log right now?"""
    validate_projection(stored)
    return rebuild(log)["projection_digest"] == stored["projection_digest"]


def render_capsule(
    projection: dict[str, Any],
    scope: str,
    max_bytes: int,
    kinds: dict[str, str] | None = None,
) -> dict[str, Any]:
    """A bounded handoff capsule. Says what it dropped."""
    validate_projection(projection)
    if not isinstance(max_bytes, int) or max_bytes < 256:
        raise ContractError("capsule max_bytes must be at least 256")

    kinds = kinds or {}
    # `validity_scope` is the proposal's scope object: a commit it is valid
    # from, the paths it covers and what invalidates it. Scope matching is on
    # the commit, because a memory recorded against one tree does not
    # automatically describe another -- matching on a name would have let any
    # scope string through.
    in_scope = [
        entry
        for entry in projection["entries"]
        if entry["validity_scope"]["valid_from_commit"] == scope
    ]
    out_of_scope = len(projection["entries"]) - len(in_scope)

    ordered = sorted(
        in_scope,
        key=lambda entry: (
            CLASS_PRIORITY.index(kinds.get(entry["canonical_key"], "HYPOTHESIS"))
            if kinds.get(entry["canonical_key"], "HYPOTHESIS") in CLASS_PRIORITY
            else len(CLASS_PRIORITY),
            entry["canonical_key"],
        ),
    )

    included: list[dict[str, Any]] = []
    used = 0
    dropped = 0
    for entry in ordered:
        line = {
            "canonical_key": entry["canonical_key"],
            "content": entry["content"],
            "falsifier": entry["falsifier"],
            "evidence_refs": entry["evidence_refs"],
        }
        size = len(digest(line)) + len(str(line))
        if used + size > max_bytes:
            dropped += 1
            continue
        included.append(line)
        used += size

    capsule = {
        "schema_version": CAPSULE_SCHEMA,
        "scope": scope,
        "entries": included,
        "included_count": len(included),
        # Both numbers, always. A truncated capsule that looked complete would
        # let a reader conclude a memory does not exist.
        "dropped_for_budget": dropped,
        "out_of_scope": out_of_scope,
        "max_bytes": max_bytes,
        "approx_bytes": used,
        "complete": dropped == 0,
        "canonical": False,
    }
    capsule["capsule_digest"] = digest(
        {k: v for k, v in capsule.items() if k != "capsule_digest"}
    )
    return capsule


def validate_capsule_bounds(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema_version") != CAPSULE_SCHEMA:
        raise ContractError("capsule schema version drifted")
    if value["approx_bytes"] > value["max_bytes"]:
        raise ContractError(
            f"the capsule is {value['approx_bytes']} bytes against a {value['max_bytes']} "
            "budget; an unbounded handoff consumes the context window it was meant "
            "to save"
        )
    if value["dropped_for_budget"] > 0 and value["complete"]:
        raise ContractError(
            "a capsule that dropped entries reported itself complete; a reader would "
            "conclude the missing memories do not exist"
        )
    if value.get("canonical") is not False:
        raise ContractError("a capsule claiming to be canonical is a cache promoted")
    return value


def cross_scope_leak(capsule: dict[str, Any], foreign_scopes: set[str]) -> list[str]:
    """Canonical keys in the capsule that belong to another project or session."""
    return sorted(
        entry["canonical_key"]
        for entry in capsule["entries"]
        if any(
            entry["canonical_key"].startswith(f"{scope}:") for scope in foreign_scopes
        )
    )
