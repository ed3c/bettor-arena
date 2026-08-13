#!/usr/bin/env python3
from __future__ import annotations
import subprocess
import sys
import unittest
from pathlib import Path

class KnowledgeProviderEvalTests(unittest.TestCase):
    def test_contract_selftest(self) -> None:
        root = Path(__file__).resolve().parents[1]
        completed = subprocess.run(
            [sys.executable, "scripts/check_knowledge_provider_module.py", "--selftest"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

if __name__ == "__main__":
    unittest.main()
