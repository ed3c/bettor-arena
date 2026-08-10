#!/usr/bin/env python3
"""Independent structural/digest verifier for one CTG output directory."""

from __future__ import annotations

import sys
from pathlib import Path

from .cli import ContractError, read_json, require_closed, resolve_artifact, sha256
from .model import validate_graph

RESULT_KEYS = {
    "schema_version",
    "packet_id",
    "observation_id",
    "actual_runner",
    "digests",
    "refs_status",
    "stages",
    "artifacts",
    "graph_summary",
    "settlement_summary",
    "next_edge",
    "human_gate",
    "overall",
    "claim_boundary",
}
RUNNER_KEYS = {
    "repo_commit",
    "repo_tree",
    "surface_version",
    "runtime_ref",
    "runtime_sha256",
}
DIGEST_KEYS = {
    "input",
    "subject_snapshot",
    "domain_profile",
    "execution_argv",
    "delivery",
}
STAGE_KEYS = {"name", "state", "exit", "diagnostics", "artifacts"}
ARTIFACT_KEYS = {"kind", "artifact_ref", "sha256"}
STAGE_STATES = {"PASSED", "FAILED", "BLOCKED", "NOT_EXERCISED", "NOT_REQUESTED"}


def verify(output: Path) -> None:
    output = output.resolve()
    result = read_json(output / "ctg-route-result.json")
    require_closed(result, RESULT_KEYS, "ctg-route-result")
    if result["schema_version"] != "ctg-route-result@1.0.0":
        raise ContractError("route-result schema_version is not ctg-route-result@1.0.0")
    runner = result["actual_runner"]
    digests = result["digests"]
    if not isinstance(runner, dict) or not isinstance(digests, dict):
        raise ContractError("actual_runner and digests must be objects")
    require_closed(runner, RUNNER_KEYS, "actual_runner")
    require_closed(digests, DIGEST_KEYS, "digests")

    stages = result["stages"]
    if not isinstance(stages, list) or [item.get("name") for item in stages] != [
        "STATIC",
        "SANDBOX",
        "PROD",
    ]:
        raise ContractError("stages must be ordered STATIC, SANDBOX, PROD")
    for index, item in enumerate(stages):
        if not isinstance(item, dict):
            raise ContractError(f"stages[{index}] must be an object")
        require_closed(item, STAGE_KEYS, f"stages[{index}]")
        if item["state"] not in STAGE_STATES:
            raise ContractError(f"stages[{index}] has invalid state")

    artifacts = result["artifacts"]
    if not isinstance(artifacts, list):
        raise ContractError("artifacts must be an array")
    graph_path: Path | None = None
    for index, item in enumerate(artifacts):
        if not isinstance(item, dict):
            raise ContractError(f"artifacts[{index}] must be an object")
        require_closed(item, ARTIFACT_KEYS, f"artifacts[{index}]")
        artifact = resolve_artifact(output, item["artifact_ref"])
        if sha256(artifact) != item["sha256"]:
            raise ContractError(f"artifact digest mismatch: {item['artifact_ref']}")
        if item["kind"] == "code_truth_graph":
            graph_path = artifact

    if result["overall"].get("exit") == 0:
        if graph_path is None:
            raise ContractError("successful result has no code_truth_graph artifact")
        graph = read_json(graph_path)
        errors = validate_graph(graph)
        if errors:
            raise ContractError(f"graph validation failed: {errors}")
        summary = result["graph_summary"]
        if summary != {
            "node_count": len(graph["nodes"]),
            "edge_count": len(graph["edges"]),
        }:
            raise ContractError("graph_summary does not match graph artifact")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2 or args[0] != "--output":
        print("usage: verify_artifacts --output <directory>", file=sys.stderr)
        return 64
    try:
        verify(Path(args[1]))
    except (ContractError, KeyError, OSError, TypeError) as exc:
        print(f"verify_artifacts FAIL: {exc}", file=sys.stderr)
        return 2
    print("PASS: CTG route-result, graph, and artifact digests verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
