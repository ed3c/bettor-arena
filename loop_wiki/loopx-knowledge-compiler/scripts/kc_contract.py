#!/usr/bin/env python3
"""Schema identity, digest and fixture checks for the six IR layers.

The manifest pins each schema by digest, so a schema edited without re-rendering
the manifest is caught here rather than at the point where something written
against the old shape quietly stops matching.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from kc_assertion import CLAIM_KINDS, VERIFICATION_STATES, validate_graph
from kc_card import validate_card_graph
from kc_codeop import validate_plan
from kc_common import ContractError, InputError, load_json
from kc_source import validate_manifest as validate_source_manifest
from kc_spec import validate_spec

MANIFEST_KEYS = {
    "schema_version",
    "interface_version",
    "requires_capabilities",
    "claim_kinds",
    "verification_states",
    "terminal_state",
    "admit_authority",
    "external_knowledge_admitted",
    "compiled_output_checked_in",
    "schemas",
}

SCHEMA_VERSIONS = {
    "assertion-graph.schema.json": "loopx/knowledge-assertion-graph/v1",
    "codeop-plan.schema.json": "loopx/knowledge-codeop-plan/v1",
    "knowledge-card-graph.schema.json": "loopx/knowledge-card-graph/v1",
    "scaffold-receipt.schema.json": "loopx/knowledge-scaffold-receipt/v1",
    "source-manifest.schema.json": "loopx/knowledge-source-manifest/v1",
    "system-spec.schema.json": "loopx/knowledge-system-spec/v1",
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

    if manifest["schema_version"] != "loopx/knowledge-contract-manifest/v1":
        raise ContractError("manifest schema version drifted")
    if manifest["interface_version"] != "1.0.0":
        raise ContractError("manifest interface version drifted")
    if manifest["requires_capabilities"] != [
        "arena.proof-kernel/v1",
        "loopx.code-truth-graph/v2",
        "loopx.contracts/v1",
    ]:
        raise ContractError("manifest capability dependencies drifted")

    # The vocabularies are pinned to the implementation's own, so a state added
    # in code without a decision about its ceiling is caught by the manifest
    # rather than by whoever first relies on it.
    if manifest["claim_kinds"] != sorted(CLAIM_KINDS):
        raise ContractError("claim kinds drifted from the implementation")
    if manifest["verification_states"] != sorted(VERIFICATION_STATES):
        raise ContractError("verification states drifted from the implementation")

    if manifest["terminal_state"] != "CANDIDATE_RECEIPT":
        raise ContractError(
            "the compiler's terminal state must be CANDIDATE_RECEIPT; anything "
            "beyond it is applying a scaffold, which is Human Admit"
        )
    if manifest["admit_authority"] != "HUMAN":
        raise ContractError("admit authority drifted from HUMAN")
    if manifest["external_knowledge_admitted"] is not False:
        raise ContractError(
            "external_knowledge_admitted may not be true; a compiler permitted to "
            "fill gaps from outside the notes produces claims no locator can reach"
        )
    if manifest["compiled_output_checked_in"] is not False:
        raise ContractError("compiled candidate trees must not be checked in")

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
        path = contracts / name
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise InputError(f"cannot read schema {path}: {exc}") from exc
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


def validate_fixtures(root: Path) -> int:
    good = root / "tests" / "fixtures" / "good"
    manifest = validate_source_manifest(load_json(good / "source-manifest.json"))
    sources_by_id = {s["source_id"]: s for s in manifest["sources"]}
    graph = validate_graph(load_json(good / "assertion-graph.json"), sources_by_id)
    assertions_by_id = {a["assertion_id"]: a for a in graph["assertions"]}

    grouping = load_json(good / "grouping.json")
    from kc_card import canonical_key

    card_keys = {
        canonical_key(spec["title"], spec["kind"]) for spec in grouping.values()
    }
    validate_spec(load_json(good / "system-spec.json"), assertions_by_id, card_keys)

    spec = load_json(good / "system-spec.json")
    requirement_ids = {r["requirement_id"] for r in spec["requirements"]}
    validate_plan(load_json(good / "codeop-plan.json"), requirement_ids)

    # The card graph is compiled rather than stored, so it is validated through
    # the compiler rather than as a checked-in fixture. A stored card graph
    # would be a second source of truth that could drift from the sources.
    from kc_card import compile_cards

    validate_card_graph(
        {
            "schema_version": "loopx/knowledge-card-graph/v1",
            "notes_subject": manifest["notes_subject"],
            "cards": compile_cards(
                graph["assertions"], graph["contradictions"], grouping
            ),
        }
    )
    return len(sorted(good.glob("*.json")))


def check_contracts(root: Path) -> tuple[int, int]:
    validate_manifest(root)
    return len(SCHEMA_VERSIONS), validate_fixtures(root)


def run_contract_selftest(root: Path) -> int:
    manifest = load_json(root / "contracts" / "manifest.json")
    mutations = [
        ("schema digest", lambda m: m["schemas"][0].__setitem__("sha256", "0" * 64)),
        (
            "terminal state promoted",
            lambda m: m.__setitem__("terminal_state", "APPLIED"),
        ),
        ("admit authority", lambda m: m.__setitem__("admit_authority", "COMPILER")),
        (
            "external knowledge admitted",
            lambda m: m.__setitem__("external_knowledge_admitted", True),
        ),
        (
            "checked-in candidate tree",
            lambda m: m.__setitem__("compiled_output_checked_in", True),
        ),
        (
            "verification state added without a ceiling",
            lambda m: m.__setitem__(
                "verification_states", sorted([*VERIFICATION_STATES, "ASSUMED"])
            ),
        ),
        ("claim kind dropped", lambda m: m.__setitem__("claim_kinds", ["NORM"])),
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
