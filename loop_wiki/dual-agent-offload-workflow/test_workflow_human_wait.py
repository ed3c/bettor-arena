#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("dual_agent_workflow_human_wait", ROOT / "workflow_human_wait.py")
assert SPEC is not None and SPEC.loader is not None
human = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(human)
reducer = human.reducer
contract = reducer.contract


def expect(code: str, fn: Callable[[], Any]) -> None:
    try:
        fn()
    except (human.HumanBoundaryError, reducer.ReplayError) as exc:
        actual = getattr(exc, "code", "")
        if actual != code:
            raise AssertionError(f"expected {code}, got {exc}") from exc
        print(f"{code}: RED/{code}")
    else:
        raise AssertionError(f"{code}: planted control survived")


def wait_specs() -> list[tuple[str, dict[str, Any]]]:
    return [
        ("ADMISSION_REQUESTED", {}),
        ("ADMISSION_ALLOWED", {}),
        ("HUMAN_WAIT_REQUIRED", {"approval_requirement":"BEFORE_EXTERNAL_WRITE","required_evidence_digest":"a"*64}),
    ]


def decision_payload(submission: dict[str, Any], decision: str) -> dict[str, Any]:
    return {
        "human_decision": decision,
        "actor_class": "HUMAN",
        "job_id": submission["job"]["job_id"],
        "tenant_scope": submission["job"]["tenant_scope"],
        "policy_digest": submission["job"]["bindings"]["policy_digest"],
        "runtime_digest": submission["job"]["bindings"]["runtime_digest"],
        "source_subject": submission["job"]["source_subject"],
        "decision_digest": "b"*64,
        "evidence_digest": "c"*64,
        "evidence_class": "DETERMINISTIC_FIXTURE",
    }


def main() -> int:
    submission = contract.fixed_submission()
    waiting = reducer.chain_events(submission, wait_specs())
    first = human.validate_human_history(submission, waiting)
    second = human.validate_human_history(copy.deepcopy(submission), copy.deepcopy(waiting))
    assert first["workflow_state"] == "WAITING_FOR_HUMAN"
    assert first["replay_digest"] == second["replay_digest"]
    print("P1: PASS Human wait survives exact replay")

    approved_specs = wait_specs() + [("HUMAN_APPROVED", decision_payload(submission, "APPROVE"))]
    approved = reducer.chain_events(submission, approved_specs)
    result = human.validate_human_history(submission, approved)
    assert result["workflow_state"] == "ADMITTED"
    assert result["human_boundary"]["live_human_session_state"] == "NOT_EXERCISED"
    print("P2: PASS typed approval + exact subject revalidation")

    refused_specs = wait_specs() + [("POLICY_REFUSED", decision_payload(submission, "REFUSE"))]
    refused = reducer.chain_events(submission, refused_specs)
    assert human.validate_human_history(submission, refused)["workflow_state"] == "POLICY_REFUSED"
    print("P3: PASS typed Human refusal remains terminal")

    bad_payload = decision_payload(submission,"APPROVE"); bad_payload["actor_class"]="WORKER"
    bad = reducer.chain_events(submission, wait_specs()+[("HUMAN_APPROVED",bad_payload)])
    expect("WORKER_SELF_APPROVAL", lambda: human.validate_human_history(submission,bad))

    bad_payload = decision_payload(submission,"APPROVE"); bad_payload["policy_digest"]="0"*64
    bad = reducer.chain_events(submission, wait_specs()+[("HUMAN_APPROVED",bad_payload)])
    expect("STALE_HUMAN_DECISION", lambda: human.validate_human_history(submission,bad))

    bad_payload = decision_payload(submission,"APPROVE"); bad_payload["tenant_scope"]="tenant-other"
    bad = reducer.chain_events(submission, wait_specs()+[("HUMAN_APPROVED",bad_payload)])
    expect("HUMAN_DECISION_SCOPE_MISMATCH", lambda: human.validate_human_history(submission,bad))

    bad = reducer.chain_events(submission, [("ADMISSION_REQUESTED",{}),("ADMISSION_ALLOWED",{}),("HUMAN_APPROVED",decision_payload(submission,"APPROVE"))])
    expect("APPROVAL_BEFORE_WAIT", lambda: human.validate_human_history(submission,bad))

    bad_wait = [("ADMISSION_REQUESTED",{}),("ADMISSION_ALLOWED",{}),("HUMAN_WAIT_REQUIRED",{"approval_requirement":"BEFORE_EXTERNAL_WRITE"})]
    bad = reducer.chain_events(submission,bad_wait)
    expect("APPROVAL_BEFORE_REQUIRED_EVIDENCE", lambda: human.validate_human_history(submission,bad))

    bad_payload = decision_payload(submission,"APPROVE"); bad_payload["evidence_class"]="LIVE_PASS"
    bad = reducer.chain_events(submission, wait_specs()+[("HUMAN_APPROVED",bad_payload)])
    expect("FIXTURE_AS_LIVE_HUMAN_PASS", lambda: human.validate_human_history(submission,bad))

    terminal = reducer.chain_events(submission, wait_specs()+[("POLICY_REFUSED",decision_payload(submission,"REFUSE")),("RECONCILED",{})])
    expect("EVENT_AFTER_TERMINAL", lambda: human.validate_human_history(submission,terminal))

    print("PASS: DA-WF-H Human wait/revalidation matrix")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
