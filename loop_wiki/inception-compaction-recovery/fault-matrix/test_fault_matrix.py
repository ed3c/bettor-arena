from __future__ import annotations

from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0, str(PARENT))

from checkpoint_contract import (  # noqa: E402
    CheckpointContractError,
    SqliteCheckpointFixture,
)

WORKER = HERE / "fault_worker.py"
EXPECTED_CODES = {
    "before-prepare": 81,
    "after-prepare": 82,
    "before-recovery": 83,
    "after-recovery": 84,
    "before-activation": 85,
    "after-activation": 86,
    "uncommitted-meta": 87,
}


class CrashFaultMatrixTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.database = self.root / "checkpoint.sqlite3"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_worker(self, mode: str) -> None:
        result = subprocess.run(
            [sys.executable, str(WORKER), mode, str(self.database)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        )
        self.assertEqual(
            result.returncode,
            EXPECTED_CODES[mode],
            msg=f"mode={mode} stdout={result.stdout!r} stderr={result.stderr!r}",
        )

    def assert_integrity(self) -> None:
        db = sqlite3.connect(self.database)
        try:
            row = db.execute("PRAGMA integrity_check").fetchone()
            self.assertEqual(row, ("ok",))
        finally:
            db.close()

    def test_crash_before_prepare_leaves_no_candidate(self) -> None:
        self.run_worker("before-prepare")
        with SqliteCheckpointFixture(self.database) as store:
            self.assertEqual(store.active_revision, 0)
            self.assertIsNone(store.active_checkpoint_id)
            with self.assertRaisesRegex(CheckpointContractError, "unknown checkpoint"):
                store.read_candidate("cp-fault-1")
        self.assert_integrity()

    def test_prepare_commit_survives_abrupt_process_exit(self) -> None:
        self.run_worker("after-prepare")
        with SqliteCheckpointFixture(self.database) as store:
            self.assertEqual(store.active_revision, 0)
            self.assertIsNone(store.active_checkpoint_id)
            self.assertEqual(store.read_candidate("cp-fault-1").new_revision, 1)
        self.assert_integrity()

    def test_crash_before_recovery_does_not_unlock_activation(self) -> None:
        self.run_worker("after-prepare")
        self.run_worker("before-recovery")
        with SqliteCheckpointFixture(self.database) as store:
            with self.assertRaisesRegex(CheckpointContractError, "recovery probe"):
                store.activate("cp-fault-1")
            self.assertEqual(store.active_revision, 0)
        self.assert_integrity()

    def test_recovery_probe_commit_survives_abrupt_exit_without_activation(self) -> None:
        self.run_worker("after-prepare")
        self.run_worker("after-recovery")
        with SqliteCheckpointFixture(self.database) as store:
            self.assertEqual(store.active_revision, 0)
            self.assertIsNone(store.active_checkpoint_id)
        self.assert_integrity()

    def test_crash_before_activation_preserves_previous_active_revision(self) -> None:
        self.run_worker("after-prepare")
        self.run_worker("after-recovery")
        self.run_worker("before-activation")
        with SqliteCheckpointFixture(self.database) as store:
            self.assertEqual(store.active_revision, 0)
            self.assertIsNone(store.active_checkpoint_id)
        self.assert_integrity()

    def test_activation_commit_survives_abrupt_exit_and_retains_candidate(self) -> None:
        self.run_worker("after-prepare")
        self.run_worker("after-recovery")
        self.run_worker("after-activation")
        with SqliteCheckpointFixture(self.database) as store:
            self.assertEqual(store.active_revision, 1)
            self.assertEqual(store.active_checkpoint_id, "cp-fault-1")
            self.assertEqual(store.read_candidate("cp-fault-1").checkpoint_id, "cp-fault-1")
        self.assert_integrity()

    def test_uncommitted_metadata_mutation_is_rolled_back_after_crash(self) -> None:
        self.run_worker("after-prepare")
        self.run_worker("after-recovery")
        self.run_worker("after-activation")
        self.run_worker("uncommitted-meta")
        with SqliteCheckpointFixture(self.database) as store:
            self.assertEqual(store.active_revision, 1)
            self.assertEqual(store.active_checkpoint_id, "cp-fault-1")
            self.assertEqual(store.read_candidate("cp-fault-1").new_revision, 1)
        self.assert_integrity()


if __name__ == "__main__":
    unittest.main()
