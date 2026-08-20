#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("dual_agent_effect_compensation", ROOT / "effect_compensation.py")
assert SPEC is not None and SPEC.loader is not None
comp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(comp)
policy = comp.policy
reducer = policy.reducer
contract = reducer.contract


def expect(code: str, fn: Callable[[], Any]) -> None:
    try:
        fn()
    except (comp.CompensationLedgerError, policy.EffectPolicyError, reducer.EffectReducerError, contract.EffectContractError) as exc:
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


def committed_parent(request: dict[str, Any]) -> dict[str, Any]:
    attempt = (
        "ATTEMPT_RECORDED",
        {
            "attempt_id": "attempt-parent",
            "outcome": "SUCCESS",
            "actor_class": "EFFECT_LEDGER",
            "request_digest": request["runtime_intent"]["normalized_request_digest"],
            "normalized_request_digest": request["runtime_intent"]["normalized_request_digest"],
            "provider_subject": request["target"]["provider_subject"],
        },
    )
    readback = (
        "READBACK_RECORDED",
        {
            "actor_class": "EFFECT_LEDGER",
            "verified": True,
            "digest": "9" * 64,
            "remote_version": request["precondition_binding"]["expected_remote_version"],
            "provider_id": request["target"]["provider_id"],
            "resource_id": request["target"]["resource_id"],
            "action": request["target"]["action"],
        },
    )
    specs = [
        transition("INTENT_VALIDATED"),
        transition("POLICY_AND_APPROVAL_CHECKED"),
        transition("IDEMPOTENCY_RESERVED"),
        transition("PRECONDITION_REVALIDATED"),
        transition("EXECUTION_AUTHORIZED"),
        attempt,
        transition("EFFECT_ATTEMPTED", attempt_result="SUCCESS"),
        transition("EFFECT_OBSERVED", attempt_result="SUCCESS"),
        readback,
        transition("EFFECT_COMMITTED", attempt_result="SUCCESS"),
    ]
    return reducer.reduce_effect_history(request, reducer.chain_events(request, specs))


def main() -> int:
    request = contract.fixed_admission_request()
    parent = committed_parent(request)
    link = comp.build_compensation_link(request, parent)
    comp.validate_compensation_link(request, parent, link)
    assert link["parent_effect_identity_digest"] == reducer.effect_identity_digest(request)
    assert link["child_effect_identity_digest"] != link["parent_effect_identity_digest"]
    assert link["child_idempotency_key"] != link["parent_idempotency_key"]
    assert link["authorization"]["mode"] == "EFFECT_EXECUTION_AUTHORIZATION"
    assert link["external_compensation_state"] == "NOT_EXERCISED"
    print("P1: PASS linked compensation identity + own admission")

    repeat = comp.build_compensation_link(copy.deepcopy(request), copy.deepcopy(parent))
    assert link == repeat
    print("P2: PASS deterministic compensation link replay")

    success = comp.compensation_result(link, "COMPENSATED", accepted=True)
    failure = comp.compensation_result(link, "COMPENSATION_FAILED", accepted=False)
    assert success["state"] == "COMPENSATED" and failure["state"] == "COMPENSATION_FAILED"
    assert success["external_execution_state"] == "NOT_EXERCISED"
    print("P3: PASS compensated/failure remain distinct proposal states")

    read_only = copy.deepcopy(request)
    read_only["runtime_intent"]["side_effect_class"] = "IRREVERSIBLE_WRITE"
    expect("COMPENSATION_REQUIRES_REVERSIBLE_PARENT", lambda: comp.build_compensation_link(read_only, parent))

    unknown = copy.deepcopy(parent); unknown["effect_state"] = "RESULT_UNKNOWN"; unknown["accepted_commit_count"] = 0
    expect("UNKNOWN_EFFECT_COMPENSATION_FORBIDDEN", lambda: comp.build_compensation_link(request, unknown))

    uncommitted = copy.deepcopy(parent); uncommitted["effect_state"] = "EFFECT_OBSERVED"; uncommitted["accepted_commit_count"] = 0
    expect("COMPENSATION_REQUIRES_COMMITTED_PARENT", lambda: comp.build_compensation_link(request, uncommitted))

    reused = copy.deepcopy(link)
    reused["child_request"]["runtime_intent"]["idempotency_key"] = reused["parent_idempotency_key"]
    reused["child_request"]["workflow_request"]["idempotency_key"] = reused["parent_idempotency_key"]
    reused["child_idempotency_key"] = reused["parent_idempotency_key"]
    reused["child_effect_identity_digest"] = reducer.effect_identity_digest(reused["child_request"])
    reused["authorization"]["effect_identity_digest"] = reused["child_effect_identity_digest"]
    expect("COMPENSATION_IDEMPOTENCY_REUSE", lambda: comp.validate_compensation_link(request, parent, reused))

    parent_drift = copy.deepcopy(link); parent_drift["parent_effect_identity_digest"] = "0" * 64
    expect("COMPENSATION_PARENT_IDENTITY_DRIFT", lambda: comp.validate_compensation_link(request, parent, parent_drift))

    deleted = copy.deepcopy(link); deleted["parent_history_head"] = "ROOT"
    expect("COMPENSATION_AUDIT_DELETION", lambda: comp.validate_compensation_link(request, parent, deleted))

    mutation = copy.deepcopy(link); mutation["original_history_mutation"] = "DELETE_PARENT"
    expect("COMPENSATION_AUDIT_DELETION", lambda: comp.validate_compensation_link(request, parent, mutation))

    provider = copy.deepcopy(link); provider["effect_authority"] = "provider-demo"
    expect("DIRECT_PROVIDER_COMPENSATION", lambda: comp.validate_compensation_link(request, parent, provider))

    no_auth = copy.deepcopy(link); no_auth.pop("authorization")
    expect("COMPENSATION_ADMISSION_REQUIRED", lambda: comp.validate_compensation_link(request, parent, no_auth))

    live = copy.deepcopy(link); live["external_compensation_state"] = "PASS"
    expect("FIXTURE_AS_LIVE_COMPENSATION", lambda: comp.validate_compensation_link(request, parent, live))

    wrong_child = copy.deepcopy(link); wrong_child["child_effect_identity_digest"] = "f" * 64
    expect("COMPENSATION_LINEAGE_MISMATCH", lambda: comp.validate_compensation_link(request, parent, wrong_child))

    expect("COMPENSATION_FAILURE_AS_SUCCESS", lambda: comp.compensation_result(link, "COMPENSATION_FAILED", accepted=True))

    direct_result = copy.deepcopy(link); direct_result["effect_authority"] = "provider-demo"
    expect("DIRECT_PROVIDER_COMPENSATION", lambda: comp.compensation_result(direct_result, "COMPENSATED", accepted=True))

    fixture_live = copy.deepcopy(link); fixture_live["external_compensation_state"] = "PASS"
    expect("FIXTURE_AS_LIVE_COMPENSATION", lambda: comp.compensation_result(fixture_live, "COMPENSATED", accepted=True))

    print("PASS: DA-EF-COMP linked compensation planted controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
