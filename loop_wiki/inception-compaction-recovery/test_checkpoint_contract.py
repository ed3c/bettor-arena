from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from checkpoint_contract import (
    CheckpointCandidate,
    CheckpointContractError,
    SafeToolTransaction,
    SqliteCheckpointFixture,
)


def digest(char: str) -> str:
    return "sha256:" + char * 64


def candidate(*, checkpoint_id: str = "cp-1", expected_revision: int = 0) -> CheckpointCandidate:
    return CheckpointCandidate(
        checkpoint_id=checkpoint_id,
        expected_revision=expected_revision,
        new_revision=expected_revision + 1,
        prior_context_digest=digest("1"),
        new_context_digest=digest("2" if expected_revision == 0 else "3"),
        state_manifest_digest=digest("4"),
        artifact_manifest_digest=digest("5"),
        unresolved_work_digest=digest("6"),
        lease_manifest_digest=digest("7"),
        pending_effects_digest=digest("8"),
    )


def safe_transaction() -> SafeToolTransaction:
    return SafeToolTransaction(
        transaction_id="txn-1",
        state="COMPLETE_SAFE",
        call_ids=("call-a", "call-b"),
        result_call_ids=("call-a", "call-b"),
    )


class CheckpointContractTests(unittest.TestCase):
    def test_file_backed_checkpoint_survives_reopen_and_activation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.sqlite3"
            first = candidate()
            with SqliteCheckpointFixture(path) as store:
                store.prepare(first, safe_transaction())
                self.assertEqual(store.active_revision, 0)
                self.assertIsNone(store.active_checkpoint_id)
                store.record_recovery_probe(first.checkpoint_id, "PASS")
                self.assertEqual(store.activate(first.checkpoint_id), 1)

            with SqliteCheckpointFixture(path) as reopened:
                self.assertEqual(reopened.active_revision, 1)
                self.assertEqual(reopened.active_checkpoint_id, "cp-1")
                self.assertEqual(reopened.read_candidate("cp-1"), first)

                second = candidate(checkpoint_id="cp-2", expected_revision=1)
                reopened.prepare(second, safe_transaction())
                reopened.record_recovery_probe("cp-2", "PASS")
                reopened.activate("cp-2")
                self.assertEqual(reopened.active_revision, 2)
                # Rollback evidence is retained instead of deleting the prior row.
                self.assertEqual(reopened.read_candidate("cp-1"), first)

    def test_in_memory_store_is_refused(self) -> None:
        with self.assertRaisesRegex(CheckpointContractError, "in-memory"):
            SqliteCheckpointFixture(":memory:")

    def test_open_or_reordered_tool_transaction_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.sqlite3"
            with SqliteCheckpointFixture(path) as store:
                with self.assertRaisesRegex(CheckpointContractError, "COMPLETE_SAFE"):
                    store.prepare(
                        candidate(), replace(safe_transaction(), state="OPEN")
                    )
                with self.assertRaisesRegex(CheckpointContractError, "identity and order"):
                    store.prepare(
                        candidate(),
                        replace(
                            safe_transaction(),
                            result_call_ids=("call-b", "call-a"),
                        ),
                    )

    def test_stale_revision_and_skipped_revision_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.sqlite3"
            with SqliteCheckpointFixture(path) as store:
                bad_increment = replace(candidate(), new_revision=2)
                with self.assertRaisesRegex(CheckpointContractError, "increment exactly once"):
                    store.prepare(bad_increment, safe_transaction())

                stale = candidate(checkpoint_id="cp-stale", expected_revision=1)
                with self.assertRaisesRegex(CheckpointContractError, "stale expected revision"):
                    store.prepare(stale, safe_transaction())

    def test_activation_requires_independent_recovery_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.sqlite3"
            with SqliteCheckpointFixture(path) as store:
                item = candidate()
                store.prepare(item, safe_transaction())
                with self.assertRaisesRegex(CheckpointContractError, "recovery probe"):
                    store.activate(item.checkpoint_id)
                store.record_recovery_probe(item.checkpoint_id, "FAIL")
                with self.assertRaisesRegex(CheckpointContractError, "recovery probe"):
                    store.activate(item.checkpoint_id)
                self.assertEqual(store.active_revision, 0)

    def test_same_checkpoint_is_idempotent_but_collision_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.sqlite3"
            with SqliteCheckpointFixture(path) as store:
                item = candidate()
                first = store.prepare(item, safe_transaction())
                second = store.prepare(item, safe_transaction())
                self.assertEqual(first, second)

                collision = replace(item, artifact_manifest_digest=digest("9"))
                with self.assertRaisesRegex(CheckpointContractError, "collision"):
                    store.prepare(collision, safe_transaction())

    def test_invalid_digest_is_refused_before_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.sqlite3"
            with SqliteCheckpointFixture(path) as store:
                with self.assertRaisesRegex(CheckpointContractError, "sha256"):
                    store.prepare(
                        replace(candidate(), state_manifest_digest="not-a-digest"),
                        safe_transaction(),
                    )


if __name__ == "__main__":
    unittest.main()
