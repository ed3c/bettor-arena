#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("dual_agent_effect_policy_gate", ROOT / "effect_policy_gate.py")
assert SPEC is not None and SPEC.loader is not None
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)
reducer = policy.reducer
contract = reducer.contract


def expect(code: str, fn: Callable[[], Any]) -> None:
    try:
        fn()
    except (policy.EffectPolicyError, reducer.EffectReducerError, contract.EffectContractError) as exc:
        actual = getattr(exc, "code", "")
        if actual != code:
            raise AssertionError(f"expected {code}, got {exc}") from exc
        print(f"{code}: RED/{code}")
    else:
        raise AssertionError(f"{code}: planted control survived")


def main() -> int:
    request = contract.fixed_admission_request()
    p = policy.fixed_policy_observation(request)
    a = policy.fixed_approval(request)
    c = policy.fixed_precondition(request)
    result = policy.authorize_effect(request, p, a, c)
    assert result["mode"] == "EFFECT_EXECUTION_AUTHORIZATION"
    assert result["effect_identity_digest"] == reducer.effect_identity_digest(request)
    assert result["provider_io_state"] == "NOT_EXERCISED"
    assert result["live_policy_state"] == "NOT_EXERCISED"
    assert result["live_human_state"] == "NOT_EXERCISED"
    print("P1: PASS exact policy/Human/precondition authorization packet")

    repeat = policy.authorize_effect(copy.deepcopy(request), copy.deepcopy(p), copy.deepcopy(a), copy.deepcopy(c))
    assert result == repeat
    print("P2: PASS deterministic admission replay")

    irreversible = copy.deepcopy(request)
    irreversible["runtime_intent"]["side_effect_class"] = "IRREVERSIBLE_WRITE"
    irreversible["runtime_intent"]["approval_requirement"] = "BEFORE_IRREVERSIBLE_ACTION"
    irreversible_p = policy.fixed_policy_observation(irreversible)
    irreversible_a = policy.fixed_approval(irreversible)
    irreversible_c = policy.fixed_precondition(irreversible)
    assert policy.authorize_effect(irreversible, irreversible_p, irreversible_a, irreversible_c)["mode"] == "EFFECT_EXECUTION_AUTHORIZATION"
    print("P3: PASS stronger irreversible-effect approval contract")

    stale = copy.deepcopy(p); stale["policy_digest"] = "0" * 64
    expect("STALE_POLICY", lambda: policy.authorize_effect(request, stale, a, c))

    wrong_scope = copy.deepcopy(p); wrong_scope["tenant_scope"] = "tenant-other"
    expect("POLICY_SCOPE_MISMATCH", lambda: policy.authorize_effect(request, wrong_scope, a, c))

    refused = copy.deepcopy(p); refused["decision"] = "REFUSE"
    expect("POLICY_REFUSED", lambda: policy.authorize_effect(request, refused, a, c))

    transport_proxy = copy.deepcopy(p); transport_proxy["decision_source"] = "TRANSPORT_AUTH"
    expect("TRANSPORT_AUTH_AS_AUTHORIZATION", lambda: policy.authorize_effect(request, transport_proxy, a, c))

    provider_proxy = copy.deepcopy(p); provider_proxy["decision_source"] = "PROVIDER_HEALTH"
    expect("TRANSPORT_AUTH_AS_AUTHORIZATION", lambda: policy.authorize_effect(request, provider_proxy, a, c))

    worker = copy.deepcopy(a); worker["actor_class"] = "WORKER"
    expect("WORKER_SELF_APPROVAL", lambda: policy.authorize_effect(request, p, worker, c))

    expired = copy.deepcopy(a); expired["approval_state"] = "EXPIRED"
    expect("EXPIRED_APPROVAL", lambda: policy.authorize_effect(request, p, expired, c))

    missing = copy.deepcopy(a); missing["decision"] = "REFUSE"
    expect("APPROVAL_REQUIRED", lambda: policy.authorize_effect(request, p, missing, c))

    approval_scope = copy.deepcopy(a); approval_scope["effect_identity_digest"] = "f" * 64
    expect("APPROVAL_SCOPE_MISMATCH", lambda: policy.authorize_effect(request, p, approval_scope, c))

    stale_target = copy.deepcopy(c); stale_target["remote_version"] = "version-other"
    expect("PRECONDITION_STALE", lambda: policy.authorize_effect(request, p, a, stale_target))

    stale_precondition = copy.deepcopy(c); stale_precondition["precondition_digest"] = "4" * 64
    expect("PRECONDITION_STALE", lambda: policy.authorize_effect(request, p, a, stale_precondition))

    human_live = copy.deepcopy(a); human_live["evidence_class"] = "LIVE_PASS"
    expect("FIXTURE_AS_LIVE_HUMAN_PASS", lambda: policy.authorize_effect(request, p, human_live, c))

    policy_live = copy.deepcopy(p); policy_live["evidence_class"] = "LIVE_PASS"
    expect("FIXTURE_AS_LIVE_POLICY_PASS", lambda: policy.authorize_effect(request, policy_live, a, c))

    pre_live = copy.deepcopy(c); pre_live["evidence_class"] = "LIVE_PASS"
    expect("FIXTURE_AS_LIVE_PRECONDITION_PASS", lambda: policy.authorize_effect(request, p, a, pre_live))

    weak_irreversible = copy.deepcopy(request)
    weak_irreversible["runtime_intent"]["side_effect_class"] = "IRREVERSIBLE_WRITE"
    weak_p = policy.fixed_policy_observation(weak_irreversible)
    weak_a = policy.fixed_approval(weak_irreversible)
    weak_c = policy.fixed_precondition(weak_irreversible)
    expect("IRREVERSIBLE_EFFECT_REQUIRES_STRONG_APPROVAL", lambda: policy.authorize_effect(weak_irreversible, weak_p, weak_a, weak_c))

    print("PASS: DA-EF-P policy/Human/precondition planted controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
