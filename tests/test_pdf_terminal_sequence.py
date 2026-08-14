from __future__ import annotations

import json
import re
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
        self.assertIn("convergence=#68", result.stdout)

        # The reported head is compared against the queue rather than against a
        # literal. `active=#82` was pinned here as well as in the gate, so
        # advancing one stage failed a test that was only ever restating what
        # the data said -- the third copy of the same mistake #111 is about.
        sequence = json.loads(
            (ROOT / "docs/git/pdf-terminal-sequence.json").read_text(encoding="utf-8")
        )
        active = [item for item in sequence["items"] if item["queue_state"] == "ACTIVE"]
        self.assertEqual(len(active), 1, "exactly one ACTIVE item expected")
        self.assertIn(f"active=#{active[0]['issues'][0]}", result.stdout)
        self.assertIn(f"order={active[0]['order']}", result.stdout)

    def test_mutation_matrix_passes(self) -> None:
        result = self.run_checker("--selftest")
        self.assertEqual(result.returncode, 0, result.stderr)
        match = re.search(r"selftest PASS: (\d+) mutations", result.stdout)
        self.assertIsNotNone(match, result.stdout)

        # A floor rather than an exact count. Pinning the exact number means
        # every added control fails this test, which trains people to update the
        # number instead of reading it; a floor still catches the case that
        # matters, which is controls being removed.
        self.assertGreaterEqual(int(match.group(1)), 19, result.stdout)

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
