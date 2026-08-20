from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from effect_contract import (
    AuthenticatedEvent,
    EffectContractError,
    SqliteEffectFixture,
    WriteIntent,
)

NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)


def event(event_id: str = "evt-restart") -> AuthenticatedEvent:
    return AuthenticatedEvent(
        event_id=event_id,
        provider="fixture-provider",
        payload_digest="sha256:" + "a" * 64,
        occurred_at=NOW - timedelta(seconds=1),
        signature_verified=True,
        replay_window_seconds=300,
    )


def intent(effect_id: str = "effect-restart") -> WriteIntent:
    return WriteIntent(
        effect_id=effect_id,
        operation_digest="sha256:" + "b" * 64,
        expected_remote_version="version-42",
        capability="fixture:update-record",
        reversible=True,
    )


class RestartReconciliationTests(unittest.TestCase):
    def test_unknown_effect_survives_restart_and_blind_retry_stays_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "effects.sqlite3"
            first = SqliteEffectFixture(path)
            self.assertTrue(first.persist_event(event(), now=NOW))
            self.assertTrue(first.reserve_effect(intent()))
            first.mark_attempted("effect-restart")
            first.mark_timeout_after_possible_mutation("effect-restart")
            self.assertEqual(first.state("effect-restart"), "UNKNOWN_EFFECT")
            self.assertFalse(first.retry_allowed("effect-restart"))
            first.close()

            second = SqliteEffectFixture(path)
            self.assertEqual(
                second.readback("effect-restart"),
                (
                    "version-42",
                    "fixture:update-record",
                    "UNKNOWN_EFFECT",
                    None,
                    None,
                ),
            )
            self.assertFalse(second.retry_allowed("effect-restart"))
            with self.assertRaisesRegex(EffectContractError, "remote version"):
                second.commit_after_readback(
                    "effect-restart",
                    remote_version="version-41",
                    readback_digest="sha256:" + "c" * 64,
                )
            self.assertEqual(second.state("effect-restart"), "UNKNOWN_EFFECT")
            self.assertFalse(second.retry_allowed("effect-restart"))

            second.commit_after_readback(
                "effect-restart",
                remote_version="version-42",
                readback_digest="sha256:" + "d" * 64,
            )
            self.assertEqual(second.state("effect-restart"), "COMMITTED")
            self.assertFalse(second.retry_allowed("effect-restart"))
            second.close()

            third = SqliteEffectFixture(path)
            self.assertEqual(
                third.readback("effect-restart"),
                (
                    "version-42",
                    "fixture:update-record",
                    "COMMITTED",
                    "version-42",
                    "sha256:" + "d" * 64,
                ),
            )
            self.assertFalse(third.retry_allowed("effect-restart"))
            self.assertFalse(third.persist_event(event(), now=NOW))
            third.close()

            residue = sorted(
                item.name
                for item in Path(directory).iterdir()
                if item.name.endswith(("-wal", "-shm"))
            )
            self.assertEqual(residue, [], f"SQLite terminal residue remains: {residue}")

    def test_restart_matrix_preserves_each_nonterminal_state(self) -> None:
        for target_state in ("RESERVED", "ATTEMPTED", "UNKNOWN_EFFECT"):
            with self.subTest(target_state=target_state), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "effects.sqlite3"
                store = SqliteEffectFixture(path)
                store.persist_event(event(f"evt-{target_state.lower()}"), now=NOW)
                store.reserve_effect(intent(f"effect-{target_state.lower()}"))
                effect_id = f"effect-{target_state.lower()}"
                if target_state in {"ATTEMPTED", "UNKNOWN_EFFECT"}:
                    store.mark_attempted(effect_id)
                if target_state == "UNKNOWN_EFFECT":
                    store.mark_timeout_after_possible_mutation(effect_id)
                store.close()

                reopened = SqliteEffectFixture(path)
                self.assertEqual(reopened.state(effect_id), target_state)
                self.assertEqual(
                    reopened.retry_allowed(effect_id),
                    target_state != "UNKNOWN_EFFECT",
                )
                reopened.close()

    def test_invalid_readback_digest_cannot_reconcile_unknown_effect(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "effects.sqlite3"
            store = SqliteEffectFixture(path)
            store.reserve_effect(intent())
            store.mark_attempted("effect-restart")
            store.mark_timeout_after_possible_mutation("effect-restart")
            store.close()

            reopened = SqliteEffectFixture(path)
            with self.assertRaisesRegex(EffectContractError, "readback_digest"):
                reopened.commit_after_readback(
                    "effect-restart",
                    remote_version="version-42",
                    readback_digest="not-a-digest",
                )
            self.assertEqual(reopened.state("effect-restart"), "UNKNOWN_EFFECT")
            reopened.close()


if __name__ == "__main__":
    unittest.main()
