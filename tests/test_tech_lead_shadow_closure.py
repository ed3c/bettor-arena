from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/gates/check_tech_lead_shadow_closure.py"
HANDOFF = ROOT / "scripts/gates/check_local_handoff_execution_queue.py"


def import_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CLOSURE = import_module(CHECKER, "closure_checker")
QUEUE = import_module(HANDOFF, "handoff_checker")


def run(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-S", str(path), "--root", str(ROOT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )


class ClosureTests(unittest.TestCase):
    def test_positive_closure(self) -> None:
        result = run(CHECKER)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("active=#172", result.stdout)

    def test_closure_mutations(self) -> None:
        result = run(CHECKER, "--selftest")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("14 mutations", result.stdout)

    def test_one_canonical_queue(self) -> None:
        result = run(HANDOFF)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("one Local Handoff authority", result.stdout)
        self.assertFalse(
            (ROOT / "docs/git/local-handoff-execution-queue.json").exists()
        )

    def test_queue_mutations(self) -> None:
        result = run(HANDOFF, "--selftest")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("11 mutations", result.stdout)

    def test_source_proposal_does_not_become_standard(self) -> None:
        matrix = json.loads(
            (ROOT / "docs/architecture/tech-lead-shadow-monitor/closure-matrix.json")
            .read_text(encoding="utf-8")
        )
        proposal = matrix["source_proposals"][0]
        self.assertEqual(proposal["authority"], "SOURCE_PROPOSAL")
        self.assertIn(
            "source-proposal-to-official-standard",
            proposal["forbidden_promotions"],
        )

    def test_physical_and_human_lanes_are_not_imputed(self) -> None:
        matrix = json.loads(
            (ROOT / "docs/architecture/tech-lead-shadow-monitor/closure-matrix.json")
            .read_text(encoding="utf-8")
        )
        items = {item["id"]: item for item in matrix["closure_items"]}
        self.assertEqual(items["parallel-tech-lead"]["live"], "NOT_EXERCISED")
        self.assertEqual(
            items["procedural-shadow-independent-live"]["live"],
            "NOT_EXERCISED",
        )
        self.assertEqual(items["final-release"]["release"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
