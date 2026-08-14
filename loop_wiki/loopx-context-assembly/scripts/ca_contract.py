#!/usr/bin/env python3
"""Schema identity, digest and vocabulary checks for the context-assembly contracts.

The manifest states the things that, if they drifted, would turn this module into
the thing it was built to prevent: a projection that carries authority, a cache
number read as a universal claim, or an evidence anchor the budget was allowed to
drop. Each has a mutation below.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from ca_common import (
    CACHE_OBSERVATION_SCOPE,
    HOSTS,
    ContractError,
    InputError,
    load_json,
)
from ca_pipeline import STATES

MANIFEST_KEYS = {
    "schema_version",
    "interface_version",
    "requires_capabilities",
    "hosts",
    "assembly_states",
    "projection_authority",
    "cache_observation_scope",
    "cache_observation_is_universal",
    "evidence_anchor_droppable",
    "prefix_may_contain_volatile",
    "law_may_differ_across_hosts",
    "live_host_state",
    "schemas",
}

SCHEMA_VERSIONS = {
    "prompt-ir.schema.json": "loopx/prompt-ir/v1",
    "host-projection.schema.json": "loopx/host-projection/v1",
    "cache-observation.schema.json": "loopx/cache-observation/v1",
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

    if manifest["schema_version"] != "loopx/context-assembly-contract-manifest/v1":
        raise ContractError("manifest schema version drifted")
    if manifest["interface_version"] != "1.0.0":
        raise ContractError("manifest interface version drifted")
    if manifest["requires_capabilities"] != [
        "arena.proof-kernel/v1",
        "loopx.contracts/v1",
        "loopx.notes-retrieval/v1",
    ]:
        raise ContractError("manifest capability dependencies drifted")

    if manifest["hosts"] != sorted(HOSTS):
        raise ContractError(
            "the host list drifted from the implementation; a host that is declared "
            "but never rendered is absent, not in agreement"
        )
    if manifest["assembly_states"] != STATES:
        raise ContractError(
            "the assembly state sequence drifted from the implementation"
        )

    if manifest["projection_authority"] != "PRESENTATION_ONLY":
        raise ContractError(
            "a host projection carries no authority; provider-specific formatting is "
            "presentation, not a change in evidence or in what may be done"
        )
    if manifest["cache_observation_scope"] != CACHE_OBSERVATION_SCOPE:
        raise ContractError(
            "the cache observation scope drifted from the implementation"
        )
    if manifest["cache_observation_is_universal"] is not False:
        raise ContractError(
            "a hit rate measured on one host with one model on one provider is not a "
            "property of prompt assembly; it does not transfer to the other five"
        )
    if manifest["evidence_anchor_droppable"] is not False:
        raise ContractError(
            "an evidence anchor may not be dropped to fit a budget; the claim it "
            "supports still reads as cited, and the citation is what a reader checks"
        )
    if manifest["prefix_may_contain_volatile"] is not False:
        raise ContractError(
            "the cacheable prefix may not contain a value that varies between "
            "requests; nothing errors when it does -- the only symptom is the bill"
        )
    if manifest["law_may_differ_across_hosts"] is not False:
        raise ContractError(
            "the normative law is identical in all six projections or the module has "
            "no purpose; the divergence is found by an agent doing on one host what "
            "another forbids"
        )
    if manifest["live_host_state"] != "NOT_EXERCISED":
        raise ContractError(
            "no live host runtime has been exercised; the six projections are rendered "
            "and compared here, not sent to six real agent runtimes"
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
        ("schema identity", lambda m: m["schemas"][1].__setitem__("id", "https://x/y")),
        (
            "projection given authority",
            lambda m: m.__setitem__("projection_authority", "NORMATIVE"),
        ),
        (
            "cache number made universal",
            lambda m: m.__setitem__("cache_observation_is_universal", True),
        ),
        (
            "cache scope widened",
            lambda m: m.__setitem__("cache_observation_scope", "ALL_HOSTS"),
        ),
        (
            "evidence anchor made droppable",
            lambda m: m.__setitem__("evidence_anchor_droppable", True),
        ),
        (
            "volatile allowed into the prefix",
            lambda m: m.__setitem__("prefix_may_contain_volatile", True),
        ),
        (
            "law allowed to differ",
            lambda m: m.__setitem__("law_may_differ_across_hosts", True),
        ),
        ("live host claimed", lambda m: m.__setitem__("live_host_state", "PASS")),
        ("a host dropped", lambda m: m["hosts"].remove("pi")),
        ("a host invented", lambda m: m["hosts"].append("gemini")),
        (
            "an assembly state dropped",
            lambda m: m["assembly_states"].remove("REGRESSION_EVAL"),
        ),
        (
            "assembly states reordered",
            lambda m: m.__setitem__(
                "assembly_states", list(reversed(m["assembly_states"]))
            ),
        ),
        ("interface version", lambda m: m.__setitem__("interface_version", "2.0.0")),
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
