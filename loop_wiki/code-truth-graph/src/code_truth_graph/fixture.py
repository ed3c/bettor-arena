#!/usr/bin/env python3
"""Materialize the domain-neutral deterministic fixture used by portability/control."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> str:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return sha256(path)


def materialize(bundle: Path) -> Path:
    (bundle / "subject/files").mkdir(parents=True)
    (bundle / "evidence").mkdir()
    source = bundle / "subject/files/rules.txt"
    evidence = bundle / "evidence/inv-demo.txt"
    source.write_text("account balance must not become negative\n", encoding="utf-8")
    evidence.write_text("fixture evidence for INV-DEMO\n", encoding="utf-8")
    snapshot_sha = write_json(
        bundle / "subject-snapshot.json",
        {
            "schema_version": "ctg-subject-snapshot@1.0.0",
            "repo_id": "fixture/ledger",
            "commit": "1" * 40,
            "tree": "2" * 40,
            "dirty": False,
            "dirty_digest": None,
            "scope": ["subject/files/rules.txt"],
            "files": [{"path": "subject/files/rules.txt", "sha256": sha256(source)}],
        },
    )
    profile_sha = write_json(
        bundle / "domain-profile.json",
        {
            "schema_version": "ctg-domain-profile@1.0.0",
            "profile_id": "fixture-ledger-v1",
            "tool_profile": "builtin-text-v1",
            "invariants": [
                {
                    "invariant_id": "INV-DEMO",
                    "statement": "balance remains non-negative",
                    "claim_boundary": "structure-only demo",
                }
            ],
        },
    )
    file_manifest_digest = hashlib.sha256(
        f"subject/files/rules.txt\0{sha256(source)}\n".encode()
    ).hexdigest()
    packet = bundle / "ctg-input.json"
    write_json(
        packet,
        {
            "schema_version": "ctg-input@1.0.0",
            "packet_id": "ctg-fixture-001",
            "packet_state": "admitted_for_measurement",
            "observation_id": "obs-fixture-001",
            "expected_runner": {
                "surface_version": "2.5.0",
                "runtime_ref": "ctg-runtime@1.0.0",
            },
            "subject_snapshot": {
                "artifact_ref": "subject-snapshot.json",
                "sha256": snapshot_sha,
                "repo_id": "fixture/ledger",
                "commit": "1" * 40,
                "tree": "2" * 40,
                "dirty": False,
                "dirty_digest": None,
                "scope": ["subject/files/rules.txt"],
                "file_manifest_digest": file_manifest_digest,
            },
            "domain_profile": {
                "schema_version": "ctg-domain-profile@1.0.0",
                "artifact_ref": "domain-profile.json",
                "sha256": profile_sha,
            },
            "source_refs": [
                {
                    "repo": "fixture/ledger",
                    "commit": "1" * 40,
                    "path": "subject/files/rules.txt",
                    "anchor": "1",
                    "sha256": sha256(source),
                }
            ],
            "evidence": [
                {
                    "evidence_id": "evidence-inv-demo",
                    "kind": "fixture",
                    "artifact_ref": "evidence/inv-demo.txt",
                    "sha256": sha256(evidence),
                    "observed_at": "2026-08-09T00:00:00Z",
                    "environment_class": "synthetic",
                    "authority": "control-group",
                    "freshness": "current",
                }
            ],
            "reach_requirements": {
                "STATIC": "required",
                "SANDBOX": "not_requested",
                "PROD": "not_requested",
            },
            "context": {
                "fixed": ["domain_profile"],
                "iteration": "portable-fixture",
                "emergent": [],
            },
            "human_gate": "required_before_invariant_admit",
        },
    )
    return packet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(materialize(args.out.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
