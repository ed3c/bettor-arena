#!/usr/bin/env python3
"""Validate the six-host Worker Gateway contract, registry, fixtures, and controls."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import shutil
from typing import Any, Callable

from gateway_common import BAD, OK, USAGE, ContractError, InputError, canonical_bytes, digest, load_json
from gateway_contract import validate_adapter, validate_event, validate_receipt, validate_registry, validate_request

SCHEMA_NAMES = {
    "adapter-descriptor.schema.json": "loopx/worker-adapter/v1",
    "worker-event.schema.json": "loopx/worker-event/v1",
    "worker-receipt.schema.json": "loopx/worker-receipt/v1",
    "worker-request.schema.json": "loopx/worker-request/v1",
}
MANIFEST_KEYS = {
    "schema_version", "interface_version", "requires_capabilities", "provides",
    "schemas", "host_ids", "live_matrix_state", "fixture_only", "forbidden_authorities",
}

def exact(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ContractError(f"{label} fields drifted")
    return value

def validate_manifest(root: Path, override: Any | None = None) -> dict[str, Any]:
    manifest = exact(load_json(root / "contracts" / "manifest.json") if override is None else override, MANIFEST_KEYS, "gateway manifest")
    if manifest["schema_version"] != "loopx/worker-gateway-manifest/v1":
        raise ContractError("gateway manifest version drifted")
    if manifest["interface_version"] != "1.0.0":
        raise ContractError("gateway interface version drifted")
    if manifest["requires_capabilities"] != ["loopx.contracts/v1", "skill-execution.runner/v1"]:
        raise ContractError("gateway capability dependencies drifted")
    if manifest["provides"] != ["loopx.worker-gateway/v1"]:
        raise ContractError("gateway provided capability drifted")
    if manifest["host_ids"] != ["codex-cli", "claude-code", "grok-build", "opencode", "pi", "ante"]:
        raise ContractError("gateway host matrix drifted")
    if manifest["live_matrix_state"] != "NOT_EXERCISED" or manifest["fixture_only"] is not True:
        raise ContractError("gateway fabricated a live host matrix")
    if manifest["forbidden_authorities"] != [
        "LOOPX_STATE_WRITE", "GATE_VERDICT", "HUMAN_ADMIT", "RELEASE_PROMOTION", "DURABLE_MEMORY_WRITE"
    ]:
        raise ContractError("gateway authority ceiling drifted")
    entries = manifest["schemas"]
    if not isinstance(entries, list) or len(entries) != len(SCHEMA_NAMES):
        raise ContractError("gateway manifest must enumerate four schemas")
    seen: set[str] = set()
    for entry in entries:
        entry = exact(entry, {"path", "id", "sha256"}, "gateway schema entry")
        name = entry["path"]
        if name in seen or name not in SCHEMA_NAMES:
            raise ContractError(f"unexpected or duplicate gateway schema: {name}")
        seen.add(name)
        path = root / "contracts" / name
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
            raise ContractError(f"gateway schema digest drifted: {name}")
        schema = load_json(path)
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise ContractError(f"gateway schema dialect drifted: {name}")
        if schema.get("$id") != entry["id"] or not entry["id"].endswith("/" + name):
            raise ContractError(f"gateway schema identity drifted: {name}")
        if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
            raise ContractError(f"gateway schema is not fail-closed: {name}")
        if schema.get("properties", {}).get("schema_version", {}).get("const") != SCHEMA_NAMES[name]:
            raise ContractError(f"gateway schema version constant drifted: {name}")
    return manifest

def validate_fixtures(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    _, descriptors = validate_registry(root)
    fixture = root / "tests" / "fixtures" / "good"
    request = validate_request(load_json(fixture / "request.json"), descriptors, "fixture request")
    descriptor = descriptors[request["adapter_id"]]
    receipt = validate_receipt(load_json(fixture / "receipt.json"), request, descriptor, "fixture receipt")
    if receipt["status"] != "NOT_EXERCISED":
        raise ContractError("fixture receipt must preserve NOT_EXERCISED")
    event = validate_event(load_json(fixture / "event.json"), request, descriptor, 0, "fixture event")
    if event["visibility"] != "EXTERNAL":
        raise ContractError("fixture event exceeds process-only evidence")
    return request, descriptor, receipt

def expect_red(action: Callable[[], Any], label: str) -> None:
    try:
        action()
    except ContractError:
        return
    raise ContractError(f"mutation unexpectedly passed: {label}")

def selftest(root: Path) -> None:
    validate_manifest(root)
    registry, descriptors = validate_registry(root)
    request, descriptor, receipt = validate_fixtures(root)
    mutations = 0

    bad_registry = copy.deepcopy(registry)
    bad_registry["adapters"][1] = bad_registry["adapters"][0]
    raw = copy.deepcopy(bad_registry); raw.pop("content_digest")
    bad_registry["content_digest"] = digest(raw)
    expect_red(lambda: validate_registry(root, bad_registry), "duplicate host registry")
    mutations += 1

    bad_descriptor = copy.deepcopy(descriptor)
    bad_descriptor["implementation_state"] = "IMPLEMENTED"
    raw = copy.deepcopy(bad_descriptor); raw.pop("content_digest")
    bad_descriptor["content_digest"] = digest(raw)
    with tempfile.TemporaryDirectory(prefix="loopx-worker-registry-mutation.") as temp:
        mutated_root = Path(temp) / "gateway"
        shutil.copytree(root, mutated_root)
        (mutated_root / "adapters" / "codex-cli.json").write_text(
            json.dumps(bad_descriptor, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        expect_red(lambda: validate_registry(mutated_root), "fabricated implemented adapter")
    mutations += 1

    for label, mutate in [
        ("adapter mismatch", lambda x: x.__setitem__("adapter_id", "claude-code")),
        ("path traversal", lambda x: x["workspace"]["writable_paths"].__setitem__(0, "../escape")),
        ("secret env", lambda x: x["policy"]["env_allowlist"].append("API_KEY")),
        ("raw authority field", lambda x: x["task"].__setitem__("gate_verdict", "PASS")),
        ("bad context digest", lambda x: x["context"].__setitem__("digest", "sha256:" + "0"*63)),
    ]:
        value = copy.deepcopy(request)
        mutate(value)
        raw = copy.deepcopy(value); raw.pop("content_digest")
        value["content_digest"] = digest(raw)
        expect_red(lambda value=value: validate_request(value, descriptors), label)
        mutations += 1

    fake_pass = copy.deepcopy(receipt)
    fake_pass["status"] = "PASS"
    fake_pass["cleanup"]["state"] = "PASS"
    raw = copy.deepcopy(fake_pass); raw.pop("content_digest")
    fake_pass["content_digest"] = digest(raw)
    expect_red(lambda: validate_receipt(fake_pass, request, descriptor), "PASS without execution")
    mutations += 1

    authority = copy.deepcopy(receipt)
    authority["authority"]["wrote_loopx_state"] = True
    raw = copy.deepcopy(authority); raw.pop("content_digest")
    authority["content_digest"] = digest(raw)
    expect_red(lambda: validate_receipt(authority, request, descriptor), "Worker state write")
    mutations += 1

    cleanup = copy.deepcopy(receipt)
    cleanup["status"] = "PASS"
    cleanup["executed"] = True
    cleanup["process"]["exit_code"] = 0
    cleanup["cleanup"]["state"] = "FAIL"
    cleanup["cleanup"]["residue_paths"] = ["workspace"]
    raw = copy.deepcopy(cleanup); raw.pop("content_digest")
    cleanup["content_digest"] = digest(raw)
    expect_red(lambda: validate_receipt(cleanup, request, descriptor), "PASS with cleanup failure")
    mutations += 1

    event = load_json(root / "tests" / "fixtures" / "good" / "event.json")
    gap = copy.deepcopy(event)
    gap["sequence"] = 2
    raw = copy.deepcopy(gap); raw.pop("content_digest")
    gap["content_digest"] = digest(raw)
    expect_red(lambda: validate_event(gap, request, descriptor, 0), "event sequence gap")
    mutations += 1

    internal = copy.deepcopy(event)
    internal["visibility"] = "SOURCE_VERIFIED_INTERNAL"
    raw = copy.deepcopy(internal); raw.pop("content_digest")
    internal["content_digest"] = digest(raw)
    expect_red(lambda: validate_event(internal, request, descriptor, 0), "gray/process-only internal event")
    mutations += 1

    private = copy.deepcopy(event)
    private["payload"]["message"] = "chain_of_thought"
    private["payload"]["chain_of_thought"] = "secret reasoning"
    raw = copy.deepcopy(private); raw.pop("content_digest")
    private["content_digest"] = digest(raw)
    expect_red(lambda: validate_event(private, request, descriptor, 0), "private reasoning")
    mutations += 1

    secret_value = copy.deepcopy(event)
    secret_value["payload"]["message"] = "Bearer abcdefghijklmnopqrstuvwxyz123456"
    raw = copy.deepcopy(secret_value); raw.pop("content_digest")
    secret_value["content_digest"] = digest(raw)
    expect_red(lambda: validate_event(secret_value, request, descriptor, 0), "secret-shaped event")
    mutations += 1

    print(f"loopx-worker-gateway selftest PASS: 1 positive, 1 not-exercised, {mutations} mutations")

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        validate_manifest(root)
        _, descriptors = validate_registry(root)
        validate_fixtures(root)
        if args.selftest:
            selftest(root)
        else:
            states = {name: descriptor["implementation_state"] for name, descriptor in descriptors.items()}
            print(
                "loopx-worker-gateway PASS: "
                f"4 schemas, 6 adapters, live_matrix=NOT_EXERCISED, states={json.dumps(states, sort_keys=True)}"
            )
        return OK
    except ContractError as exc:
        print(f"loopx-worker-gateway RED: {exc}", file=sys.stderr)
        return BAD
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE

if __name__ == "__main__":
    raise SystemExit(main())
