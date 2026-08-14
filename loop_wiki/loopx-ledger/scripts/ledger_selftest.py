#!/usr/bin/env python3
# ruff: noqa: F401,F403,F405  # this module family composes through star imports; the names ruff reads as unused are deliberate re-exports the downstream modules import through.
"""Mutation, crash-recovery, and writer-contention controls for LoopX Ledger v1."""

from __future__ import annotations

import copy
import fcntl
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

from ledger_common import *
from ledger_engine import *
from ledger_cli import append_event, initialize, recover_store, replay_to, verify_store


def request_for(
    event: dict[str, Any], revision: int, request_id: str
) -> dict[str, Any]:
    return {
        "schema_version": "loopx/append-request/v1",
        "request_id": request_id,
        "expected_state_revision": revision,
        "event": event,
    }


def expect_error(callable_: Any, label: str, contains: str | None = None) -> None:
    try:
        callable_()
    except (ContractError, InputError, BusyError) as exc:
        if contains is not None and contains not in str(exc):
            raise ContractError(f"{label}: wrong error: {exc}") from exc
        return
    raise ContractError(f"{label}: mutation unexpectedly passed")


def run_selftest(root: Path) -> None:
    fixtures = root / "tests" / "fixtures" / "good"
    contract_path = fixtures / "contract.json"
    event_paths = sorted((fixtures / "events").glob("*.json"))
    if len(event_paths) < 6:
        raise InputError("positive ledger fixtures are incomplete")
    mutations = 0
    with tempfile.TemporaryDirectory(prefix="loopx-ledger-selftest.") as temp:
        temp_root = Path(temp)
        store = temp_root / "store"
        initialize(
            contract_path,
            store,
            "2026-08-14T00:00:00Z",
            temp_root / "init.json",
            "selftest-init",
        )
        for index, event_path in enumerate(event_paths):
            event = load_json(event_path)
            request_path = temp_root / f"request-{index}.json"
            atomic_write_json(
                request_path, request_for(event, index, f"request-{index}")
            )
            append_event(
                store,
                request_path,
                temp_root / f"append-{index}.json",
                f"selftest-append-{index}",
            )
        verify_store(store, temp_root / "verify.json", "selftest-verify")
        replay_to(
            store,
            temp_root / "replay-a.json",
            temp_root / "replay-a-receipt.json",
            "selftest-replay-a",
        )
        replay_to(
            store,
            temp_root / "replay-b.json",
            temp_root / "replay-b-receipt.json",
            "selftest-replay-b",
        )
        if (temp_root / "replay-a.json").read_bytes() != (
            temp_root / "replay-b.json"
        ).read_bytes():
            raise ContractError("replay is not byte deterministic")
        expected_snapshot = fixtures / "expected-snapshot.json"
        if (
            not expected_snapshot.is_file()
            or (temp_root / "replay-a.json").read_bytes()
            != expected_snapshot.read_bytes()
        ):
            raise ContractError("replay disagrees with the checked positive snapshot")
        duplicate_request = temp_root / "duplicate.json"
        atomic_write_json(
            duplicate_request,
            request_for(
                load_json(event_paths[-1]), len(event_paths), "request-duplicate"
            ),
        )
        receipt = append_event(
            store,
            duplicate_request,
            temp_root / "duplicate-receipt.json",
            "selftest-duplicate",
        )
        if receipt["status"] != "NOOP":
            raise ContractError("identical event did not become NOOP")

        stale_event = copy.deepcopy(load_json(event_paths[-1]))
        stale_event["event_id"] = "event-stale"
        stale_event["sequence"] = len(event_paths)
        stale_event["previous_event_digest"] = load_json(store / "snapshot.json")[
            "ledger"
        ]["head_digest"]
        stale_event["event_digest"] = ""
        raw = copy.deepcopy(stale_event)
        raw.pop("event_digest")
        stale_event["event_digest"] = digest(raw)
        stale_request = temp_root / "stale.json"
        atomic_write_json(stale_request, request_for(stale_event, 0, "request-stale"))
        expect_error(
            lambda: append_event(
                store, stale_request, temp_root / "stale-receipt.json", "selftest-stale"
            ),
            "stale revision",
            "stale expected revision",
        )
        mutations += 1

        collision = copy.deepcopy(load_json(event_paths[-1]))
        collision["occurred_at"] = "2026-08-14T00:00:59Z"
        raw = copy.deepcopy(collision)
        raw.pop("event_digest")
        collision["event_digest"] = digest(raw)
        collision_request = temp_root / "collision.json"
        atomic_write_json(
            collision_request,
            request_for(collision, len(event_paths), "request-collision"),
        )
        expect_error(
            lambda: append_event(
                store,
                collision_request,
                temp_root / "collision-receipt.json",
                "selftest-collision",
            ),
            "event ID collision",
            "collision",
        )
        mutations += 1

        def mutated_store(name: str) -> Path:
            target = temp_root / name
            shutil.copytree(store, target)
            return target

        cases: list[tuple[str, Any]] = []
        delete_store = mutated_store("delete")
        lines = (delete_store / "events.jsonl").read_text().splitlines(True)
        (delete_store / "events.jsonl").write_text("".join(lines[:2] + lines[3:]))
        cases.append(("event deletion", lambda: replay_store(delete_store)))
        reorder_store = mutated_store("reorder")
        lines = (reorder_store / "events.jsonl").read_text().splitlines(True)
        lines[2], lines[3] = lines[3], lines[2]
        (reorder_store / "events.jsonl").write_text("".join(lines))
        cases.append(("event reorder", lambda: replay_store(reorder_store)))
        for name, mutate in [
            ("digest", lambda e: e.__setitem__("event_digest", "sha256:" + "0" * 64)),
            (
                "previous",
                lambda e: e.__setitem__("previous_event_digest", "sha256:" + "0" * 64),
            ),
            ("subject", lambda e: e["subject"].__setitem__("tree", "3" * 40)),
            ("sequence", lambda e: e.__setitem__("sequence", 99)),
            (
                "worker-authority",
                lambda e: e["payload"].__setitem__(
                    "gate_observation", {"gate_id": "gate-tests"}
                ),
            ),
            (
                "transition",
                lambda e: e["payload"]["transition"].__setitem__("to", "ACTIVE"),
            ),
        ]:
            target = mutated_store(name)
            event_lines = (target / "events.jsonl").read_text().splitlines()
            index = (
                2
                if name == "worker-authority"
                else (len(event_lines) - 1 if name == "transition" else 3)
            )
            event = json.loads(event_lines[index])
            mutate(event)
            event_lines[index] = json.dumps(
                event, sort_keys=True, separators=(",", ":")
            )
            (target / "events.jsonl").write_text("\n".join(event_lines) + "\n")
            cases.append((name, lambda target=target: replay_store(target)))
        snapshot_store = mutated_store("snapshot")
        drift = load_json(snapshot_store / "snapshot.json")
        drift["state_revision"] += 1
        atomic_write_json(snapshot_store / "snapshot.json", drift)
        cases.append(
            (
                "snapshot drift",
                lambda: verify_store(
                    snapshot_store,
                    temp_root / "snapshot-drift-receipt.json",
                    "selftest-snapshot-drift",
                ),
            )
        )
        for label, call in cases:
            expect_error(call, label)
            mutations += 1

        torn_store = mutated_store("torn")
        with (torn_store / "events.jsonl").open("ab") as handle:
            handle.write(b'{"schema_version":"loopx/event/v1"')
        inspect_receipt, code = recover_store(
            torn_store, False, temp_root / "torn-inspect.json", "selftest-torn-inspect"
        )
        if code != BAD or inspect_receipt["status"] != "FAIL":
            raise ContractError("torn tail inspection did not fail closed")
        recover_receipt, code = recover_store(
            torn_store, True, temp_root / "torn-recover.json", "selftest-torn-recover"
        )
        if code != OK or recover_receipt["status"] != "RECOVERED":
            raise ContractError("torn tail recovery failed")
        verify_store(torn_store, temp_root / "torn-verify.json", "selftest-torn-verify")
        mutations += 1

        quota_store = temp_root / "quota-exhaustion"
        initialize(
            contract_path,
            quota_store,
            "2026-08-14T00:00:00Z",
            temp_root / "quota-init.json",
            "selftest-quota-init",
        )
        for index, event_path in enumerate(event_paths[:5]):
            request_path = temp_root / f"quota-request-{index}.json"
            atomic_write_json(
                request_path,
                request_for(load_json(event_path), index, f"quota-request-{index}"),
            )
            append_event(
                quota_store,
                request_path,
                temp_root / f"quota-append-{index}.json",
                f"selftest-quota-append-{index}",
            )
        quota_event = copy.deepcopy(load_json(event_paths[5]))
        quota_event["payload"]["quota_delta"]["attempts"] = 2
        raw = copy.deepcopy(quota_event)
        raw.pop("event_digest")
        quota_event["event_digest"] = digest(raw)
        quota_request = temp_root / "quota-exhaust.json"
        atomic_write_json(quota_request, request_for(quota_event, 5, "quota-exhaust"))
        append_event(
            quota_store,
            quota_request,
            temp_root / "quota-exhaust-receipt.json",
            "selftest-quota-exhaust",
        )
        quota_snapshot = load_json(quota_store / "snapshot.json")
        if (
            quota_snapshot["state"]["lifecycle"] != "HITL_PENDING"
            or quota_snapshot["state"]["todos"][0]["status"] != "HITL_PENDING"
        ):
            raise ContractError("Quota exhaustion did not produce HITL_PENDING")
        terminal_event = copy.deepcopy(load_json(event_paths[-1]))
        terminal_event["previous_event_digest"] = quota_event["event_digest"]
        terminal_event["event_digest"] = ""
        raw = copy.deepcopy(terminal_event)
        raw.pop("event_digest")
        terminal_event["event_digest"] = digest(raw)
        terminal_request = temp_root / "quota-terminal.json"
        atomic_write_json(
            terminal_request, request_for(terminal_event, 6, "quota-terminal")
        )
        expect_error(
            lambda: append_event(
                quota_store,
                terminal_request,
                temp_root / "quota-terminal-receipt.json",
                "selftest-quota-terminal",
            ),
            "Quota exhausted completion",
            "transition source",
        )
        mutations += 1

        lock_handle = (store / ".writer.lock").open("a+b")
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).with_name("ledger.py").resolve()),
                    "append",
                    "--store",
                    str(store),
                    "--request",
                    str(duplicate_request),
                    "--receipt",
                    str(temp_root / "busy-receipt.json"),
                    "--operation-id",
                    "selftest-busy",
                ],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if result.returncode != BAD or "writer lease" not in result.stderr:
                raise ContractError("concurrent writer was not rejected")
        finally:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
            lock_handle.close()
        mutations += 1

        expect_error(
            lambda: validate_contract(
                load_json(root / "tests" / "fixtures" / "hollow" / "contract.json")
            ),
            "hollow contract",
        )
        mutations += 1

    print(
        f"loopx-ledger selftest PASS: 1 positive replay, 1 hollow, {mutations} mutations/controls"
    )
