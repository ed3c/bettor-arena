"""Deterministic Dual-Agent offload workflow contract for #199.

This module validates metadata and workflow authority only. It performs no
network/provider call, does not append the canonical LoopX ledger, and never
executes an external effect.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

RUNTIME_REPO = "ed3c/runtime-env"
RUNTIME_COMMIT = "1fd6a65a2e628ba1b31e89800297e7202dadf126"
RUNTIME_TREE = "cc287010c96391e0a718141c2f4afb92bac3db06"
RUNTIME_CONTRACT_SET_DIGEST = "e6671977dbf0a378474f924a142a82843bc0e3429f4546ffb0145af73f7827fe"
OFFLOAD_SCHEMA_ID = "https://runtime-env.invalid/contracts/dual-agent/offload-job.v1.schema.json"

H40 = re.compile(r"^[0-9a-f]{40}$")
H64 = re.compile(r"^[0-9a-f]{64}$")
H32 = re.compile(r"^[0-9a-f]{32}$")

WORKFLOW_STATES = (
    "SUBMITTED", "ADMISSION_PENDING", "ADMITTED", "DELIVERY_PENDING",
    "REMOTE_DISPATCHED", "RUNNING", "WAITING_FOR_RESULT", "WAITING_FOR_HUMAN",
    "VERIFYING", "RECONCILING", "RETRY_SCHEDULED", "CANCEL_REQUESTED",
    "CANCELLING", "CANCELLED", "DEADLINE_EXPIRED", "POLICY_REFUSED",
    "RUNTIME_ABSENT", "ACTIVITY_FAILED", "RESULT_STALE", "RESULT_REFUSED",
    "COMPENSATING", "COMPENSATED", "COMPENSATION_FAILED", "FAILED_CLEANUP",
    "FAILED", "COMPLETED",
)
TERMINALS = {
    "CANCELLED", "DEADLINE_EXPIRED", "POLICY_REFUSED", "RUNTIME_ABSENT",
    "RESULT_STALE", "RESULT_REFUSED", "COMPENSATED", "COMPENSATION_FAILED",
    "FAILED_CLEANUP", "FAILED", "COMPLETED",
}
ACTIVITY_KINDS = {
    "ADMISSION_CHECK", "TRANSPORT_DISPATCH", "REMOTE_EXECUTION", "RESULT_FETCH",
    "HUMAN_WAIT", "RESULT_VERIFY", "RECONCILE", "CANCEL", "COMPENSATE", "CLEANUP",
}
TRANSITIONS = {
    "SUBMITTED": {"ADMISSION_PENDING"},
    "ADMISSION_PENDING": {"ADMITTED", "POLICY_REFUSED", "RUNTIME_ABSENT", "DEADLINE_EXPIRED"},
    "ADMITTED": {"DELIVERY_PENDING", "WAITING_FOR_HUMAN", "CANCEL_REQUESTED"},
    "DELIVERY_PENDING": {"REMOTE_DISPATCHED", "RETRY_SCHEDULED", "CANCEL_REQUESTED", "DEADLINE_EXPIRED", "RUNTIME_ABSENT"},
    "REMOTE_DISPATCHED": {"RUNNING", "RETRY_SCHEDULED", "CANCEL_REQUESTED", "ACTIVITY_FAILED"},
    "RUNNING": {"WAITING_FOR_RESULT", "WAITING_FOR_HUMAN", "RETRY_SCHEDULED", "CANCEL_REQUESTED", "ACTIVITY_FAILED", "DEADLINE_EXPIRED"},
    "WAITING_FOR_RESULT": {"VERIFYING", "RETRY_SCHEDULED", "CANCEL_REQUESTED", "DEADLINE_EXPIRED"},
    "WAITING_FOR_HUMAN": {"ADMITTED", "CANCEL_REQUESTED", "DEADLINE_EXPIRED", "POLICY_REFUSED"},
    "VERIFYING": {"RECONCILING", "RESULT_STALE", "RESULT_REFUSED", "COMPENSATING", "FAILED_CLEANUP"},
    "RECONCILING": {"COMPLETED", "COMPENSATING", "FAILED_CLEANUP", "FAILED"},
    "RETRY_SCHEDULED": {"DELIVERY_PENDING", "CANCEL_REQUESTED", "DEADLINE_EXPIRED"},
    "CANCEL_REQUESTED": {"CANCELLING"},
    "CANCELLING": {"CANCELLED", "COMPENSATING", "FAILED_CLEANUP"},
    "ACTIVITY_FAILED": {"RETRY_SCHEDULED", "COMPENSATING", "FAILED"},
    "COMPENSATING": {"COMPENSATED", "COMPENSATION_FAILED"},
    "CANCELLED": set(), "DEADLINE_EXPIRED": set(), "POLICY_REFUSED": set(),
    "RUNTIME_ABSENT": set(), "RESULT_STALE": set(), "RESULT_REFUSED": set(),
    "COMPENSATED": set(), "COMPENSATION_FAILED": set(), "FAILED_CLEANUP": set(),
    "FAILED": set(), "COMPLETED": set(),
}
NON_WORKFLOW_LANES = (
    "transport_state", "provider_state", "effect_state", "gate_state",
    "task_state", "user_outcome_state", "release_state",
)


class WorkflowContractError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (f": {detail}" if detail else ""))


def refuse(code: str, detail: str = "") -> None:
    raise WorkflowContractError(code, detail)


def fixed_contract() -> dict[str, Any]:
    return {
        "schema": "bettor-arena/dual-agent-offload-workflow/contract/v1",
        "runtime_contract": {
            "repository": RUNTIME_REPO,
            "commit": RUNTIME_COMMIT,
            "tree": RUNTIME_TREE,
            "contract_set_digest": RUNTIME_CONTRACT_SET_DIGEST,
            "offload_schema_id": OFFLOAD_SCHEMA_ID,
        },
        "canonical_task_writer": "loopx-ledger",
        "loopx_write_mode": "PROPOSAL_ONLY",
        "effect_owner": "dual-agent-effect-ledger",
        "decision_sources": ["HISTORY_ONLY"],
        "activity_kinds": sorted(ACTIVITY_KINDS),
        "states": list(WORKFLOW_STATES),
        "terminal_states": sorted(TERMINALS),
        "evidence_ceiling": "DETERMINISTIC_WORKFLOW_CONTRACT_ONLY",
    }


def fixed_job() -> dict[str, Any]:
    return {
        "schema": "runtime-env/dual-agent/offload-job/v1",
        "job_id": "dual-agent-workflow-job-1",
        "idempotency_key": "dual-agent-workflow-idem-1",
        "tenant_scope": "tenant-demo",
        "requester_identity_ref": "spiffe://example.test/workload/requester",
        "source_subject": {"repository": "example/workload", "commit": "a" * 40, "tree": "b" * 40},
        "goal": "Exercise deterministic workflow contract only.",
        "non_goals": ["No provider execution"],
        "deadline": "2026-08-20T00:00:00Z",
        "budget": {"max_cpu_seconds": 30, "max_output_bytes": 65536, "max_attempts": 3, "max_cost_microunits": 0},
        "retry_policy": {"max_attempts": 3, "backoff_class": "EXPONENTIAL_BOUNDED"},
        "data_classification": "PUBLIC",
        "side_effect_class": "READ_ONLY",
        "execution_lane": "CLOUD",
        "capability_grant_ref": "grant-dual-agent-workflow",
        "bindings": {
            "runtime_digest": "1" * 64, "profile_digest": "2" * 64,
            "policy_digest": "3" * 64, "skill_digest": "4" * 64,
            "tool_digests": ["5" * 64], "image_digest": "6" * 64,
        },
        "allowlists": {
            "filesystem_paths": ["workspace/input.json", "workspace/output.json"],
            "network_origins": ["https://api.example.test"], "environment_names": ["LANG", "TZ"],
        },
        "secret_handles": [],
        "approval_requirement": "NONE",
        "artifact_requirements": [{"logical_name": "result-json", "media_type": "application/json", "required": True, "max_bytes": 65536}],
        "trace_id": "7" * 32,
        "method_contract": {
            "id": "https://skills-shared.invalid/agentic-tech-lead-orchestration/dual-agent-offload/method-contract.v1.schema.json",
            "sha256": "8" * 64,
        },
        "contract_set_ref": {
            "schema": "runtime-env/dual-agent/contract-set-manifest/v1",
            "manifest_digest": RUNTIME_CONTRACT_SET_DIGEST,
        },
    }


def fixed_submission() -> dict[str, Any]:
    return {
        "schema": "bettor-arena/dual-agent-offload-workflow/submission/v1",
        "workflow_subject": {"repository": "ed3c/bettor-arena", "commit": "c" * 40, "tree": "d" * 40},
        "workflow_state": "SUBMITTED",
        "job": fixed_job(),
        "decision_sources": ["HISTORY_ONLY"],
        "canonical_task_writer": "loopx-ledger",
        "loopx_write_mode": "PROPOSAL_ONLY",
        "effect_routing": "SEPARATE_OWNER_REQUIRED_FOR_WRITES",
        "history_fields": ["typed_events", "artifact_digests", "receipts"],
        "private_reasoning": None,
        "evidence": {lane: "NOT_EXERCISED" for lane in NON_WORKFLOW_LANES},
    }


def fixed_activity(kind: str = "ADMISSION_CHECK", attempt: int = 1) -> dict[str, Any]:
    return {
        "schema": "bettor-arena/dual-agent-offload-workflow/activity/v1",
        "activity_id": f"activity-{kind.lower()}-{attempt}",
        "kind": kind,
        "attempt": attempt,
        "attempt_id": f"attempt-{attempt}",
        "parent_attempt_id": None if attempt == 1 else f"attempt-{attempt - 1}",
        "input_digest": "9" * 64,
        "decision_source": "HISTORY_EVENT",
        "authority": "OBSERVATION_ONLY",
        "loopx_write_mode": "PROPOSAL_ONLY",
    }


def _digest(value: Any, code: str) -> None:
    if not isinstance(value, str) or H64.fullmatch(value) is None:
        refuse(code)


def validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema") != "bettor-arena/dual-agent-offload-workflow/contract/v1":
        refuse("WORKFLOW_SCHEMA_MISMATCH")
    runtime = contract.get("runtime_contract")
    if not isinstance(runtime, dict) or runtime != fixed_contract()["runtime_contract"]:
        refuse("RUNTIME_CONTRACT_MISMATCH")
    if contract.get("canonical_task_writer") != "loopx-ledger":
        refuse("SECOND_TASK_WRITER")
    if contract.get("loopx_write_mode") != "PROPOSAL_ONLY":
        refuse("DIRECT_LOOPX_WRITE")
    if contract.get("effect_owner") != "dual-agent-effect-ledger":
        refuse("EFFECT_OWNER_BYPASS")
    if contract.get("decision_sources") != ["HISTORY_ONLY"]:
        refuse("NONDETERMINISTIC_DECISION_SOURCE")
    if set(contract.get("activity_kinds", [])) != ACTIVITY_KINDS:
        refuse("ACTIVITY_VOCABULARY_DRIFT")
    if tuple(contract.get("states", [])) != WORKFLOW_STATES or set(contract.get("terminal_states", [])) != TERMINALS:
        refuse("STATE_VOCABULARY_DRIFT")


def validate_job(job: dict[str, Any]) -> None:
    if job.get("schema") != "runtime-env/dual-agent/offload-job/v1":
        refuse("OFFLOAD_JOB_SCHEMA_MISMATCH")
    source = job.get("source_subject")
    if not isinstance(source, dict) or H40.fullmatch(str(source.get("commit", ""))) is None or H40.fullmatch(str(source.get("tree", ""))) is None:
        refuse("MUTABLE_SOURCE_SUBJECT")
    bindings = job.get("bindings")
    if not isinstance(bindings, dict):
        refuse("OFFLOAD_JOB_SCHEMA_MISMATCH")
    for key in ("runtime_digest", "profile_digest", "policy_digest", "skill_digest", "image_digest"):
        _digest(bindings.get(key), "MUTABLE_RUNTIME_SUBJECT")
    tools = bindings.get("tool_digests")
    if not isinstance(tools, list) or not tools or any(H64.fullmatch(str(value)) is None for value in tools):
        refuse("MUTABLE_RUNTIME_SUBJECT")
    ref = job.get("contract_set_ref")
    if not isinstance(ref, dict) or ref.get("manifest_digest") != RUNTIME_CONTRACT_SET_DIGEST:
        refuse("RUNTIME_CONTRACT_MISMATCH")
    if H32.fullmatch(str(job.get("trace_id", ""))) is None:
        refuse("OFFLOAD_JOB_SCHEMA_MISMATCH")
    budget = job.get("budget")
    retry = job.get("retry_policy")
    if not isinstance(budget, dict) or not isinstance(retry, dict):
        refuse("UNBOUNDED_WORKFLOW")
    max_attempts = budget.get("max_attempts")
    retry_attempts = retry.get("max_attempts")
    if not isinstance(max_attempts, int) or max_attempts < 1 or max_attempts > 20:
        refuse("UNBOUNDED_WORKFLOW")
    if not isinstance(retry_attempts, int) or retry_attempts < 1 or retry_attempts > max_attempts:
        refuse("UNBOUNDED_WORKFLOW")
    try:
        deadline = str(job.get("deadline", ""))
        if not deadline.endswith("Z"):
            raise ValueError
        datetime.fromisoformat(deadline[:-1] + "+00:00")
    except ValueError:
        refuse("UNBOUNDED_WORKFLOW")
    for handle in job.get("secret_handles", []):
        if not isinstance(handle, str) or not handle.startswith("secret://"):
            refuse("SECRET_OR_REASONING_LEAK")


def validate_activity(activity: dict[str, Any], max_attempts: int) -> None:
    if activity.get("schema") != "bettor-arena/dual-agent-offload-workflow/activity/v1":
        refuse("ACTIVITY_SCHEMA_MISMATCH")
    if activity.get("kind") not in ACTIVITY_KINDS:
        refuse("ACTIVITY_VOCABULARY_DRIFT")
    attempt = activity.get("attempt")
    if not isinstance(attempt, int) or attempt < 1 or attempt > max_attempts:
        refuse("UNBOUNDED_WORKFLOW")
    _digest(activity.get("input_digest"), "MUTABLE_RUNTIME_SUBJECT")
    if activity.get("decision_source") != "HISTORY_EVENT":
        refuse("NONDETERMINISTIC_DECISION_SOURCE")
    if activity.get("authority") != "OBSERVATION_ONLY" or activity.get("loopx_write_mode") != "PROPOSAL_ONLY":
        refuse("DIRECT_LOOPX_WRITE")


def validate_transition(current: str, target: str) -> None:
    if current == "WAITING_FOR_HUMAN" and target == "COMPLETED":
        refuse("HUMAN_WAIT_AS_SUCCESS")
    if current in TERMINALS and current != "COMPLETED" and target == "COMPLETED":
        refuse("TERMINAL_COMPLETION_LAUNDERING")
    if current not in TRANSITIONS or target not in TRANSITIONS[current]:
        refuse("ILLEGAL_WORKFLOW_TRANSITION", f"{current}->{target}")


def validate_submission(submission: dict[str, Any]) -> None:
    if submission.get("schema") != "bettor-arena/dual-agent-offload-workflow/submission/v1":
        refuse("WORKFLOW_SCHEMA_MISMATCH")
    subject = submission.get("workflow_subject")
    if not isinstance(subject, dict) or subject.get("repository") != "ed3c/bettor-arena":
        refuse("MUTABLE_WORKFLOW_SUBJECT")
    if H40.fullmatch(str(subject.get("commit", ""))) is None or H40.fullmatch(str(subject.get("tree", ""))) is None:
        refuse("MUTABLE_WORKFLOW_SUBJECT")
    if submission.get("workflow_state") != "SUBMITTED":
        refuse("ILLEGAL_INITIAL_STATE")
    if submission.get("decision_sources") != ["HISTORY_ONLY"]:
        refuse("NONDETERMINISTIC_DECISION_SOURCE")
    if submission.get("canonical_task_writer") != "loopx-ledger":
        refuse("SECOND_TASK_WRITER")
    if submission.get("loopx_write_mode") != "PROPOSAL_ONLY":
        refuse("DIRECT_LOOPX_WRITE")
    if submission.get("effect_routing") != "SEPARATE_OWNER_REQUIRED_FOR_WRITES":
        refuse("EFFECT_OWNER_BYPASS")
    fields = submission.get("history_fields")
    if not isinstance(fields, list) or any(name in {"private_reasoning", "secret_value", "credential_value"} for name in fields):
        refuse("SECRET_OR_REASONING_LEAK")
    if submission.get("private_reasoning") is not None:
        refuse("SECRET_OR_REASONING_LEAK")
    evidence = submission.get("evidence")
    if not isinstance(evidence, dict) or any(evidence.get(lane) != "NOT_EXERCISED" for lane in NON_WORKFLOW_LANES):
        refuse("LANE_SUBSTITUTION")
    validate_job(submission.get("job", {}))


def workflow_receipt(submission: dict[str, Any]) -> dict[str, Any]:
    validate_contract(fixed_contract())
    validate_submission(submission)
    return {
        "schema": "bettor-arena/dual-agent-offload-workflow/contract-receipt/v1",
        "contract_state": "PASS",
        "workflow_state": "SUBMITTED",
        "canonical_task_writer": "loopx-ledger",
        "loopx_write_mode": "PROPOSAL_ONLY",
        "transport_state": "NOT_EXERCISED",
        "provider_state": "NOT_EXERCISED",
        "effect_state": "NOT_EXERCISED",
        "gate_state": "NOT_EXERCISED",
        "task_state": "NOT_EXERCISED",
        "user_outcome_state": "NOT_EXERCISED",
        "release_state": "NOT_EXERCISED",
        "evidence_ceiling": "DETERMINISTIC_WORKFLOW_CONTRACT_ONLY",
    }
