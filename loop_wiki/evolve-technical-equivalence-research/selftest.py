#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from equivalence import digest
from drift import assess_hard_drift

ROOT = Path(__file__).resolve().parent


def run(name: str, argv: list[str], env: dict[str, str] | None = None) -> dict:
    result = subprocess.run(
        argv,
        cwd=ROOT.parents[1],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    value = {"name": name, "exit": result.returncode}
    for line in result.stdout.splitlines():
        if line.startswith("PASS: route_result="):
            value["route_result"] = line.split("=", 1)[1]
    return value


def live_observation(route_path: Path) -> tuple[dict, dict]:
    route = json.loads(route_path.read_text(encoding="utf-8"))
    receipt = json.loads(
        Path(route["artifacts"]["adapter_receipt"]).read_text(encoding="utf-8")
    )
    result = json.loads(
        Path(route["artifacts"]["research_result"]).read_text(encoding="utf-8")
    )
    invocations = receipt["invocations"]
    candidates = result["candidates"]
    research_fields = {
        "candidate_id",
        "claim",
        "repo_url",
        "commit",
        "spdx",
        "source_urls",
        "code_anchors",
        "load_bearing",
        "equivalence_uncertain",
        "wrong_decision_costly",
        "inference",
        "code_audit",
        "probe",
    }
    groundable = sum(
        1
        for item in candidates
        if item.get("inference") is True or research_fields.issubset(item)
    )
    count = len(invocations)
    observation = {
        "schema_version": "technical-equivalence-canary-observation@1.0.0",
        "metrics": {
            "candidate_appendix_rate": sum(
                item.get("structured_candidate_count", 0) > 0 for item in invocations
            )
            / count,
            "completion_rate": sum(
                bool(item.get("raw_exit") == 0 and item.get("output_sha256"))
                for item in invocations
            )
            / count,
            "groundable_candidate_rate": groundable / len(candidates),
        },
        "critical_false_pass": False,
        "critical_false_pass_status": "NOT_EXERCISED_REQUIRES_FRESH_JUDGE",
        "adapter_receipt_digest": receipt["adapter_receipt_digest"],
        "research_result_digest": result["research_result_digest"],
    }
    observation["observation_digest"] = digest(observation, "observation_digest")
    return observation, route


def load_history(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("live history must be a JSON array")
    return value


def assurance_states(*, red: bool, live: str) -> dict[str, str]:
    live_state = live
    maximum = (
        "carrier_exercised_candidate_ready"
        if live == "CARRIER_EXERCISED_PASS" and not red
        else "offline_surface_implemented"
        if not red
        else "no_positive_claim"
    )
    return {
        "offline_surface": "EXERCISED_FAIL" if red else "EXERCISED_PASS",
        "live_carrier": live_state,
        "fresh_semantic_judge": "NOT_EXERCISED_REQUIRES_TWO_BLINDED_BATCHES",
        "human_admit": "NOT_EXERCISED_REQUIRES_EXTERNAL_HUMAN",
        "maximum_claim": maximum,
    }


def main() -> int:
    target_peer = Path(
        os.environ.get("SKILL_BETTOR_PEER", ROOT.parents[2] / "skill-bettor")
    ).resolve()
    hard = assess_hard_drift(target_peer)
    checks = [
        run("public-cli", [sys.executable, str(ROOT / "tests" / "test_cli.py")]),
        run("drift-gates", [sys.executable, str(ROOT / "tests" / "test_drift.py")]),
        run(
            "profile-controls",
            [sys.executable, str(ROOT / "profile_validator.py"), "--selftest"],
        ),
        run(
            "legacy-vs-rebuild",
            [sys.executable, str(ROOT / "legacy_compare.py"), "--selftest"],
        ),
        {
            "name": "hard-drift",
            "exit": 0 if hard["state"] in {"not_admitted", "no_drift"} else 2,
            "state": hard["state"],
        },
    ]
    offline_red = any(check["exit"] != 0 for check in checks)
    live = "NOT_EXERCISED"
    live_root: Path | None = None
    if os.environ.get("EQUIVALENCE_LIVE") == "1":
        source_peer = Path(
            os.environ.get("ANTIGRAVITY_PEER", ROOT.parents[2] / "antigravity")
        ).resolve()
        configured_live_root = os.environ.get("EQUIVALENCE_LIVE_RUN_ROOT")
        live_root = (
            Path(configured_live_root).resolve()
            if configured_live_root
            else ROOT / "_runs" / "live" / str(time.time_ns())
        )
        request = {
            "schema_version": "technical-equivalence-request@1.0.0",
            "request_id": "gemini-live-canary",
            "original_intent_ssot": "loopctl equivalence test --live",
            "technical_viewpoint": (
                "A resumable multi-stage research workflow must bind every transition "
                "to immutable input and output digests and fail closed on absent evidence."
            ),
            "source_anchors": [
                {
                    "repo": "antigravity",
                    "commit": "c151ac49b6d4dd664e61d7050e14a91e5dce3327",
                    "path": "data.js",
                    "anchor": "PATH_B_REFINE_TEMPLATE",
                }
            ],
            "fixed_context": ["profile/technical-equivalence.md"],
            "iteration_context": [],
            "emergent_context": [],
            "target_binding": ".skill-bindings/dr-research-loop/technical-equivalence",
        }
        request["request_digest"] = digest(request, "request_digest")
        request_path = live_root / "canary-request.json"
        request_path.parent.mkdir(parents=True, exist_ok=True)
        request_path.write_text(
            json.dumps(request, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        env = dict(os.environ)
        env["EQUIVALENCE_RUN_ROOT"] = str(live_root / "runs")
        check = run(
            "gemini-live",
            [
                sys.executable,
                str(ROOT / "equivalence.py"),
                "run",
                "--request",
                str(request_path),
                "--target-peer",
                str(target_peer),
                "--source-peer",
                str(source_peer),
                "--execute-gemini",
            ],
            env=env,
        )
        route_value = check.pop("route_result", None)
        if check["exit"] == 0 and route_value:
            observation, _route = live_observation(Path(route_value))
            history_path = (
                ROOT / "_runs" / "live-history" / "human-admitted-observations.json"
            )
            history = load_history(history_path)
            soft = {
                "state": "not_exercised",
                "reason": "critical false-pass requires a fresh semantic judge before this observation may enter the Human-admitted baseline",
                "human_admitted_baseline_count": len(history),
            }
            drift_receipt = {
                "schema_version": "technical-equivalence-drift-receipt@1.0.0",
                "hard": hard,
                "soft": soft,
                "observation": observation,
            }
            drift_receipt["drift_receipt_digest"] = digest(
                drift_receipt, "drift_receipt_digest"
            )
            drift_path = live_root / "drift-receipt.json"
            drift_path.write_text(
                json.dumps(drift_receipt, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )
            print(f"drift_receipt={drift_path}")
            check["note"] = (
                "carrier_exercised; semantic_false_pass_and_human_admitted_jitter_baseline_not_exercised"
            )
        checks.append(check)
        live = (
            "CARRIER_EXERCISED_PASS" if check["exit"] == 0 else "CARRIER_EXERCISED_FAIL"
        )
    red = any(check["exit"] != 0 for check in checks)
    profile_sha = hashlib.sha256(
        (ROOT / "profile" / "technical-equivalence.md").read_bytes()
    ).hexdigest()
    receipt = {
        "schema_version": "technical-equivalence-selftest-receipt@1.1.0",
        "status": "failed" if red else "passed",
        "live_gemini": live,
        "assurance": assurance_states(red=offline_red, live=live),
        "hard_drift": hard,
        "profile_sha256": f"sha256:{profile_sha}",
        "checks": checks,
    }
    default_receipt = (
        live_root / "selftest-receipt.json"
        if live_root is not None
        else ROOT / "_runs" / "selftest" / "receipt.json"
    )
    path = Path(os.environ.get("EQUIVALENCE_RECEIPT_PATH", default_receipt))
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if (
        path.exists()
        and path.read_text(encoding="utf-8") != encoded
        and os.environ.get("EQUIVALENCE_FORCE_RECEIPT") != "1"
    ):
        print(
            f"SELFTEST FATAL: receipt collision {path}; set EQUIVALENCE_FORCE_RECEIPT=1",
            file=sys.stderr,
        )
        return 64
    path.write_text(encoded, encoding="utf-8")
    print(f"receipt={path}")
    print("SELFTEST " + ("RED" if red else "GREEN") + f" live={live}")
    return 2 if red else 0


if __name__ == "__main__":
    raise SystemExit(main())
