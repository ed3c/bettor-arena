"""Durable public fixture for ingress and idempotent effect semantics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
import sqlite3

_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_TERMINAL = {"COMMITTED", "COMPENSATED", "HUMAN_ESCALATED"}
_STATES = {"RESERVED", "ATTEMPTED", "UNKNOWN_EFFECT", *_TERMINAL}


class EffectContractError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EffectContractError(message)


def _aware(value: datetime, field: str) -> datetime:
    _require(value.tzinfo is not None, f"{field} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _digest(value: str, field: str) -> str:
    _require(_SHA256.fullmatch(value) is not None, field)
    return value


@dataclass(frozen=True)
class AuthenticatedEvent:
    event_id: str
    provider: str
    payload_digest: str
    occurred_at: datetime
    signature_verified: bool
    replay_window_seconds: int

    def validate(self, *, now: datetime) -> None:
        current = _aware(now, "now")
        occurred = _aware(self.occurred_at, "occurred_at")
        _require(bool(self.event_id.strip()), "event_id")
        _require(bool(self.provider.strip()), "provider")
        _digest(self.payload_digest, "payload_digest")
        _require(self.signature_verified is True, "signature not verified")
        _require(self.replay_window_seconds > 0, "replay_window_seconds")
        age = (current - occurred).total_seconds()
        _require(age >= 0, "event is from the future")
        _require(age <= self.replay_window_seconds, "event outside replay window")


@dataclass(frozen=True)
class WriteIntent:
    effect_id: str
    operation_digest: str
    expected_remote_version: str
    capability: str
    reversible: bool

    def validate(self) -> None:
        _require(bool(self.effect_id.strip()), "effect_id")
        _digest(self.operation_digest, "operation_digest")
        _require(bool(self.expected_remote_version.strip()), "expected_remote_version")
        _require(bool(self.capability.strip()), "capability")
        _require(self.reversible is True, "public fixture must be reversible")


class SqliteEffectFixture:
    """File-backed fixture; not a production queue or remote-effect authority."""

    def __init__(self, path: Path) -> None:
        _require(str(path) != ":memory:", "in-memory database cannot prove durable ingress")
        self.path = path
        self.connection = sqlite3.connect(path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=FULL")
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS inbox (event_id TEXT PRIMARY KEY, provider TEXT NOT NULL, payload_digest TEXT NOT NULL)"
        )
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS effects (effect_id TEXT PRIMARY KEY, operation_digest TEXT NOT NULL, expected_remote_version TEXT NOT NULL, capability TEXT NOT NULL, state TEXT NOT NULL, readback_version TEXT, readback_digest TEXT)"
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def persist_event(self, event: AuthenticatedEvent, *, now: datetime) -> bool:
        event.validate(now=now)
        before = self.connection.total_changes
        self.connection.execute(
            "INSERT OR IGNORE INTO inbox(event_id, provider, payload_digest) VALUES (?, ?, ?)",
            (event.event_id, event.provider, event.payload_digest),
        )
        row = self.connection.execute(
            "SELECT provider, payload_digest FROM inbox WHERE event_id = ?", (event.event_id,)
        ).fetchone()
        _require(row == (event.provider, event.payload_digest), "event identity collision")
        self.connection.commit()
        return self.connection.total_changes > before

    def reserve_effect(self, intent: WriteIntent) -> bool:
        intent.validate()
        before = self.connection.total_changes
        self.connection.execute(
            "INSERT OR IGNORE INTO effects(effect_id, operation_digest, expected_remote_version, capability, state) VALUES (?, ?, ?, ?, 'RESERVED')",
            (intent.effect_id, intent.operation_digest, intent.expected_remote_version, intent.capability),
        )
        row = self.connection.execute(
            "SELECT operation_digest, expected_remote_version, capability FROM effects WHERE effect_id = ?",
            (intent.effect_id,),
        ).fetchone()
        _require(row == (intent.operation_digest, intent.expected_remote_version, intent.capability), "effect identity collision")
        self.connection.commit()
        return self.connection.total_changes > before

    def mark_attempted(self, effect_id: str) -> None:
        self._transition(effect_id, {"RESERVED"}, "ATTEMPTED")

    def mark_timeout_after_possible_mutation(self, effect_id: str) -> None:
        self._transition(effect_id, {"ATTEMPTED"}, "UNKNOWN_EFFECT")

    def retry_allowed(self, effect_id: str) -> bool:
        return self.state(effect_id) not in {"UNKNOWN_EFFECT", *_TERMINAL}

    def commit_after_readback(self, effect_id: str, *, remote_version: str, readback_digest: str) -> None:
        _digest(readback_digest, "readback_digest")
        row = self.connection.execute(
            "SELECT expected_remote_version, state FROM effects WHERE effect_id = ?", (effect_id,)
        ).fetchone()
        _require(row is not None, "unknown effect")
        expected, state = row
        _require(state in {"ATTEMPTED", "UNKNOWN_EFFECT"}, "readback before attempt")
        _require(remote_version == expected, "stale or unexpected remote version")
        self.connection.execute(
            "UPDATE effects SET state='COMMITTED', readback_version=?, readback_digest=? WHERE effect_id=?",
            (remote_version, readback_digest, effect_id),
        )
        self.connection.commit()

    def state(self, effect_id: str) -> str:
        row = self.connection.execute("SELECT state FROM effects WHERE effect_id = ?", (effect_id,)).fetchone()
        _require(row is not None, "unknown effect")
        state = str(row[0])
        _require(state in _STATES, "invalid effect state")
        return state

    def _transition(self, effect_id: str, allowed: set[str], target: str) -> None:
        current = self.state(effect_id)
        _require(current in allowed, f"illegal transition {current}->{target}")
        self.connection.execute("UPDATE effects SET state=? WHERE effect_id=?", (target, effect_id))
        self.connection.commit()
