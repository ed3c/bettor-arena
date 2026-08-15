#!/usr/bin/env python3
"""Manifest identity, digests and vocabulary for the Git Town runtime contracts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from gt_common import (
    ADMISSION_STATES,
    AUTHORITY,
    FORBIDDEN_FLAGS,
    MODES,
    STATES,
    ContractError,
    InputError,
    load_json,
)

CONTRACTS_REL = ".github-delivery/git-town"

MANIFEST_KEYS = {
    "schema_version",
    "interface_version",
    "states",
    "admission_states",
    "modes",
    "sync_argv",
    "forbidden_flags",
    "authority",
    "executable_state",
    "live_sync_state",
    "agent_may_continue_skip_undo_ship_push",
    "publication_is_separate_operation",
    "tool_exit_zero_is_repository_pass",
    "human_admit_required",
    "schemas",
}

SCHEMA_VERSIONS = {
    "admission.schema.json": "loopx/git-town-admission/v1",
    "publication-decision.schema.json": "loopx/git-town-publication-decision/v1",
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
    contracts = root / CONTRACTS_REL
    loaded = load_json(contracts / "manifest.json") if override is None else override
    manifest = exact(loaded, MANIFEST_KEYS, "manifest")

    if manifest["schema_version"] != "loopx/git-town-contract-manifest/v1":
        raise ContractError("manifest schema version drifted")
    if manifest["interface_version"] != "1.0.0":
        raise ContractError("manifest interface version drifted")

    if manifest["states"] != STATES:
        raise ContractError("the state sequence drifted from the implementation")
    if manifest["admission_states"] != list(ADMISSION_STATES):
        raise ContractError(
            "the admission vocabulary drifted; it starts at EXECUTABLE_ABSENT because "
            "that is the state an admission is most likely to paper over"
        )
    if manifest["modes"] != sorted(MODES):
        raise ContractError(
            "the mode set drifted; it is closed because a caller that can supply argv can "
            "supply --continue"
        )
    if manifest["sync_argv"] != MODES["sync_local_no_push"]:
        raise ContractError(
            "the non-negotiable command shape drifted from the implementation"
        )
    if manifest["forbidden_flags"] != sorted(FORBIDDEN_FLAGS):
        raise ContractError(
            "the forbidden flag list drifted; each one is a decision a human owns and "
            "every one has a plausible reason to be added at 2am"
        )
    if manifest["authority"] != {k: sorted(v) for k, v in AUTHORITY.items()}:
        raise ContractError("the authority table drifted from the implementation")

    if manifest["executable_state"] != "EXECUTABLE_ABSENT":
        raise ContractError(
            "git-town is not installed in this environment; recording anything else "
            "would describe a machine this receipt was not produced on"
        )
    if manifest["live_sync_state"] != "NOT_EXERCISED":
        raise ContractError(
            "no live Git Town sync has been run here. The invariants around it are "
            "exercised against real repositories; the tool itself is not"
        )
    if manifest["agent_may_continue_skip_undo_ship_push"] is not False:
        raise ContractError(
            "continue, skip, undo, ship and push are decisions a human owns; an agent "
            "that can reach any of them has removed the gate"
        )
    if manifest["publication_is_separate_operation"] is not True:
        raise ContractError(
            "publication is the one operation a human performs, and it is separate from "
            "everything local by construction"
        )
    if manifest["tool_exit_zero_is_repository_pass"] is not False:
        raise ContractError(
            "a tool exiting zero says the tool finished. Whether the repository is in an "
            "acceptable state is a different question with a different answer"
        )
    if manifest["human_admit_required"] is not True:
        raise ContractError("merge and config activation remain Human Admit")

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
    return len(SCHEMA_VERSIONS), len(sorted((root / CONTRACTS_REL).glob("*.json")))


def run_contract_selftest(root: Path) -> int:
    manifest = load_json(root / CONTRACTS_REL / "manifest.json")
    mutations = [
        ("schema digest", lambda m: m["schemas"][0].__setitem__("sha256", "0" * 64)),
        ("schema identity", lambda m: m["schemas"][1].__setitem__("id", "https://x/y")),
        ("--no-push dropped", lambda m: m["sync_argv"].remove("--no-push")),
        (
            "--non-interactive dropped",
            lambda m: m["sync_argv"].remove("--non-interactive"),
        ),
        (
            "--no-auto-resolve dropped",
            lambda m: m["sync_argv"].remove("--no-auto-resolve"),
        ),
        ("--continue allowed", lambda m: m["forbidden_flags"].remove("--continue")),
        (
            "--force-with-lease allowed",
            lambda m: m["forbidden_flags"].remove("--force-with-lease"),
        ),
        (
            "agent given the escape hatches",
            lambda m: m.__setitem__("agent_may_continue_skip_undo_ship_push", True),
        ),
        (
            "publication folded in",
            lambda m: m.__setitem__("publication_is_separate_operation", False),
        ),
        (
            "tool exit made a repository PASS",
            lambda m: m.__setitem__("tool_exit_zero_is_repository_pass", True),
        ),
        ("human admit dropped", lambda m: m.__setitem__("human_admit_required", False)),
        (
            "an absent executable claimed present",
            lambda m: m.__setitem__("executable_state", "ADMITTED_LOCAL_NO_PUSH"),
        ),
        ("a live sync claimed", lambda m: m.__setitem__("live_sync_state", "PASS")),
        ("a mode invented", lambda m: m["modes"].append("ship")),
        (
            "the absent state dropped",
            lambda m: m["admission_states"].remove("EXECUTABLE_ABSENT"),
        ),
        (
            "semantic conflicts taken from the human",
            lambda m: m["authority"]["HUMAN"].remove("semantic conflicts"),
        ),
        (
            "publication taken from the human",
            lambda m: m["authority"]["HUMAN"].remove("remote publication"),
        ),
        ("a state dropped", lambda m: m["states"].remove("HUMAN_ADMIT")),
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
