#!/usr/bin/env python3
"""LoopX Strategy + HITL v1.

Proposal-only strategy validation, subject-bound interrupt construction, signed Human
decision validation, resume-plan generation, and projection-only graph checkpoints.

Exit codes:
  0 checked operation passed
  2 checked contract/policy/state failure
 64 usage/input/output/tool failure
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
DECISIONS = {"RETRY_AFTER_FIX", "UPDATE_CONTRACT", "CANCEL_TASK", "SCOPED_EXCEPTION"}
HUMAN_ROLES = {"OWNER", "MAINTAINER", "SECURITY_APPROVER", "OPERATOR"}
FORBIDDEN = {
    "force_skip", "thought_stream", "chain_of_thought", "private_reasoning",
    "gate_verdict", "todo_status", "task_state", "promotion", "rollback",
}
LIFECYCLES = {
    "READY", "RUNNING", "VERIFYING", "RETRY_AVAILABLE", "HITL_PENDING",
    "COMPLETED", "COMPLETED_WITH_EXCEPTION", "FAILED", "CANCELLED",
}
COMMANDS = {
    "DISPATCH_TODO", "RETRY_TODO", "REQUEST_HUMAN", "HANDOFF",
    "COMPLETE_TODO", "FAIL_TASK", "CANCEL_TASK",
}
REASONS = {
    "QUOTA_EXHAUSTED", "GATE_FAILURE", "CAPABILITY_MISMATCH",
    "AUTHORIZATION_REQUIRED", "POLICY_BLOCK", "MANUAL_REVIEW",
}


class CheckedError(ValueError):
    pass


class FatalError(RuntimeError):
    pass


class StrictParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise FatalError(message)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FatalError(f"missing JSON input: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise FatalError(f"unreadable JSON input: {path}: {exc}") from exc


def write_new(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
    except FileExistsError as exc:
        raise FatalError(f"refusing to replace immutable output: {path}") from exc
    except OSError as exc:
        raise FatalError(f"cannot write output: {path}: {exc}") from exc


def obj(value: Any, required: set[str], where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CheckedError(f"{where} must be an object")
    if set(value) != required:
        missing = sorted(required - set(value))
        extra = sorted(set(value) - required)
        raise CheckedError(f"{where} field drift: missing={missing} extra={extra}")
    return value


def string(value: Any, where: str, *, minimum: int = 1, maximum: int = 4096) -> str:
    if not isinstance(value, str) or not minimum <= len(value) <= maximum:
        raise CheckedError(f"{where} must be a bounded string")
    return value


def parse_time(value: Any, where: str) -> dt.datetime:
    text = string(value, where, maximum=64)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        result = dt.datetime.fromisoformat(text)
    except ValueError as exc:
        raise CheckedError(f"{where} is not RFC3339") from exc
    if result.tzinfo is None:
        raise CheckedError(f"{where} must include timezone")
    return result.astimezone(dt.timezone.utc)


def scan(value: Any, where: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN:
                raise CheckedError(f"forbidden authority/private field {key!r} at {where}")
            scan(item, f"{where}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            scan(item, f"{where}[{index}]")


def subject(value: Any, where: str = "subject") -> dict[str, Any]:
    value = obj(value, {"repository", "commit", "tree", "task_id"}, where)
    if string(value["repository"], f"{where}.repository", maximum=200).count("/") != 1:
        raise CheckedError(f"{where}.repository must be owner/name")
    if not SHA_RE.fullmatch(string(value["commit"], f"{where}.commit", maximum=40)):
        raise CheckedError(f"{where}.commit must be a 40-character SHA")
    if not SHA_RE.fullmatch(string(value["tree"], f"{where}.tree", maximum=40)):
        raise CheckedError(f"{where}.tree must be a 40-character SHA")
    if not ID_RE.fullmatch(string(value["task_id"], f"{where}.task_id", maximum=128)):
        raise CheckedError(f"{where}.task_id invalid")
    return value


def artifact(value: Any, where: str) -> dict[str, Any]:
    value = obj(value, {"artifact_id", "digest", "media_type", "bytes"}, where)
    if not ID_RE.fullmatch(string(value["artifact_id"], f"{where}.artifact_id", maximum=128)):
        raise CheckedError(f"{where}.artifact_id invalid")
    if not DIGEST_RE.fullmatch(string(value["digest"], f"{where}.digest", maximum=71)):
        raise CheckedError(f"{where}.digest invalid")
    string(value["media_type"], f"{where}.media_type", maximum=128)
    if not isinstance(value["bytes"], int) or not 1 <= value["bytes"] <= 10_485_760:
        raise CheckedError(f"{where}.bytes invalid")
    return value


def snapshot(value: Any) -> dict[str, Any]:
    value = obj(
        value,
        {
            "schema_version", "subject", "state_revision", "ledger_head_digest",
            "state_digest", "lifecycle", "quota_state", "current_todo_id",
            "failed_gate_ids",
        },
        "snapshot",
    )
    if value["schema_version"] != "loopx/hitl-snapshot-fixture/v1":
        raise CheckedError("snapshot schema_version mismatch")
    subject(value["subject"])
    if not isinstance(value["state_revision"], int) or value["state_revision"] < 0:
        raise CheckedError("snapshot state_revision invalid")
    for field in ("ledger_head_digest", "state_digest"):
        if not DIGEST_RE.fullmatch(string(value[field], f"snapshot.{field}", maximum=71)):
            raise CheckedError(f"snapshot {field} invalid")
    if value["lifecycle"] not in LIFECYCLES:
        raise CheckedError("snapshot lifecycle invalid")
    if value["quota_state"] not in {"AVAILABLE", "EXHAUSTED"}:
        raise CheckedError("snapshot quota_state invalid")
    todo = value["current_todo_id"]
    if todo is not None and (not isinstance(todo, str) or not ID_RE.fullmatch(todo)):
        raise CheckedError("snapshot current_todo_id invalid")
    gates = value["failed_gate_ids"]
    if (
        not isinstance(gates, list)
        or len(gates) != len(set(gates))
        or any(not isinstance(item, str) or not ID_RE.fullmatch(item) for item in gates)
    ):
        raise CheckedError("snapshot failed_gate_ids invalid")
    scan(value)
    return value


def proposal(value: Any) -> dict[str, Any]:
    value = obj(
        value,
        {
            "schema_version", "proposal_id", "subject", "snapshot", "strategy",
            "proposed_command", "rationale_ref", "authority",
        },
        "strategy proposal",
    )
    if value["schema_version"] != "loopx/strategy-proposal/v1":
        raise CheckedError("strategy proposal schema_version mismatch")
    if not ID_RE.fullmatch(string(value["proposal_id"], "proposal_id", maximum=128)):
        raise CheckedError("proposal_id invalid")
    subject(value["subject"])
    snap = obj(
        value["snapshot"],
        {"state_revision", "ledger_head_digest", "state_digest", "lifecycle"},
        "proposal.snapshot",
    )
    if not isinstance(snap["state_revision"], int) or snap["state_revision"] < 0:
        raise CheckedError("proposal snapshot revision invalid")
    for field in ("ledger_head_digest", "state_digest"):
        if not DIGEST_RE.fullmatch(string(snap[field], f"proposal.snapshot.{field}", maximum=71)):
            raise CheckedError(f"proposal snapshot {field} invalid")
    if snap["lifecycle"] not in LIFECYCLES:
        raise CheckedError("proposal snapshot lifecycle invalid")
    strategy = obj(
        value["strategy"], {"strategy_id", "version", "digest", "implementation"},
        "proposal.strategy",
    )
    if not ID_RE.fullmatch(string(strategy["strategy_id"], "strategy_id", maximum=128)):
        raise CheckedError("strategy_id invalid")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", string(strategy["version"], "strategy.version", maximum=32)):
        raise CheckedError("strategy.version invalid")
    if not DIGEST_RE.fullmatch(string(strategy["digest"], "strategy.digest", maximum=71)):
        raise CheckedError("strategy.digest invalid")
    if strategy["implementation"] not in {"DETERMINISTIC_POLICY", "LANGGRAPH_ADAPTER", "HUMAN_PROPOSAL"}:
        raise CheckedError("strategy implementation invalid")
    command = obj(
        value["proposed_command"],
        {"command_id", "kind", "expected_state_revision", "todo_id", "reason_ref"},
        "proposed_command",
    )
    if not ID_RE.fullmatch(string(command["command_id"], "command_id", maximum=128)):
        raise CheckedError("command_id invalid")
    if command["kind"] not in COMMANDS:
        raise CheckedError("command kind invalid")
    if not isinstance(command["expected_state_revision"], int) or command["expected_state_revision"] < 0:
        raise CheckedError("command expected_state_revision invalid")
    artifact(command["reason_ref"], "proposed_command.reason_ref")
    artifact(value["rationale_ref"], "rationale_ref")
    authority = obj(
        value["authority"],
        {
            "proposal_only", "writes_loopx_state", "writes_gate_verdict",
            "performs_human_admit", "promotes_release",
        },
        "proposal.authority",
    )
    if authority != {
        "proposal_only": True,
        "writes_loopx_state": False,
        "writes_gate_verdict": False,
        "performs_human_admit": False,
        "promotes_release": False,
    }:
        raise CheckedError("strategy proposal claims forbidden authority")
    scan(value)
    return value


def proposal_for_snapshot(snap_value: Any, prop_value: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    snap = snapshot(snap_value)
    prop = proposal(prop_value)
    if prop["subject"] != snap["subject"]:
        raise CheckedError("proposal subject mismatch")
    for field in ("state_revision", "ledger_head_digest", "state_digest", "lifecycle"):
        if prop["snapshot"][field] != snap[field]:
            raise CheckedError(f"proposal snapshot {field} stale")
    command = prop["proposed_command"]
    if command["expected_state_revision"] != snap["state_revision"]:
        raise CheckedError("proposal command revision stale")
    allowed = {
        "READY": {"DISPATCH_TODO", "REQUEST_HUMAN", "CANCEL_TASK"},
        "RUNNING": {"REQUEST_HUMAN", "HANDOFF", "FAIL_TASK", "CANCEL_TASK"},
        "VERIFYING": {"RETRY_TODO", "REQUEST_HUMAN", "COMPLETE_TODO", "FAIL_TASK", "CANCEL_TASK"},
        "RETRY_AVAILABLE": {"RETRY_TODO", "REQUEST_HUMAN", "HANDOFF", "FAIL_TASK", "CANCEL_TASK"},
        "HITL_PENDING": {"REQUEST_HUMAN", "CANCEL_TASK"},
        "COMPLETED": set(), "COMPLETED_WITH_EXCEPTION": set(),
        "FAILED": set(), "CANCELLED": set(),
    }
    if command["kind"] not in allowed[snap["lifecycle"]]:
        raise CheckedError("command invalid for lifecycle")
    if snap["quota_state"] == "EXHAUSTED" and command["kind"] not in {"REQUEST_HUMAN", "FAIL_TASK", "CANCEL_TASK"}:
        raise CheckedError("Quota exhaustion requires HITL, fail, or cancel")
    if snap["failed_gate_ids"] and command["kind"] == "COMPLETE_TODO":
        raise CheckedError("cannot complete while Gates remain failed")
    return snap, prop


def interrupt_request(value: Any) -> dict[str, Any]:
    value = obj(
        value,
        {
            "schema_version", "request_id", "subject", "expected_state_revision",
            "reason", "todo_id", "gate_ids", "evidence_refs", "allowed_decisions",
            "requested_by",
        },
        "interrupt request",
    )
    if value["schema_version"] != "loopx/interrupt-request/v1":
        raise CheckedError("interrupt request schema_version mismatch")
    if not ID_RE.fullmatch(string(value["request_id"], "interrupt request_id", maximum=128)):
        raise CheckedError("interrupt request_id invalid")
    subject(value["subject"])
    if not isinstance(value["expected_state_revision"], int) or value["expected_state_revision"] < 0:
        raise CheckedError("interrupt revision invalid")
    if value["reason"] not in REASONS:
        raise CheckedError("interrupt reason invalid")
    for field in ("gate_ids", "allowed_decisions"):
        items = value[field]
        if not isinstance(items, list) or len(items) != len(set(items)):
            raise CheckedError(f"interrupt {field} invalid")
    if not value["allowed_decisions"] or any(item not in DECISIONS for item in value["allowed_decisions"]):
        raise CheckedError("interrupt allowed_decisions invalid")
    refs = value["evidence_refs"]
    if not isinstance(refs, list) or not refs or len(refs) > 64:
        raise CheckedError("interrupt evidence_refs invalid")
    for index, ref in enumerate(refs):
        artifact(ref, f"evidence_refs[{index}]")
    actor = obj(value["requested_by"], {"actor_id", "class"}, "requested_by")
    if actor["class"] not in {"LOOPX", "STRATEGY", "GATE_ENGINE", "HUMAN_OPERATOR"}:
        raise CheckedError("requested_by.class invalid")
    scan(value)
    return value


def make_interrupt(snap_value: Any, request_value: Any, *, at: dt.datetime) -> dict[str, Any]:
    snap = snapshot(snap_value)
    request = interrupt_request(request_value)
    if request["subject"] != snap["subject"]:
        raise CheckedError("interrupt subject mismatch")
    if request["expected_state_revision"] != snap["state_revision"]:
        raise CheckedError("interrupt revision stale")
    if snap["lifecycle"] not in {"RUNNING", "VERIFYING", "RETRY_AVAILABLE", "HITL_PENDING"}:
        raise CheckedError("invalid lifecycle for interrupt")
    if request["reason"] == "QUOTA_EXHAUSTED" and snap["quota_state"] != "EXHAUSTED":
        raise CheckedError("QUOTA_EXHAUSTED requires exhausted Quota")
    if request["reason"] == "GATE_FAILURE":
        if not snap["failed_gate_ids"] or not set(snap["failed_gate_ids"]).issubset(set(request["gate_ids"])):
            raise CheckedError("GATE_FAILURE interrupt omits failed Gates")
    if request["todo_id"] != snap["current_todo_id"]:
        raise CheckedError("interrupt Todo mismatch")
    result = {
        "schema_version": "loopx/interrupt/v1",
        "interrupt_id": request["request_id"] + "-interrupt",
        "request_digest": digest(request),
        "subject": snap["subject"],
        "state_revision": snap["state_revision"],
        "ledger_head_digest": snap["ledger_head_digest"],
        "state_digest": snap["state_digest"],
        "reason": request["reason"],
        "todo_id": request["todo_id"],
        "gate_ids": request["gate_ids"],
        "evidence_refs": request["evidence_refs"],
        "allowed_decisions": request["allowed_decisions"],
        "created_at": at.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "canonical_authority": False,
    }
    return interrupt(result)


def interrupt(value: Any) -> dict[str, Any]:
    value = obj(
        value,
        {
            "schema_version", "interrupt_id", "request_digest", "subject",
            "state_revision", "ledger_head_digest", "state_digest", "reason",
            "todo_id", "gate_ids", "evidence_refs", "allowed_decisions",
            "created_at", "canonical_authority",
        },
        "interrupt",
    )
    if value["schema_version"] != "loopx/interrupt/v1":
        raise CheckedError("interrupt schema_version mismatch")
    if not ID_RE.fullmatch(string(value["interrupt_id"], "interrupt_id", maximum=128)):
        raise CheckedError("interrupt_id invalid")
    if not DIGEST_RE.fullmatch(string(value["request_digest"], "request_digest", maximum=71)):
        raise CheckedError("interrupt request_digest invalid")
    subject(value["subject"])
    if not isinstance(value["state_revision"], int) or value["state_revision"] < 0:
        raise CheckedError("interrupt revision invalid")
    for field in ("ledger_head_digest", "state_digest"):
        if not DIGEST_RE.fullmatch(string(value[field], field, maximum=71)):
            raise CheckedError(f"interrupt {field} invalid")
    if value["reason"] not in REASONS:
        raise CheckedError("interrupt reason invalid")
    if not isinstance(value["allowed_decisions"], list) or not value["allowed_decisions"] or any(item not in DECISIONS for item in value["allowed_decisions"]):
        raise CheckedError("interrupt allowed_decisions invalid")
    for index, ref in enumerate(value["evidence_refs"]):
        artifact(ref, f"interrupt.evidence_refs[{index}]")
    parse_time(value["created_at"], "interrupt.created_at")
    if value["canonical_authority"] is not False:
        raise CheckedError("interrupt cannot be canonical authority")
    scan(value)
    return value


def signing_payload(value: dict[str, Any]) -> dict[str, Any]:
    return {
        key: item for key, item in value.items()
        if key not in {"decision_digest", "signature_ref", "signature_verification"}
    }


def decision(value: Any) -> dict[str, Any]:
    value = obj(
        value,
        {
            "schema_version", "decision_id", "subject", "interrupt_id",
            "expected_state_revision", "decision", "scope", "reason_ref",
            "signer", "signed_at", "expires_at", "decision_digest",
            "signature_ref", "signature_verification", "revalidation",
            "exception", "authority",
        },
        "human decision",
    )
    if value["schema_version"] != "loopx/human-decision/v1":
        raise CheckedError("human decision schema_version mismatch")
    if not ID_RE.fullmatch(string(value["decision_id"], "decision_id", maximum=128)):
        raise CheckedError("decision_id invalid")
    subject(value["subject"])
    if not ID_RE.fullmatch(string(value["interrupt_id"], "decision interrupt_id", maximum=128)):
        raise CheckedError("decision interrupt_id invalid")
    if not isinstance(value["expected_state_revision"], int) or value["expected_state_revision"] < 0:
        raise CheckedError("decision revision invalid")
    if value["decision"] not in DECISIONS:
        raise CheckedError("decision kind invalid")
    scope = obj(value["scope"], {"todo_ids", "gate_ids", "command_ids"}, "decision.scope")
    for field in ("todo_ids", "gate_ids", "command_ids"):
        items = scope[field]
        if (
            not isinstance(items, list)
            or len(items) != len(set(items))
            or any(not isinstance(item, str) or not ID_RE.fullmatch(item) for item in items)
        ):
            raise CheckedError(f"decision scope {field} invalid")
    artifact(value["reason_ref"], "decision.reason_ref")
    signer = obj(value["signer"], {"principal_id", "role", "key_id"}, "decision.signer")
    if signer["role"] not in HUMAN_ROLES:
        raise CheckedError("decision signer role invalid")
    string(signer["principal_id"], "signer principal", maximum=128)
    string(signer["key_id"], "signer key_id", minimum=3, maximum=256)
    signed = parse_time(value["signed_at"], "decision.signed_at")
    expires = parse_time(value["expires_at"], "decision.expires_at")
    if expires <= signed:
        raise CheckedError("decision expiry must follow signature")
    if value["decision_digest"] != digest(signing_payload(value)):
        raise CheckedError("decision_digest does not bind decision payload")
    artifact(value["signature_ref"], "decision.signature_ref")
    verification = obj(
        value["signature_verification"],
        {"state", "verifier_digest", "artifact_ref"},
        "signature_verification",
    )
    if verification["state"] != "PASS":
        raise CheckedError("decision signature not independently verified")
    if not DIGEST_RE.fullmatch(string(verification["verifier_digest"], "verifier_digest", maximum=71)):
        raise CheckedError("verifier_digest invalid")
    artifact(verification["artifact_ref"], "signature verification artifact")
    revalidation = obj(
        value["revalidation"], {"required", "before_resume", "gate_ids"},
        "decision.revalidation",
    )
    if not isinstance(revalidation["gate_ids"], list) or len(revalidation["gate_ids"]) != len(set(revalidation["gate_ids"])):
        raise CheckedError("revalidation gate_ids invalid")
    authority = obj(
        value["authority"],
        {
            "human_decision", "writes_loopx_state", "writes_gate_verdict",
            "promotes_release", "performs_rollback",
        },
        "decision.authority",
    )
    if authority != {
        "human_decision": True,
        "writes_loopx_state": False,
        "writes_gate_verdict": False,
        "promotes_release": False,
        "performs_rollback": False,
    }:
        raise CheckedError("decision claims forbidden authority")
    if value["decision"] in {"RETRY_AFTER_FIX", "UPDATE_CONTRACT", "SCOPED_EXCEPTION"}:
        if revalidation["required"] is not True or revalidation["before_resume"] is not True:
            raise CheckedError("resuming decision requires revalidation before resume")
    if value["decision"] == "SCOPED_EXCEPTION":
        if not scope["todo_ids"] or not scope["gate_ids"]:
            raise CheckedError("scoped exception requires Todo and Gate scope")
        exception = value["exception"]
        if not isinstance(exception, dict):
            raise CheckedError("scoped exception details missing")
        exception = obj(exception, {"exception_id", "limitations", "consequence"}, "exception")
        if exception["consequence"] != "COMPLETED_WITH_EXCEPTION":
            raise CheckedError("exception consequence must remain visible")
        if not isinstance(exception["limitations"], list) or not exception["limitations"]:
            raise CheckedError("exception limitations missing")
        if not set(scope["gate_ids"]).issubset(set(revalidation["gate_ids"])):
            raise CheckedError("exception Gates must be revalidated")
    elif value["exception"] is not None:
        raise CheckedError("non-exception decision carried exception details")
    scan(value)
    return value


def decision_for_interrupt(decision_value: Any, interrupt_value: Any, *, at: dt.datetime) -> tuple[dict[str, Any], dict[str, Any]]:
    dec = decision(decision_value)
    intr = interrupt(interrupt_value)
    if dec["subject"] != intr["subject"]:
        raise CheckedError("decision subject mismatch")
    if dec["interrupt_id"] != intr["interrupt_id"]:
        raise CheckedError("decision interrupt mismatch")
    if dec["expected_state_revision"] != intr["state_revision"]:
        raise CheckedError("decision revision stale")
    if dec["decision"] not in intr["allowed_decisions"]:
        raise CheckedError("decision not allowed by interrupt")
    if at > parse_time(dec["expires_at"], "decision.expires_at"):
        raise CheckedError("human decision expired")
    if intr["todo_id"] is not None and dec["decision"] != "CANCEL_TASK" and intr["todo_id"] not in dec["scope"]["todo_ids"]:
        raise CheckedError("decision scope omits interrupted Todo")
    if intr["gate_ids"] and dec["decision"] in {"RETRY_AFTER_FIX", "UPDATE_CONTRACT", "SCOPED_EXCEPTION"}:
        if not set(intr["gate_ids"]).issubset(set(dec["revalidation"]["gate_ids"])):
            raise CheckedError("decision omits interrupted Gates from revalidation")
    return dec, intr


def resume_plan(snap_value: Any, intr_value: Any, dec_value: Any, *, at: dt.datetime) -> dict[str, Any]:
    snap = snapshot(snap_value)
    dec, intr = decision_for_interrupt(dec_value, intr_value, at=at)
    if intr["subject"] != snap["subject"]:
        raise CheckedError("interrupt/snapshot subject mismatch")
    if snap["lifecycle"] != "HITL_PENDING":
        raise CheckedError("resume requires HITL_PENDING")
    for field in ("state_revision", "ledger_head_digest", "state_digest"):
        if intr[field] != snap[field]:
            raise CheckedError(f"interrupt {field} stale")
    actions = {
        "RETRY_AFTER_FIX": "RETRY_TODO",
        "UPDATE_CONTRACT": "UPDATE_CONTRACT",
        "CANCEL_TASK": "CANCEL_TASK",
        "SCOPED_EXCEPTION": "APPLY_SCOPED_EXCEPTION",
    }
    decision_payload = {
        "decision_id": dec["decision_id"],
        "decision_digest": dec["decision_digest"],
        "interrupt_id": intr["interrupt_id"],
        "subject": dec["subject"],
    }
    transition_payload = {
        "next_action": actions[dec["decision"]],
        "expected_state_revision": dec["expected_state_revision"],
        "revalidation": dec["revalidation"],
    }
    return {
        "schema_version": "loopx/hitl-resume-plan/v1",
        "resume_plan_id": dec["decision_id"] + "-resume",
        "subject": dec["subject"],
        "interrupt_id": intr["interrupt_id"],
        "decision_id": dec["decision_id"],
        "decision_digest": dec["decision_digest"],
        "expected_state_revision": dec["expected_state_revision"],
        "next_action": actions[dec["decision"]],
        "revalidation": dec["revalidation"],
        "ledger_event_proposals": [
            {
                "type": "HUMAN_DECISION_RECORDED",
                "authority": "PROPOSAL_ONLY",
                "payload_digest": digest(decision_payload),
            },
            {
                "type": "STATE_TRANSITION_REQUESTED",
                "authority": "PROPOSAL_ONLY",
                "payload_digest": digest(transition_payload),
            },
        ],
        "canonical_authority": False,
    }


def checkpoint(snap_value: Any, intr_value: Any, *, thread_id: str) -> dict[str, Any]:
    snap = snapshot(snap_value)
    intr = interrupt(intr_value)
    if intr["subject"] != snap["subject"]:
        raise CheckedError("checkpoint subject mismatch")
    for field in ("state_revision", "ledger_head_digest", "state_digest"):
        if intr[field] != snap[field]:
            raise CheckedError(f"checkpoint {field} mismatch")
    if snap["lifecycle"] != "HITL_PENDING":
        raise CheckedError("checkpoint requires HITL_PENDING")
    if not isinstance(thread_id, str) or not 3 <= len(thread_id) <= 256:
        raise CheckedError("thread_id invalid")
    return {
        "schema_version": "loopx/graph-checkpoint-projection/v1",
        "graph_thread_id": thread_id,
        "subject": snap["subject"],
        "state_revision": snap["state_revision"],
        "ledger_head_digest": snap["ledger_head_digest"],
        "state_digest": snap["state_digest"],
        "interrupt_id": intr["interrupt_id"],
        "interrupt_digest": digest(intr),
        "rebuildable": True,
        "canonical_authority": False,
        "resume_requires_checked_human_decision": True,
    }


def reject_checkpoint_as_state(value: dict[str, Any]) -> None:
    if value.get("canonical_authority") is not False:
        raise CheckedError("graph checkpoint cannot become canonical state")
    if value.get("resume_requires_checked_human_decision") is not True:
        raise CheckedError("graph checkpoint cannot bypass Human decision")


def fixture_bundle() -> dict[str, Any]:
    def art(name: str, char: str) -> dict[str, Any]:
        return {
            "artifact_id": name,
            "digest": "sha256:" + char * 64,
            "media_type": "application/json",
            "bytes": 128,
        }

    subj = {
        "repository": "ed3c/bettor-arena",
        "commit": "1" * 40,
        "tree": "2" * 40,
        "task_id": "fixture-hitl-task-v1",
    }
    snap = {
        "schema_version": "loopx/hitl-snapshot-fixture/v1",
        "subject": subj,
        "state_revision": 7,
        "ledger_head_digest": "sha256:" + "3" * 64,
        "state_digest": "sha256:" + "4" * 64,
        "lifecycle": "HITL_PENDING",
        "quota_state": "EXHAUSTED",
        "current_todo_id": "todo-compile",
        "failed_gate_ids": ["gate-tests", "gate-lsp"],
    }
    prop_snap = copy.deepcopy(snap)
    prop_snap["lifecycle"] = "VERIFYING"
    prop_snap["quota_state"] = "AVAILABLE"
    prop = {
        "schema_version": "loopx/strategy-proposal/v1",
        "proposal_id": "strategy-proposal-human",
        "subject": subj,
        "snapshot": {
            "state_revision": 7,
            "ledger_head_digest": snap["ledger_head_digest"],
            "state_digest": snap["state_digest"],
            "lifecycle": "VERIFYING",
        },
        "strategy": {
            "strategy_id": "deterministic-fallback",
            "version": "1.0.0",
            "digest": "sha256:" + "5" * 64,
            "implementation": "DETERMINISTIC_POLICY",
        },
        "proposed_command": {
            "command_id": "command-request-human",
            "kind": "REQUEST_HUMAN",
            "expected_state_revision": 7,
            "todo_id": "todo-compile",
            "reason_ref": art("reason-quota", "6"),
        },
        "rationale_ref": art("rationale-strategy", "7"),
        "authority": {
            "proposal_only": True,
            "writes_loopx_state": False,
            "writes_gate_verdict": False,
            "performs_human_admit": False,
            "promotes_release": False,
        },
    }
    req = {
        "schema_version": "loopx/interrupt-request/v1",
        "request_id": "interrupt-quota-exhausted",
        "subject": subj,
        "expected_state_revision": 7,
        "reason": "QUOTA_EXHAUSTED",
        "todo_id": "todo-compile",
        "gate_ids": ["gate-tests", "gate-lsp"],
        "evidence_refs": [art("evidence-quota", "8")],
        "allowed_decisions": [
            "RETRY_AFTER_FIX", "UPDATE_CONTRACT", "CANCEL_TASK", "SCOPED_EXCEPTION"
        ],
        "requested_by": {"actor_id": "loopx-reducer", "class": "LOOPX"},
    }
    intr = make_interrupt(
        snap, req, at=dt.datetime(2026, 8, 14, 2, 0, tzinfo=dt.timezone.utc)
    )

    def make_decision(kind: str, decision_id: str) -> dict[str, Any]:
        scope = {
            "todo_ids": ["todo-compile"],
            "gate_ids": ["gate-tests", "gate-lsp"],
            "command_ids": [],
        }
        revalidation = {
            "required": True,
            "before_resume": True,
            "gate_ids": ["gate-tests", "gate-lsp"],
        }
        exception = None
        if kind == "CANCEL_TASK":
            scope["gate_ids"] = []
            revalidation = {"required": False, "before_resume": False, "gate_ids": []}
        if kind == "SCOPED_EXCEPTION":
            exception = {
                "exception_id": "exception-gate-lsp",
                "limitations": ["Only the named Todo and Gates are covered."],
                "consequence": "COMPLETED_WITH_EXCEPTION",
            }
        result = {
            "schema_version": "loopx/human-decision/v1",
            "decision_id": decision_id,
            "subject": subj,
            "interrupt_id": intr["interrupt_id"],
            "expected_state_revision": 7,
            "decision": kind,
            "scope": scope,
            "reason_ref": art("decision-reason", "9"),
            "signer": {
                "principal_id": "ed3c",
                "role": "OWNER",
                "key_id": "fixture-ed25519-key",
            },
            "signed_at": "2026-08-14T02:01:00Z",
            "expires_at": "2026-08-15T02:00:00Z",
            "decision_digest": "",
            "signature_ref": art("signature", "a"),
            "signature_verification": {
                "state": "PASS",
                "verifier_digest": "sha256:" + "b" * 64,
                "artifact_ref": art("signature-verification", "c"),
            },
            "revalidation": revalidation,
            "exception": exception,
            "authority": {
                "human_decision": True,
                "writes_loopx_state": False,
                "writes_gate_verdict": False,
                "promotes_release": False,
                "performs_rollback": False,
            },
        }
        result["decision_digest"] = digest(signing_payload(result))
        return result

    return {
        "snapshot": snap,
        "proposal_snapshot": prop_snap,
        "proposal": prop,
        "interrupt_request": req,
        "interrupt": intr,
        "retry": make_decision("RETRY_AFTER_FIX", "decision-retry-after-fix"),
        "cancel": make_decision("CANCEL_TASK", "decision-cancel-task"),
        "exception": make_decision("SCOPED_EXCEPTION", "decision-scoped-exception"),
    }


def expect_red(call: Callable[[], Any], name: str) -> None:
    try:
        call()
    except CheckedError:
        return
    raise CheckedError(f"negative control accepted: {name}")


def rehash(dec: dict[str, Any]) -> dict[str, Any]:
    dec["decision_digest"] = digest(signing_payload(dec))
    return dec


def check_contracts(module: Path) -> None:
    manifest = load(module / "contracts" / "manifest.json")
    required = {
        "schema_version", "files", "authority_law",
        "human_decisions", "forbidden_shortcuts",
    }
    obj(manifest, required, "manifest")
    if manifest["schema_version"] != "loopx/strategy-hitl-manifest/v1":
        raise CheckedError("manifest schema_version mismatch")
    expected = {
        "strategy-proposal.schema.json", "interrupt-request.schema.json",
        "interrupt.schema.json", "human-decision.schema.json",
        "resume-plan.schema.json", "checkpoint-projection.schema.json",
    }
    if set(manifest["files"]) != expected or len(manifest["files"]) != len(set(manifest["files"])):
        raise CheckedError("manifest file set drifted")
    if manifest["authority_law"] != [
        "STRATEGY_PROPOSES", "WORKER_EXECUTES", "GATES_OBSERVE",
        "LOOPX_COMMITS", "HUMAN_ADMITS",
    ]:
        raise CheckedError("authority law drifted")
    for name in manifest["files"]:
        schema = load(module / "contracts" / name)
        if (
            not isinstance(schema, dict)
            or schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
            or schema.get("additionalProperties") is not False
        ):
            raise CheckedError(f"{name}: schema must fail closed")
    bundle = fixture_bundle()
    snapshot(bundle["snapshot"])
    snapshot(bundle["proposal_snapshot"])
    proposal(bundle["proposal"])
    interrupt_request(bundle["interrupt_request"])
    interrupt(bundle["interrupt"])
    decision(bundle["retry"])
    decision(bundle["cancel"])
    decision(bundle["exception"])


def selftest() -> None:
    bundle = fixture_bundle()
    snap = bundle["snapshot"]
    prop_snap = bundle["proposal_snapshot"]
    prop = bundle["proposal"]
    req = bundle["interrupt_request"]
    intr = bundle["interrupt"]
    retry = bundle["retry"]
    cancel = bundle["cancel"]
    exception_decision = bundle["exception"]
    now = dt.datetime(2026, 8, 14, 3, 0, tzinfo=dt.timezone.utc)

    proposal_for_snapshot(prop_snap, prop)
    if make_interrupt(snap, req, at=dt.datetime(2026, 8, 14, 2, 0, tzinfo=dt.timezone.utc)) != intr:
        raise CheckedError("interrupt construction is not deterministic")
    for value in (retry, cancel, exception_decision):
        decision_for_interrupt(value, intr, at=now)
    if resume_plan(snap, intr, retry, at=now)["next_action"] != "RETRY_TODO":
        raise CheckedError("retry mapping drifted")
    if resume_plan(snap, intr, cancel, at=now)["next_action"] != "CANCEL_TASK":
        raise CheckedError("cancel mapping drifted")
    if resume_plan(snap, intr, exception_decision, at=now)["next_action"] != "APPLY_SCOPED_EXCEPTION":
        raise CheckedError("exception mapping drifted")
    cp = checkpoint(snap, intr, thread_id="fixture:thread:1")
    reject_checkpoint_as_state(cp)

    value = copy.deepcopy(retry)
    value["force_skip"] = True
    expect_red(lambda: decision(value), "force-skip")

    value = copy.deepcopy(prop)
    value["snapshot"]["state_revision"] = 6
    value["proposed_command"]["expected_state_revision"] = 6
    expect_red(lambda: proposal_for_snapshot(prop_snap, value), "stale-strategy")

    value = copy.deepcopy(prop)
    value["authority"]["writes_loopx_state"] = True
    expect_red(lambda: proposal_for_snapshot(prop_snap, value), "strategy-state-write")

    value = copy.deepcopy(prop)
    value["proposed_command"]["kind"] = "COMPLETE_TODO"
    expect_red(lambda: proposal_for_snapshot(prop_snap, value), "complete-with-failed-gates")

    exhausted = copy.deepcopy(prop_snap)
    exhausted["quota_state"] = "EXHAUSTED"
    value = copy.deepcopy(prop)
    value["proposed_command"]["kind"] = "RETRY_TODO"
    expect_red(lambda: proposal_for_snapshot(exhausted, value), "retry-after-quota")

    value = copy.deepcopy(req)
    value["expected_state_revision"] = 6
    expect_red(lambda: make_interrupt(snap, value, at=now), "stale-interrupt")

    value = copy.deepcopy(req)
    value["subject"]["tree"] = "f" * 40
    expect_red(lambda: make_interrupt(snap, value, at=now), "interrupt-subject")

    value = copy.deepcopy(req)
    value["reason"] = "GATE_FAILURE"
    value["gate_ids"] = ["gate-tests"]
    expect_red(lambda: make_interrupt(snap, value, at=now), "interrupt-gate-omission")

    value = copy.deepcopy(retry)
    value["signature_verification"]["state"] = "NOT_RUN"
    expect_red(lambda: decision(value), "unsigned-decision")

    value = copy.deepcopy(retry)
    value["reason_ref"]["digest"] = "sha256:" + "d" * 64
    expect_red(lambda: decision(value), "decision-digest-drift")

    value = copy.deepcopy(retry)
    value["expires_at"] = "2026-08-14T02:30:00Z"
    rehash(value)
    expect_red(lambda: decision_for_interrupt(value, intr, at=now), "expired-decision")

    value = copy.deepcopy(retry)
    value["expected_state_revision"] = 6
    rehash(value)
    expect_red(lambda: decision_for_interrupt(value, intr, at=now), "stale-decision")

    value = copy.deepcopy(retry)
    value["subject"]["commit"] = "e" * 40
    rehash(value)
    expect_red(lambda: decision_for_interrupt(value, intr, at=now), "decision-subject")

    value = copy.deepcopy(retry)
    value["revalidation"]["before_resume"] = False
    rehash(value)
    expect_red(lambda: decision(value), "bypass-revalidation")

    value = copy.deepcopy(exception_decision)
    value["scope"]["gate_ids"] = []
    value["revalidation"]["gate_ids"] = []
    rehash(value)
    expect_red(lambda: decision(value), "empty-exception-scope")

    value = copy.deepcopy(retry)
    value["thought_stream"] = "private"
    expect_red(lambda: decision(value), "private-thought-stream")

    value = copy.deepcopy(retry)
    value["authority"]["promotes_release"] = True
    expect_red(lambda: decision(value), "decision-promotion")

    value = copy.deepcopy(retry)
    value["signer"]["role"] = "WORKER"
    rehash(value)
    expect_red(lambda: decision(value), "worker-human-decision")

    value = copy.deepcopy(retry)
    value["gate_verdict"] = "PASS"
    expect_red(lambda: decision(value), "provider-gate-verdict")

    value = copy.deepcopy(cp)
    value["canonical_authority"] = True
    expect_red(lambda: reject_checkpoint_as_state(value), "checkpoint-authority")

    newer = copy.deepcopy(snap)
    newer["state_revision"] = 8
    newer["ledger_head_digest"] = "sha256:" + "e" * 64
    newer["state_digest"] = "sha256:" + "f" * 64
    expect_red(lambda: resume_plan(newer, intr, retry, at=now), "interrupt-replay")

    with tempfile.TemporaryDirectory(prefix="loopx-hitl-collision-") as temp:
        path = Path(temp) / "resume-plan.json"
        plan = resume_plan(snap, intr, retry, at=now)
        write_new(path, plan)
        try:
            write_new(path, plan)
        except FatalError:
            pass
        else:
            raise CheckedError("resume output collision accepted")


def write_bundle(temp: Path) -> dict[str, Path]:
    bundle = fixture_bundle()
    paths: dict[str, Path] = {}
    for name, value in bundle.items():
        path = temp / f"{name}.json"
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        paths[name] = path
    hollow = copy.deepcopy(bundle["retry"])
    hollow["force_skip"] = True
    path = temp / "force-skip.json"
    path.write_text(json.dumps(hollow, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    paths["force_skip"] = path
    return paths


def control(script: Path) -> None:
    def run(argv: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(argv, text=True, capture_output=True, shell=False, check=False)

    with tempfile.TemporaryDirectory(prefix="loopx-hitl-control-") as temp_name:
        temp = Path(temp_name)
        paths = write_bundle(temp)
        cases = {
            "proposal": run([sys.executable, str(script), "validate-proposal", "--snapshot", str(paths["proposal_snapshot"]), "--proposal", str(paths["proposal"])]),
            "interrupt": run([sys.executable, str(script), "interrupt", "--snapshot", str(paths["snapshot"]), "--request", str(paths["interrupt_request"]), "--at", "2026-08-14T02:00:00Z", "--output", str(temp / "interrupt-out")]),
            "decision": run([sys.executable, str(script), "decide", "--interrupt", str(paths["interrupt"]), "--decision", str(paths["retry"]), "--at", "2026-08-14T03:00:00Z"]),
            "resume": run([sys.executable, str(script), "resume", "--snapshot", str(paths["snapshot"]), "--interrupt", str(paths["interrupt"]), "--decision", str(paths["retry"]), "--at", "2026-08-14T03:00:00Z", "--output", str(temp / "resume-out"), "--json"]),
            "checkpoint": run([sys.executable, str(script), "checkpoint", "--snapshot", str(paths["snapshot"]), "--interrupt", str(paths["interrupt"]), "--thread-id", "fixture:thread:1", "--output", str(temp / "checkpoint-out"), "--json"]),
            "force_skip": run([sys.executable, str(script), "decide", "--interrupt", str(paths["interrupt"]), "--decision", str(paths["force_skip"]), "--at", "2026-08-14T03:00:00Z"]),
            "missing": run([sys.executable, str(script), "decide", "--interrupt", str(temp / "missing.json"), "--decision", str(paths["retry"]), "--at", "2026-08-14T03:00:00Z"]),
            "invocation": run([sys.executable, str(script)]),
        }
        expected = {
            "proposal": 0, "interrupt": 0, "decision": 0, "resume": 0,
            "checkpoint": 0, "force_skip": 2, "missing": 64, "invocation": 64,
        }
        failures = [
            f"{name}: expected {expected[name]}, got {result.returncode}"
            for name, result in cases.items()
            if result.returncode != expected[name]
        ]
        if not failures:
            plan = json.loads(cases["resume"].stdout)
            cp = json.loads(cases["checkpoint"].stdout)
            if plan["next_action"] != "RETRY_TODO" or plan["canonical_authority"] is not False:
                failures.append("resume plan drifted")
            if cp["canonical_authority"] is not False or cp["resume_requires_checked_human_decision"] is not True:
                failures.append("checkpoint authority drifted")
        if failures:
            raise CheckedError("; ".join(failures))


def resolve_at(text: str | None) -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc) if text is None else parse_time(text, "--at")


def module_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def cmd_check(_: argparse.Namespace) -> int:
    check_contracts(module_dir())
    print("loopx-strategy-hitl contracts PASS: 6 schemas")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    snap, prop = proposal_for_snapshot(load(args.snapshot), load(args.proposal))
    print(f"loopx-strategy-hitl PROPOSAL_VALID proposal={prop['proposal_id']} revision={snap['state_revision']} command={prop['proposed_command']['kind']}")
    return 0


def cmd_interrupt(args: argparse.Namespace) -> int:
    result = make_interrupt(load(args.snapshot), load(args.request), at=resolve_at(args.at))
    if args.output.exists():
        raise FatalError(f"output path already exists: {args.output}")
    args.output.mkdir(parents=True)
    write_new(args.output / "interrupt.json", result)
    print(f"loopx-strategy-hitl INTERRUPT_CREATED id={result['interrupt_id']} revision={result['state_revision']}")
    return 0


def cmd_decide(args: argparse.Namespace) -> int:
    dec, _ = decision_for_interrupt(load(args.decision), load(args.interrupt), at=resolve_at(args.at))
    print(f"loopx-strategy-hitl DECISION_VALID id={dec['decision_id']} kind={dec['decision']}")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    result = resume_plan(load(args.snapshot), load(args.interrupt), load(args.decision), at=resolve_at(args.at))
    if args.output.exists():
        raise FatalError(f"output path already exists: {args.output}")
    args.output.mkdir(parents=True)
    write_new(args.output / "resume-plan.json", result)
    print(json.dumps(result, sort_keys=True) if args.json else f"loopx-strategy-hitl RESUME_PLAN id={result['resume_plan_id']} action={result['next_action']}")
    return 0


def cmd_checkpoint(args: argparse.Namespace) -> int:
    result = checkpoint(load(args.snapshot), load(args.interrupt), thread_id=args.thread_id)
    if args.output.exists():
        raise FatalError(f"output path already exists: {args.output}")
    args.output.mkdir(parents=True)
    write_new(args.output / "checkpoint.json", result)
    print(json.dumps(result, sort_keys=True) if args.json else f"loopx-strategy-hitl CHECKPOINT_PROJECTION thread={result['graph_thread_id']} authority=false")
    return 0


def cmd_selftest(_: argparse.Namespace) -> int:
    check_contracts(module_dir())
    selftest()
    print("loopx-strategy-hitl selftest PASS: positive and planted mutations")
    return 0


def cmd_control(_: argparse.Namespace) -> int:
    control(Path(__file__).resolve())
    print("loopx-strategy-hitl control PASS: proposal/interrupt/decision/resume/checkpoint and 2/64 controls")
    return 0


def parser() -> argparse.ArgumentParser:
    p = StrictParser(prog="loopx-strategy-hitl")
    sub = p.add_subparsers(dest="command", required=True)

    q = sub.add_parser("check")
    q.set_defaults(func=cmd_check)

    q = sub.add_parser("validate-proposal")
    q.add_argument("--snapshot", type=Path, required=True)
    q.add_argument("--proposal", type=Path, required=True)
    q.set_defaults(func=cmd_validate)

    q = sub.add_parser("interrupt")
    q.add_argument("--snapshot", type=Path, required=True)
    q.add_argument("--request", type=Path, required=True)
    q.add_argument("--output", type=Path, required=True)
    q.add_argument("--at")
    q.set_defaults(func=cmd_interrupt)

    q = sub.add_parser("decide")
    q.add_argument("--interrupt", type=Path, required=True)
    q.add_argument("--decision", type=Path, required=True)
    q.add_argument("--at", required=True)
    q.set_defaults(func=cmd_decide)

    q = sub.add_parser("resume")
    q.add_argument("--snapshot", type=Path, required=True)
    q.add_argument("--interrupt", type=Path, required=True)
    q.add_argument("--decision", type=Path, required=True)
    q.add_argument("--at", required=True)
    q.add_argument("--output", type=Path, required=True)
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_resume)

    q = sub.add_parser("checkpoint")
    q.add_argument("--snapshot", type=Path, required=True)
    q.add_argument("--interrupt", type=Path, required=True)
    q.add_argument("--thread-id", required=True)
    q.add_argument("--output", type=Path, required=True)
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_checkpoint)

    q = sub.add_parser("selftest")
    q.set_defaults(func=cmd_selftest)

    q = sub.add_parser("control")
    q.set_defaults(func=cmd_control)
    return p


def main(argv: list[str] | None = None) -> int:
    try:
        args = parser().parse_args(argv)
        return int(args.func(args))
    except CheckedError as exc:
        print(f"loopx-strategy-hitl RED: {exc}", file=sys.stderr)
        return 2
    except FatalError as exc:
        print(f"loopx-strategy-hitl FATAL: {exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
