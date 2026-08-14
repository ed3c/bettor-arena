#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


class PdfHarnessIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def run_gate(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "scripts/gates/check_pdf_harness_integration.py", *args],
            cwd=self.root,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_current_tree(self) -> None:
        completed = self.run_gate()
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_mutation_controls(self) -> None:
        completed = self.run_gate("--selftest")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
