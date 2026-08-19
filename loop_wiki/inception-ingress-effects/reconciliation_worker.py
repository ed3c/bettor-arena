from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import sys

from effect_contract import AuthenticatedEvent, SqliteEffectFixture, WriteIntent

NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)


def main() -> int:
    if len(sys.argv) != 2:
        return 64
    path = Path(sys.argv[1])
    fixture = SqliteEffectFixture(path)
    event = AuthenticatedEvent(
        event_id="evt-restart-001",
        provider="fixture-provider",
        payload_digest="sha256:" + "a" * 64,
        occurred_at=NOW - timedelta(seconds=1),
        signature_verified=True,
        replay_window_seconds=300,
    )
    intent = WriteIntent(
        effect_id="effect-restart-001",
        operation_digest="sha256:" + "b" * 64,
        expected_remote_version="version-7",
        capability="fixture:update-record",
        reversible=True,
    )
    fixture.persist_event(event, now=NOW)
    fixture.reserve_effect(intent)
    fixture.mark_attempted(intent.effect_id)
    fixture.mark_timeout_after_possible_mutation(intent.effect_id)
    # Deliberately skip close(): emulate process death after a possibly-mutating timeout.
    os._exit(91)


if __name__ == "__main__":
    raise SystemExit(main())
