#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("dual_agent_workflow_retry_restart", ROOT / "workflow_retry_restart.py")
assert SPEC is not None and SPEC.loader is not None
ops = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ops)
reducer = ops.reducer
contract = reducer.contract


def expect(code: str, fn: Callable[[], Any]) -> None:
    try:
        fn()
    except (ops.BoundaryError, reducer.ReplayError) as exc:
        actual = getattr(exc, "code", "")
        if actual != code:
            raise AssertionError(f"expected {code}, got {exc}") from exc
        print(f"{code}: RED/{code}")
    else:
        raise AssertionError(f"{code}: planted control survived")


def retry_history(submission: dict[str, Any]) -> list[dict[str, Any]]:
    return reducer.chain_events(submission, [
        ("ADMISSION_REQUESTED", {}),
        ("ADMISSION_ALLOWED", {}),
        ("DELIVERY_REQUESTED", {}),
        ("RETRY_REQUESTED", {"parent_attempt_id":"attempt-1","next_attempt_id":"attempt-2","reason":"typed-timeout"}),
        ("RETRY_READY", {"attempt_id":"attempt-2","timer_receipt_digest":"a"*64}),
    ])


def cancel_history(submission: dict[str, Any], during_execution: bool) -> list[dict[str, Any]]:
    specs: list[tuple[str, dict[str, Any]]] = [
        ("ADMISSION_REQUESTED", {}), ("ADMISSION_ALLOWED", {})
    ]
    requested_from = "ADMITTED"
    if during_execution:
        specs += [("DELIVERY_REQUESTED", {}), ("REMOTE_DISPATCHED", {}), ("EXECUTION_STARTED", {})]
        requested_from = "RUNNING"
    specs += [
        ("CANCEL_REQUESTED", {"requested_from":requested_from,"decision_source":"HISTORY_EVENT"}),
        ("CANCEL_STARTED", {"cancellation_activity_digest":"b"*64}),
        ("CANCELLED", {"cancellation_receipt_digest":"c"*64}),
    ]
    return reducer.chain_events(submission, specs)


def fresh_process_bytes(submission: dict[str, Any], history: list[dict[str, Any]]) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "input.json"
        p.write_text(json.dumps({"submission":submission,"history":history}), encoding="utf-8")
        code = (
            "import importlib.util,json,sys;"
            f"spec=importlib.util.spec_from_file_location('r',{str(ROOT / 'workflow_reducer.py')!r});"
            "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);"
            "x=json.load(open(sys.argv[1]));sys.stdout.buffer.write(m.replay_bytes(x['submission'],x['history']))"
        )
        return subprocess.check_output([sys.executable, "-c", code, str(p)])


def main() -> int:
    submission = contract.fixed_submission()

    retry = retry_history(submission)
    result = ops.validate_operational_history(submission, retry)
    assert result["workflow_state"] == "DELIVERY_PENDING"
    assert result["retry_count"] == 1
    assert result["operational_boundary"]["current_attempt_id"] == "attempt-2"
    print("P1: PASS retry lineage + typed timer")

    direct = reducer.replay_bytes(submission, retry)
    restarted = fresh_process_bytes(submission, retry)
    assert direct == restarted
    print("P2: PASS fresh-process exact replay")

    before = ops.validate_operational_history(submission, cancel_history(submission, False))
    assert before["workflow_state"] == "CANCELLED"
    print("P3: PASS cancellation before dispatch")

    during = ops.validate_operational_history(submission, cancel_history(submission, True))
    assert during["workflow_state"] == "CANCELLED"
    print("P4: PASS cancellation during execution")

    deadline = reducer.chain_events(submission, [
        ("ADMISSION_REQUESTED", {}),
        ("DEADLINE_EXPIRED", {"decision_source":"HISTORY_EVENT","observation_digest":"d"*64}),
    ])
    assert ops.validate_operational_history(submission, deadline)["workflow_state"] == "DEADLINE_EXPIRED"
    print("P5: PASS typed deadline observation")

    bad = copy.deepcopy(retry); bad[3]["payload"]["parent_attempt_id"]="attempt-other"
    bad[3]["event_digest"] = reducer.digest({k:v for k,v in bad[3].items() if k!="event_digest"})
    expect("LOST_PARENT_ATTEMPT", lambda: ops.validate_operational_history(submission,bad))

    bad = copy.deepcopy(retry); bad[4]["payload"].pop("timer_receipt_digest")
    bad[4]["event_digest"] = reducer.digest({k:v for k,v in bad[4].items() if k!="event_digest"})
    expect("UNTYPED_TIMER", lambda: ops.validate_operational_history(submission,bad))

    bad = reducer.chain_events(submission, [("ADMISSION_REQUESTED", {}),("DEADLINE_EXPIRED", {"wall_clock":"2026-08-19T00:00:00Z","observation_digest":"e"*64})])
    expect("WALL_CLOCK_DECISION_SOURCE", lambda: ops.validate_operational_history(submission,bad))

    bad = cancel_history(submission, False); bad[2]["payload"]["requested_from"]="RUNNING"
    bad[2]["event_digest"] = reducer.digest({k:v for k,v in bad[2].items() if k!="event_digest"})
    expect("CANCEL_STATE_MISMATCH", lambda: ops.validate_operational_history(submission,bad))

    bad = cancel_history(submission, True); bad[-1]["payload"].pop("cancellation_receipt_digest")
    bad[-1]["event_digest"] = reducer.digest({k:v for k,v in bad[-1].items() if k!="event_digest"})
    expect("UNTYPED_CANCELLATION", lambda: ops.validate_operational_history(submission,bad))

    terminal = cancel_history(submission, False)
    terminal.append(reducer.make_event(submission,len(terminal),"RECONCILED",{},terminal[-1]["event_digest"]))
    expect("EVENT_AFTER_TERMINAL", lambda: ops.validate_operational_history(submission,terminal))

    print("PASS: DA-WF-R retry/timer/restart/cancel/deadline matrix")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
