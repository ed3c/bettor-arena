#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
PREFLIGHT = ROOT / "effect-matrix-preflight.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


provider = load_module("dual_agent_effect_provider", ROOT / "effect_provider_adapter.py")
comp = load_module("dual_agent_effect_compensation", ROOT / "effect_compensation.py")
policy = provider.policy
reducer = policy.reducer
contract = reducer.contract


class MatrixError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (f": {detail}" if detail else ""))


def refuse(code: str, detail: str = "") -> None:
    raise MatrixError(code, detail)


def expect(code: str, fn: Callable[[], Any]) -> str:
    try:
        fn()
    except (
        MatrixError,
        provider.ProviderBoundaryError,
        comp.CompensationLedgerError,
        policy.EffectPolicyError,
        reducer.EffectReducerError,
        contract.EffectContractError,
    ) as exc:
        actual = getattr(exc, "code", "")
        if actual != code:
            raise AssertionError(f"expected {code}, got {exc}") from exc
        print(f"{code}: RED/{code}")
        return code
    raise AssertionError(f"{code}: planted control survived")


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def assert_materialized(preflight: dict[str, Any]) -> None:
    if preflight.get("schema") != "bettor-arena/dual-agent-effect-ledger/matrix-preflight/v1":
        refuse("PREFLIGHT_SCHEMA_MISMATCH")
    base = preflight.get("base_parent", {})
    if base.get("commit") != "ba9ebfe5f4efa01d040ec3b51f93b32045899b23" or base.get("tree") != "a128ea330647d9a3c83f7852eb7174bcdbbd6511":
        refuse("BASE_SUBJECT_DRIFT")
    siblings = preflight.get("siblings")
    if not isinstance(siblings, list) or {row.get("atom") for row in siblings} != {"DA-EF-A", "DA-EF-COMP"}:
        refuse("INCOMPLETE_SIBLING_SET")
    for row in siblings:
        files = row.get("files")
        if not isinstance(files, dict) or not files:
            refuse("INCOMPLETE_SIBLING_SET")
        for relative_path, expected in files.items():
            actual = git_blob_sha(REPO_ROOT / str(relative_path))
            if actual != expected:
                refuse("SIBLING_BLOB_DRIFT", f"{relative_path}: {actual} != {expected}")
    external = preflight.get("external_states")
    if not isinstance(external, dict) or any(value != "NOT_EXERCISED" for value in external.values()):
        refuse("EVIDENCE_LAUNDERING")


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


def readback_event(request: dict[str, Any], digest_char: str = "9") -> tuple[str, dict[str, Any]]:
    return (
        "READBACK_RECORDED",
        {
            "actor_class": "EFFECT_LEDGER",
            "verified": True,
            "digest": digest_char * 64,
            "remote_version": request["precondition_binding"]["expected_remote_version"],
            "provider_id": request["target"]["provider_id"],
            "resource_id": request["target"]["resource_id"],
            "action": request["target"]["action"],
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


def committed_parent(request: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    specs = admitted_prefix() + [
        attempt(request, "attempt-parent", "SUCCESS"),
        transition("EFFECT_ATTEMPTED", attempt_result="SUCCESS"),
        transition("EFFECT_OBSERVED", attempt_result="SUCCESS"),
        readback_event(request),
        transition("EFFECT_COMMITTED", attempt_result="SUCCESS"),
    ]
    history = reducer.chain_events(request, specs)
    return history, reducer.reduce_effect_history(request, history)


def authorization(request: dict[str, Any]) -> dict[str, Any]:
    return policy.authorize_effect(
        request,
        policy.fixed_policy_observation(request),
        policy.fixed_approval(request),
        policy.fixed_precondition(request),
    )


def provider_result(packet: dict[str, Any], outcome: str, *, cleanup_state: str = "CLEAN") -> dict[str, Any]:
    return {
        "schema": "bettor-arena/dual-agent-effect-ledger/provider-observation/v1",
        "effect_identity_digest": packet["effect_identity_digest"],
        "attempt_id": packet["attempt_id"],
        "provider_id": packet["provider_id"],
        "resource_id": packet["resource_id"],
        "action": packet["action"],
        "provider_subject": packet["provider_subject"],
        "outcome": outcome,
        "provider_result_digest": "a" * 64,
        "provider_native_idempotency_observed": True,
        "provider_native_idempotency_is_authority": False,
        "canonical_write_mode": "OBSERVATION_ONLY",
        "canonical_effect_state": "NOT_COMMITTED",
        "cleanup_state": cleanup_state,
        "evidence_class": "DETERMINISTIC_FIXTURE",
    }


def target_readback(packet: dict[str, Any], *, version: str | None = None) -> dict[str, Any]:
    return {
        "schema": "bettor-arena/dual-agent-effect-ledger/target-readback/v1",
        "provider_id": packet["provider_id"],
        "resource_id": packet["resource_id"],
        "action": packet["action"],
        "verified": True,
        "digest": "b" * 64,
        "remote_version": packet["expected_remote_version"] if version is None else version,
        "cleanup_state": "CLEAN",
        "evidence_class": "API_READBACK_FIXTURE",
    }


def assert_denominator(rows: dict[str, Any], preflight: dict[str, Any]) -> None:
    required = set(preflight.get("required_cases", []))
    if set(rows) != required:
        refuse("INCOMPLETE_EFFECT_DENOMINATOR", f"missing={sorted(required-set(rows))} extra={sorted(set(rows)-required)}")


def run_matrix() -> dict[str, Any]:
    request = contract.fixed_admission_request()
    rows: dict[str, Any] = {}

    duplicate = reducer.reservation_batch([request], copy.deepcopy(request))
    assert duplicate["decision"] == "DUPLICATE_REFUSED"
    rows["exact_duplicate"] = duplicate["decision"]

    collision = copy.deepcopy(request)
    collision["runtime_intent"]["normalized_request_digest"] = "6" * 64
    collision["workflow_request"]["request_digest"] = "6" * 64
    rows["idempotency_collision"] = expect("IDEMPOTENCY_COLLISION", lambda: reducer.reservation_batch([request], collision))

    cross = copy.deepcopy(request)
    cross["tenant_scope"] = "tenant-other"
    cross["workflow_request"]["tenant_scope"] = "tenant-other"
    rows["cross_tenant_collision"] = expect("CROSS_TENANT_EFFECT_IDENTITY", lambda: reducer.reservation_batch([request], cross))

    p = policy.fixed_policy_observation(request)
    a = policy.fixed_approval(request)
    c = policy.fixed_precondition(request)
    refused = copy.deepcopy(p); refused["decision"] = "REFUSE"
    rows["policy_refusal"] = expect("POLICY_REFUSED", lambda: policy.authorize_effect(request, refused, a, c))
    approval = copy.deepcopy(a); approval["decision"] = "REFUSE"
    rows["approval_required"] = expect("APPROVAL_REQUIRED", lambda: policy.authorize_effect(request, p, approval, c))
    stale = copy.deepcopy(c); stale["remote_version"] = "version-other"
    rows["precondition_stale"] = expect("PRECONDITION_STALE", lambda: policy.authorize_effect(request, p, a, stale))

    auth = authorization(request)
    packet = provider.build_attempt_packet(auth, credential_handle="secret://provider/demo", route_kind="API")
    failure = provider.classify_attempt_result(packet, provider_result(packet, "FAILURE"))
    assert failure["effect_state_proposal"] == "ATTEMPT_FAILED"
    rows["provider_failure"] = failure["effect_state_proposal"]

    unknown = provider.classify_attempt_result(packet, provider_result(packet, "CONNECTION_LOST"))
    assert unknown["effect_state_proposal"] == "RESULT_UNKNOWN"
    rows["timeout_connection_unknown"] = "CONNECTION_LOST"
    rows["result_unknown"] = unknown["effect_state_proposal"]

    rb = provider.validate_target_readback(packet, unknown, target_readback(packet))
    assert rb["verified"] is True
    rows["reconciliation"] = "READBACK_VERIFIED"
    proposal = provider.propose_commit(packet, unknown, rb)
    assert proposal["mode"] == "EFFECT_COMMIT_PROPOSAL"
    rows["verified_readback_commit"] = proposal["mode"]

    rows["readback_disagreement"] = expect(
        "READBACK_DISAGREEMENT",
        lambda: provider.validate_target_readback(packet, unknown, target_readback(packet, version="version-other")),
    )

    _, parent_result = committed_parent(request)
    link = comp.build_compensation_link(request, parent_result)
    comp.validate_compensation_link(request, parent_result, link)
    rows["compensation_required"] = "LINKED_EFFECT_AUTHORIZED"
    rows["compensated"] = comp.compensation_result(link, "COMPENSATED", accepted=True)["state"]
    rows["compensation_failure"] = comp.compensation_result(link, "COMPENSATION_FAILED", accepted=False)["state"]

    rows["cleanup_residue"] = expect(
        "CLEANUP_RESIDUE_HIDDEN",
        lambda: provider.classify_attempt_result(packet, provider_result(packet, "SUCCESS", cleanup_state="DIRTY")),
    )
    return rows


def main() -> int:
    preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    assert_materialized(preflight)
    print("P1: PASS byte-preserving provider/compensation materialization")

    rows = run_matrix()
    assert_denominator(rows, preflight)
    print(f"P2: PASS complete effect denominator {len(rows)}/{len(preflight['required_cases'])}")

    repeat = run_matrix()
    if json.dumps(rows, sort_keys=True, separators=(",", ":")) != json.dumps(repeat, sort_keys=True, separators=(",", ":")):
        refuse("NONDETERMINISTIC_EFFECT_MATRIX")
    print("P3: PASS byte-identical deterministic matrix result")

    bad_preflight = copy.deepcopy(preflight)
    bad_preflight["siblings"][0]["files"]["loop_wiki/dual-agent-effect-ledger/effect_provider_adapter.py"] = "0" * 40
    expect("SIBLING_BLOB_DRIFT", lambda: assert_materialized(bad_preflight))

    incomplete = copy.deepcopy(rows); incomplete.pop("provider_failure")
    expect("INCOMPLETE_EFFECT_DENOMINATOR", lambda: assert_denominator(incomplete, preflight))

    launder = copy.deepcopy(preflight); launder["external_states"]["provider_io"] = "PASS"
    expect("EVIDENCE_LAUNDERING", lambda: assert_materialized(launder))

    request = contract.fixed_admission_request()
    auth = authorization(request)
    packet = provider.build_attempt_packet(auth, credential_handle="secret://provider/demo", route_kind="API")

    authority = provider_result(packet, "SUCCESS"); authority["provider_native_idempotency_is_authority"] = True
    expect("PROVIDER_IDEMPOTENCY_AS_AUTHORITY", lambda: provider.classify_attempt_result(packet, authority))

    self_commit = provider_result(packet, "SUCCESS"); self_commit["canonical_write_mode"] = "CANONICAL_WRITE"
    expect("PROVIDER_SELF_COMMIT", lambda: provider.classify_attempt_result(packet, self_commit))

    live = provider_result(packet, "SUCCESS"); live["evidence_class"] = "LIVE_PASS"
    expect("FIXTURE_AS_LIVE_PROVIDER_PASS", lambda: provider.classify_attempt_result(packet, live))

    mutable = provider_result(packet, "SUCCESS"); mutable["provider_subject"] = copy.deepcopy(packet["provider_subject"]); mutable["provider_subject"]["commit"] = "0" * 40
    expect("MUTABLE_PROVIDER_SUBJECT", lambda: provider.classify_attempt_result(packet, mutable))

    secret = provider_result(packet, "SUCCESS"); secret["token_value"] = "forbidden"
    expect("RAW_CREDENTIAL", lambda: provider.classify_attempt_result(packet, secret))

    unknown_specs = admitted_prefix() + [
        attempt(request, "attempt-u", "TIMEOUT"),
        transition("EFFECT_ATTEMPTED", attempt_result="TIMEOUT"),
        transition("RESULT_UNKNOWN", attempt_result="TIMEOUT"),
        ("TASK_PROJECTION", {"task_state": "COMPLETED", "loopx_write_mode": "PROPOSAL_ONLY"}),
    ]
    expect("UNRESOLVED_EFFECT_HIDDEN", lambda: reducer.reduce_effect_history(request, reducer.chain_events(request, unknown_specs)))

    blind_commit = admitted_prefix() + [
        attempt(request, "attempt-b", "TIMEOUT"),
        transition("EFFECT_ATTEMPTED", attempt_result="TIMEOUT"),
        transition("RESULT_UNKNOWN", attempt_result="TIMEOUT"),
        transition("EFFECT_COMMITTED", attempt_result="TIMEOUT"),
    ]
    expect("UNRESOLVED_EFFECT_COMMIT", lambda: reducer.reduce_effect_history(request, reducer.chain_events(request, blind_commit)))

    committed_history, committed_result = committed_parent(request)
    double = list(committed_history)
    double.append(reducer.make_event(request, len(double), "STATE_TRANSITION", {"target_state": "EFFECT_COMMITTED", "actor_class": "EFFECT_LEDGER"}, double[-1]["event_digest"]))
    expect("DOUBLE_COMMIT", lambda: reducer.reduce_effect_history(request, double))

    link = comp.build_compensation_link(request, committed_result)
    deleted = copy.deepcopy(link); deleted["parent_history_head"] = "ROOT"
    expect("COMPENSATION_AUDIT_DELETION", lambda: comp.validate_compensation_link(request, committed_result, deleted))

    print("PASS: DA-EF-E complete effect matrix + planted controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
