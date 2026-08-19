from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import sys

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0, str(PARENT))

from checkpoint_contract import (  # noqa: E402
    CheckpointCandidate,
    SafeToolTransaction,
    SqliteCheckpointFixture,
)


def digest(char: str) -> str:
    return "sha256:" + char * 64


def candidate() -> CheckpointCandidate:
    return CheckpointCandidate(
        checkpoint_id="cp-fault-1",
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


def safe_transaction() -> SafeToolTransaction:
    return SafeToolTransaction(
        transaction_id="txn-fault-1",
        state="COMPLETE_SAFE",
        call_ids=("call-a", "call-b"),
        result_call_ids=("call-a", "call-b"),
    )


def crash(code: int) -> None:
    os._exit(code)


def main() -> int:
    if len(sys.argv) != 3:
        return 64
    mode = sys.argv[1]
    path = Path(sys.argv[2])

    if mode == "before-prepare":
        SqliteCheckpointFixture(path)
        crash(81)
    if mode == "after-prepare":
        store = SqliteCheckpointFixture(path)
        store.prepare(candidate(), safe_transaction())
        crash(82)
    if mode == "before-recovery":
        SqliteCheckpointFixture(path)
        crash(83)
    if mode == "after-recovery":
        store = SqliteCheckpointFixture(path)
        store.record_recovery_probe(candidate().checkpoint_id, "PASS")
        crash(84)
    if mode == "before-activation":
        SqliteCheckpointFixture(path)
        crash(85)
    if mode == "after-activation":
        store = SqliteCheckpointFixture(path)
        store.activate(candidate().checkpoint_id)
        crash(86)
    if mode == "uncommitted-meta":
        db = sqlite3.connect(path)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("BEGIN IMMEDIATE")
        db.execute(
            "UPDATE checkpoint_meta SET active_revision=999, active_checkpoint_id='torn' WHERE singleton=1"
        )
        crash(87)
    return 65


if __name__ == "__main__":
    raise SystemExit(main())
