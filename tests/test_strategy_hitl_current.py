from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "gates" / "check_strategy_hitl_current.py"


class StrategyHitlCurrentTest(unittest.TestCase):
    def run_checker(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CHECKER), "--root", str(ROOT), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_current_subject_and_receipt_pass(self) -> None:
        with tempfile.TemporaryDirectory(prefix="strategy-hitl-current-") as tmp:
            receipt = Path(tmp) / "receipt.json"
            result = self.run_checker(
                "--observed-at",
                "UNIT_TEST",
                "--output",
                str(receipt),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PASS Stage 2 Strategy/HITL validation", result.stdout)
            self.assertTrue(receipt.is_file())
            self.assertIn('"result": "PASS"', receipt.read_text(encoding="utf-8"))
            self.assertIn(
                '"langgraph_checkpoint_backend": "NOT_EXERCISED"',
                receipt.read_text(encoding="utf-8"),
            )

    def test_mutation_matrix_passes(self) -> None:
        result = self.run_checker("--selftest")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("selftest PASS: 13 mutations", result.stdout)

    def test_missing_root_is_checked_failure(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CHECKER), "--root", str(ROOT / "missing-root")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("repository root not found", result.stderr)


if __name__ == "__main__":
    unittest.main()
