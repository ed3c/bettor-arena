from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/gates/check_git_town_stack_docs.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-S", str(CHECKER), "--root", str(ROOT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )


class StackSnapshotTests(unittest.TestCase):
    def test_current_snapshot_passes(self) -> None:
        result = run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("active=#172", result.stdout)

    def test_mutations_turn_red(self) -> None:
        result = run("--selftest")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("10 mutations", result.stdout)


if __name__ == "__main__":
    unittest.main()
