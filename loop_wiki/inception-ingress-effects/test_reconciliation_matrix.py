from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from effect_contract import (
    AuthenticatedEvent,
    EffectContractError,
    SqliteEffectFixture,
    WriteIntent,
)

HERE = Path(__file__).resolve().parent
WORKER = HERE / "reconciliation_worker.py"
NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)


def event(**changes) -> AuthenticatedEvent:
    values = {
        "event_id": "evt-restart-001",
        "provider": "fixture-provider",
        "payload_digest": "sha256:" + "a" * 64,
        "occurred_at": NOW - timedelta(seconds=1),
        "signature_verified": True,
        "replay_window_seconds": 300,
    }
    values.update(changes)
    return AuthenticatedEvent(**values)


def intent(**changes) -> WriteIntent:
    values = {
        "effect_id": "effect-restart-001",
        "operation_digest": "sha256:" + "b" * 64,
        "expected_remote_version": "version-7",
        "capability": "fixture:update-record",
        "reversible": True,
    }
    values.update(changes)
    return WriteIntent(**values)


class RestartReconciliationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="inception-a6-restart-"))
        self.database = self.root / "effects.sqlite3"

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
        self.assertFalse(self.root.exists(), "fixture cleanup left path residue")

    def crash_after_unknown_effect(self) -> None:
        result = subprocess.run(
            [sys.executable, str(WORKER), str(self.database)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        )
        self.assertEqual(
            result.returncode,
            91,
            msg=f"worker stdout={result.stdout!r} stderr={result.stderr!r}",
        )

    def test_unknown_effect_survives_process_death_and_blocks_blind_retry(self) -> None:
        self.crash_after_unknown_effect()
        reopened = SqliteEffectFixture(self.database)
        try:
            self.assertEqual(reopened.state("effect-restart-001"), "UNKNOWN_EFFECT")
            self.assertFalse(reopened.retry_allowed("effect-restart-001"))
            self.assertFalse(reopened.persist_event(event(), now=NOW))
            self.assertFalse(reopened.reserve_effect(intent()))
        finally:
            reopened.close()

    def test_stale_readback_does_not_clear_unknown_effect(self) -> None:
        self.crash_after_unknown_effect()
        reopened = SqliteEffectFixture(self.database)
        try:
            with self.assertRaisesRegex(EffectContractError, "remote version"):
                reopened.commit_after_readback(
                    "effect-restart-001",
                    remote_version="version-6",
                    readback_digest="sha256:" + "c" * 64,
                )
            self.assertEqual(reopened.state("effect-restart-001"), "UNKNOWN_EFFECT")
            self.assertFalse(reopened.retry_allowed("effect-restart-001"))
        finally:
            reopened.close()

        second = SqliteEffectFixture(self.database)
        try:
            self.assertEqual(second.state("effect-restart-001"), "UNKNOWN_EFFECT")
        finally:
            second.close()

    def test_exact_readback_reconciles_then_persists_committed_state(self) -> None:
        self.crash_after_unknown_effect()
        reopened = SqliteEffectFixture(self.database)
        try:
            reopened.commit_after_readback(
                "effect-restart-001",
                remote_version="version-7",
                readback_digest="sha256:" + "d" * 64,
            )
            self.assertEqual(reopened.state("effect-restart-001"), "COMMITTED")
            self.assertFalse(reopened.retry_allowed("effect-restart-001"))
        finally:
            reopened.close()

        final = SqliteEffectFixture(self.database)
        try:
            self.assertEqual(final.state("effect-restart-001"), "COMMITTED")
            self.assertFalse(final.retry_allowed("effect-restart-001"))
            self.assertFalse(final.persist_event(event(), now=NOW))
        finally:
            final.close()

    def test_identity_collisions_remain_refused_after_restart(self) -> None:
        self.crash_after_unknown_effect()
        reopened = SqliteEffectFixture(self.database)
        try:
            with self.assertRaisesRegex(EffectContractError, "event identity collision"):
                reopened.persist_event(
                    event(payload_digest="sha256:" + "e" * 64),
                    now=NOW,
                )
            with self.assertRaisesRegex(EffectContractError, "effect identity collision"):
                reopened.reserve_effect(
                    intent(operation_digest="sha256:" + "f" * 64)
                )
            self.assertEqual(reopened.state("effect-restart-001"), "UNKNOWN_EFFECT")
        finally:
            reopened.close()


if __name__ == "__main__":
    unittest.main()
