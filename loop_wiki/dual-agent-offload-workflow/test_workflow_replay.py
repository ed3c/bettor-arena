#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("dual_agent_workflow_reducer", ROOT / "workflow_reducer.py")
assert SPEC is not None and SPEC.loader is not None
reducer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reducer)
contract = reducer.contract


def expect(code: str, fn: Callable[[], Any]) -> None:
    try:
        fn()
    except reducer.ReplayError as exc:
        if exc.code != code:
            raise AssertionError(f"expected {code}, got {exc}") from exc
        print(f"{code}: RED/{code}")
    else:
        raise AssertionError(f"{code}: planted control survived")


def read_only_history(submission: dict[str, Any]) -> list[dict[str, Any]]:
    return reducer.chain_events(
        submission,
        [
            ("ADMISSION_REQUESTED", {}),
            ("ADMISSION_ALLOWED", {}),
            ("DELIVERY_REQUESTED", {}),
            ("REMOTE_DISPATCHED", {}),
            ("EXECUTION_STARTED", {}),
            ("RESULT_WAITING", {}),
            ("RESULT_RECEIVED", {"artifact_digest": "a" * 64}),
            ("RESULT_VERIFIED", {"verification_digest": "b" * 64}),
            ("RECONCILED", {"result_digest": "c" * 64}),
        ],
    )


def main() -> int:
    submission = contract.fixed_submission()
    history = read_only_history(submission)
    first = reducer.replay_bytes(submission, history)
    second = reducer.replay_bytes(copy.deepcopy(submission), copy.deepcopy(history))
    assert first == second
    result = reducer.reduce_history(submission, history)
    assert result["workflow_state"] == "COMPLETED"
    assert result["loopx_proposal"]["mode"] == "PROPOSAL_ONLY"
    assert result["task_state"] == "NOT_EXERCISED"
    assert result["effect_requests"] == []
    print("P1: PASS exact-history byte-identical replay")

    human = reducer.chain_events(
        submission,
        [
            ("ADMISSION_REQUESTED", {}),
            ("ADMISSION_ALLOWED", {}),
            ("HUMAN_WAIT_REQUIRED", {"approval_requirement": "BEFORE_EXTERNAL_WRITE"}),
        ],
    )
    human_result = reducer.reduce_history(submission, human)
    assert human_result["workflow_state"] == "WAITING_FOR_HUMAN"
    resumed = human + [
        reducer.make_event(
            submission,
            len(human),
            "HUMAN_APPROVED",
            {"approval_receipt_digest": "d" * 64},
            human[-1]["event_digest"],
        )
    ]
    assert reducer.reduce_history(submission, resumed)["workflow_state"] == "ADMITTED"
    print("P2: PASS Human wait survives replay and requires typed approval")

    retry_history = reducer.chain_events(
        submission,
        [
            ("ADMISSION_REQUESTED", {}),
            ("ADMISSION_ALLOWED", {}),
            ("DELIVERY_REQUESTED", {}),
            ("RETRY_REQUESTED", {"reason": "typed-timeout"}),
            ("RETRY_READY", {"backoff_receipt_digest": "e" * 64}),
        ],
    )
    retry_result = reducer.reduce_history(submission, retry_history)
    assert retry_result["workflow_state"] == "DELIVERY_PENDING"
    assert retry_result["retry_count"] == 1
    print("P3: PASS bounded retry replay")

    write_submission = contract.fixed_submission()
    write_submission["job"]["side_effect_class"] = "REVERSIBLE_WRITE"
    write_submission["job"]["approval_requirement"] = "BEFORE_EXTERNAL_WRITE"
    write_history = reducer.chain_events(
        write_submission,
        [
            ("ADMISSION_REQUESTED", {}),
            ("ADMISSION_ALLOWED", {}),
            (
                "EFFECT_REQUESTED",
                {
                    "mode": "EFFECT_ADMISSION_REQUEST",
                    "effect_owner": "dual-agent-effect-ledger",
                    "idempotency_key": "effect-idem-1",
                    "operation": "create-demo-record",
                },
            ),
        ],
    )
    write_result = reducer.reduce_history(write_submission, write_history)
    assert write_result["workflow_state"] == "ADMITTED"
    assert write_result["effect_requests"][0]["execution_state"] == "NOT_EXERCISED"
    print("P4: PASS write path emits effect-admission request only")

    bad = copy.deepcopy(history)
    bad[0]["workflow_subject"]["commit"] = "f" * 40
    bad[0]["event_digest"] = reducer.digest({k: v for k, v in bad[0].items() if k != "event_digest"})
    expect("HISTORY_SUBJECT_MISMATCH", lambda: reducer.reduce_history(submission, bad))

    bad = copy.deepcopy(history)
    bad[2]["sequence"] = 99
    bad[2]["event_digest"] = reducer.digest({k: v for k, v in bad[2].items() if k != "event_digest"})
    expect("HISTORY_SEQUENCE_MISMATCH", lambda: reducer.reduce_history(submission, bad))

    bad = copy.deepcopy(history)
    bad[3]["payload"]["tampered"] = True
    expect("HISTORY_DIGEST_MISMATCH", lambda: reducer.reduce_history(submission, bad))

    terminal = reducer.chain_events(
        submission,
        [("ADMISSION_REQUESTED", {}), ("DEADLINE_EXPIRED", {}), ("RECONCILED", {})],
    )
    expect("EVENT_AFTER_TERMINAL", lambda: reducer.reduce_history(submission, terminal))

    stale = reducer.chain_events(
        submission,
        [
            ("ADMISSION_REQUESTED", {}),
            ("ADMISSION_ALLOWED", {}),
            ("DELIVERY_REQUESTED", {}),
            ("REMOTE_DISPATCHED", {}),
            ("EXECUTION_STARTED", {}),
            ("RESULT_WAITING", {}),
            ("RESULT_RECEIVED", {}),
            ("RESULT_STALE", {"policy_digest": "0" * 64}),
            ("RECONCILED", {}),
        ],
    )
    expect("STALE_RESULT_RECONCILIATION", lambda: reducer.reduce_history(submission, stale))

    retry_over = reducer.chain_events(
        submission,
        [
            ("ADMISSION_REQUESTED", {}),
            ("ADMISSION_ALLOWED", {}),
            ("DELIVERY_REQUESTED", {}),
            ("RETRY_REQUESTED", {}),
            ("RETRY_READY", {}),
            ("RETRY_REQUESTED", {}),
            ("RETRY_READY", {}),
            ("RETRY_REQUESTED", {}),
        ],
    )
    expect("RETRY_BUDGET_EXCEEDED", lambda: reducer.reduce_history(submission, retry_over))

    bad_write = copy.deepcopy(write_history)
    effect_event = bad_write[-1]
    effect_event["payload"]["mode"] = "DIRECT_PROVIDER_WRITE"
    effect_event["event_digest"] = reducer.digest({k: v for k, v in effect_event.items() if k != "event_digest"})
    expect("EFFECT_OWNER_BYPASS", lambda: reducer.reduce_history(write_submission, bad_write))

    direct = reducer.chain_events(
        submission,
        [("ADMISSION_REQUESTED", {"loopx_write_mode": "DIRECT_APPEND"})],
    )
    expect("DIRECT_LOOPX_WRITE", lambda: reducer.reduce_history(submission, direct))

    secret = reducer.chain_events(
        submission,
        [("ADMISSION_REQUESTED", {"private_reasoning": "must-not-persist"})],
    )
    expect("SECRET_OR_REASONING_LEAK", lambda: reducer.reduce_history(submission, secret))

    reducer_source = (ROOT / "workflow_reducer.py").read_text(encoding="utf-8")
    reducer.assert_deterministic_source(reducer_source)
    expect(
        "NONDETERMINISTIC_REDUCER_SOURCE",
        lambda: reducer.assert_deterministic_source(reducer_source + "\nimport random\n"),
    )

    print("PASS: DA-WF-K replay/reducer positive paths + planted controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
