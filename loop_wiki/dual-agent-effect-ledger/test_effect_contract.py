#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("dual_agent_effect_contract", ROOT / "effect_contract.py")
assert SPEC is not None and SPEC.loader is not None
effect = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(effect)


def expect(code: str, fn: Callable[[], Any]) -> None:
    try:
        fn()
    except effect.EffectContractError as exc:
        if exc.code != code:
            raise AssertionError(f"expected {code}, got {exc}") from exc
        print(f"{code}: RED/{code}")
    else:
        raise AssertionError(f"{code}: planted control survived")


def main() -> int:
    preflight = json.loads((ROOT / "preflight.json").read_text(encoding="utf-8"))
    assert preflight["git_parent"]["commit"] == effect.WORKFLOW_COMMIT
    assert preflight["git_parent"]["tree"] == effect.WORKFLOW_TREE
    assert preflight["git_parent"]["workflow_reducer_blob"] == effect.WORKFLOW_REDUCER_BLOB
    assert preflight["runtime_contract"]["effect_intent_blob"] == effect.RUNTIME_EFFECT_SCHEMA_BLOB
    assert preflight["substrate_reference"]["effect_contract_blob"] == effect.SUBSTRATE_EFFECT_BLOB
    assert preflight["substrate_reference"]["reconciliation_worker_blob"] == effect.SUBSTRATE_WORKER_BLOB
    assert preflight["substrate_reference"]["writer_authority"] == "NONE"
    assert all(value == "NOT_EXERCISED" for value in preflight["external_states"].values())
    print("P1: PASS exact workflow/runtime/substrate preflight")

    contract = effect.fixed_contract()
    effect.validate_contract(contract)
    request = effect.fixed_admission_request()
    receipt = effect.mechanism_receipt(request)
    assert receipt["contract_state"] == "PASS"
    assert receipt["canonical_effect_writer"] == "dual-agent-effect-ledger"
    assert receipt["substrate_state"] == "REFERENCE_ONLY"
    assert receipt["observable_effect_state"] == "NOT_EXERCISED"
    print("P2: PASS single-writer effect contract + request interface")

    sequence = [
        "EFFECT_PROPOSED",
        "INTENT_VALIDATED",
        "POLICY_AND_APPROVAL_CHECKED",
        "IDEMPOTENCY_RESERVED",
        "PRECONDITION_REVALIDATED",
        "EXECUTION_AUTHORIZED",
        "EFFECT_ATTEMPTED",
        "EFFECT_OBSERVED",
        "EFFECT_COMMITTED",
    ]
    for current, target in zip(sequence, sequence[1:]):
        kwargs: dict[str, Any] = {}
        if target == "EFFECT_COMMITTED":
            kwargs = {
                "attempt_result": "SUCCESS",
                "readback": {"verified": True, "digest": "4" * 64, "remote_version": "version-7"},
                "expected_remote_version": "version-7",
            }
        effect.validate_transition(current, target, **kwargs)
    print("P3: PASS deterministic write-state vocabulary through readback-gated commit")

    duplicate = copy.deepcopy(request)
    assert effect.classify_duplicate(request, duplicate) == "DUPLICATE_REFUSED"
    distinct = copy.deepcopy(request)
    distinct["runtime_intent"]["effect_id"] = "effect-demo-002"
    distinct["runtime_intent"]["idempotency_key"] = "effect-idem-002"
    distinct["runtime_intent"]["normalized_request_digest"] = "5" * 64
    distinct["workflow_request"]["idempotency_key"] = "effect-idem-002"
    distinct["workflow_request"]["request_digest"] = "5" * 64
    assert effect.classify_duplicate(request, distinct) == "DISTINCT_EFFECT"
    print("P4: PASS duplicate refusal and distinct logical effect classification")

    effect.validate_transition("EFFECT_ATTEMPTED", "RESULT_UNKNOWN")
    effect.validate_transition("RESULT_UNKNOWN", "RECONCILIATION_REQUIRED")
    effect.validate_task_projection("RESULT_UNKNOWN", "NOT_EXERCISED")
    print("P5: PASS unknown effect stays unresolved until reconciliation")

    bad_contract = copy.deepcopy(contract)
    bad_contract["canonical_effect_writer"] = "inception-ingress-effects"
    expect("DUPLICATE_EFFECT_AUTHORITY", lambda: effect.validate_contract(bad_contract))

    bad_contract = copy.deepcopy(contract)
    bad_contract["runtime_contract"]["effect_intent_blob"] = "0" * 40
    expect("UPSTREAM_SUBJECT_DRIFT", lambda: effect.validate_contract(bad_contract))

    bad_contract = copy.deepcopy(contract)
    bad_contract["substrate_reference"]["writer_authority"] = "SQLITE_FIXTURE"
    expect("SUBSTRATE_AUTHORITY_DRIFT", lambda: effect.validate_contract(bad_contract))

    collision = copy.deepcopy(request)
    collision["runtime_intent"]["normalized_request_digest"] = "6" * 64
    collision["workflow_request"]["request_digest"] = "6" * 64
    expect("IDEMPOTENCY_COLLISION", lambda: effect.classify_duplicate(request, collision))

    cross_tenant = copy.deepcopy(request)
    cross_tenant["tenant_scope"] = "tenant-other"
    cross_tenant["workflow_request"]["tenant_scope"] = "tenant-other"
    expect("CROSS_TENANT_EFFECT_IDENTITY", lambda: effect.classify_duplicate(request, cross_tenant))

    expect(
        "READBACK_REQUIRED",
        lambda: effect.validate_transition(
            "EFFECT_OBSERVED", "EFFECT_COMMITTED", attempt_result="SUCCESS", readback=None
        ),
    )

    expect(
        "TIMEOUT_AS_COMMIT",
        lambda: effect.validate_transition(
            "EFFECT_OBSERVED",
            "EFFECT_COMMITTED",
            attempt_result="TIMEOUT",
            readback={"verified": True, "digest": "7" * 64, "remote_version": "version-7"},
        ),
    )

    expect(
        "UNRESOLVED_EFFECT_COMMIT",
        lambda: effect.validate_transition(
            "RESULT_UNKNOWN",
            "EFFECT_COMMITTED",
            attempt_result="SUCCESS",
            readback={"verified": True, "digest": "8" * 64, "remote_version": "version-7"},
        ),
    )

    bad = copy.deepcopy(request)
    bad["target"]["provider_subject"]["commit"] = "latest"
    expect("MUTABLE_EFFECT_SUBJECT", lambda: effect.validate_admission_request(bad))

    expect(
        "WORKER_OR_PROVIDER_SELF_COMMIT",
        lambda: effect.validate_transition("EFFECT_OBSERVED", "EFFECT_COMMITTED", actor_class="PROVIDER"),
    )

    bad = copy.deepcopy(request)
    bad["external_states"]["provider_write"] = "PASS"
    expect("FIXTURE_AS_LIVE_EFFECT", lambda: effect.validate_admission_request(bad))

    expect("UNRESOLVED_EFFECT_HIDDEN", lambda: effect.validate_task_projection("RESULT_UNKNOWN", "COMPLETED"))

    bad = copy.deepcopy(request)
    bad["private_reasoning"] = "must-not-persist"
    expect("SECRET_OR_REASONING_LEAK", lambda: effect.validate_admission_request(bad))

    bad_contract = copy.deepcopy(contract)
    bad_contract["provider_native_idempotency_is_authority"] = True
    expect("PROVIDER_IDEMPOTENCY_AS_AUTHORITY", lambda: effect.validate_contract(bad_contract))

    expect(
        "READBACK_DISAGREEMENT",
        lambda: effect.validate_transition(
            "EFFECT_OBSERVED",
            "EFFECT_COMMITTED",
            attempt_result="SUCCESS",
            readback={"verified": True, "digest": "9" * 64, "remote_version": "version-stale"},
            expected_remote_version="version-7",
        ),
    )

    print("PASS: DA-EF-C effect identity/authority/readback planted controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
