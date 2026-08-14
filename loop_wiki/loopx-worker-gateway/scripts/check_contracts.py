#!/usr/bin/env python3
"""Validate LoopX Worker Gateway v1 contracts without network access."""

from __future__ import annotations

import argparse
import copy
import hashlib
import sys
from pathlib import Path
from typing import Callable

from gateway_common import GatewayError, load_json, validate_registry, validate_request

EXPECTED_SCHEMAS = {
    "host-descriptor.schema.json",
    "worker-request.schema.json",
    "worker-event.schema.json",
    "worker-receipt.schema.json",
}
EXPECTED_MUTATIONS = {
    "duplicate-host",
    "fixture-host-in-production",
    "shell-binary",
    "gray-box-internal-trace",
    "unknown-host",
    "raw-shell-field",
    "path-traversal-arg",
    "secret-shaped-arg",
    "reusable-workspace",
    "trace-above-host-ceiling",
    "fake-pass-without-execution",
    "host-replay",
    "subject-drift",
    "skill-context-drift",
    "worker-authority-escalation",
    "gray-box-fabricated-event",
    "cleanup-failure",
    "timeout-process-group",
}


def digest_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def module_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def check(root: Path) -> None:
    contracts = root / "contracts"
    manifest = load_json(contracts / "manifest.json")
    required = {"schema_version", "files", "canonical_hosts", "evidence_states", "authority_law"}
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise GatewayError("manifest fields drifted")
    if manifest["schema_version"] != "loopx/worker-gateway-manifest/v1":
        raise GatewayError("manifest schema_version mismatch")
    if not isinstance(manifest["files"], list) or set(manifest["files"]) != EXPECTED_SCHEMAS | {"host-registry.json"}:
        raise GatewayError("manifest file set drifted")
    if len(manifest["files"]) != len(set(manifest["files"])):
        raise GatewayError("manifest file list contains duplicates")
    for name in manifest["files"]:
        digest_file(contracts / name)
    if manifest["canonical_hosts"] != [
        "codex-cli", "claude-code", "grok-build", "opencode", "pi", "ante"
    ]:
        raise GatewayError("canonical host order drifted")
    if manifest["evidence_states"] != [
        "PASS", "FAIL", "NOT_EXERCISED", "SKIPPED_BY_POLICY", "ABSENT"
    ]:
        raise GatewayError("evidence vocabulary drifted")
    if manifest["authority_law"] != [
        "STRATEGY_PROPOSES", "WORKER_EXECUTES", "GATES_OBSERVE",
        "LOOPX_COMMITS", "HUMAN_ADMITS",
    ]:
        raise GatewayError("authority law drifted")

    for name in EXPECTED_SCHEMAS:
        schema = load_json(contracts / name)
        if not isinstance(schema, dict) or schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise GatewayError(f"{name}: not a Draft 2020-12 schema")
        if schema.get("additionalProperties") is not False:
            raise GatewayError(f"{name}: top level must fail closed")

    registry = validate_registry(load_json(contracts / "host-registry.json"))
    if registry["evidence_scope"] != "CONTRACT_ONLY":
        raise GatewayError("production registry must remain CONTRACT_ONLY")
    if any(host["implementation_state"] != "NOT_EXERCISED" for host in registry["hosts"]):
        raise GatewayError("production registry must not claim live execution")

    fixture_root = root / "tests" / "fixtures"
    validate_registry(load_json(fixture_root / "good" / "fixture-registry.json"))
    validate_request(load_json(fixture_root / "good" / "request.json"))
    validate_request(load_json(fixture_root / "hollow" / "request.json"))
    mutations = load_json(fixture_root / "mutations.json")
    if not isinstance(mutations, list) or {item.get("id") for item in mutations if isinstance(item, dict)} != EXPECTED_MUTATIONS:
        raise GatewayError("mutation registry drifted")


def expect_red(call: Callable[[], object], name: str) -> None:
    try:
        call()
    except GatewayError:
        return
    raise GatewayError(f"negative control accepted: {name}")


def selftest(root: Path) -> None:
    check(root)
    contracts = root / "contracts"
    fixture_root = root / "tests" / "fixtures"
    production = load_json(contracts / "host-registry.json")
    fixture = load_json(fixture_root / "good" / "fixture-registry.json")
    request = load_json(fixture_root / "good" / "request.json")

    value = copy.deepcopy(production)
    value["hosts"][1]["host_id"] = value["hosts"][0]["host_id"]
    expect_red(lambda: validate_registry(value), "duplicate-host")

    value = copy.deepcopy(production)
    value["hosts"][0]["implementation_state"] = "FIXTURE_READY"
    value["hosts"][0]["adapter"]["kind"] = "FIXTURE_PROCESS"
    expect_red(lambda: validate_registry(value), "fixture-host-in-production")

    value = copy.deepcopy(fixture)
    value["hosts"][0]["adapter"]["binary"] = "bash"
    expect_red(lambda: validate_registry(value), "shell-binary")

    value = copy.deepcopy(fixture)
    value["hosts"][1]["trace_ceiling"] = "TOOL_EVENTS"
    expect_red(lambda: validate_registry(value), "gray-box-internal-trace")

    value = copy.deepcopy(fixture)
    value["hosts"][0]["host_id"] = "unknown"
    expect_red(lambda: validate_registry(value), "unknown-host")

    value = copy.deepcopy(request)
    value["shell"] = True
    expect_red(lambda: validate_request(value), "raw-shell-field")

    value = copy.deepcopy(request)
    value["invocation"]["args"].append("../escape")
    expect_red(lambda: validate_request(value), "path-traversal-arg")

    value = copy.deepcopy(request)
    value["invocation"]["args"].append("api_key=super-secret-value")
    expect_red(lambda: validate_request(value), "secret-shaped-arg")

    value = copy.deepcopy(request)
    value["workspace"]["allow_reuse"] = True
    expect_red(lambda: validate_request(value), "reusable-workspace")

    print("loopx-worker-gateway contracts selftest PASS: registry and request mutations")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    try:
        root = module_dir()
        if args.selftest:
            selftest(root)
        else:
            check(root)
            print("loopx-worker-gateway contracts PASS: 4 schemas, 6 canonical hosts")
        return 0
    except GatewayError as exc:
        print(f"loopx-worker-gateway contracts RED: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"loopx-worker-gateway contracts FATAL: {exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
