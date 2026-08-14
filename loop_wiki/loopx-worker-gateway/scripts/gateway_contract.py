#!/usr/bin/env python3
"""Semantic contract checks for LoopX Worker Gateway v1."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from gateway_common import *

ADAPTER_KEYS = {
    "schema_version", "adapter_id", "host_id", "classification", "transport",
    "binary", "version_argv", "implementation_state", "source_identity",
    "skill_roots", "instruction_routes", "adapter_entry", "trace_ceiling",
    "capabilities", "content_digest",
}
REQUEST_KEYS = {
    "schema_version", "request_id", "subject", "adapter_id", "host_id", "skill",
    "context", "workspace", "policy", "task", "credential_refs", "content_digest",
}
EVENT_KEYS = {
    "schema_version", "event_id", "request_id", "host_id", "sequence",
    "occurred_at", "kind", "visibility", "payload", "content_digest",
}
RECEIPT_KEYS = {
    "schema_version", "receipt_id", "request_id", "subject", "adapter", "skill",
    "context", "status", "executed", "process", "trace", "artifacts", "cleanup",
    "authority", "content_digest",
}
REGISTRY_KEYS = {"schema_version", "adapters", "live_matrix_state", "human_admit", "content_digest"}
CLASSIFICATIONS = {
    "WHITE_BOX_REFERENCE", "SOURCE_VISIBLE_GRAY_MODEL", "GRAY_BOX", "EXPERIMENTAL_GRAY_BOX"
}
IMPLEMENTATION_STATES = {"IMPLEMENTED", "NOT_IMPLEMENTED", "NOT_EXERCISED", "ABSENT", "SKIPPED_BY_POLICY"}
TRACE_CEILINGS = {"PROCESS_ONLY", "TOOL_OBSERVED", "SOURCE_VERIFIED_INTERNAL"}
EVENT_VISIBILITIES = {"EXTERNAL", "HOST_REPORTED", "SOURCE_VERIFIED_INTERNAL"}

def validate_adapter(value: Any, label: str = "adapter", *, allow_fixture: bool = False) -> dict[str, Any]:
    adapter = exact_object(value, ADAPTER_KEYS, label)
    if adapter["schema_version"] != "loopx/worker-adapter/v1":
        raise ContractError(f"{label}.schema_version drifted")
    if stable_id(adapter["adapter_id"], f"{label}.adapter_id") != adapter["host_id"]:
        raise ContractError(f"{label} adapter_id and host_id must match")
    allowed_hosts = HOSTS if allow_fixture else HOSTS - {"fixture-host"}
    if adapter["host_id"] not in allowed_hosts:
        raise ContractError(f"{label}.host_id unsupported")
    if adapter["classification"] not in CLASSIFICATIONS:
        raise ContractError(f"{label}.classification unsupported")
    if adapter["transport"] not in {"CLI", "RPC", "HTTP", "SDK", "JSONL"}:
        raise ContractError(f"{label}.transport unsupported")
    binary = bounded(adapter["binary"], f"{label}.binary", 128)
    if "/" in binary or "\\" in binary or not re.fullmatch(r"[A-Za-z0-9_.+-]+", binary):
        raise ContractError(f"{label}.binary must be a PATH-resolved basename")
    argv = adapter["version_argv"]
    if not isinstance(argv, list) or len(argv) > 8:
        raise ContractError(f"{label}.version_argv invalid")
    for index, item in enumerate(argv):
        bounded(item, f"{label}.version_argv[{index}]", 128)
        if "\n" in item or "\r" in item or "\0" in item:
            raise ContractError(f"{label}.version_argv[{index}] contains a control character")
    if adapter["implementation_state"] not in IMPLEMENTATION_STATES:
        raise ContractError(f"{label}.implementation_state unsupported")
    source = adapter["source_identity"]
    if source is not None:
        source = exact_object(source, {"repository", "ref", "digest"}, f"{label}.source_identity")
        if not REPO.fullmatch(bounded(source["repository"], f"{label}.source_identity.repository", 256)):
            raise ContractError(f"{label}.source_identity.repository invalid")
        bounded(source["ref"], f"{label}.source_identity.ref", 128)
        sha_ref(source["digest"], f"{label}.source_identity.digest")
    for key in ("skill_roots", "instruction_routes"):
        values = adapter[key]
        if not isinstance(values, list) or not values or len(values) != len(set(values)):
            raise ContractError(f"{label}.{key} must be unique non-empty paths")
        for index, item in enumerate(values):
            relpath(item, f"{label}.{key}[{index}]")
    relpath(adapter["adapter_entry"], f"{label}.adapter_entry")
    if adapter["trace_ceiling"] not in TRACE_CEILINGS:
        raise ContractError(f"{label}.trace_ceiling unsupported")
    if adapter["trace_ceiling"] == "SOURCE_VERIFIED_INTERNAL" and source is None and not allow_fixture:
        raise ContractError(f"{label} claims source-verified internals without a pinned source identity")
    caps = exact_object(
        adapter["capabilities"],
        {"structured_output", "streaming", "session_resume", "loaded_skill_digest", "loaded_context_digest", "offline"},
        f"{label}.capabilities",
    )
    if any(type(value) is not bool for value in caps.values()):
        raise ContractError(f"{label}.capabilities must be booleans")
    if adapter["classification"] in {"GRAY_BOX", "EXPERIMENTAL_GRAY_BOX"} and adapter["trace_ceiling"] == "SOURCE_VERIFIED_INTERNAL":
        raise ContractError(f"{label} gray-box adapter cannot claim source-verified internal trace")
    reject_authority_or_private_fields(adapter, label)
    reject_secret_payload(adapter, label)
    verify_content_digest(adapter, label)
    return adapter

def validate_registry(root: Path, value: Any | None = None) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    registry_path = root / "adapters" / "registry.json"
    registry = exact_object(load_json(registry_path) if value is None else value, REGISTRY_KEYS, "adapter registry")
    if registry["schema_version"] != "loopx/worker-adapter-registry/v1":
        raise ContractError("adapter registry version drifted")
    names = registry["adapters"]
    expected = ["codex-cli", "claude-code", "grok-build", "opencode", "pi", "ante"]
    if names != expected:
        raise ContractError(f"adapter registry must preserve exact six-host order: {expected}")
    if registry["live_matrix_state"] != "NOT_EXERCISED" or registry["human_admit"] is not False:
        raise ContractError("adapter registry fabricated live matrix or Human Admit")
    descriptors: dict[str, dict[str, Any]] = {}
    for name in names:
        descriptor = validate_adapter(load_json(root / "adapters" / f"{name}.json"), f"adapter[{name}]")
        if descriptor["adapter_id"] != name:
            raise ContractError(f"adapter file identity mismatch: {name}")
        descriptors[name] = descriptor
    if descriptors["grok-build"]["source_identity"] is None:
        raise ContractError("Grok Build white-box reference lacks the reviewed source pin")
    if descriptors["ante"]["implementation_state"] != "NOT_IMPLEMENTED":
        raise ContractError("Ante must remain NOT_IMPLEMENTED until its runtime adapter is physically admitted")
    if any(item["implementation_state"] == "IMPLEMENTED" for item in descriptors.values()):
        raise ContractError("live host adapter support was fabricated in the contract-only registry")
    verify_content_digest(registry, "adapter registry")
    return registry, descriptors

def validate_request(value: Any, adapters: dict[str, dict[str, Any]] | None = None, label: str = "worker request") -> dict[str, Any]:
    request = exact_object(value, REQUEST_KEYS, label)
    if request["schema_version"] != "loopx/worker-request/v1":
        raise ContractError(f"{label}.schema_version drifted")
    stable_id(request["request_id"], f"{label}.request_id")
    validate_subject(request["subject"], f"{label}.subject")
    adapter_id = stable_id(request["adapter_id"], f"{label}.adapter_id")
    if request["host_id"] not in HOSTS:
        raise ContractError(f"{label}.host_id unsupported")
    if adapters is not None:
        if adapter_id not in adapters or adapters[adapter_id]["host_id"] != request["host_id"]:
            raise ContractError(f"{label} adapter/host identity mismatch")
    skill = exact_object(request["skill"], {"name", "digest", "source_ref"}, f"{label}.skill")
    stable_id(skill["name"], f"{label}.skill.name")
    sha_ref(skill["digest"], f"{label}.skill.digest")
    relpath(skill["source_ref"], f"{label}.skill.source_ref")
    context = exact_object(request["context"], {"digest", "entry_files"}, f"{label}.context")
    sha_ref(context["digest"], f"{label}.context.digest")
    if not isinstance(context["entry_files"], list) or not context["entry_files"] or len(context["entry_files"]) != len(set(context["entry_files"])):
        raise ContractError(f"{label}.context.entry_files invalid")
    for index, item in enumerate(context["entry_files"]):
        relpath(item, f"{label}.context.entry_files[{index}]")
    workspace = exact_object(request["workspace"], {"lease_id", "writable_paths", "read_only_paths", "cleanup"}, f"{label}.workspace")
    stable_id(workspace["lease_id"], f"{label}.workspace.lease_id")
    if workspace["cleanup"] != "REQUIRED":
        raise ContractError(f"{label}.workspace.cleanup must be REQUIRED")
    all_paths: set[str] = set()
    for key in ("writable_paths", "read_only_paths"):
        values = workspace[key]
        if not isinstance(values, list) or len(values) != len(set(values)):
            raise ContractError(f"{label}.workspace.{key} invalid")
        for index, item in enumerate(values):
            normalized = relpath(item, f"{label}.workspace.{key}[{index}]")
            if normalized in all_paths:
                raise ContractError(f"{label}.workspace path is both writable and read-only: {normalized}")
            all_paths.add(normalized)
    policy = exact_object(
        request["policy"],
        {"timeout_ms", "max_output_bytes", "max_processes", "network", "env_allowlist", "require_process_group"},
        f"{label}.policy",
    )
    if type(policy["timeout_ms"]) is not int or not 1000 <= policy["timeout_ms"] <= 3_600_000:
        raise ContractError(f"{label}.policy.timeout_ms invalid")
    if type(policy["max_output_bytes"]) is not int or not 1024 <= policy["max_output_bytes"] <= 104_857_600:
        raise ContractError(f"{label}.policy.max_output_bytes invalid")
    if type(policy["max_processes"]) is not int or not 1 <= policy["max_processes"] <= 64:
        raise ContractError(f"{label}.policy.max_processes invalid")
    if policy["network"] not in {"HOST_POLICY", "DENY", "ALLOWLISTED"}:
        raise ContractError(f"{label}.policy.network unsupported")
    if policy["require_process_group"] is not True:
        raise ContractError(f"{label} must require a process group")
    envs = policy["env_allowlist"]
    if not isinstance(envs, list) or len(envs) != len(set(envs)):
        raise ContractError(f"{label}.policy.env_allowlist invalid")
    for item in envs:
        if not isinstance(item, str) or not ENV.fullmatch(item) or SECRET_KEYS.search(item):
            raise ContractError(f"{label}.policy.env_allowlist contains unsafe key: {item!r}")
    task = exact_object(request["task"], {"prompt_ref", "mode", "expected_artifacts"}, f"{label}.task")
    validate_artifact(task["prompt_ref"], f"{label}.task.prompt_ref")
    if task["prompt_ref"]["kind"] != "FILE":
        raise ContractError(f"{label}.task.prompt_ref must be a FILE artifact")
    if task["mode"] not in {"READ_ONLY", "EDIT"}:
        raise ContractError(f"{label}.task.mode unsupported")
    expected = task["expected_artifacts"]
    allowed_expected = {"STDOUT", "STDERR", "GIT_DIFF", "WORKER_EVENT", "CLEANUP_REPORT"}
    if not isinstance(expected, list) or len(expected) != len(set(expected)) or set(expected) - allowed_expected:
        raise ContractError(f"{label}.task.expected_artifacts invalid")
    credentials = request["credential_refs"]
    if not isinstance(credentials, list) or len(credentials) != len(set(credentials)):
        raise ContractError(f"{label}.credential_refs invalid")
    for index, item in enumerate(credentials):
        stable_id(item, f"{label}.credential_refs[{index}]")
    reject_authority_or_private_fields(request, label)
    reject_secret_payload(request, label)
    verify_content_digest(request, label)
    return request

def validate_event(
    value: Any,
    request: dict[str, Any],
    descriptor: dict[str, Any],
    expected_sequence: int,
    label: str = "worker event",
) -> dict[str, Any]:
    event = exact_object(value, EVENT_KEYS, label)
    if event["schema_version"] != "loopx/worker-event/v1":
        raise ContractError(f"{label}.schema_version drifted")
    stable_id(event["event_id"], f"{label}.event_id")
    if event["request_id"] != request["request_id"] or event["host_id"] != request["host_id"]:
        raise ContractError(f"{label} request/host identity mismatch")
    if event["sequence"] != expected_sequence:
        raise ContractError(f"{label}.sequence gap")
    bounded(event["occurred_at"], f"{label}.occurred_at", 32)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", event["occurred_at"]):
        raise ContractError(f"{label}.occurred_at must be canonical UTC seconds")
    if event["kind"] not in {"PROCESS_STARTED", "STDOUT", "STDERR", "TOOL_OBSERVED", "ARTIFACT", "PROCESS_EXIT", "CLEANUP"}:
        raise ContractError(f"{label}.kind unsupported")
    if event["visibility"] not in EVENT_VISIBILITIES:
        raise ContractError(f"{label}.visibility unsupported")
    ceiling = descriptor["trace_ceiling"]
    ranks = {"EXTERNAL": 0, "HOST_REPORTED": 1, "SOURCE_VERIFIED_INTERNAL": 2}
    ceiling_rank = {"PROCESS_ONLY": 0, "TOOL_OBSERVED": 1, "SOURCE_VERIFIED_INTERNAL": 2}[ceiling]
    if ranks[event["visibility"]] > ceiling_rank:
        raise ContractError(f"{label} exceeds adapter trace ceiling")
    if descriptor["classification"] in {"GRAY_BOX", "EXPERIMENTAL_GRAY_BOX"} and event["visibility"] == "SOURCE_VERIFIED_INTERNAL":
        raise ContractError(f"{label} fabricated gray-box internals")
    payload = exact_object(event["payload"], {"message", "exit_code", "tool", "artifact_ref", "cleanup_state"}, f"{label}.payload")
    if payload["message"] is not None:
        bounded(payload["message"], f"{label}.payload.message", 4096, allow_empty=True)
    if payload["exit_code"] is not None and type(payload["exit_code"]) is not int:
        raise ContractError(f"{label}.payload.exit_code invalid")
    if payload["tool"] is not None:
        stable_id(payload["tool"], f"{label}.payload.tool")
    if payload["artifact_ref"] is not None:
        validate_artifact(payload["artifact_ref"], f"{label}.payload.artifact_ref")
    if payload["cleanup_state"] not in {None, "PASS", "FAIL", "NOT_RUN"}:
        raise ContractError(f"{label}.payload.cleanup_state invalid")
    if event["kind"] == "PROCESS_EXIT" and payload["exit_code"] is None:
        raise ContractError(f"{label} PROCESS_EXIT lacks exit code")
    if event["kind"] == "CLEANUP" and payload["cleanup_state"] is None:
        raise ContractError(f"{label} CLEANUP lacks state")
    reject_authority_or_private_fields(event, label)
    reject_secret_payload(event, label)
    verify_content_digest(event, label)
    return event

def validate_receipt(
    value: Any,
    request: dict[str, Any],
    descriptor: dict[str, Any],
    label: str = "worker receipt",
) -> dict[str, Any]:
    receipt = exact_object(value, RECEIPT_KEYS, label)
    if receipt["schema_version"] != "loopx/worker-receipt/v1":
        raise ContractError(f"{label}.schema_version drifted")
    stable_id(receipt["receipt_id"], f"{label}.receipt_id")
    if receipt["request_id"] != request["request_id"]:
        raise ContractError(f"{label}.request_id mismatch")
    if validate_subject(receipt["subject"], f"{label}.subject") != request["subject"]:
        raise ContractError(f"{label}.subject mismatch")
    adapter = exact_object(
        receipt["adapter"],
        {"adapter_id", "host_id", "descriptor_digest", "binary_identity", "implementation_state"},
        f"{label}.adapter",
    )
    if adapter["adapter_id"] != descriptor["adapter_id"] or adapter["host_id"] != descriptor["host_id"]:
        raise ContractError(f"{label}.adapter identity mismatch")
    if adapter["descriptor_digest"] != descriptor["content_digest"]:
        raise ContractError(f"{label}.adapter descriptor digest mismatch")
    if adapter["implementation_state"] != descriptor["implementation_state"]:
        raise ContractError(f"{label}.adapter implementation state mismatch")
    if adapter["binary_identity"] is not None:
        bounded(adapter["binary_identity"], f"{label}.adapter.binary_identity", 512)
    if receipt["skill"] != {"name": request["skill"]["name"], "digest": request["skill"]["digest"]}:
        raise ContractError(f"{label}.skill mismatch")
    if receipt["context"] != {"digest": request["context"]["digest"]}:
        raise ContractError(f"{label}.context mismatch")
    if receipt["status"] not in STATUSES or type(receipt["executed"]) is not bool:
        raise ContractError(f"{label}.status/executed invalid")
    process = exact_object(receipt["process"], {"exit_code", "timed_out", "cancelled", "process_group_killed"}, f"{label}.process")
    if process["exit_code"] is not None and type(process["exit_code"]) is not int:
        raise ContractError(f"{label}.process.exit_code invalid")
    if any(type(process[key]) is not bool for key in ("timed_out", "cancelled", "process_group_killed")):
        raise ContractError(f"{label}.process flags invalid")
    trace = exact_object(receipt["trace"], {"completeness", "events_digest", "event_count", "opaque_segments"}, f"{label}.trace")
    if trace["completeness"] not in TRACE_CEILINGS:
        raise ContractError(f"{label}.trace.completeness unsupported")
    sha_ref(trace["events_digest"], f"{label}.trace.events_digest")
    if type(trace["event_count"]) is not int or trace["event_count"] < 0:
        raise ContractError(f"{label}.trace.event_count invalid")
    if not isinstance(trace["opaque_segments"], list):
        raise ContractError(f"{label}.trace.opaque_segments invalid")
    for item in trace["opaque_segments"]:
        bounded(item, f"{label}.trace.opaque_segments", 256)
    artifacts = receipt["artifacts"]
    if not isinstance(artifacts, list):
        raise ContractError(f"{label}.artifacts invalid")
    for index, artifact in enumerate(artifacts):
        validate_artifact(artifact, f"{label}.artifacts[{index}]")
    cleanup = exact_object(receipt["cleanup"], {"state", "residue_paths"}, f"{label}.cleanup")
    if cleanup["state"] not in {"PASS", "FAIL", "NOT_RUN"} or not isinstance(cleanup["residue_paths"], list):
        raise ContractError(f"{label}.cleanup invalid")
    for item in cleanup["residue_paths"]:
        relpath(item, f"{label}.cleanup.residue_paths")
    authority = exact_object(
        receipt["authority"],
        {"wrote_loopx_state", "submitted_gate_verdict", "performed_human_admit", "promoted_release", "wrote_durable_memory"},
        f"{label}.authority",
    )
    if any(value is not False for value in authority.values()):
        raise ContractError(f"{label} exceeds Worker authority")
    if receipt["status"] == "PASS":
        if receipt["executed"] is not True or process["exit_code"] != 0 or cleanup["state"] != "PASS":
            raise ContractError(f"{label} fabricated PASS")
    if receipt["status"] in {"NOT_EXERCISED", "ABSENT", "SKIPPED_BY_POLICY"}:
        if receipt["executed"] is not False or process["exit_code"] is not None:
            raise ContractError(f"{label} non-execution state contains execution evidence")
    reject_authority_or_private_fields(receipt, label)
    reject_secret_payload(receipt, label)
    verify_content_digest(receipt, label)
    return receipt
