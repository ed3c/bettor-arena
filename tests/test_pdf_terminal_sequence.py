from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "gates" / "check_pdf_terminal_sequence.py"


class PdfTerminalSequenceTest(unittest.TestCase):
    def run_checker(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CHECKER), "--root", str(ROOT), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_repository_sequence_passes(self) -> None:
        result = self.run_checker()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("pdf-terminal-sequence PASS", result.stdout)
        self.assertIn("active=#82", result.stdout)
        self.assertIn("convergence=#68", result.stdout)

    def test_mutation_matrix_passes(self) -> None:
        result = self.run_checker("--selftest")
        self.assertEqual(result.returncode, 0, result.stderr)
        # 15 since human-boundary gained a second control: the original mutation
        # tripped the length floor before reaching the marker check it was
        # written for, so the marker case and the floor case are now separate.
        self.assertIn("selftest PASS: 15 mutations", result.stdout)

    def test_invalid_root_is_checked_failure(self) -> None:
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
