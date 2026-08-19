#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
PREFLIGHT = ROOT / "matrix-preflight.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


retry = load_module("dual_agent_retry", ROOT / "workflow_retry_restart.py")
human = load_module("dual_agent_human", ROOT / "workflow_human_wait.py")
comp = load_module("dual_agent_comp", ROOT / "workflow_compensation.py")
reducer = retry.reducer
contract = reducer.contract

REQUIRED_CASES = {
    "ordinary_completion",
    "retry",
    "typed_timer",
    "deadline",
    "restart_replay",
    "human_wait",
    "human_resume",
    "human_refusal",
    "cancellation",
    "stale_result",
    "activity_failure",
    "effect_admission_request",
    "compensation",
    "compensation_failure",
    "cleanup_failure",
}
SEPARATE_LANES = (
    "transport_state",
    "provider_state",
    "effect_state",
    "gate_state",
    "task_state",
    "user_outcome_state",
    "release_state",
)


class MatrixError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (f": {detail}" if detail else ""))


def refuse(code: str, detail: str = "") -> None:
    raise MatrixError(code, detail)


def expect(code: str, fn: Callable[[], Any]) -> None:
    try:
        fn()
    except (MatrixError, reducer.ReplayError, retry.BoundaryError, human.HumanBoundaryError, comp.CompensationError) as exc:
        actual = getattr(exc, "code", "")
        if actual != code:
            raise AssertionError(f"expected {code}, got {exc}") from exc
        print(f"{code}: RED/{code}")
    else:
        raise AssertionError(f"{code}: planted control survived")


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def check_blob(relative_path: str, expected: str) -> None:
    actual = git_blob_sha(REPO_ROOT / relative_path)
    if actual != expected:
        refuse("SIBLING_BLOB_DRIFT", f"{relative_path}: {actual} != {expected}")


def assert_materialized_siblings(preflight: dict[str, Any]) -> None:
    if preflight.get("schema") != "bettor-arena/dual-agent-offload-workflow/matrix-preflight/v1":
        refuse("PREFLIGHT_SCHEMA_MISMATCH")
    parent = preflight.get("common_parent", {})
    if parent.get("commit") != "7821e81f15d64ff3119d9bdb9278fc725e5aa398" or parent.get("tree") != "60d486041b36608d5d03e33b2eb8944c9899b50b":
        refuse("PARENT_SUBJECT_DRIFT")
    if preflight.get("runtime_contract_set") != "e6671977dbf0a378474f924a142a82843bc0e3429f4546ffb0145af73f7827fe":
        refuse("RUNTIME_CONTRACT_DRIFT")
    siblings = preflight.get("siblings")
    if not isinstance(siblings, list) or {item.get("atom") for item in siblings} != {"DA-WF-R", "DA-WF-H", "DA-WF-COMP"}:
        refuse("INCOMPLETE_SIBLING_SET")
    for item in siblings:
        files = item.get("files")
        if not isinstance(files, dict) or not files:
            refuse("INCOMPLETE_SIBLING_SET")
        for path, expected in files.items():
            check_blob(str(path), str(expected))
    external = preflight.get("external_states")
    if not isinstance(external, dict) or any(value != "NOT_EXERCISED" for value in external.values()):
        refuse("EVIDENCE_LAUNDERING")


def assert_denominator(rows: dict[str, Any]) -> None:
    actual = set(rows)
    if actual != REQUIRED_CASES:
        missing = sorted(REQUIRED_CASES - actual)
        extra = sorted(actual - REQUIRED_CASES)
        refuse("INCOMPLETE_REPLAY_DENOMINATOR", f"missing={missing} extra={extra}")


def assert_lane_separation(result: dict[str, Any]) -> None:
    for lane in SEPARATE_LANES:
        if result.get(lane) != "NOT_EXERCISED":
            refuse("EVIDENCE_LAUNDERING", lane)
    proposal = result.get("loopx_proposal")
    if not isinstance(proposal, dict) or proposal.get("mode") != "PROPOSAL_ONLY":
        refuse("DIRECT_LOOPX_WRITE")


def assert_same_replay(first: bytes, second: bytes) -> None:
    if first != second:
        refuse("NON_BYTE_IDENTICAL_REPLAY")


def ordinary_history(submission: dict[str, Any]) -> list[dict[str, Any]]:
    return reducer.chain_events(submission, [
        ("ADMISSION_REQUESTED", {}),
        ("ADMISSION_ALLOWED", {}),
        ("DELIVERY_REQUESTED", {}),
        ("REMOTE_DISPATCHED", {}),
        ("EXECUTION_STARTED", {}),
        ("RESULT_WAITING", {}),
        ("RESULT_RECEIVED", {"artifact_digest": "a" * 64}),
        ("RESULT_VERIFIED", {"verification_digest": "b" * 64}),
        ("RECONCILED", {"result_digest": "c" * 64}),
    ])


def retry_history(submission: dict[str, Any]) -> list[dict[str, Any]]:
    return reducer.chain_events(submission, [
        ("ADMISSION_REQUESTED", {}),
        ("ADMISSION_ALLOWED", {}),
        ("DELIVERY_REQUESTED", {}),
        ("RETRY_REQUESTED", {"parent_attempt_id": "attempt-1", "next_attempt_id": "attempt-2", "reason": "typed-timeout"}),
        ("RETRY_READY", {"attempt_id": "attempt-2", "timer_receipt_digest": "d" * 64}),
    ])


def fresh_process_bytes(submission: dict[str, Any], history: list[dict[str, Any]]) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        payload = Path(td) / "input.json"
        payload.write_text(json.dumps({"submission": submission, "history": history}), encoding="utf-8")
        code = (
            "import importlib.util,json,sys;"
            f"spec=importlib.util.spec_from_file_location('r',{str(ROOT / 'workflow_reducer.py')!r});"
            "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);"
            "x=json.load(open(sys.argv[1]));sys.stdout.buffer.write(m.replay_bytes(x['submission'],x['history']))"
        )
        return subprocess.check_output([sys.executable, "-c", code, str(payload)])


def human_decision(submission: dict[str, Any], decision: str) -> dict[str, Any]:
    return {
        "human_decision": decision,
        "actor_class": "HUMAN",
        "job_id": submission["job"]["job_id"],
        "tenant_scope": submission["job"]["tenant_scope"],
        "policy_digest": submission["job"]["bindings"]["policy_digest"],
        "runtime_digest": submission["job"]["bindings"]["runtime_digest"],
        "source_subject": submission["job"]["source_subject"],
        "decision_digest": "e" * 64,
        "evidence_digest": "f" * 64,
        "evidence_class": "DETERMINISTIC_FIXTURE",
    }


def human_wait_specs() -> list[tuple[str, dict[str, Any]]]:
    return [
        ("ADMISSION_REQUESTED", {}),
        ("ADMISSION_ALLOWED", {}),
        ("HUMAN_WAIT_REQUIRED", {"approval_requirement": "BEFORE_EXTERNAL_WRITE", "required_evidence_digest": "1" * 64}),
    ]


def write_submission() -> dict[str, Any]:
    submission = contract.fixed_submission()
    submission["job"]["side_effect_class"] = "REVERSIBLE_WRITE"
    submission["job"]["approval_requirement"] = "BEFORE_EXTERNAL_WRITE"
    return submission


def compensation_base() -> list[tuple[str, dict[str, Any]]]:
    return [
        ("ADMISSION_REQUESTED", {}),
        ("ADMISSION_ALLOWED", {}),
        ("DELIVERY_REQUESTED", {}),
        ("REMOTE_DISPATCHED", {}),
        ("EXECUTION_STARTED", {}),
        ("RESULT_WAITING", {}),
        ("RESULT_RECEIVED", {"artifact_digest": "2" * 64}),
        ("RESULT_VERIFIED", {"verification_digest": "3" * 64}),
    ]


def compensation_request() -> dict[str, Any]:
    return {
        "mode": "EFFECT_COMPENSATION_REQUEST",
        "effect_owner": "dual-agent-effect-ledger",
        "effect_id": "effect-demo-1",
        "parent_idempotency_key": "effect-idem-1",
        "compensation_idempotency_key": "comp-idem-1",
        "reversible": True,
        "original_effect_state": "COMMITTED",
        "original_effect_receipt_digest": "4" * 64,
        "external_execution_state": "NOT_EXERCISED",
    }


def compensation_result(digest_char: str = "5") -> dict[str, Any]:
    return {
        "effect_owner": "dual-agent-effect-ledger",
        "effect_id": "effect-demo-1",
        "compensation_idempotency_key": "comp-idem-1",
        "compensation_receipt_digest": digest_char * 64,
        "external_execution_state": "NOT_EXERCISED",
    }


def run_matrix() -> dict[str, Any]:
    submission = contract.fixed_submission()
    rows: dict[str, Any] = {}

    ordinary = ordinary_history(submission)
    ordinary_result = reducer.reduce_history(submission, ordinary)
    assert ordinary_result["workflow_state"] == "COMPLETED"
    assert_lane_separation(ordinary_result)
    rows["ordinary_completion"] = ordinary_result["workflow_state"]

    retry_events = retry_history(submission)
    retry_result = retry.validate_operational_history(submission, retry_events)
    assert retry_result["workflow_state"] == "DELIVERY_PENDING" and retry_result["retry_count"] == 1
    assert_lane_separation(retry_result)
    rows["retry"] = retry_result["retry_count"]
    assert retry_result["operational_boundary"]["typed_timer_state"] == "PASS"
    rows["typed_timer"] = "PASS"

    deadline_events = reducer.chain_events(submission, [
        ("ADMISSION_REQUESTED", {}),
        ("DEADLINE_EXPIRED", {"decision_source": "HISTORY_EVENT", "observation_digest": "6" * 64}),
    ])
    deadline_result = retry.validate_operational_history(submission, deadline_events)
    assert deadline_result["workflow_state"] == "DEADLINE_EXPIRED"
    assert_lane_separation(deadline_result)
    rows["deadline"] = deadline_result["workflow_state"]

    direct = reducer.replay_bytes(submission, retry_events)
    restarted = fresh_process_bytes(submission, retry_events)
    assert_same_replay(direct, restarted)
    rows["restart_replay"] = "BYTE_IDENTICAL"

    wait_events = reducer.chain_events(submission, human_wait_specs())
    wait_result = human.validate_human_history(submission, wait_events)
    assert wait_result["workflow_state"] == "WAITING_FOR_HUMAN"
    assert_lane_separation(wait_result)
    rows["human_wait"] = wait_result["workflow_state"]

    approved_events = reducer.chain_events(submission, human_wait_specs() + [("HUMAN_APPROVED", human_decision(submission, "APPROVE"))])
    approved_result = human.validate_human_history(submission, approved_events)
    assert approved_result["workflow_state"] == "ADMITTED"
    assert_lane_separation(approved_result)
    rows["human_resume"] = approved_result["workflow_state"]

    refused_events = reducer.chain_events(submission, human_wait_specs() + [("POLICY_REFUSED", human_decision(submission, "REFUSE"))])
    refused_result = human.validate_human_history(submission, refused_events)
    assert refused_result["workflow_state"] == "POLICY_REFUSED"
    assert_lane_separation(refused_result)
    rows["human_refusal"] = refused_result["workflow_state"]

    cancel_events = reducer.chain_events(submission, [
        ("ADMISSION_REQUESTED", {}),
        ("ADMISSION_ALLOWED", {}),
        ("CANCEL_REQUESTED", {"requested_from": "ADMITTED", "decision_source": "HISTORY_EVENT"}),
        ("CANCEL_STARTED", {"cancellation_activity_digest": "7" * 64}),
        ("CANCELLED", {"cancellation_receipt_digest": "8" * 64}),
    ])
    cancel_result = retry.validate_operational_history(submission, cancel_events)
    assert cancel_result["workflow_state"] == "CANCELLED"
    assert_lane_separation(cancel_result)
    rows["cancellation"] = cancel_result["workflow_state"]

    stale_events = reducer.chain_events(submission, [
        ("ADMISSION_REQUESTED", {}),
        ("ADMISSION_ALLOWED", {}),
        ("DELIVERY_REQUESTED", {}),
        ("REMOTE_DISPATCHED", {}),
        ("EXECUTION_STARTED", {}),
        ("RESULT_WAITING", {}),
        ("RESULT_RECEIVED", {}),
        ("RESULT_STALE", {"policy_digest": "0" * 64}),
    ])
    stale_result = reducer.reduce_history(submission, stale_events)
    assert stale_result["workflow_state"] == "RESULT_STALE"
    assert_lane_separation(stale_result)
    rows["stale_result"] = stale_result["workflow_state"]

    failed_events = reducer.chain_events(submission, [
        ("ADMISSION_REQUESTED", {}),
        ("ADMISSION_ALLOWED", {}),
        ("DELIVERY_REQUESTED", {}),
        ("REMOTE_DISPATCHED", {}),
        ("ACTIVITY_FAILED", {"activity_receipt_digest": "9" * 64}),
        ("FAILED", {"failure_receipt_digest": "a" * 64}),
    ])
    failed_result = reducer.reduce_history(submission, failed_events)
    assert failed_result["workflow_state"] == "FAILED"
    assert_lane_separation(failed_result)
    rows["activity_failure"] = failed_result["workflow_state"]

    write = write_submission()
    effect_events = reducer.chain_events(write, [
        ("ADMISSION_REQUESTED", {}),
        ("ADMISSION_ALLOWED", {}),
        ("EFFECT_REQUESTED", {
            "mode": "EFFECT_ADMISSION_REQUEST",
            "effect_owner": "dual-agent-effect-ledger",
            "idempotency_key": "effect-idem-1",
            "operation": "create-demo-record",
        }),
    ])
    effect_result = reducer.reduce_history(write, effect_events)
    assert effect_result["effect_requests"] and effect_result["effect_requests"][0]["execution_state"] == "NOT_EXERCISED"
    assert_lane_separation(effect_result)
    rows["effect_admission_request"] = "REQUEST_ONLY"

    comp_events = reducer.chain_events(write, compensation_base() + [
        ("COMPENSATION_REQUIRED", compensation_request()),
        ("COMPENSATED", compensation_result("b")),
    ])
    comp_result = comp.validate_compensation_history(write, comp_events)
    assert comp_result["workflow_state"] == "COMPENSATED"
    assert_lane_separation(comp_result)
    rows["compensation"] = comp_result["workflow_state"]

    comp_fail_events = reducer.chain_events(write, compensation_base() + [
        ("COMPENSATION_REQUIRED", compensation_request()),
        ("COMPENSATION_FAILED", compensation_result("c")),
    ])
    comp_fail_result = comp.validate_compensation_history(write, comp_fail_events)
    assert comp_fail_result["workflow_state"] == "COMPENSATION_FAILED"
    assert_lane_separation(comp_fail_result)
    rows["compensation_failure"] = comp_fail_result["workflow_state"]

    cleanup_events = reducer.chain_events(write, compensation_base() + [
        ("CLEANUP_FAILED", {"cleanup_receipt_digest": "d" * 64}),
    ])
    cleanup_result = comp.validate_compensation_history(write, cleanup_events)
    assert cleanup_result["workflow_state"] == "FAILED_CLEANUP"
    assert_lane_separation(cleanup_result)
    rows["cleanup_failure"] = cleanup_result["workflow_state"]

    assert_denominator(rows)
    return rows


def main() -> int:
    preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    assert_materialized_siblings(preflight)
    print("P1: PASS byte-preserving sibling materialization")

    rows = run_matrix()
    print(f"P2: PASS complete denominator {len(rows)}/{len(REQUIRED_CASES)}")

    first = reducer.replay_bytes(contract.fixed_submission(), ordinary_history(contract.fixed_submission()))
    second = reducer.replay_bytes(contract.fixed_submission(), ordinary_history(contract.fixed_submission()))
    assert_same_replay(first, second)
    print("P3: PASS byte-identical convergence replay")

    one_path = "loop_wiki/dual-agent-offload-workflow/workflow_retry_restart.py"
    expect("SIBLING_BLOB_DRIFT", lambda: check_blob(one_path, "0" * 40))

    incomplete = dict(rows)
    incomplete.pop("cleanup_failure")
    expect("INCOMPLETE_REPLAY_DENOMINATOR", lambda: assert_denominator(incomplete))

    bad_history = ordinary_history(contract.fixed_submission())
    bad_history[0]["workflow_subject"]["commit"] = "f" * 40
    bad_history[0]["event_digest"] = reducer.digest({k: v for k, v in bad_history[0].items() if k != "event_digest"})
    expect("HISTORY_SUBJECT_MISMATCH", lambda: reducer.reduce_history(contract.fixed_submission(), bad_history))

    expect("NON_BYTE_IDENTICAL_REPLAY", lambda: assert_same_replay(first, first + b"x"))

    laundered = reducer.reduce_history(contract.fixed_submission(), ordinary_history(contract.fixed_submission()))
    laundered["provider_state"] = "PASS"
    expect("EVIDENCE_LAUNDERING", lambda: assert_lane_separation(laundered))

    direct_loopx = reducer.chain_events(contract.fixed_submission(), [("ADMISSION_REQUESTED", {"loopx_write_mode": "DIRECT_APPEND"})])
    expect("DIRECT_LOOPX_WRITE", lambda: reducer.reduce_history(contract.fixed_submission(), direct_loopx))

    write = write_submission()
    direct_effect = reducer.chain_events(write, [
        ("ADMISSION_REQUESTED", {}),
        ("ADMISSION_ALLOWED", {}),
        ("EFFECT_REQUESTED", {"mode": "DIRECT_PROVIDER_WRITE", "effect_owner": "dual-agent-effect-ledger", "idempotency_key": "effect-idem-1"}),
    ])
    expect("EFFECT_OWNER_BYPASS", lambda: reducer.reduce_history(write, direct_effect))

    terminal = reducer.chain_events(contract.fixed_submission(), [
        ("ADMISSION_REQUESTED", {}),
        ("DEADLINE_EXPIRED", {}),
        ("RECONCILED", {}),
    ])
    expect("EVENT_AFTER_TERMINAL", lambda: reducer.reduce_history(contract.fixed_submission(), terminal))

    drift = contract.fixed_submission()
    drift["job"]["contract_set_ref"]["manifest_digest"] = "0" * 64
    expect("RUNTIME_CONTRACT_MISMATCH", lambda: reducer.reduce_history(drift, []))

    print("PASS: DA-WF-E complete deterministic replay/mutation matrix")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
