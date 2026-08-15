#!/usr/bin/env python3
"""Manifest identity, digests and vocabulary for the Harness Console contracts.

The manifest states the things that, if they drifted, would make the console the
thing it was built against: a screen with authority, an exception folded into a
completion, or a rendered UI claimed where none exists. Each has a mutation below.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from hc_vocab import (
    CONSOLE_MAY,
    CONSOLE_MAY_NOT,
    LIVE_CONSOLE_STATE,
    RENDER_STATE,
    SIGNATURE_ALGORITHM,
    TASK_STATES,
    UI_STATES,
    VIEWS,
    ContractError,
    InputError,
    load_json,
)

CONTRACTS_REL = "packages/harness-console-contracts/schemas"

MANIFEST_KEYS = {
    "schema_version",
    "interface_version",
    "ui_states",
    "views",
    "task_states",
    "console_may",
    "console_may_not",
    "signature_algorithm",
    "projection_authority",
    "console_writes_ledger",
    "console_marks_gate_pass",
    "exception_is_ordinary_completion",
    "projection_is_rebuildable",
    "render_state",
    "live_console_state",
    "schemas",
}

SCHEMA_VERSIONS = {
    "console-projection.schema.json": "loopx/console-projection/v1",
    "console-views.schema.json": "loopx/console-views/v1",
    "decision-request.schema.json": "loopx/console-decision-request/v1",
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

    if manifest["schema_version"] != "loopx/harness-console-contract-manifest/v1":
        raise ContractError("manifest schema version drifted")
    if manifest["interface_version"] != "1.0.0":
        raise ContractError("manifest interface version drifted")

    if manifest["ui_states"] != UI_STATES:
        raise ContractError("the UI state sequence drifted from the implementation")
    if manifest["views"] != sorted(VIEWS):
        raise ContractError(
            "the view list drifted; a declared view with no builder is a screen nobody "
            "opened, and it is indistinguishable from one that renders empty"
        )
    if manifest["task_states"] != sorted(TASK_STATES):
        raise ContractError("the task state list drifted from the implementation")
    if manifest["console_may"] != sorted(CONSOLE_MAY):
        raise ContractError(
            "the drafted-action set drifted; it is closed so that an escape hatch "
            "cannot be added by passing a different string"
        )
    if manifest["console_may_not"] != sorted(CONSOLE_MAY_NOT):
        raise ContractError(
            "the refused-action list drifted; it is a list rather than a principle "
            "because a principle gets weakened one adjective at a time"
        )
    if manifest["signature_algorithm"] != SIGNATURE_ALGORITHM:
        raise ContractError("the signature algorithm drifted from the implementation")

    if manifest["projection_authority"] != "READ_ONLY_PROJECTION":
        raise ContractError(
            "the console projection has no authority; a screen that becomes a source of "
            "truth updates, and the ledger learns about it afterwards or never"
        )
    if manifest["console_writes_ledger"] is not False:
        raise ContractError("the console never writes a ledger event; it asks")
    if manifest["console_marks_gate_pass"] is not False:
        raise ContractError(
            "the console displays a gate verdict and never writes one; no evidence "
            "state may be promoted to PASS from a screen"
        )
    if manifest["exception_is_ordinary_completion"] is not False:
        raise ContractError(
            "COMPLETED_WITH_EXCEPTION is not a completion. It renders as one in every "
            "summary anyone would write by hand, which is why it is counted separately"
        )
    if manifest["projection_is_rebuildable"] is not True:
        raise ContractError(
            "the projection must be rebuildable from canonical events; a UI database "
            "that has drifted from the ledger renders confidently and wrongly, and the "
            "screen looks the same either way"
        )
    if manifest["render_state"] != RENDER_STATE or RENDER_STATE != "NOT_IMPLEMENTED":
        raise ContractError(
            "there is no HTML, no websocket and no browser here. This is the view model "
            "and the request path; claiming a rendered console would be claiming a "
            "mechanism that exists only in Markdown"
        )
    if manifest["live_console_state"] != LIVE_CONSOLE_STATE:
        raise ContractError(
            "no live console has been activated; production console activation is Human "
            "Admit"
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
    return len(SCHEMA_VERSIONS), len(sorted((root / CONTRACTS_REL).glob("*.json")))


def run_contract_selftest(root: Path) -> int:
    manifest = load_json(root / CONTRACTS_REL / "manifest.json")
    mutations = [
        ("schema digest", lambda m: m["schemas"][0].__setitem__("sha256", "0" * 64)),
        ("schema identity", lambda m: m["schemas"][1].__setitem__("id", "https://x/y")),
        (
            "projection given authority",
            lambda m: m.__setitem__("projection_authority", "AUTHORITATIVE"),
        ),
        (
            "console writes the ledger",
            lambda m: m.__setitem__("console_writes_ledger", True),
        ),
        (
            "console marks a gate PASS",
            lambda m: m.__setitem__("console_marks_gate_pass", True),
        ),
        (
            "exception folded into completion",
            lambda m: m.__setitem__("exception_is_ordinary_completion", True),
        ),
        (
            "projection no longer rebuildable",
            lambda m: m.__setitem__("projection_is_rebuildable", False),
        ),
        ("a rendered UI claimed", lambda m: m.__setitem__("render_state", "PASS")),
        (
            "a live console claimed",
            lambda m: m.__setitem__("live_console_state", "PASS"),
        ),
        ("merge added to the allowed set", lambda m: m["console_may"].append("MERGE")),
        (
            "force skip removed from the refused list",
            lambda m: m["console_may_not"].remove("UNSCOPED_FORCE_SKIP"),
        ),
        (
            "rollback removed from the refused list",
            lambda m: m["console_may_not"].remove("ROLLBACK_PRODUCTION"),
        ),
        ("a view dropped", lambda m: m["views"].remove("gate_evidence_inspector")),
        (
            "the exception task state dropped",
            lambda m: m["task_states"].remove("COMPLETED_WITH_EXCEPTION"),
        ),
        (
            "the signer verification state dropped",
            lambda m: m["ui_states"].remove("SIGNER_REVISION_LEDGER_HEAD_VERIFIED"),
        ),
        (
            "UI states reordered",
            lambda m: m.__setitem__("ui_states", list(reversed(m["ui_states"]))),
        ),
        (
            "signature algorithm drifted",
            lambda m: m.__setitem__("signature_algorithm", "NONE"),
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
