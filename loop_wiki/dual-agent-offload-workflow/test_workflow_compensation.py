#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("dual_agent_workflow_compensation", ROOT / "workflow_compensation.py")
assert SPEC is not None and SPEC.loader is not None
comp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(comp)
reducer = comp.reducer
contract = reducer.contract


def expect(code: str, fn: Callable[[], Any]) -> None:
    try:
        fn()
    except (comp.CompensationError, reducer.ReplayError) as exc:
        actual = getattr(exc, "code", "")
        if actual != code:
            raise AssertionError(f"expected {code}, got {exc}") from exc
        print(f"{code}: RED/{code}")
    else:
        raise AssertionError(f"{code}: planted control survived")


def write_submission() -> dict[str, Any]:
    s = contract.fixed_submission()
    s["job"]["side_effect_class"] = "REVERSIBLE_WRITE"
    s["job"]["approval_requirement"] = "BEFORE_EXTERNAL_WRITE"
    return s


def base_specs() -> list[tuple[str, dict[str, Any]]]:
    return [
        ("ADMISSION_REQUESTED", {}),
        ("ADMISSION_ALLOWED", {}),
        ("DELIVERY_REQUESTED", {}),
        ("REMOTE_DISPATCHED", {}),
        ("EXECUTION_STARTED", {}),
        ("RESULT_WAITING", {}),
        ("RESULT_RECEIVED", {"artifact_digest":"a"*64}),
        ("RESULT_VERIFIED", {"verification_digest":"b"*64}),
    ]


def request_payload() -> dict[str, Any]:
    return {
        "mode":"EFFECT_COMPENSATION_REQUEST",
        "effect_owner":"dual-agent-effect-ledger",
        "effect_id":"effect-demo-1",
        "parent_idempotency_key":"effect-idem-1",
        "compensation_idempotency_key":"comp-idem-1",
        "reversible":True,
        "original_effect_state":"COMMITTED",
        "original_effect_receipt_digest":"c"*64,
        "external_execution_state":"NOT_EXERCISED",
    }


def result_payload() -> dict[str, Any]:
    return {
        "effect_owner":"dual-agent-effect-ledger",
        "effect_id":"effect-demo-1",
        "compensation_idempotency_key":"comp-idem-1",
        "compensation_receipt_digest":"d"*64,
        "external_execution_state":"NOT_EXERCISED",
    }


def main() -> int:
    submission = write_submission()
    history = reducer.chain_events(submission, base_specs()+[("COMPENSATION_REQUIRED",request_payload()),("COMPENSATED",result_payload())])
    first = comp.validate_compensation_history(submission, history)
    second = comp.validate_compensation_history(copy.deepcopy(submission), copy.deepcopy(history))
    assert first["workflow_state"] == "COMPENSATED"
    assert first["replay_digest"] == second["replay_digest"]
    assert first["compensation_boundary"]["external_compensation_state"] == "NOT_EXERCISED"
    print("P1: PASS typed compensation lineage replay")

    failed_payload = result_payload(); failed_payload["compensation_receipt_digest"]="e"*64
    failed = reducer.chain_events(submission, base_specs()+[("COMPENSATION_REQUIRED",request_payload()),("COMPENSATION_FAILED",failed_payload)])
    assert comp.validate_compensation_history(submission, failed)["workflow_state"] == "COMPENSATION_FAILED"
    print("P2: PASS compensation failure remains distinct")

    cleanup = reducer.chain_events(submission, base_specs()+[("CLEANUP_FAILED", {"cleanup_receipt_digest":"f"*64})])
    assert comp.validate_compensation_history(submission, cleanup)["workflow_state"] == "FAILED_CLEANUP"
    print("P3: PASS cleanup failure remains distinct")

    read_only = contract.fixed_submission()
    expect("COMPENSATION_REQUIRES_REVERSIBLE_EFFECT", lambda: comp.validate_compensation_history(read_only, []))

    p = request_payload(); p["original_effect_state"]="UNKNOWN_EFFECT"
    bad = reducer.chain_events(submission, base_specs()+[("COMPENSATION_REQUIRED",p)])
    expect("UNKNOWN_EFFECT_BLIND_COMPENSATION", lambda: comp.validate_compensation_history(submission,bad))

    p = request_payload(); p["mode"]="DIRECT_PROVIDER_WRITE"
    bad = reducer.chain_events(submission, base_specs()+[("COMPENSATION_REQUIRED",p)])
    expect("DIRECT_PROVIDER_COMPENSATION", lambda: comp.validate_compensation_history(submission,bad))

    p = request_payload(); p["compensation_idempotency_key"] = p["parent_idempotency_key"]
    bad = reducer.chain_events(submission, base_specs()+[("COMPENSATION_REQUIRED",p)])
    expect("COMPENSATION_LINEAGE_MISMATCH", lambda: comp.validate_compensation_history(submission,bad))

    rp = result_payload(); rp["effect_id"]="effect-other"
    bad = reducer.chain_events(submission, base_specs()+[("COMPENSATION_REQUIRED",request_payload()),("COMPENSATED",rp)])
    expect("COMPENSATION_LINEAGE_MISMATCH", lambda: comp.validate_compensation_history(submission,bad))

    p = request_payload(); p["external_execution_state"]="PASS"
    bad = reducer.chain_events(submission, base_specs()+[("COMPENSATION_REQUIRED",p)])
    expect("FIXTURE_AS_LIVE_COMPENSATION", lambda: comp.validate_compensation_history(submission,bad))

    bad = reducer.chain_events(submission, base_specs()+[("COMPENSATED",result_payload())])
    expect("COMPENSATION_WITHOUT_PARENT", lambda: comp.validate_compensation_history(submission,bad))

    terminal = cleanup + [reducer.make_event(submission,len(cleanup),"RECONCILED",{},cleanup[-1]["event_digest"])]
    expect("EVENT_AFTER_TERMINAL", lambda: comp.validate_compensation_history(submission,terminal))

    print("PASS: DA-WF-COMP compensation/cleanup replay matrix")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
