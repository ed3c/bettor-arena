#!/usr/bin/env python3
"""Independent derivation/projection helpers for control_ctg_entry.sh."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


class ControlError(ValueError):
    pass


CTG_PREFIX = "loop_wiki/code-truth-graph/"
CTG_EXTERNAL_PATHS = {
    "loopctl/contract.json",
    "loopctl/loopctl.sh",
    "loopctl/mcp_server.py",
    "loopctl/mcp_tools.py",
    "tests/test_ctg_cli.sh",
    "tests/test_ctg_domain_projection.py",
    "tests/test_ctg_java_core.sh",
    "tests/test_ctg_local_build.sh",
    "tests/test_ctg_mcp_carrier.sh",
}


def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ControlError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates
    )
    if not isinstance(value, dict):
        raise ControlError(f"expected object: {path}")
    return value


def safe_ref(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or Path(value).is_absolute()
        or ".." in Path(value).parts
    ):
        raise ControlError(f"unsafe artifact reference: {value!r}")
    return value


def candidates(packet_path: Path) -> list[str]:
    packet = read_json(packet_path)
    bundle = packet_path.parent
    refs = {
        safe_ref(packet["subject_snapshot"]["artifact_ref"]),  # type: ignore[index]
        safe_ref(packet["domain_profile"]["artifact_ref"]),  # type: ignore[index]
    }
    for item in packet["evidence"]:  # type: ignore[union-attr]
        refs.add(safe_ref(item["artifact_ref"]))
    for item in packet["source_refs"]:  # type: ignore[union-attr]
        refs.add(safe_ref(item["path"]))
    snapshot_ref = safe_ref(packet["subject_snapshot"]["artifact_ref"])  # type: ignore[index]
    snapshot = read_json(bundle / snapshot_ref)
    for item in snapshot["files"]:  # type: ignore[union-attr]
        refs.add(safe_ref(item["path"]))
    if not refs:
        raise ControlError("packet closure is empty")
    for ref in refs:
        if not (bundle / ref).is_file():
            raise ControlError(f"closure input is absent before probing: {ref}")
    return sorted(refs)


def canonical_projection(result_path: Path) -> str:
    if not result_path.is_file():
        return "ABSENT"
    result = read_json(result_path)
    projection = {
        "schema_version": result.get("schema_version"),
        "packet_id": result.get("packet_id"),
        "observation_id": result.get("observation_id"),
        "refs_status": result.get("refs_status"),
        "stages": [
            {
                "name": item.get("name"),
                "state": item.get("state"),
                "exit": item.get("exit"),
                "diagnostics": item.get("diagnostics"),
            }
            for item in result.get("stages", [])
        ],
        "artifacts": [
            {"kind": item.get("kind"), "sha256": item.get("sha256")}
            for item in result.get("artifacts", [])
        ],
        "graph_summary": result.get("graph_summary"),
        "settlement_summary": result.get("settlement_summary"),
        "next_edge": result.get("next_edge"),
        "human_gate": result.get("human_gate"),
        "overall": result.get("overall"),
        "claim_boundary": result.get("claim_boundary"),
    }
    payload = json.dumps(projection, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def produced(result_path: Path) -> list[str]:
    result = read_json(result_path)
    refs = ["ctg-route-result.json"]
    refs.extend(safe_ref(item["artifact_ref"]) for item in result["artifacts"])  # type: ignore[union-attr]
    return sorted(set(refs))


def git_output(repo: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, check=True
    ).stdout


def expected_proof_inventory(repo: Path) -> set[str]:
    tracked = {
        line
        for line in git_output(repo, "ls-tree", "-r", "--name-only", "HEAD", CTG_PREFIX)
        .decode()
        .splitlines()
        if line
    }
    if not tracked:
        raise ControlError("tracked CTG inventory is empty")
    missing_external = []
    for path in sorted(CTG_EXTERNAL_PATHS):
        try:
            git_output(repo, "cat-file", "-e", f"HEAD:{path}")
        except subprocess.CalledProcessError:
            missing_external.append(path)
    if missing_external:
        raise ControlError(f"CTG external proof inputs are absent: {missing_external}")
    return tracked | CTG_EXTERNAL_PATHS


def proof_check(repo: Path, receipt: Path) -> str:
    value = read_json(receipt)
    head = git_output(repo, "rev-parse", "HEAD").decode().strip()
    tree = git_output(repo, "rev-parse", "HEAD^{tree}").decode().strip()
    if value.get("loop") != "ctg" or value.get("status") != "passed":
        raise ControlError("receipt is not a passed CTG traversal proof")
    if value.get("worktree_dirty") is not False or receipt.name.endswith("-dirty.json"):
        raise ControlError("CTG control requires a clean traversal proof")
    if value.get("commit") != head or value.get("tree") != tree:
        raise ControlError("CTG proof is not bound to current HEAD and tree")

    hashed_steps = [
        item
        for item in value.get("steps", [])
        if item.get("path") and item.get("sha256") and item.get("kind") != "note"
    ]
    paths = [item["path"] for item in hashed_steps]
    if len(paths) != len(set(paths)):
        raise ControlError("CTG proof hashes a path more than once")
    expected = expected_proof_inventory(repo)
    if set(paths) != expected:
        missing = sorted(expected - set(paths))
        foreign = sorted(set(paths) - expected)
        raise ControlError(
            f"CTG proof inventory mismatch: missing={missing} foreign={foreign}"
        )

    manifest = []
    for item in hashed_steps:
        actual = hashlib.sha256(
            git_output(repo, "cat-file", "blob", f"HEAD:{item['path']}")
        ).hexdigest()
        if item["sha256"] != actual:
            raise ControlError(f"CTG proof hash differs from HEAD: {item['path']}")
        manifest.append(f"{actual}  {item['path']}\n")
    actual_digest = hashlib.sha256("".join(sorted(manifest)).encode()).hexdigest()
    hardening = value.get("molecular_hardening")
    digest = hardening.get("proof_digest") if isinstance(hardening, dict) else None
    if digest != actual_digest:
        raise ControlError("CTG proof digest does not match its HEAD-bound manifest")
    counts = value.get("counts", {})
    if counts.get("hashed_files") != len(manifest):
        raise ControlError("CTG proof hashed_files count is inconsistent")
    return digest


def control_check(receipt: Path) -> str:
    value = read_json(receipt)
    required = {
        "schema_version",
        "commit",
        "run_id",
        "status",
        "baseline",
        "input_classifications",
        "produced_artifacts",
        "proof_digest",
        "runs",
        "planted_defects",
        "assurance",
        "claim_boundary",
    }
    if set(value) != required:
        raise ControlError(
            f"CTG control receipt is not closed: missing={sorted(required - set(value))} extra={sorted(set(value) - required)}"
        )
    if value["schema_version"] != "bettor-arena-ctg-control@2.0.0":
        raise ControlError("unexpected CTG control schema version")
    assurance = value["assurance"]
    expected_axes = {
        "portable_packet",
        "verifier_negative_control",
        "relocation",
        "trusted_local",
        "mcp_inline_carrier",
        "live_prod_device",
        "human_admit",
        "maximum_claim",
    }
    if not isinstance(assurance, dict) or set(assurance) != expected_axes:
        raise ControlError("CTG assurance axes are missing or not closed")
    plants = value["planted_defects"]
    if not isinstance(plants, list) or len(plants) < 4:
        raise ControlError("CTG control receipt has fewer than four planted defects")
    for plant in plants:
        if not isinstance(plant, dict) or set(plant) != {
            "id",
            "axis",
            "target",
            "byte_guard",
            "exit",
            "caught",
        }:
            raise ControlError("CTG planted-defect record is not closed")
        if plant["byte_guard"] is not True:
            raise ControlError(f"plant has no byte guard: {plant.get('id')}")
        if plant["caught"] is not (plant["exit"] == 2):
            raise ControlError(f"plant exit/caught fields disagree: {plant.get('id')}")
    plant_axes = {plant["axis"] for plant in plants}
    expected_plant_axes = {
        "verifier_negative_control",
        "relocation",
        "trusted_local",
        "mcp_inline_carrier",
    }
    if plant_axes != expected_plant_axes:
        raise ControlError(
            f"CTG planted-defect axes mismatch: {sorted(plant_axes ^ expected_plant_axes)}"
        )
    offline_pass = all(
        assurance[axis] == "EXERCISED_PASS"
        for axis in {"portable_packet"} | expected_plant_axes
    ) and all(plant["caught"] for plant in plants)
    expected_claim = (
        "offline_multi_surface_implemented" if offline_pass else "no_positive_claim"
    )
    if assurance["maximum_claim"] != expected_claim:
        raise ControlError("CTG maximum claim does not follow the assurance axes")
    if value["status"] != ("passed" if offline_pass else "failed"):
        raise ControlError("CTG control status does not follow the assurance axes")
    runs = value["runs"]
    if not isinstance(runs, list) or len(runs) < 8:
        raise ControlError("CTG control receipt has too few captured runs")
    if any(run.get("exit") not in {0, 2, 64} for run in runs if isinstance(run, dict)):
        raise ControlError("CTG control receipt contains an undeclared exit")
    digest = value["proof_digest"]
    if not isinstance(digest, str) or len(digest) != 64:
        raise ControlError("CTG control receipt has no proof digest")
    return digest


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("candidates")
    c.add_argument("--packet", required=True, type=Path)
    p = sub.add_parser("projection")
    p.add_argument("--result", required=True, type=Path)
    o = sub.add_parser("produced")
    o.add_argument("--result", required=True, type=Path)
    q = sub.add_parser("proof-check")
    q.add_argument("--receipt", required=True, type=Path)
    q.add_argument("--repo", required=True, type=Path)
    v = sub.add_parser("control-check")
    v.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "candidates":
            print("\n".join(candidates(args.packet.resolve())))
        elif args.command == "projection":
            print(canonical_projection(args.result.resolve()))
        elif args.command == "produced":
            print("\n".join(produced(args.result.resolve())))
        elif args.command == "proof-check":
            print(proof_check(args.repo.resolve(), args.receipt.resolve()))
        else:
            print(control_check(args.receipt.resolve()))
    except (
        ControlError,
        KeyError,
        OSError,
        TypeError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"ctg-control FATAL: {exc}", file=sys.stderr)
        return 64
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
