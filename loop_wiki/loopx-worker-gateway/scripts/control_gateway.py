#!/usr/bin/env python3
"""Independent subprocess control for the Worker Gateway public CLI."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, text=True, capture_output=True, shell=False, check=False)


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    module = root / "loop_wiki" / "loopx-worker-gateway"
    cli = module / "scripts" / "gateway.py"
    fixture_registry = module / "tests" / "fixtures" / "good" / "fixture-registry.json"
    production_registry = module / "contracts" / "host-registry.json"
    good = module / "tests" / "fixtures" / "good" / "request.json"
    hollow = module / "tests" / "fixtures" / "hollow" / "request.json"

    with tempfile.TemporaryDirectory(prefix="loopx-worker-gateway-control-") as temp:
        out = Path(temp)
        cases = {
            "validate": run([sys.executable, str(cli), "validate", "--registry", str(fixture_registry), "--request", str(good)]),
            "positive": run([sys.executable, str(cli), "run", "--root", str(root), "--registry", str(fixture_registry), "--request", str(good), "--output", str(out / "positive"), "--json"]),
            "hollow": run([sys.executable, str(cli), "run", "--root", str(root), "--registry", str(fixture_registry), "--request", str(hollow), "--output", str(out / "hollow"), "--json"]),
            "not_exercised": run([sys.executable, str(cli), "run", "--root", str(root), "--registry", str(production_registry), "--request", str(good), "--output", str(out / "not-exercised"), "--json"]),
            "missing": run([sys.executable, str(cli), "validate", "--registry", str(fixture_registry), "--request", str(out / "missing.json")]),
            "invocation": run([sys.executable, str(cli)]),
        }

        expected = {
            "validate": 0,
            "positive": 0,
            "hollow": 2,
            "not_exercised": 2,
            "missing": 64,
            "invocation": 64,
        }
        failures = [
            f"{name}: expected {expected[name]}, got {result.returncode}"
            for name, result in cases.items()
            if result.returncode != expected[name]
        ]
        if not failures:
            positive = json.loads(cases["positive"].stdout)
            hollow_receipt = json.loads(cases["hollow"].stdout)
            non_live = json.loads(cases["not_exercised"].stdout)
            if positive["state"] != "PASS":
                failures.append("positive receipt did not PASS")
            if hollow_receipt["state"] != "FAIL" or hollow_receipt["execution"]["exit_code"] != 7:
                failures.append("hollow receipt did not preserve exit 7")
            if non_live["state"] != "NOT_EXERCISED" or non_live["execution"]["executed"]:
                failures.append("production registry presence was treated as execution")

        if failures:
            for failure in failures:
                print(f"loopx-worker-gateway control RED: {failure}", file=sys.stderr)
            return 2

        print(
            "loopx-worker-gateway control PASS: "
            "validate=0 positive=0 hollow=2 not-exercised=2 missing=64 invocation=64"
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
