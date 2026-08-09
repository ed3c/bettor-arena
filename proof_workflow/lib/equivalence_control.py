#!/usr/bin/env python3
"""Build the independent control receipt for the equivalence loop.

The traversal proof supplies a handwritten path claim.  This comparator derives
the canonical inventory from Git at HEAD and refuses a receipt that omits any of
those files.  It also keeps offline, live-carrier, semantic-judge, and Human
authority states separate; an unexercised edge can never inherit an offline
green.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


LOOP_PREFIX = "loop_wiki/evolve-technical-equivalence-research/"


def covered_paths(proof: dict) -> set[str]:
    return {
        step["path"]
        for step in proof.get("steps", [])
        if step.get("path") and step.get("sha256") and step.get("kind") != "note"
    }


def missing_from_proof(tracked: set[str], proof: dict) -> list[str]:
    return sorted(tracked - covered_paths(proof))


def tracked_inventory(repo: Path) -> set[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "-r", "--name-only", "HEAD", LOOP_PREFIX],
        text=True,
        capture_output=True,
        check=True,
    )
    paths = {line for line in result.stdout.splitlines() if line}
    if not paths:
        raise ValueError("tracked equivalence inventory is empty")
    return paths


def stream_manifest(rundir: Path) -> list[dict]:
    records: list[dict] = []
    runlog = rundir / "run.jsonl"
    if not runlog.is_file() or not runlog.read_text(encoding="utf-8").strip():
        raise ValueError("control trace is empty")
    for line in runlog.read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        for lane in ("stdout", "stderr"):
            records.append(
                {
                    "step": item["id"],
                    "path": f"{rundir.name}/{item[lane]['path']}",
                    "sha256": item[lane]["sha256"],
                    "bytes": item[lane]["bytes"],
                }
            )
    return records


def assurance(offline_rc: int, live_state: str) -> dict[str, str]:
    offline = "EXERCISED_PASS" if offline_rc == 0 else "EXERCISED_FAIL"
    maximum = (
        "carrier_exercised_candidate_ready"
        if offline_rc == 0 and live_state == "CARRIER_EXERCISED_PASS"
        else "offline_surface_implemented"
        if offline_rc == 0
        else "no_positive_claim"
    )
    return {
        "offline_surface": offline,
        "live_carrier": live_state,
        "fresh_semantic_judge": "NOT_EXERCISED_REQUIRES_TWO_BLINDED_BATCHES",
        "human_admit": "NOT_EXERCISED_REQUIRES_EXTERNAL_HUMAN",
        "maximum_claim": maximum,
    }


def verdict_exit(control_rc: int, failed: bool) -> int:
    if control_rc == 64:
        return 64
    return 2 if failed else 0


def ensure_receipt_writable(path: Path, *, force: bool) -> None:
    if path.exists() and not force:
        raise ValueError(
            f"receipt already exists: {path}; set "
            "CONTROL_EQUIVALENCE_FORCE_RECEIPT=1 to overwrite explicitly"
        )


def build(
    repo: Path,
    rundir: Path,
    proof_path: Path,
    receipt_path: Path,
    offline_rc: int,
    control_rc: int,
    live_state: str,
) -> int:
    proof = json.loads(proof_path.read_text(encoding="utf-8"))
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    if proof.get("loop") != "equivalence":
        raise ValueError("comparison receipt is not an equivalence proof")
    if proof.get("commit") != head:
        raise ValueError(
            f"proof is stale: receipt={proof.get('commit')} current={head}"
        )
    if proof.get("status") != "passed":
        raise ValueError("equivalence traversal proof is not passed")
    if proof.get("worktree_dirty") is not False or proof_path.name.endswith(
        "-dirty.json"
    ):
        raise ValueError(
            "equivalence traversal proof is dirty; control requires clean HEAD bytes"
        )
    if offline_rc not in {0, 2, 64} or control_rc not in {0, 2, 64}:
        raise ValueError("offline and control exits must be one of 0, 2, 64")

    tracked = tracked_inventory(repo)
    missing = missing_from_proof(tracked, proof)
    classes: dict[str, dict[str, int | str]] = {}
    class_path = rundir / "path-class.txt"
    if not class_path.is_file() or not class_path.read_text(encoding="utf-8").strip():
        raise ValueError("path-ablation result is empty")
    for line in class_path.read_text(encoding="utf-8").splitlines():
        path, classification, exit_text = line.split("\t")
        classes[path] = {"class": classification, "probe_exit": int(exit_text)}

    optional_core = sorted(
        path for path, result in classes.items() if result["class"] != "required"
    )
    states = assurance(offline_rc, live_state)
    failed = bool(control_rc or missing or optional_core)
    receipt = {
        "schema_version": "bettor-arena-control-equivalence-receipt@1.0.0",
        "control_of": "prove_equivalence.sh",
        "method": "run committed offline seams in a disposable worktree; remove core inputs one at a time; plant digest, judge-authority and HEAD-binding defects; derive canonical file inventory from Git rather than the proof step list",
        "run_id": rundir.name,
        "commit": head,
        "status": "failed" if failed else "passed",
        "control_exit": control_rc,
        "compared_against": proof_path.name,
        "compared_against_dirty_stamp": False,
        "proof_digest": proof["molecular_hardening"]["proof_digest"],
        "capture_dir": f"proof_workflow/data/{rundir.name}",
        "capture_dir_tracked": False,
        "captured_streams": stream_manifest(rundir),
        "comparison": {
            "tracked_inventory_count": len(tracked),
            "proof_covered_count": len(tracked) - len(missing),
            "tracked_uncovered": missing,
            "core_input_ablation": classes,
            "core_inputs_not_required": optional_core,
        },
        "assurance": states,
    }
    ensure_receipt_writable(
        receipt_path,
        force=os.environ.get("CONTROL_EQUIVALENCE_FORCE_RECEIPT") == "1",
    )
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"control[equivalence-entry] receipt={receipt_path.relative_to(repo)}")
    for path in missing:
        print(
            f"GAP: tracked mechanism path has no equivalence proof coverage: {path}",
            file=sys.stderr,
        )
    for path in optional_core:
        print(
            f"GAP: core input removal did not turn the loop red: {path}",
            file=sys.stderr,
        )
    return verdict_exit(control_rc, failed)


def selftest() -> int:
    proof = {
        "steps": [
            {"kind": "context", "path": "a", "sha256": "1"},
            {"kind": "note", "path": "b", "sha256": None},
        ]
    }
    checks = [
        ("all-covered", missing_from_proof({"a"}, proof), []),
        ("note-is-not-coverage", missing_from_proof({"a", "b"}, proof), ["b"]),
        ("unlisted-is-gap", missing_from_proof({"a", "c"}, proof), ["c"]),
        (
            "offline-does-not-promote-live",
            assurance(0, "NOT_EXERCISED")["live_carrier"],
            "NOT_EXERCISED",
        ),
        (
            "offline-does-not-promote-human",
            assurance(0, "NOT_EXERCISED")["human_admit"],
            "NOT_EXERCISED_REQUIRES_EXTERNAL_HUMAN",
        ),
        (
            "live-failure-does-not-downgrade-offline",
            assurance(0, "CARRIER_EXERCISED_FAIL")["offline_surface"],
            "EXERCISED_PASS",
        ),
        ("fatal-exit-is-preserved", verdict_exit(64, True), 64),
    ]
    failed = False
    for name, got, want in checks:
        if got != want:
            print(
                f"SELFTEST case failed: {name}: got {got!r}, want {want!r}",
                file=sys.stderr,
            )
            failed = True
    with tempfile.TemporaryDirectory() as tmp:
        receipt = Path(tmp) / "receipt.json"
        receipt.write_text("frozen\n", encoding="utf-8")
        try:
            ensure_receipt_writable(receipt, force=False)
        except ValueError:
            pass
        else:
            print(
                "SELFTEST case failed: receipt-collision-is-fatal",
                file=sys.stderr,
            )
            failed = True
        ensure_receipt_writable(receipt, force=True)
    print("SELFTEST " + ("RED" if failed else "GREEN"))
    return 2 if failed else 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    if len(argv) != 7:
        print(
            "usage: equivalence_control.py <repo> <rundir> <proof> <receipt> <offline-rc> <control-rc> <live-state>",
            file=sys.stderr,
        )
        return 64
    try:
        return build(
            Path(argv[0]).resolve(),
            Path(argv[1]).resolve(),
            Path(argv[2]).resolve(),
            Path(argv[3]).resolve(),
            int(argv[4]),
            int(argv[5]),
            argv[6],
        )
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"control FATAL: {exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
