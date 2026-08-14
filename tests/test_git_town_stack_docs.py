from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/gates/check_git_town_stack_docs.py"


def load_module():
    spec = importlib.util.spec_from_file_location("git_town_stack_docs", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GitTownStackDocsTest(unittest.TestCase):
    def test_repository_contract_passes(self) -> None:
        module = load_module()
        self.assertEqual([], module.check(ROOT))

    def test_public_cli_and_selftest(self) -> None:
        checked = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(ROOT)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, checked.returncode, checked.stderr)
        self.assertIn("PASS Git Town Stack governance", checked.stdout)

        selftest = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(ROOT), "--selftest"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, selftest.returncode, selftest.stderr)
        self.assertIn("13 mutations", selftest.stdout)


if __name__ == "__main__":
    unittest.main()
