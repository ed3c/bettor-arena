#!/usr/bin/env python3
"""Verify the exact KAW/Bettor consumer binding and implementation ceiling."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

MODULE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_ROOT.parents[1]
BINDING_PATH = MODULE_ROOT / "contracts/upstream-binding.json"
LIMITS_PATH = MODULE_ROOT / "receipts/implementation-limits.json"
FIXTURE_PATH = MODULE_ROOT / "tests/fixtures/admitted-envelope.json"
CONSUMER_PATH = MODULE_ROOT / "scripts/capability_workspace.py"
REQUIRED_PATHS = [
    MODULE_ROOT / "AGENTS.md",
    MODULE_ROOT / "README.md",
    MODULE_ROOT / "contracts/kaw-route-proposal.schema.json",
    MODULE_ROOT / "contracts/bettor-route-result.schema.json",
    BINDING_PATH,
    LIMITS_PATH,
    FIXTURE_PATH,
    CONSUMER_PATH,
    MODULE_ROOT / "tests/test_capability_workspace.py",
    REPO_ROOT / ".arena/modules/capability-workspace-control-plane/module.json",
]

spec = importlib.util.spec_from_file_location("capability_workspace", CONSUMER_PATH)
assert spec and spec.loader
consumer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(consumer)


class CheckError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckError(message)


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CheckError(f"cannot parse {path}") from exc
    require(isinstance(value, dict), f"{path} must contain a JSON object")
    return value


def git_blob_sha(content: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(content)).encode("ascii") + b"\0" + content).hexdigest()


def local_git_blob(path: Path) -> str:
    process = subprocess.run(
        ["git", "hash-object", str(path)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    require(process.returncode == 0, f"git hash-object failed for {path}")
    return process.stdout.strip()


def run_git(args: list[str], cwd: Path) -> str:
    process = subprocess.run(["git", *args], cwd=cwd, check=False, capture_output=True, text=True)
    require(process.returncode == 0, f"git command failed: {' '.join(args)}: {process.stderr.strip()}")
    return process.stdout.strip()


def verify_remote(binding: dict[str, Any]) -> None:
    upstream = binding["upstream"]
    commit = upstream["commit"]
    repository = upstream["repository"]
    with tempfile.TemporaryDirectory(prefix="bettor-kaw-binding-") as temporary:
        checkout = Path(temporary) / "upstream.git"
        checkout.mkdir()
        run_git(["init", "--bare"], checkout)
        run_git(["fetch", "--no-tags", "--depth=1", f"https://github.com/{repository}.git", commit], checkout)
        require(run_git(["rev-parse", "FETCH_HEAD"], checkout) == commit, "remote KAW commit drift")
        require(run_git(["rev-parse", "FETCH_HEAD^{tree}"], checkout) == upstream["tree"], "remote KAW tree drift")
        for path_key, blob_key in (("routerPath", "routerBlob"), ("contractsPath", "contractsBlob")):
            actual = run_git(["rev-parse", f"FETCH_HEAD:{upstream[path_key]}"], checkout)
            require(actual == upstream[blob_key], f"remote KAW blob drift: {upstream[path_key]}")


def verify_limits(limits: dict[str, Any]) -> None:
    require(set(limits) == {"schema", "maximumClaim", "states", "externalAuthority", "forbiddenClaims"}, "limits keys mismatch")
    require(limits["schema"] == "bettor.capability-workspace-implementation-limits/v1", "limits schema mismatch")
    require(limits["maximumClaim"] == "BETTOR_CONSUMER_CONTRACT_AND_ROUTE_ACK_CODE_READY", "maximum claim widened")
    expected_states = {
        "consumerContract": "PASS",
        "routeAdmissionCode": "PASS",
        "routeAcknowledgementFixture": "PASS",
        "workerRuntime": "NOT_EXERCISED",
        "gateRuntime": "NOT_EXERCISED",
        "loopxReducer": "NOT_EXERCISED",
        "liveBettorHandoff": "NOT_EXERCISED",
        "providerRuntime": "NOT_EXERCISED",
        "userOutcome": "ABSENT",
    }
    require(limits["states"] == expected_states, "implementation state denominator mismatch")
    require(set(limits["externalAuthority"]) == {
        "BETTOR_DEPLOYMENT",
        "PROVIDER_CREDENTIALS",
        "WORKER_RUNTIME",
        "COST_AND_BUDGET",
        "MERGE",
        "RELEASE",
    }, "external authority denominator mismatch")
    require(set(limits["forbiddenClaims"]) == {
        "ROUTE_ACK_IS_WORKER_EXECUTION",
        "WORKER_EXECUTION_IS_GATE_SUCCESS",
        "GATE_RECEIPT_IS_DOMAIN_TRUTH",
        "FIXTURE_IS_LIVE",
        "KAW_WROTE_LOOPX_STATE",
        "PROVIDER_OUTPUT_GRANTED_AUTHORITY",
        "USER_OUTCOME_ESTABLISHED",
        "MERGE_OR_RELEASE_PERFORMED",
    }, "forbidden claim denominator mismatch")


def verify(remote: bool) -> None:
    for path in REQUIRED_PATHS:
        require(path.is_file(), f"required path missing: {path.relative_to(REPO_ROOT)}")
    binding = load(BINDING_PATH)
    consumer._validate_binding(binding)
    verify_limits(load(LIMITS_PATH))

    bettor = binding["bettor"]
    manifest_path = REPO_ROOT / bettor["workerManifestPath"]
    receipt_schema_path = REPO_ROOT / bettor["workerReceiptSchemaPath"]
    require(local_git_blob(manifest_path) == bettor["workerManifestBlob"], "local worker manifest blob drift")
    require(local_git_blob(receipt_schema_path) == bettor["workerReceiptSchemaBlob"], "local worker receipt schema blob drift")
    manifest = load(manifest_path)
    require(manifest["fixture_only"] is True, "worker gateway unexpectedly became live")
    require(manifest["live_matrix_state"] == "NOT_EXERCISED", "worker live matrix state widened")

    for path in (
        MODULE_ROOT / "contracts/kaw-route-proposal.schema.json",
        MODULE_ROOT / "contracts/bettor-route-result.schema.json",
        REPO_ROOT / ".arena/modules/capability-workspace-control-plane/module.json",
    ):
        load(path)

    result = consumer.route_envelope(load(FIXTURE_PATH), binding, {})
    require(result["state"] == "ACKNOWLEDGED", "positive fixture was not acknowledged")
    require(result["execution"]["state"] == "NOT_EXERCISED", "fixture promoted Worker execution")
    require(result["authority"]["consumerGrantedExecutionAuthority"] is False, "consumer granted execution authority")
    if remote:
        verify_remote(binding)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--remote", action="store_true")
    args = parser.parse_args(argv)
    try:
        verify(args.remote)
    except (CheckError, consumer.ContractError, OSError, subprocess.SubprocessError, json.JSONDecodeError, KeyError) as exc:
        print(f"capability workspace control-plane check: FAIL: {exc}", file=sys.stderr)
        return 1
    print("capability workspace control-plane check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
