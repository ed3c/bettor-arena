#!/usr/bin/env python3
"""Contract manifest for the Mem0 provider projection."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "scripts"))

from memory import ContractError, load  # noqa: E402

from mem0_authority import LADDER  # noqa: E402
from mem0_identity import MODES, PROVIDER_STATES  # noqa: E402

MANIFEST_KEYS = {
    "schema_version",
    "interface_version",
    "requires_capabilities",
    "modes",
    "provider_states",
    "authority_ladder",
    "projection_is_canonical",
    "writeback_is_automatic",
    "cross_mode_evidence_allowed",
    "live_canary_state",
    "schemas",
}

SCHEMA_VERSIONS = {
    "mem0-projection.schema.json": "loopx/mem0-projection/v1",
    "mem0-provider-identity.schema.json": "loopx/mem0-provider-identity/v1",
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
    loaded = load(contracts / "manifest.json") if override is None else override
    manifest = exact(loaded, MANIFEST_KEYS, "manifest")

    if manifest["schema_version"] != "loopx/mem0-contract-manifest/v1":
        raise ContractError("manifest schema version drifted")
    if manifest["interface_version"] != "1.0.0":
        raise ContractError("manifest interface version drifted")
    if manifest["requires_capabilities"] != [
        "arena.proof-kernel/v1",
        "loopx.decision-memory-runtime/v1",
        "loopx.ledger/v1",
    ]:
        raise ContractError("manifest capability dependencies drifted")

    if manifest["modes"] != sorted(MODES):
        raise ContractError("provider modes drifted from the implementation")
    if manifest["provider_states"] != sorted(PROVIDER_STATES):
        raise ContractError("provider states drifted from the implementation")
    if manifest["authority_ladder"] != list(LADDER):
        raise ContractError("the authority ladder drifted from the implementation")
    if manifest["authority_ladder"][-2:] != ["MEM0_PROJECTION", "MODEL_SUMMARY"]:
        raise ContractError(
            "the projection and the model summary must be the lowest two rungs; a "
            "retrieval result reads as authoritative because it came back from a "
            "system, and that is exactly the reading this ladder exists to prevent"
        )
    if manifest["projection_is_canonical"] is not False:
        raise ContractError(
            "a projection promoted to canonical makes the vector store the record of "
            "what a human admitted"
        )
    if manifest["writeback_is_automatic"] is not False:
        raise ContractError(
            "an automatic writeback makes the vector store an author, and the next "
            "session reads its output as something a person decided"
        )
    if manifest["cross_mode_evidence_allowed"] is not False:
        raise ContractError(
            "managed and self-hosted numbers do not describe each other; the model, "
            "the hardware and the index are all different"
        )
    if manifest["live_canary_state"] != "NOT_EXERCISED":
        raise ContractError(
            "no live Mem0 deployment has been exercised; a deterministic fixture is "
            "not a running store, and admitting one as the other is the whole failure"
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
    manifest = load(root / "contracts" / "manifest.json")
    mutations = [
        ("schema digest", lambda m: m["schemas"][0].__setitem__("sha256", "0" * 64)),
        (
            "projection made canonical",
            lambda m: m.__setitem__("projection_is_canonical", True),
        ),
        (
            "writeback made automatic",
            lambda m: m.__setitem__("writeback_is_automatic", True),
        ),
        (
            "cross-mode evidence allowed",
            lambda m: m.__setitem__("cross_mode_evidence_allowed", True),
        ),
        ("live canary claimed", lambda m: m.__setitem__("live_canary_state", "PASS")),
        (
            "projection promoted above memory",
            lambda m: m.__setitem__(
                "authority_ladder", ["MEM0_PROJECTION", *LADDER[:-2], "MODEL_SUMMARY"]
            ),
        ),
        ("mode dropped", lambda m: m.__setitem__("modes", ["OSS_SELF_HOSTED"])),
        (
            "provider state dropped",
            lambda m: m.__setitem__("provider_states", ["AVAILABLE"]),
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
