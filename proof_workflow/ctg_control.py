#!/usr/bin/env python3
"""Independent derivation/projection helpers for control_ctg_entry.sh."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


class ControlError(ValueError):
    pass


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


def proof_check(receipt: Path) -> str:
    value = read_json(receipt)
    ids = {item.get("id") for item in value.get("steps", [])}
    required = {
        "input-schema",
        "result-schema",
        "runtime",
        "trigger",
        "verify",
        "public-contract",
    }
    missing = sorted(required - ids)
    if missing:
        raise ControlError(f"CTG proof misses control-required steps: {missing}")
    hardening = value.get("molecular_hardening")
    digest = hardening.get("proof_digest") if isinstance(hardening, dict) else None
    if not isinstance(digest, str) or len(digest) != 64:
        raise ControlError("CTG proof receipt has no molecular digest")
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
    args = parser.parse_args()
    try:
        if args.command == "candidates":
            print("\n".join(candidates(args.packet.resolve())))
        elif args.command == "projection":
            print(canonical_projection(args.result.resolve()))
        elif args.command == "produced":
            print("\n".join(produced(args.result.resolve())))
        else:
            print(proof_check(args.receipt.resolve()))
    except (ControlError, KeyError, OSError, TypeError, json.JSONDecodeError) as exc:
        print(f"ctg-control FATAL: {exc}", file=sys.stderr)
        return 64
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
