from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

from checkpoint_contract import (
    CheckpointCandidate,
    CheckpointContractError,
    SafeToolTransaction,
    SqliteCheckpointFixture,
)


CRASH_EXIT = 91
PHASES = (
    "prepare_before_commit",
    "prepare_after_commit",
    "recovery_before_commit",
    "recovery_after_commit",
    "activate_before_commit",
    "activate_after_commit",
)


def digest(char: str) -> str:
    return "sha256:" + char * 64


def candidate() -> CheckpointCandidate:
    return CheckpointCandidate(
        checkpoint_id="cp-crash",
        expected_revision=0,
        new_revision=1,
        prior_context_digest=digest("1"),
        new_context_digest=digest("2"),
        state_manifest_digest=digest("3"),
        artifact_manifest_digest=digest("4"),
        unresolved_work_digest=digest("5"),
        lease_manifest_digest=digest("6"),
        pending_effects_digest=digest("7"),
    )


def transaction() -> SafeToolTransaction:
    return SafeToolTransaction(
        transaction_id="txn-crash",
        state="COMPLETE_SAFE",
        call_ids=("call-1",),
        result_call_ids=("call-1",),
    )


def crash_hook(target: str):
    def hook(phase: str) -> None:
        if phase == target:
            os._exit(CRASH_EXIT)

    return hook


def child(path: Path, phase: str) -> None:
    item = candidate()
    if phase.startswith("prepare_"):
        store = SqliteCheckpointFixture(path, fault_hook=crash_hook(phase))
        store.prepare(item, transaction())
        raise AssertionError("fault hook did not terminate prepare")

    with SqliteCheckpointFixture(path) as store:
        store.prepare(item, transaction())

    if phase.startswith("recovery_"):
        store = SqliteCheckpointFixture(path, fault_hook=crash_hook(phase))
        store.record_recovery_probe(item.checkpoint_id, "PASS")
        raise AssertionError("fault hook did not terminate recovery probe")

    with SqliteCheckpointFixture(path) as store:
        store.record_recovery_probe(item.checkpoint_id, "PASS")

    store = SqliteCheckpointFixture(path, fault_hook=crash_hook(phase))
    store.activate(item.checkpoint_id)
    raise AssertionError("fault hook did not terminate activation")


def run_child(path: Path, phase: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, __file__, "--child", str(path), phase],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class CrashMatrixTests(unittest.TestCase):
    def test_all_named_fault_boundaries_exit_abruptly(self) -> None:
        for phase in PHASES:
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "checkpoint.sqlite3"
                result = run_child(path, phase)
                self.assertEqual(
                    result.returncode,
                    CRASH_EXIT,
                    msg=f"{phase}: stdout={result.stdout!r} stderr={result.stderr!r}",
                )

    def test_prepare_crash_has_atomic_visibility(self) -> None:
        expectations = {
            "prepare_before_commit": False,
            "prepare_after_commit": True,
        }
        for phase, should_exist in expectations.items():
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "checkpoint.sqlite3"
                self.assertEqual(run_child(path, phase).returncode, CRASH_EXIT)
                with SqliteCheckpointFixture(path) as reopened:
                    self.assertEqual(reopened.active_revision, 0)
                    if should_exist:
                        self.assertEqual(reopened.read_candidate("cp-crash"), candidate())
                        self.assertEqual(reopened.recovery_state("cp-crash"), "NOT_EXERCISED")
                    else:
                        with self.assertRaisesRegex(CheckpointContractError, "unknown"):
                            reopened.read_candidate("cp-crash")

    def test_recovery_crash_has_atomic_visibility(self) -> None:
        expectations = {
            "recovery_before_commit": "NOT_EXERCISED",
            "recovery_after_commit": "PASS",
        }
        for phase, expected_state in expectations.items():
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "checkpoint.sqlite3"
                self.assertEqual(run_child(path, phase).returncode, CRASH_EXIT)
                with SqliteCheckpointFixture(path) as reopened:
                    self.assertEqual(reopened.active_revision, 0)
                    self.assertEqual(reopened.recovery_state("cp-crash"), expected_state)
                    if expected_state != "PASS":
                        with self.assertRaisesRegex(CheckpointContractError, "recovery probe"):
                            reopened.activate("cp-crash")

    def test_activation_crash_has_atomic_visibility(self) -> None:
        expectations = {
            "activate_before_commit": (0, None),
            "activate_after_commit": (1, "cp-crash"),
        }
        for phase, expected in expectations.items():
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "checkpoint.sqlite3"
                self.assertEqual(run_child(path, phase).returncode, CRASH_EXIT)
                with SqliteCheckpointFixture(path) as reopened:
                    self.assertEqual(
                        (reopened.active_revision, reopened.active_checkpoint_id),
                        expected,
                    )
                    self.assertEqual(reopened.recovery_state("cp-crash"), "PASS")
                    self.assertEqual(reopened.read_candidate("cp-crash"), candidate())

                residue = sorted(
                    item.name for item in Path(directory).iterdir()
                    if item.name.endswith(("-wal", "-shm"))
                )
                self.assertEqual(residue, [], f"SQLite residue remains: {residue}")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--child":
        child(Path(sys.argv[2]), sys.argv[3])
    else:
        unittest.main()
