#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


class KnowledgeProviderEvalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]

    def run_command(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, *args],
            cwd=self.root,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_fixture_suite(self) -> None:
        completed = self.run_command("scripts/evaluate_knowledge_providers.py")
        self.assertEqual(
            completed.returncode,
            0,
            completed.stdout + completed.stderr,
        )
        self.assertIn("pairs=7/7", completed.stdout)

    def test_contract_selftest(self) -> None:
        completed = self.run_command(
            "scripts/check_knowledge_provider_module.py",
            "--selftest",
        )
        self.assertEqual(
            completed.returncode,
            0,
            completed.stdout + completed.stderr,
        )


if __name__ == "__main__":
    unittest.main()
