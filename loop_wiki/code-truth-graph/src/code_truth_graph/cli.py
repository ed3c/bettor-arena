#!/usr/bin/env python3
"""Run one content-addressed Code Truth Graph measurement."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

from . import RUNTIME_REF
from .graphrag import compute_communities, export_graphrag
from .java_ast import JavaAstError, extract_java_records, ingest_java_ast
from .model import (
    add_evidence,
    attach_evidence_to_node,
    ensure_edge,
    ensure_node,
    new_graph,
    validate_graph,
)
from .render import render_html
from .settlement import add_invariants_and_events, evaluate_all
from .util import stable_id

SURFACE_VERSION = "2.5.0"
SAFE_ARTIFACT_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
TOOL_PROFILES = {"builtin-text-v1", "java-compiler-v1"}


class ContractError(ValueError):
    """The caller supplied an invalid or unverifiable input packet."""


class MeasurementError(ValueError):
    """The contract parsed, but a measured identity or required lane is red."""


PACKET_KEYS = {
    "schema_version",
    "packet_id",
    "packet_state",
    "observation_id",
    "expected_runner",
    "subject_snapshot",
    "domain_profile",
    "source_refs",
    "evidence",
    "reach_requirements",
    "context",
    "human_gate",
}
EXPECTED_RUNNER_KEYS = {"surface_version", "runtime_ref"}
SUBJECT_DESCRIPTOR_KEYS = {
    "artifact_ref",
    "sha256",
    "repo_id",
    "commit",
    "tree",
    "dirty",
    "dirty_digest",
    "scope",
    "file_manifest_digest",
}
DOMAIN_DESCRIPTOR_KEYS = {"schema_version", "artifact_ref", "sha256"}
SOURCE_REF_KEYS = {"repo", "commit", "path", "anchor", "sha256"}
EVIDENCE_KEYS = {
    "evidence_id",
    "kind",
    "artifact_ref",
    "sha256",
    "observed_at",
    "environment_class",
    "authority",
    "freshness",
}
REACH_KEYS = {"STATIC", "SANDBOX", "PROD"}
CONTEXT_KEYS = {"fixed", "iteration", "emergent"}
SNAPSHOT_KEYS = {
    "schema_version",
    "repo_id",
    "commit",
    "tree",
    "dirty",
    "dirty_digest",
    "scope",
    "files",
}
SNAPSHOT_FILE_KEYS = {"path", "sha256"}
PROFILE_KEYS = {"schema_version", "profile_id", "tool_profile", "invariants"}
INVARIANT_KEYS = {"invariant_id", "statement", "claim_boundary"}


def require_closed(value: dict[str, object], allowed: set[str], label: str) -> None:
    unknown = sorted(set(value) - allowed)
    missing = sorted(allowed - set(value))
    if unknown or missing:
        parts = []
        if unknown:
            parts.append(f"unknown keys {unknown}")
        if missing:
            parts.append(f"missing keys {missing}")
        raise ContractError(f"{label} is not closed: {', '.join(parts)}")


def require_object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    return value


def validate_packet_shape(packet: dict[str, object]) -> None:
    require_closed(packet, PACKET_KEYS, "ctg-input")
    expected_runner = require_object(packet["expected_runner"], "expected_runner")
    subject = require_object(packet["subject_snapshot"], "subject_snapshot")
    profile = require_object(packet["domain_profile"], "domain_profile")
    reach = require_object(packet["reach_requirements"], "reach_requirements")
    context = require_object(packet["context"], "context")
    require_closed(expected_runner, EXPECTED_RUNNER_KEYS, "expected_runner")
    require_closed(subject, SUBJECT_DESCRIPTOR_KEYS, "subject_snapshot")
    require_closed(profile, DOMAIN_DESCRIPTOR_KEYS, "domain_profile")
    require_closed(reach, REACH_KEYS, "reach_requirements")
    require_closed(context, CONTEXT_KEYS, "context")

    source_refs = packet["source_refs"]
    if not isinstance(source_refs, list) or not source_refs:
        raise ContractError("source_refs must be a non-empty array")
    for index, value in enumerate(source_refs):
        item = require_object(value, f"source_refs[{index}]")
        require_closed(item, SOURCE_REF_KEYS, f"source_refs[{index}]")

    evidence = packet["evidence"]
    if not isinstance(evidence, list):
        raise ContractError("evidence must be an array")
    for index, value in enumerate(evidence):
        item = require_object(value, f"evidence[{index}]")
        require_closed(item, EVIDENCE_KEYS, f"evidence[{index}]")

    for lane, requirement in reach.items():
        if requirement not in {"required", "optional", "not_requested"}:
            raise ContractError(
                f"reach_requirements.{lane} has invalid value: {requirement}"
            )
    if not isinstance(context["fixed"], list) or not isinstance(
        context["emergent"], list
    ):
        raise ContractError("context.fixed and context.emergent must be arrays")
    if not isinstance(context["iteration"], str):
        raise ContractError("context.iteration must be a string")
    if packet["human_gate"] != "required_before_invariant_admit":
        raise ContractError("human_gate must be required_before_invariant_admit")


def validate_snapshot_shape(snapshot: dict[str, object]) -> list[dict[str, object]]:
    require_closed(snapshot, SNAPSHOT_KEYS, "subject snapshot")
    files = snapshot["files"]
    if not isinstance(files, list) or not files:
        raise ContractError("subject snapshot files must be a non-empty array")
    result: list[dict[str, object]] = []
    for index, value in enumerate(files):
        item = require_object(value, f"subject snapshot files[{index}]")
        require_closed(item, SNAPSHOT_FILE_KEYS, f"subject snapshot files[{index}]")
        result.append(item)
    return result


def validate_profile_shape(profile: dict[str, object]) -> list[dict[str, object]]:
    require_closed(profile, PROFILE_KEYS, "domain profile")
    invariants = profile["invariants"]
    if not isinstance(invariants, list):
        raise ContractError("domain profile invariants must be an array")
    result: list[dict[str, object]] = []
    for index, value in enumerate(invariants):
        item = require_object(value, f"domain profile invariants[{index}]")
        require_closed(item, INVARIANT_KEYS, f"domain profile invariants[{index}]")
        result.append(item)
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_value(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def runner_identity() -> dict[str, str]:
    root = Path(__file__).resolve().parents[2]
    paths = [root / "run.sh", root / "trigger.sh"]
    paths.extend(sorted((root / "src/code_truth_graph").glob("*.py")))
    paths.extend(sorted((root / "schemas").glob("*.json")))
    paths.extend(sorted((root / "tools").rglob("*")))
    manifest = [
        f"{path.relative_to(root).as_posix()}\0{sha256(path)}\n"
        for path in paths
        if path.is_file()
    ]
    return {
        "repo_commit": "UNRELEASED",
        "repo_tree": "UNRELEASED",
        "surface_version": SURFACE_VERSION,
        "runtime_ref": RUNTIME_REF,
        "runtime_sha256": hashlib.sha256("".join(manifest).encode()).hexdigest(),
    }


def execution_digests(packet_path: Path) -> dict[str, str]:
    return {
        "execution_argv": sha256_value(
            {
                "command": "ctg run",
                "packet_sha256": sha256(packet_path),
                "transport": "one-shot",
            }
        ),
        "delivery": sha256_value(
            {
                "artifact_refs": "output-relative",
                "output_contract": "fresh-absolute-directory",
            }
        ),
    }


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ContractError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def read_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"expected a JSON object: {path}")
    return value


def resolve_artifact(bundle: Path, artifact_ref: object) -> Path:
    if not isinstance(artifact_ref, str) or not artifact_ref:
        raise ContractError("artifact_ref must be a non-empty string")
    if not SAFE_ARTIFACT_REF.fullmatch(artifact_ref):
        raise ContractError(f"artifact_ref contains unsafe characters: {artifact_ref}")
    relative = Path(artifact_ref)
    if relative.is_absolute() or ".." in relative.parts:
        raise ContractError(
            f"artifact_ref must stay inside the packet bundle: {artifact_ref}"
        )
    resolved = (bundle / relative).resolve()
    try:
        resolved.relative_to(bundle.resolve())
    except ValueError as exc:
        raise ContractError(
            f"artifact_ref escapes the packet bundle: {artifact_ref}"
        ) from exc
    if not resolved.is_file():
        raise ContractError(f"artifact_ref does not name a file: {artifact_ref}")
    return resolved


def verify_ref(bundle: Path, descriptor: object, label: str) -> tuple[Path, str]:
    if not isinstance(descriptor, dict):
        raise ContractError(f"{label} must be an object")
    artifact = resolve_artifact(bundle, descriptor.get("artifact_ref"))
    expected = descriptor.get("sha256")
    actual = sha256(artifact)
    if expected != actual:
        raise ContractError(
            f"{label} digest mismatch: expected {expected}, got {actual}"
        )
    return artifact, actual


def write_json(path: Path, value: object) -> str:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return sha256(path)


def manifest_digest(files: list[dict[str, object]]) -> str:
    rows = []
    for item in sorted(files, key=lambda value: str(value["path"])):
        rows.append(f"{item['path']}\0{item['sha256']}\n")
    return hashlib.sha256("".join(rows).encode("utf-8")).hexdigest()


def stage(
    name: str, state: str, exit_code: int | None, artifacts: list[dict[str, str]]
) -> dict[str, object]:
    return {
        "name": name,
        "state": state,
        "exit": exit_code,
        "diagnostics": [],
        "artifacts": artifacts,
    }


def failed_result(packet_path: Path, output: Path, diagnostic: str) -> None:
    packet = read_json(packet_path.resolve())
    subject = require_object(packet["subject_snapshot"], "subject_snapshot")
    profile = require_object(packet["domain_profile"], "domain_profile")
    requirements = require_object(packet["reach_requirements"], "reach_requirements")
    stages = [
        {
            "name": "STATIC",
            "state": "FAILED",
            "exit": 2,
            "diagnostics": [diagnostic],
            "artifacts": [],
        }
    ]
    for lane in ("SANDBOX", "PROD"):
        requirement = requirements[lane]
        state = "NOT_REQUESTED" if requirement == "not_requested" else "BLOCKED"
        stages.append(stage(lane, state, None, []))
    result = {
        "schema_version": "ctg-route-result@1.0.0",
        "packet_id": packet["packet_id"],
        "observation_id": packet["observation_id"],
        "actual_runner": runner_identity(),
        "digests": {
            "input": sha256(packet_path),
            "subject_snapshot": subject["sha256"],
            "domain_profile": profile["sha256"],
            **execution_digests(packet_path),
        },
        "refs_status": "stale",
        "stages": stages,
        "artifacts": [],
        "graph_summary": {"node_count": 0, "edge_count": 0},
        "settlement_summary": {
            "invariant_outcome": "UNCHALLENGED",
            "evidence_availability": "INVALID",
        },
        "next_edge": "packet_or_evidence_repair",
        "human_gate": packet["human_gate"],
        "overall": {"state": "FAILED", "exit": 2},
        "claim_boundary": "measurement failed before a graph could be admitted",
    }
    write_json(output / "ctg-route-result.json", result)


def run(packet_path: Path, output: Path) -> int:
    if not output.is_absolute():
        raise ContractError(f"output must be absolute: {output}")
    if output.exists():
        raise ContractError(f"output must not already exist: {output}")
    packet_path = packet_path.resolve()
    bundle = packet_path.parent
    packet = read_json(packet_path)
    validate_packet_shape(packet)
    if packet.get("schema_version") != "ctg-input@1.0.0":
        raise ContractError("schema_version must be ctg-input@1.0.0")
    if packet.get("packet_state") != "admitted_for_measurement":
        raise ContractError("packet_state must be admitted_for_measurement")
    expected_runner = packet.get("expected_runner")
    if not isinstance(expected_runner, dict):
        raise ContractError("expected_runner must be an object")
    if expected_runner.get("surface_version") != SURFACE_VERSION:
        raise ContractError(
            f"expected_runner.surface_version must be {SURFACE_VERSION}"
        )
    if expected_runner.get("runtime_ref") != RUNTIME_REF:
        raise ContractError(f"expected_runner.runtime_ref must be {RUNTIME_REF}")
    try:
        output.mkdir(parents=True)
    except OSError as exc:
        raise ContractError(f"cannot create output directory {output}: {exc}") from exc

    subject_descriptor = packet.get("subject_snapshot")
    snapshot_path, snapshot_sha = verify_ref(
        bundle, subject_descriptor, "subject_snapshot"
    )
    profile_path, profile_sha = verify_ref(
        bundle, packet.get("domain_profile"), "domain_profile"
    )
    snapshot = read_json(snapshot_path)
    profile = read_json(profile_path)
    if snapshot.get("schema_version") != "ctg-subject-snapshot@1.0.0":
        raise ContractError(
            "subject snapshot schema must be ctg-subject-snapshot@1.0.0"
        )
    if profile.get("schema_version") != "ctg-domain-profile@1.0.0":
        raise ContractError("domain profile schema must be ctg-domain-profile@1.0.0")
    if profile.get("tool_profile") not in TOOL_PROFILES:
        raise ContractError(
            f"domain profile tool_profile must be pinned to one of {sorted(TOOL_PROFILES)}"
        )
    files = validate_snapshot_shape(snapshot)
    invariants = validate_profile_shape(profile)
    assert isinstance(subject_descriptor, dict)
    for identity_key in ("repo_id", "commit", "tree", "dirty", "dirty_digest", "scope"):
        if subject_descriptor.get(identity_key) != snapshot.get(identity_key):
            raise MeasurementError(
                f"stale subject identity: {identity_key} does not match snapshot"
            )

    snapshot_files: list[tuple[dict[str, object], str, Path]] = []
    for entry in files:
        if not isinstance(entry, dict):
            raise ContractError("subject snapshot file entry must be an object")
        source = resolve_artifact(bundle, entry.get("path"))
        actual = sha256(source)
        if entry.get("sha256") != actual:
            raise ContractError(f"subject file digest mismatch: {entry.get('path')}")
        snapshot_files.append((entry, actual, source))
    if subject_descriptor.get("file_manifest_digest") != manifest_digest(files):
        raise MeasurementError(
            "stale subject identity: file_manifest_digest does not match snapshot"
        )

    evidence_records: list[dict[str, object]] = []
    for item in packet["evidence"]:
        assert isinstance(item, dict)
        artifact = resolve_artifact(bundle, item["artifact_ref"])
        actual = sha256(artifact)
        if item["sha256"] != actual:
            raise MeasurementError(f"evidence digest mismatch: {item['evidence_id']}")
        evidence_records.append(item)

    requirements = packet.get("reach_requirements")
    if not isinstance(requirements, dict) or requirements.get("STATIC") != "required":
        raise ContractError("this runtime requires reach_requirements.STATIC=required")

    observed = sorted(
        str(item["observed_at"]) for item in evidence_records if item.get("observed_at")
    )
    graph = new_graph(
        title=str(profile["profile_id"]),
        snapshot={
            "repo": snapshot["repo_id"],
            "sha": snapshot["commit"],
            "tree": snapshot["tree"],
            "dirty": snapshot["dirty"],
            "manifest_sha256": subject_descriptor["file_manifest_digest"],
        },
        scope={
            "mode": "demo",
            "repo": snapshot["repo_id"],
            "files": [str(item["path"]) for item in files],
            "synthetic": True,
        },
    )
    graph["generated_at"] = observed[0] if observed else "1970-01-01T00:00:00Z"

    file_node_ids: list[str] = []
    for entry, actual, _source in snapshot_files:
        path = str(entry["path"])
        node_id = stable_id("file", snapshot["repo_id"], path, actual)
        file_node_ids.append(node_id)
        ensure_node(
            graph,
            node_id=node_id,
            kind="file",
            label=Path(path).name,
            location={
                "repo": snapshot["repo_id"],
                "path": path,
                "start_line": 1,
                "end_line": 1,
                "symbol": "",
                "sha": snapshot["commit"],
            },
            metadata={"sha256": actual, "extractor": profile["tool_profile"]},
        )
        evidence_id = add_evidence(
            graph,
            method="DOCUMENT",
            status="documented",
            source=f"{snapshot['repo_id']}@{snapshot['commit']}:{path}",
            summary="Content-addressed subject file admitted for static measurement",
            authority="snapshot",
            environment_class="source",
            details={"sha256": actual},
        )
        attach_evidence_to_node(graph, node_id, evidence_id)

    if profile["tool_profile"] == "java-compiler-v1":
        java_sources = [source for _entry, _sha, source in snapshot_files]
        if any(source.suffix != ".java" for source in java_sources):
            raise ContractError("java-compiler-v1 accepts only .java snapshot files")
        tool_source = (
            Path(__file__).resolve().parents[2]
            / "tools/java/CodeGraphAstExtractor.java"
        )
        try:
            with tempfile.TemporaryDirectory(prefix="ctg-java-") as build_dir:
                records = extract_java_records(
                    root=bundle,
                    source_files=java_sources,
                    tool_source=tool_source,
                    build_dir=Path(build_dir),
                )
            ingest_java_ast(
                graph,
                root=bundle,
                repo=str(snapshot["repo_id"]),
                sha=str(snapshot["commit"]),
                records=records,
            )
        except JavaAstError as exc:
            if "not found" in str(exc):
                raise ContractError(str(exc)) from exc
            raise MeasurementError(str(exc)) from exc

    packet_evidence_ids: list[str] = []
    for item in evidence_records:
        evidence_id = add_evidence(
            graph,
            evidence_id=str(item["evidence_id"]),
            method="DOCUMENT",
            status="documented",
            source=str(item["artifact_ref"]),
            summary=f"Typed {item['kind']} evidence admitted by the packet",
            authority=str(item["authority"]),
            environment_class=str(item["environment_class"]),
            observed_at=str(item["observed_at"]),
            details={"freshness": item["freshness"], "sha256": item["sha256"]},
        )
        packet_evidence_ids.append(evidence_id)

    invariant_rows: list[dict[str, object]] = []
    event_rows: list[dict[str, object]] = []
    for invariant in invariants:
        invariant_id = str(invariant["invariant_id"])
        invariant_node = f"invariant:{invariant_id}"
        ensure_node(
            graph,
            node_id=invariant_node,
            kind="business_invariant",
            label=invariant_id,
            critical=False,
            metadata={"description": invariant["statement"]},
        )
        for node_id in file_node_ids:
            ensure_edge(
                graph,
                source=node_id,
                target=invariant_node,
                kind="AFFECTS_INVARIANT",
            )
        invariant_rows.append(
            {
                "id": invariant_id,
                "statement": invariant["statement"],
                "critical": False,
                "repeat_sensitive": False,
                "subject_ids": file_node_ids,
                "settlement_policy": {
                    "min_independent_reaches": 2,
                    "min_independence_groups": 2,
                    "require_prod": False,
                },
            }
        )
        event_rows.append(
            {
                "id": stable_id("event", invariant_id, packet["observation_id"]),
                "invariant_id": invariant_id,
                "sequence": 1,
                "action": "ASSERTED",
                "reach": "TEXT",
                "independence_group": "packet-declared-evidence",
                "evidence_ids": packet_evidence_ids,
                "note": invariant["claim_boundary"],
            }
        )
    add_invariants_and_events(graph, invariants=invariant_rows, events=event_rows)
    evaluate_all(graph)
    compute_communities(graph)
    graph_errors = validate_graph(graph)
    if graph_errors:
        raise MeasurementError(f"graph validation failed: {graph_errors}")

    graph_path = output / "code-truth-graph.json"
    graph["packet_id"] = packet["packet_id"]
    graph["observation_id"] = packet["observation_id"]
    graph["claim_boundary"] = "structure-only demo"
    graph_sha = write_json(graph_path, graph)
    graphrag_dir = output / "graphrag"
    export_graphrag(graph, graphrag_dir)
    report_path = output / "report.html"
    render_html(graph, report_path)
    graph_artifact = {
        "kind": "code_truth_graph",
        "artifact_ref": graph_path.name,
        "sha256": graph_sha,
    }
    exported_artifacts = [
        {
            "kind": f"graphrag_{name.removesuffix('.csv')}",
            "artifact_ref": f"graphrag/{name}",
            "sha256": sha256(graphrag_dir / name),
        }
        for name in ("entities.csv", "relationships.csv", "text_units.csv")
    ]
    exported_artifacts.append(
        {
            "kind": "html_report",
            "artifact_ref": report_path.name,
            "sha256": sha256(report_path),
        }
    )
    stages = [
        stage("STATIC", "PASSED", 0, [graph_artifact]),
        stage("SANDBOX", "NOT_REQUESTED", None, []),
        stage("PROD", "NOT_REQUESTED", None, []),
    ]
    result_path = output / "ctg-route-result.json"
    result = {
        "schema_version": "ctg-route-result@1.0.0",
        "packet_id": packet.get("packet_id"),
        "observation_id": packet.get("observation_id"),
        "actual_runner": runner_identity(),
        "digests": {
            "input": sha256(packet_path),
            "subject_snapshot": snapshot_sha,
            "domain_profile": profile_sha,
            **execution_digests(packet_path),
        },
        "refs_status": "resolved",
        "stages": stages,
        "artifacts": [graph_artifact, *exported_artifacts],
        "graph_summary": {
            "node_count": len(graph["nodes"]),
            "edge_count": len(graph["edges"]),
        },
        "settlement_summary": {
            "invariant_outcome": (
                graph["invariants"][0]["current_status"]
                if graph["invariants"]
                else "UNCHALLENGED"
            ),
            "evidence_availability": "CONSUMED",
        },
        "next_edge": "human_review",
        "human_gate": packet.get("human_gate"),
        "overall": {"state": "PASSED", "exit": 0},
        "claim_boundary": "structure-only demo",
    }
    write_json(result_path, result)
    print(f"route_result={result_path}")
    print(f"ctg_graph={graph_path}")
    return 0


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(prog="code-truth-graph")
    value.add_argument("--packet", required=True, type=Path)
    value.add_argument("--output", required=True, type=Path)
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return run(args.packet, args.output)
    except ContractError as exc:
        print(f"ctg FATAL: {exc}", file=sys.stderr)
        return 64
    except MeasurementError as exc:
        try:
            failed_result(args.packet, args.output, str(exc))
        except (ContractError, OSError) as result_exc:
            print(
                f"ctg FATAL: failed to materialize route-result: {result_exc}",
                file=sys.stderr,
            )
            return 64
        print(f"ctg FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
