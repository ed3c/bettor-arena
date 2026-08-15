#!/usr/bin/env python3
"""Schema identity, digest and fixture checks for the fold-back contracts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from fb_common import (
    EVIDENCE_CLASSES,
    ContractError,
    InputError,
    load_json,
)
from fb_delta import validate_delta
from fb_history import validate_history
from fb_patch import NORMATIVE_CARD_KINDS, PATCH_KINDS, validate_card

MANIFEST_KEYS = {
    "schema_version",
    "interface_version",
    "requires_capabilities",
    "evidence_classes",
    "patch_kinds",
    "normative_card_kinds",
    "similarity_may_patch",
    "history_is_append_only",
    "admit_authority",
    "terminal_state",
    "schemas",
}

SCHEMA_VERSIONS = {
    "candidate-bundle.schema.json": "loopx/foldback-candidate-bundle/v1",
    "change-delta.schema.json": "loopx/foldback-change-delta/v1",
    "foldback-receipt.schema.json": "loopx/foldback-receipt/v1",
    "revision-history.schema.json": "loopx/foldback-revision-history/v1",
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

    if manifest["schema_version"] != "loopx/foldback-contract-manifest/v1":
        raise ContractError("manifest schema version drifted")
    if manifest["interface_version"] != "1.0.0":
        raise ContractError("manifest interface version drifted")
    if manifest["requires_capabilities"] != [
        "arena.proof-kernel/v1",
        "loopx.code-truth-graph/v2",
        "loopx.contracts/v1",
        "loopx.ledger/v1",
    ]:
        raise ContractError("manifest capability dependencies drifted")

    if manifest["evidence_classes"] != sorted(EVIDENCE_CLASSES):
        raise ContractError("evidence classes drifted from the implementation")
    if manifest["patch_kinds"] != sorted(PATCH_KINDS):
        raise ContractError("patch kinds drifted from the implementation")
    if manifest["normative_card_kinds"] != sorted(NORMATIVE_CARD_KINDS):
        raise ContractError("normative card kinds drifted from the implementation")

    # The three that are policy rather than vocabulary, pinned here so a change
    # to any of them has to be a deliberate edit to the contract.
    if manifest["similarity_may_patch"] is not False:
        raise ContractError(
            "similarity_may_patch may not be true; a score can surface a card for "
            "review, and an unrelated card rewritten on vocabulary overlap becomes a "
            "wrong fact wearing a citation"
        )
    if manifest["history_is_append_only"] is not True:
        raise ContractError(
            "history_is_append_only may not be false; a history that can be edited "
            "loses the rejections and supersessions that explain how it got here"
        )
    if manifest["admit_authority"] != "HUMAN":
        raise ContractError("admit authority drifted from HUMAN")
    if manifest["terminal_state"] != "CANDIDATE_FOLD_BACK_BUNDLE":
        raise ContractError(
            "the compiler's terminal state must be CANDIDATE_FOLD_BACK_BUNDLE; "
            "anything past it is a knowledge write, which is Human Admit"
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
    validate_delta(load_json(good / "change-delta.json"))
    validate_history(load_json(good / "revision-history.json"))
    for card in load_json(good / "cards.json"):
        validate_card(card, f"card {card.get('canonical_key')!r}")
    return len(sorted(good.glob("*.json")))


def check_contracts(root: Path) -> tuple[int, int]:
    validate_manifest(root)
    return len(SCHEMA_VERSIONS), validate_fixtures(root)


def run_contract_selftest(root: Path) -> int:
    manifest = load_json(root / "contracts" / "manifest.json")
    mutations = [
        ("schema digest", lambda m: m["schemas"][0].__setitem__("sha256", "0" * 64)),
        (
            "similarity allowed to patch",
            lambda m: m.__setitem__("similarity_may_patch", True),
        ),
        (
            "history no longer append-only",
            lambda m: m.__setitem__("history_is_append_only", False),
        ),
        ("admit authority", lambda m: m.__setitem__("admit_authority", "COMPILER")),
        (
            "terminal state promoted",
            lambda m: m.__setitem__("terminal_state", "KNOWLEDGE_WRITTEN"),
        ),
        (
            "evidence class collapsed",
            lambda m: m.__setitem__("evidence_classes", ["VERIFIED"]),
        ),
        (
            "normative kinds narrowed",
            lambda m: m.__setitem__("normative_card_kinds", ["NORM"]),
        ),
        (
            "patch kind dropped",
            lambda m: m.__setitem__("patch_kinds", ["NOOP", "UPDATE"]),
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
