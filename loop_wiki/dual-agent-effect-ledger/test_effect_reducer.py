#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("dual_agent_effect_reducer", ROOT / "effect_reducer.py")
assert SPEC is not None and SPEC.loader is not None
reducer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reducer)
contract = reducer.contract


def expect(code: str, fn: Callable[[], Any]) -> None:
    try:
        fn()
    except (reducer.EffectReducerError, contract.EffectContractError) as exc:
        actual = getattr(exc, "code", "")
        if actual != code:
            raise AssertionError(f"expected {code}, got {exc}") from exc
        print(f"{code}: RED/{code}")
    else:
        raise AssertionError(f"{code}: planted control survived")


def transition(target: str, **extra: Any) -> tuple[str, dict[str, Any]]:
    payload: dict[str, Any] = {"target_state": target, "actor_class": "EFFECT_LEDGER"}
    payload.update(extra)
    return ("STATE_TRANSITION", payload)


def attempt(request: dict[str, Any], attempt_id: str, outcome: str) -> tuple[str, dict[str, Any]]:
    return (
        "ATTEMPT_RECORDED",
        {
            "attempt_id": attempt_id,
            "outcome": outcome,
            "actor_class": "EFFECT_LEDGER",
            "request_digest": request["runtime_intent"]["normalized_request_digest"],
            "normalized_request_digest": request["runtime_intent"]["normalized_request_digest"],
            "provider_subject": request["target"]["provider_subject"],
        },
    )


def readback(request: dict[str, Any], digest_char: str = "9") -> tuple[str, dict[str, Any]]:
    target = request["target"]
    return (
        "READBACK_RECORDED",
        {
            "actor_class": "EFFECT_LEDGER",
            "verified": True,
            "digest": digest_char * 64,
            "remote_version": request["precondition_binding"]["expected_remote_version"],
            "provider_id": target["provider_id"],
            "resource_id": target["resource_id"],
            "action": target["action"],
        },
    )


def admitted_prefix() -> list[tuple[str, dict[str, Any]]]:
    return [
        transition("INTENT_VALIDATED"),
        transition("POLICY_AND_APPROVAL_CHECKED"),
        transition("IDEMPOTENCY_RESERVED"),
        transition("PRECONDITION_REVALIDATED"),
        transition("EXECUTION_AUTHORIZED"),
    ]


def committed_history(request: dict[str, Any]) -> list[dict[str, Any]]:
    specs = admitted_prefix() + [
        attempt(request, "attempt-1", "RETRYABLE_FAILURE"),
        attempt(request, "attempt-2", "SUCCESS"),
        transition("EFFECT_ATTEMPTED", attempt_result="SUCCESS"),
        transition("EFFECT_OBSERVED", attempt_result="SUCCESS"),
        readback(request),
        transition("EFFECT_COMMITTED", attempt_result="SUCCESS"),
    ]
    return reducer.chain_events(request, specs)


def unknown_history(request: dict[str, Any]) -> list[dict[str, Any]]:
    specs = admitted_prefix() + [
        attempt(request, "attempt-unknown", "TIMEOUT"),
        transition("EFFECT_ATTEMPTED", attempt_result="TIMEOUT"),
        transition("RESULT_UNKNOWN", attempt_result="TIMEOUT"),
        transition("RECONCILIATION_REQUIRED"),
        readback(request, "8"),
        transition("EFFECT_OBSERVED"),
        transition("EFFECT_COMMITTED", attempt_result="READBACK_VERIFIED"),
    ]
    return reducer.chain_events(request, specs)


def main() -> int:
    request = contract.fixed_admission_request()

    first_reservation = reducer.reservation_batch([], request)
    assert first_reservation["decision"] == "RESERVATION_ACCEPTED"
    duplicate = reducer.reservation_batch([request], copy.deepcopy(request))
    assert duplicate["decision"] == "DUPLICATE_REFUSED" and duplicate["execute"] is False
    print("P1: PASS deterministic reservation + exact duplicate refusal")

    history = committed_history(request)
    result = reducer.reduce_effect_history(request, history)
    assert result["effect_state"] == "EFFECT_COMMITTED"
    assert result["attempt_count"] == 2
    assert result["accepted_commit_count"] == 1
    assert [row["attempt_id"] for row in result["attempts"]] == ["attempt-1", "attempt-2"]
    assert result["provider_io_state"] == "NOT_EXERCISED"
    print("P2: PASS complete attempt denominator + one accepted commit")

    unknown = unknown_history(request)
    unknown_result = reducer.reduce_effect_history(request, unknown)
    assert unknown_result["effect_state"] == "EFFECT_COMMITTED"
    assert unknown_result["attempts"][0]["outcome"] == "TIMEOUT"
    assert len(unknown_result["readbacks"]) == 1
    print("P3: PASS RESULT_UNKNOWN reconciliation + exact readback commit")

    assert reducer.replay_bytes(request, history) == reducer.replay_bytes(copy.deepcopy(request), copy.deepcopy(history))
    print("P4: PASS byte-identical effect replay")

    distinct = copy.deepcopy(request)
    distinct["runtime_intent"]["effect_id"] = "effect-demo-002"
    distinct["runtime_intent"]["idempotency_key"] = "effect-idem-002"
    distinct["runtime_intent"]["normalized_request_digest"] = "7" * 64
    distinct["workflow_request"]["idempotency_key"] = "effect-idem-002"
    distinct["workflow_request"]["request_digest"] = "7" * 64
    assert reducer.reservation_batch([request], distinct)["decision"] == "RESERVATION_ACCEPTED"
    print("P5: PASS distinct logical effect reservation")

    collision = copy.deepcopy(request)
    collision["runtime_intent"]["normalized_request_digest"] = "6" * 64
    collision["workflow_request"]["request_digest"] = "6" * 64
    expect("IDEMPOTENCY_COLLISION", lambda: reducer.reservation_batch([request], collision))

    cross = copy.deepcopy(request)
    cross["tenant_scope"] = "tenant-other"
    cross["workflow_request"]["tenant_scope"] = "tenant-other"
    expect("CROSS_TENANT_EFFECT_IDENTITY", lambda: reducer.reservation_batch([request], cross))

    double = committed_history(request)
    double.append(reducer.make_event(request, len(double), "STATE_TRANSITION", {"target_state":"EFFECT_COMMITTED","actor_class":"EFFECT_LEDGER"}, double[-1]["event_digest"]))
    expect("DOUBLE_COMMIT", lambda: reducer.reduce_effect_history(request, double))

    unresolved_specs = admitted_prefix() + [
        attempt(request, "attempt-u", "TIMEOUT"),
        transition("EFFECT_ATTEMPTED", attempt_result="TIMEOUT"),
        transition("RESULT_UNKNOWN", attempt_result="TIMEOUT"),
        transition("EFFECT_COMMITTED", attempt_result="TIMEOUT"),
    ]
    expect("UNRESOLVED_EFFECT_COMMIT", lambda: reducer.reduce_effect_history(request, reducer.chain_events(request, unresolved_specs)))

    provider_commit = committed_history(request)
    provider_commit[-1]["payload"]["actor_class"] = "PROVIDER"
    provider_commit[-1]["event_digest"] = reducer.digest({k:v for k,v in provider_commit[-1].items() if k != "event_digest"})
    expect("WORKER_OR_PROVIDER_SELF_COMMIT", lambda: reducer.reduce_effect_history(request, provider_commit))

    no_attempt = reducer.chain_events(request, admitted_prefix() + [transition("EFFECT_ATTEMPTED", attempt_result="SUCCESS")])
    expect("ATTEMPT_DENOMINATOR_MISSING", lambda: reducer.reduce_effect_history(request, no_attempt))

    task_launder = reducer.chain_events(request, admitted_prefix() + [
        attempt(request, "attempt-x", "TIMEOUT"),
        transition("EFFECT_ATTEMPTED", attempt_result="TIMEOUT"),
        transition("RESULT_UNKNOWN", attempt_result="TIMEOUT"),
        ("TASK_PROJECTION", {"task_state":"COMPLETED","loopx_write_mode":"PROPOSAL_ONLY"}),
    ])
    expect("UNRESOLVED_EFFECT_HIDDEN", lambda: reducer.reduce_effect_history(request, task_launder))

    direct_loopx = reducer.chain_events(request, [("TASK_PROJECTION", {"task_state":"NOT_EXERCISED","loopx_write_mode":"DIRECT_APPEND"})])
    expect("DIRECT_LOOPX_WRITE", lambda: reducer.reduce_effect_history(request, direct_loopx))

    promoted = copy.deepcopy(request)
    promoted["substrate"]["writer_authority"] = "dual-agent-effect-ledger"
    expect("SUBSTRATE_AUTHORITY_DRIFT", lambda: reducer.reduce_effect_history(promoted, []))

    secret = reducer.chain_events(request, [("TASK_PROJECTION", {"task_state":"NOT_EXERCISED","secret_value":"forbidden"})])
    expect("SECRET_OR_REASONING_PERSISTENCE", lambda: reducer.reduce_effect_history(request, secret))

    unknown_retry = reducer.chain_events(request, admitted_prefix() + [
        attempt(request, "attempt-z", "TIMEOUT"),
        transition("EFFECT_ATTEMPTED", attempt_result="TIMEOUT"),
        transition("RESULT_UNKNOWN", attempt_result="TIMEOUT"),
        attempt(request, "attempt-z2", "SUCCESS"),
    ])
    expect("UNKNOWN_EFFECT_RETRY_FORBIDDEN", lambda: reducer.reduce_effect_history(request, unknown_retry))

    drift_attempt = admitted_prefix() + [attempt(request, "attempt-drift", "SUCCESS")]
    drift_attempt[-1][1]["request_digest"] = "5" * 64
    expect("ATTEMPT_REQUEST_DRIFT", lambda: reducer.reduce_effect_history(request, reducer.chain_events(request, drift_attempt)))

    wrong_readback = admitted_prefix() + [
        attempt(request, "attempt-r", "SUCCESS"),
        transition("EFFECT_ATTEMPTED", attempt_result="SUCCESS"),
        transition("EFFECT_OBSERVED", attempt_result="SUCCESS"),
        readback(request),
    ]
    wrong_readback[-1][1]["remote_version"] = "version-other"
    expect("READBACK_DISAGREEMENT", lambda: reducer.reduce_effect_history(request, reducer.chain_events(request, wrong_readback)))

    source = (ROOT / "effect_reducer.py").read_text(encoding="utf-8")
    reducer.assert_deterministic_source(source)
    expect("PROVIDER_IO_IN_REDUCER", lambda: reducer.assert_deterministic_source(source + "\nimport requests\n"))

    print("PASS: DA-EF-K deterministic reservation/commit/reconciliation controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
