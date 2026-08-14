#!/usr/bin/env python3
"""Contract manifest for the memory runtime.

The runtime adds three schemas to the four this module already had. The four are
not re-validated here -- `memory.py check` already does that, and a second
validator is a second thing to keep in step.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from memory import ContractError, load  # noqa: E402

from dmr_authority import LADDER
from dmr_event import EVENT_KINDS, MEMORY_STATES, WRITER

MANIFEST_KEYS = {
    "schema_version",
    "interface_version",
    "requires_capabilities",
    "event_kinds",
    "memory_states",
    "authority_ladder",
    "canonical_writer",
    "projection_is_canonical",
    "mem0_required",
    "delete_preserves_history",
    "schemas",
}

SCHEMA_VERSIONS = {
    "memory-event.schema.json": "loopx/memory-event/v1",
    "memory-projection.schema.json": "loopx/memory-projection/v1",
    "memory-tombstone.schema.json": "loopx/memory-tombstone/v1",
}


def exact(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    if set(value) != keys:
        raise ContractError(
            f"{label} fields drifted; missing={sorted(keys - set(value))}, "
            f"extra={sorted(set(value) - keys)}"
        )
    return value


def validate_manifest(root: Path, override: Any | None = None) -> dict[str, Any]:
    contracts = root / "runtime" / "contracts"
    loaded = load(contracts / "manifest.json") if override is None else override
    manifest = exact(loaded, MANIFEST_KEYS, "manifest")

    if manifest["schema_version"] != "loopx/memory-runtime-contract-manifest/v1":
        raise ContractError("manifest schema version drifted")
    if manifest["interface_version"] != "1.0.0":
        raise ContractError("manifest interface version drifted")
    if manifest["requires_capabilities"] != [
        "arena.proof-kernel/v1",
        "loopx.decision-memory/v1",
        "loopx.ledger/v1",
    ]:
        raise ContractError("manifest capability dependencies drifted")

    if manifest["event_kinds"] != sorted(EVENT_KINDS):
        raise ContractError("event kinds drifted from the implementation")
    if manifest["memory_states"] != sorted(MEMORY_STATES):
        raise ContractError("memory states drifted from the implementation")
    if manifest["authority_ladder"] != list(LADDER):
        raise ContractError("the authority ladder drifted from the implementation")
    if manifest["authority_ladder"][-1] != "MEMORY":
        raise ContractError(
            "MEMORY must be the lowest rung; a memory that outranks source is a "
            "six-month-old conclusion overriding the code as it is now"
        )
    if manifest["canonical_writer"] != WRITER:
        raise ContractError("canonical writer drifted from the reducer")
    if manifest["projection_is_canonical"] is not False:
        raise ContractError(
            "a projection promoted to canonical is a cache that can no longer be "
            "deleted without losing something"
        )
    if manifest["mem0_required"] is not False:
        raise ContractError(
            "Mem0 may not be required; canonical memory is a ledger event and the "
            "vector store is a later optional projection"
        )
    if manifest["delete_preserves_history"] is not True:
        raise ContractError(
            "a delete that does not preserve history erases the audit trail, and the "
            "next person finds a memory that never existed"
        )

    entries = manifest["schemas"]
    if not isinstance(entries, list) or len(entries) != len(SCHEMA_VERSIONS):
        raise ContractError(f"manifest must enumerate {len(SCHEMA_VERSIONS)} schemas")
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        entry = exact(entry, {"id", "path", "sha256"}, f"manifest.schemas[{index}]")
        name = entry["path"]
        if name in seen or name not in SCHEMA_VERSIONS:
            raise ContractError(f"unexpected or duplicate schema: {name}")
        seen.add(name)
        raw = (contracts / name).read_bytes()
        if entry["sha256"] != hashlib.sha256(raw).hexdigest():
            raise ContractError(f"schema digest drifted: {name}")
        schema = json.loads(raw)
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise ContractError(f"schema dialect drifted: {name}")
        if schema.get("$id") != entry["id"]:
            raise ContractError(f"schema identity drifted: {name}")
        if (
            schema.get("type") != "object"
            or schema.get("additionalProperties") is not False
        ):
            raise ContractError(f"schema must fail closed: {name}")
        const = schema.get("properties", {}).get("schema_version", {}).get("const")
        if const != SCHEMA_VERSIONS[name]:
            raise ContractError(f"schema version constant drifted: {name}")
    if seen != set(SCHEMA_VERSIONS):
        raise ContractError("schema coverage drifted")
    return manifest


def check_contracts(root: Path) -> tuple[int, int]:
    validate_manifest(root)
    return len(SCHEMA_VERSIONS), len(sorted((root / "contracts").glob("*.json")))


def run_contract_selftest(root: Path) -> int:
    manifest = load(root / "runtime" / "contracts" / "manifest.json")
    mutations = [
        ("schema digest", lambda m: m["schemas"][0].__setitem__("sha256", "0" * 64)),
        (
            "memory promoted above source",
            lambda m: m.__setitem__("authority_ladder", ["MEMORY", *LADDER[:-1]]),
        ),
        (
            "projection made canonical",
            lambda m: m.__setitem__("projection_is_canonical", True),
        ),
        ("mem0 required", lambda m: m.__setitem__("mem0_required", True)),
        (
            "delete stops preserving history",
            lambda m: m.__setitem__("delete_preserves_history", False),
        ),
        ("writer changed", lambda m: m.__setitem__("canonical_writer", "AGENT")),
        (
            "event kind dropped",
            lambda m: m.__setitem__("event_kinds", ["MEMORY_ADMITTED"]),
        ),
        ("memory state dropped", lambda m: m.__setitem__("memory_states", ["ACTIVE"])),
    ]
    for name, mutate in mutations:
        mutated = copy.deepcopy(manifest)
        mutate(mutated)
        try:
            validate_manifest(root, mutated)
        except ContractError:
            continue
        raise ContractError(f"manifest mutation survived: {name}")
    return len(mutations)
