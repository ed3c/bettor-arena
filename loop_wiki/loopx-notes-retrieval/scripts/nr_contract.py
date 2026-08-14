#!/usr/bin/env python3
"""Schema identity, digest and vocabulary checks for the notes-retrieval contracts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from nr_common import (
    FINAL_AUTHORITY,
    FRESHNESS_STATES,
    PROJECTION_ROLES,
    RETRIEVAL_STATES,
    ContractError,
    InputError,
    load_json,
)

MANIFEST_KEYS = {
    "schema_version",
    "interface_version",
    "requires_capabilities",
    "retrieval_states",
    "freshness_states",
    "projection_roles",
    "final_authority",
    "any_state_proves_absence",
    "openwiki_admissible_as_evidence",
    "retrieval_hit_is_a_fact",
    "live_provider_state",
    "schemas",
}

SCHEMA_VERSIONS = {
    "index-subject.schema.json": "loopx/notes-index-subject/v1",
    "openwiki-projection.schema.json": "loopx/openwiki-projection/v1",
    "retrieval-result.schema.json": "loopx/notes-retrieval-result/v1",
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
    contracts = root / "contracts"
    loaded = load_json(contracts / "manifest.json") if override is None else override
    manifest = exact(loaded, MANIFEST_KEYS, "manifest")

    if manifest["schema_version"] != "loopx/notes-retrieval-contract-manifest/v1":
        raise ContractError("manifest schema version drifted")
    if manifest["interface_version"] != "1.0.0":
        raise ContractError("manifest interface version drifted")
    if manifest["requires_capabilities"] != [
        "arena.proof-kernel/v1",
        "loopx.contracts/v1",
        "loopx.source-ingest/v1",
    ]:
        raise ContractError("manifest capability dependencies drifted")

    if manifest["retrieval_states"] != sorted(RETRIEVAL_STATES):
        raise ContractError("retrieval states drifted from the implementation")
    if manifest["freshness_states"] != sorted(FRESHNESS_STATES):
        raise ContractError("freshness states drifted from the implementation")
    if manifest["projection_roles"] != sorted(PROJECTION_ROLES):
        raise ContractError("projection roles drifted from the implementation")
    if manifest["final_authority"] != FINAL_AUTHORITY:
        raise ContractError(
            "the final authority drifted; a projection is a way of finding source "
            "and evidence, not a replacement for them"
        )

    # The three that would each, on their own, turn this module into the thing
    # it was built to prevent.
    if manifest["any_state_proves_absence"] is not False:
        raise ContractError(
            "no retrieval state may prove absence; a vector search returning nothing "
            "says one thing -- no chunk in this index was close enough"
        )
    if manifest["openwiki_admissible_as_evidence"] is not False:
        raise ContractError(
            "generated navigation may not be evidence for what generated it; every "
            "rebuild would tighten the circle"
        )
    if manifest["retrieval_hit_is_a_fact"] is not False:
        raise ContractError(
            "a retrieval hit is a place to look. Whether the claim holds is settled "
            "by the source it cites"
        )
    if manifest["live_provider_state"] != "NOT_EXERCISED":
        raise ContractError(
            "no live vector or graph provider has been exercised; LanceDB or any other "
            "store is an adapter choice after exact version and license admission"
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
        try:
            raw = (contracts / name).read_bytes()
        except OSError as exc:
            raise InputError(f"cannot read schema {name}: {exc}") from exc
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
    manifest = load_json(root / "contracts" / "manifest.json")
    mutations = [
        ("schema digest", lambda m: m["schemas"][0].__setitem__("sha256", "0" * 64)),
        ("absence provable", lambda m: m.__setitem__("any_state_proves_absence", True)),
        (
            "wiki admissible",
            lambda m: m.__setitem__("openwiki_admissible_as_evidence", True),
        ),
        ("hit made a fact", lambda m: m.__setitem__("retrieval_hit_is_a_fact", True)),
        (
            "live provider claimed",
            lambda m: m.__setitem__("live_provider_state", "PASS"),
        ),
        (
            "authority moved to the index",
            lambda m: m.__setitem__("final_authority", "VECTOR_INDEX"),
        ),
        (
            "retrieval state dropped",
            lambda m: m.__setitem__("retrieval_states", ["HIT", "MISS"]),
        ),
        (
            "freshness collapsed",
            lambda m: m.__setitem__("freshness_states", ["CURRENT"]),
        ),
        (
            "projection role dropped",
            lambda m: m.__setitem__("projection_roles", ["VECTOR"]),
        ),
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
