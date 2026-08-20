from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile

from effect_contract import (
    AuthenticatedEvent,
    EffectContractError,
    SqliteEffectFixture,
    WriteIntent,
)

NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)


def event(**changes) -> AuthenticatedEvent:
    values = {
        "event_id": "evt-001",
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
        "effect_id": "effect-001",
        "operation_digest": "sha256:" + "b" * 64,
        "expected_remote_version": "version-7",
        "capability": "fixture:update-record",
        "reversible": True,
    }
    values.update(changes)
    return WriteIntent(**values)


def must_refuse(label: str, operation, expected: str) -> None:
    try:
        operation()
    except EffectContractError as exc:
        assert expected in str(exc), f"{label}: {exc}"
        return
    raise AssertionError(f"{label}: operation was not refused")


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "inception-effects.sqlite3"
        fixture = SqliteEffectFixture(path)

        assert fixture.persist_event(event(), now=NOW) is True
        assert fixture.persist_event(event(), now=NOW) is False
        must_refuse(
            "event collision",
            lambda: fixture.persist_event(event(payload_digest="sha256:" + "c" * 64), now=NOW),
            "event identity collision",
        )

        must_refuse(
            "bad signature",
            lambda: fixture.persist_event(event(event_id="evt-bad", signature_verified=False), now=NOW),
            "signature not verified",
        )
        must_refuse(
            "replay window",
            lambda: fixture.persist_event(event(event_id="evt-old", occurred_at=NOW - timedelta(minutes=10)), now=NOW),
            "replay window",
        )

        assert fixture.reserve_effect(intent()) is True
        assert fixture.reserve_effect(intent()) is False
        must_refuse(
            "effect collision",
            lambda: fixture.reserve_effect(intent(operation_digest="sha256:" + "d" * 64)),
            "effect identity collision",
        )

        fixture.mark_attempted("effect-001")
        assert fixture.state("effect-001") == "ATTEMPTED"
        fixture.mark_timeout_after_possible_mutation("effect-001")
        assert fixture.state("effect-001") == "UNKNOWN_EFFECT"
        assert fixture.retry_allowed("effect-001") is False

        must_refuse(
            "stale remote version",
            lambda: fixture.commit_after_readback(
                "effect-001",
                remote_version="version-6",
                readback_digest="sha256:" + "e" * 64,
            ),
            "remote version",
        )
        fixture.commit_after_readback(
            "effect-001",
            remote_version="version-7",
            readback_digest="sha256:" + "f" * 64,
        )
        assert fixture.state("effect-001") == "COMMITTED"
        assert fixture.retry_allowed("effect-001") is False
        fixture.close()

        reopened = SqliteEffectFixture(path)
        assert reopened.state("effect-001") == "COMMITTED"
        assert reopened.persist_event(event(), now=NOW) is False
        reopened.close()

    must_refuse(
        "in-memory durability",
        lambda: SqliteEffectFixture(Path(":memory:")),
        "in-memory database",
    )
    must_refuse(
        "non-reversible public fixture",
        lambda: intent(reversible=False).validate(),
        "reversible",
    )
    must_refuse(
        "naive event time",
        lambda: event(occurred_at=NOW.replace(tzinfo=None)).validate(now=NOW),
        "timezone-aware",
    )

    print("PASS inception-a6 durable inbox and effect disagreement controls")


if __name__ == "__main__":
    main()
