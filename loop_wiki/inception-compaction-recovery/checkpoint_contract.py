"""Bounded durable checkpoint contract for the Inception A1 public fixture.

This module is deliberately small: it proves the persistence/CAS/recovery semantics
needed before a production compactor can be admitted. It is not a second LoopX
ledger and it does not summarize model context.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Literal


_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
FaultHook = Callable[[str], None]


class CheckpointContractError(ValueError):
    """Raised when a checkpoint transition fails closed."""


def _require_digest(name: str, value: str) -> None:
    if not _DIGEST.fullmatch(value):
        raise CheckpointContractError(f"{name} must be an exact sha256 digest")


@dataclass(frozen=True)
class SafeToolTransaction:
    transaction_id: str
    state: Literal["COMPLETE_SAFE", "OPEN", "FAILED"]
    call_ids: tuple[str, ...]
    result_call_ids: tuple[str, ...]

    def validate_for_compaction(self) -> None:
        if not self.transaction_id.strip():
            raise CheckpointContractError("transaction_id is required")
        if self.state != "COMPLETE_SAFE":
            raise CheckpointContractError("tool transaction is not COMPLETE_SAFE")
        if not self.call_ids:
            raise CheckpointContractError("tool transaction must contain at least one call")
        if self.call_ids != self.result_call_ids:
            raise CheckpointContractError(
                "tool call/result identity and order must remain atomic"
            )
        if len(set(self.call_ids)) != len(self.call_ids):
            raise CheckpointContractError("tool call ids must be unique")


@dataclass(frozen=True)
class CheckpointCandidate:
    checkpoint_id: str
    expected_revision: int
    new_revision: int
    prior_context_digest: str
    new_context_digest: str
    state_manifest_digest: str
    artifact_manifest_digest: str
    unresolved_work_digest: str
    lease_manifest_digest: str
    pending_effects_digest: str

    def validate(self) -> None:
        if not self.checkpoint_id.strip():
            raise CheckpointContractError("checkpoint_id is required")
        if self.expected_revision < 0:
            raise CheckpointContractError("expected_revision must be non-negative")
        if self.new_revision != self.expected_revision + 1:
            raise CheckpointContractError("new_revision must increment exactly once")
        for name in (
            "prior_context_digest",
            "new_context_digest",
            "state_manifest_digest",
            "artifact_manifest_digest",
            "unresolved_work_digest",
            "lease_manifest_digest",
            "pending_effects_digest",
        ):
            _require_digest(name, getattr(self, name))
        if self.prior_context_digest == self.new_context_digest:
            raise CheckpointContractError("compaction must bind a new context digest")

    @property
    def candidate_digest(self) -> str:
        payload = json.dumps(
            asdict(self), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(payload).hexdigest()


class SqliteCheckpointFixture:
    """File-backed SQLite fixture for prepare/recovery/activation semantics.

    `fault_hook` is a deterministic public-test seam. A test process may terminate
    at named durability boundaries and a fresh process can then read back the file.
    Production storage remains owned by the existing LoopX persistence path.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        fault_hook: FaultHook | None = None,
    ) -> None:
        raw = str(path)
        if raw == ":memory:" or "mode=memory" in raw:
            raise CheckpointContractError(
                "in-memory SQLite cannot provide durable recovery evidence"
            )
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fault_hook = fault_hook
        self._db = sqlite3.connect(self.path)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=FULL")
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS checkpoint_meta (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                active_revision INTEGER NOT NULL,
                active_checkpoint_id TEXT
            );
            INSERT OR IGNORE INTO checkpoint_meta(singleton, active_revision, active_checkpoint_id)
            VALUES (1, 0, NULL);

            CREATE TABLE IF NOT EXISTS checkpoints (
                checkpoint_id TEXT PRIMARY KEY,
                expected_revision INTEGER NOT NULL,
                new_revision INTEGER NOT NULL UNIQUE,
                candidate_digest TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                recovery_state TEXT NOT NULL CHECK (recovery_state IN ('NOT_EXERCISED','PASS','FAIL')),
                activated INTEGER NOT NULL DEFAULT 0 CHECK (activated IN (0,1))
            );
            """
        )
        self._db.commit()

    def _fault(self, phase: str) -> None:
        if self._fault_hook is not None:
            self._fault_hook(phase)

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> "SqliteCheckpointFixture":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @property
    def active_revision(self) -> int:
        row = self._db.execute(
            "SELECT active_revision FROM checkpoint_meta WHERE singleton=1"
        ).fetchone()
        assert row is not None
        return int(row[0])

    @property
    def active_checkpoint_id(self) -> str | None:
        row = self._db.execute(
            "SELECT active_checkpoint_id FROM checkpoint_meta WHERE singleton=1"
        ).fetchone()
        assert row is not None
        return None if row[0] is None else str(row[0])

    def prepare(
        self, candidate: CheckpointCandidate, transaction: SafeToolTransaction
    ) -> str:
        candidate.validate()
        transaction.validate_for_compaction()
        if candidate.expected_revision != self.active_revision:
            raise CheckpointContractError("stale expected revision")

        payload_json = json.dumps(
            asdict(candidate), sort_keys=True, separators=(",", ":")
        )
        existing = self._db.execute(
            "SELECT candidate_digest FROM checkpoints WHERE checkpoint_id=?",
            (candidate.checkpoint_id,),
        ).fetchone()
        if existing is not None:
            if str(existing[0]) != candidate.candidate_digest:
                raise CheckpointContractError("checkpoint id collision")
            return candidate.candidate_digest

        try:
            self._db.execute("BEGIN IMMEDIATE")
            current = self._db.execute(
                "SELECT active_revision FROM checkpoint_meta WHERE singleton=1"
            ).fetchone()
            assert current is not None
            if int(current[0]) != candidate.expected_revision:
                raise CheckpointContractError("stale expected revision")
            self._db.execute(
                """
                INSERT INTO checkpoints(
                    checkpoint_id, expected_revision, new_revision,
                    candidate_digest, payload_json, recovery_state, activated
                ) VALUES (?, ?, ?, ?, ?, 'NOT_EXERCISED', 0)
                """,
                (
                    candidate.checkpoint_id,
                    candidate.expected_revision,
                    candidate.new_revision,
                    candidate.candidate_digest,
                    payload_json,
                ),
            )
            self._fault("prepare_before_commit")
            self._db.commit()
            self._fault("prepare_after_commit")
        except Exception:
            self._db.rollback()
            raise
        return candidate.candidate_digest

    def record_recovery_probe(
        self, checkpoint_id: str, state: Literal["PASS", "FAIL"]
    ) -> None:
        try:
            self._db.execute("BEGIN IMMEDIATE")
            cursor = self._db.execute(
                "UPDATE checkpoints SET recovery_state=? WHERE checkpoint_id=? AND activated=0",
                (state, checkpoint_id),
            )
            if cursor.rowcount != 1:
                raise CheckpointContractError("unknown or already activated checkpoint")
            self._fault("recovery_before_commit")
            self._db.commit()
            self._fault("recovery_after_commit")
        except Exception:
            self._db.rollback()
            raise

    def activate(self, checkpoint_id: str) -> int:
        try:
            self._db.execute("BEGIN IMMEDIATE")
            row = self._db.execute(
                """
                SELECT expected_revision, new_revision, recovery_state, activated
                FROM checkpoints WHERE checkpoint_id=?
                """,
                (checkpoint_id,),
            ).fetchone()
            if row is None:
                raise CheckpointContractError("unknown checkpoint")
            expected_revision, new_revision, recovery_state, activated = row
            if int(activated):
                if self.active_checkpoint_id == checkpoint_id:
                    self._db.commit()
                    return int(new_revision)
                raise CheckpointContractError("checkpoint activation conflict")
            if recovery_state != "PASS":
                raise CheckpointContractError("recovery probe must PASS before activation")
            current = self._db.execute(
                "SELECT active_revision FROM checkpoint_meta WHERE singleton=1"
            ).fetchone()
            assert current is not None
            if int(current[0]) != int(expected_revision):
                raise CheckpointContractError("stale activation revision")
            self._db.execute(
                "UPDATE checkpoint_meta SET active_revision=?, active_checkpoint_id=? WHERE singleton=1",
                (int(new_revision), checkpoint_id),
            )
            self._db.execute(
                "UPDATE checkpoints SET activated=1 WHERE checkpoint_id=?",
                (checkpoint_id,),
            )
            self._fault("activate_before_commit")
            self._db.commit()
            self._fault("activate_after_commit")
            return int(new_revision)
        except Exception:
            self._db.rollback()
            raise

    def read_candidate(self, checkpoint_id: str) -> CheckpointCandidate:
        row = self._db.execute(
            "SELECT payload_json FROM checkpoints WHERE checkpoint_id=?",
            (checkpoint_id,),
        ).fetchone()
        if row is None:
            raise CheckpointContractError("unknown checkpoint")
        return CheckpointCandidate(**json.loads(str(row[0])))

    def recovery_state(
        self, checkpoint_id: str
    ) -> Literal["NOT_EXERCISED", "PASS", "FAIL"]:
        row = self._db.execute(
            "SELECT recovery_state FROM checkpoints WHERE checkpoint_id=?",
            (checkpoint_id,),
        ).fetchone()
        if row is None:
            raise CheckpointContractError("unknown checkpoint")
        value = str(row[0])
        if value not in {"NOT_EXERCISED", "PASS", "FAIL"}:
            raise CheckpointContractError("invalid persisted recovery state")
        return value  # type: ignore[return-value]
