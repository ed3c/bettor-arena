#!/usr/bin/env python3
"""Common primitives for the LoopX Worker Gateway v1."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

HOST_IDS = ("codex-cli", "claude-code", "grok-build", "opencode", "pi", "ante")
TRACE_ORDER = {"PROCESS_ONLY": 0, "TOOL_EVENTS": 1, "STRUCTURED_LOOP_EVENTS": 2}
GRAY_CLASSES = {"GRAY_BOX_HOST", "EXPERIMENTAL_GRAY_BOX_HOST"}
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")
ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
SECRET_PATTERNS = (
    re.compile(r"(?i)\b(?:api[_-]?key|secret|password|token)\s*[:=]\s*\S+"),
    re.compile(r"\b(?:sk|ghp|github_pat)_[A-Za-z0-9_-]{8,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{8,}"),
)
FORBIDDEN_AUTHORITY_KEYS = {
    "gate_verdict", "gate_result", "state_transition", "task_state", "todo_status",
    "human_admit", "human_decision", "promotion", "rollback", "force_skip",
    "ledger_sequence", "event_digest", "previous_event_digest",
}
FORBIDDEN_EVENT_KINDS = {
    "GATE_OBSERVED", "STATE_TRANSITION_COMMITTED", "HUMAN_DECISION_RECORDED",
    "PROMOTION_COMMITTED", "ROLLBACK_COMMITTED",
}
SHELL_BINARIES = {"sh", "bash", "zsh", "fish", "cmd", "cmd.exe", "powershell", "pwsh"}


class GatewayError(ValueError):
    """Checked contract/policy failure (exit 2)."""


class GatewayFatal(RuntimeError):
    """Input/tool/runtime failure that prevents a meaningful check (exit 64)."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest_value(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise GatewayFatal(f"missing JSON input: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise GatewayFatal(f"unreadable JSON input: {path}: {exc}") from exc


def write_json_exclusive(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise GatewayFatal(f"refusing to replace immutable output: {path}") from exc
    except OSError as exc:
        raise GatewayFatal(f"cannot write output: {path}: {exc}") from exc


def require_exact_keys(value: Any, required: set[str], optional: set[str], where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GatewayError(f"{where} must be an object")
    keys = set(value)
    missing = required - keys
    extra = keys - required - optional
    if missing:
        raise GatewayError(f"{where} missing fields: {sorted(missing)}")
    if extra:
        raise GatewayError(f"{where} unexpected fields: {sorted(extra)}")
    return value


def require_string(value: Any, where: str, *, minimum: int = 1, maximum: int = 4096) -> str:
    if not isinstance(value, str) or not (minimum <= len(value) <= maximum):
        raise GatewayError(f"{where} must be a string of length {minimum}..{maximum}")
    return value


def is_clean_relative_path(value: str) -> bool:
    if not value or "\x00" in value or "\\" in value:
        return False
    path = Path(value)
    if path.is_absolute():
        return False
    parts = path.parts
    return all(part not in {"", ".", ".."} for part in parts)


def scan_secret(value: Any, where: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            scan_secret(item, f"{where}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            scan_secret(item, f"{where}[{index}]")
    elif isinstance(value, str):
        for pattern in SECRET_PATTERNS:
            if pattern.search(value):
                raise GatewayError(f"secret-shaped value at {where}")


def scan_authority(value: Any, where: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_AUTHORITY_KEYS:
                raise GatewayError(f"forbidden Worker authority field {key!r} at {where}")
            scan_authority(item, f"{where}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            scan_authority(item, f"{where}[{index}]")


def validate_subject(subject: Any, where: str = "subject") -> dict[str, Any]:
    obj = require_exact_keys(subject, {"repository", "commit", "tree", "task_id"}, set(), where)
    repository = require_string(obj["repository"], f"{where}.repository", maximum=200)
    if repository.count("/") != 1:
        raise GatewayError(f"{where}.repository must be owner/name")
    if not SHA_RE.fullmatch(require_string(obj["commit"], f"{where}.commit", maximum=40)):
        raise GatewayError(f"{where}.commit must be a 40-character SHA")
    if not SHA_RE.fullmatch(require_string(obj["tree"], f"{where}.tree", maximum=40)):
        raise GatewayError(f"{where}.tree must be a 40-character SHA")
    if not ID_RE.fullmatch(require_string(obj["task_id"], f"{where}.task_id", maximum=128)):
        raise GatewayError(f"{where}.task_id is invalid")
    return obj


def validate_descriptor(value: Any, *, fixture_scope: bool = False) -> dict[str, Any]:
    required = {
        "schema_version", "host_id", "display_name", "classification", "transport",
        "implementation_state", "trace_ceiling", "adapter", "skill_discovery",
        "instruction_route", "source_identity",
    }
    obj = require_exact_keys(value, required, set(), "host descriptor")
    if obj["schema_version"] != "loopx/worker-host-descriptor/v1":
        raise GatewayError("host descriptor schema_version mismatch")
    if obj["host_id"] not in HOST_IDS:
        raise GatewayError(f"unsupported host_id: {obj['host_id']!r}")
    if obj["classification"] not in {
        "SOURCE_VISIBLE_HOST", "GRAY_BOX_HOST", "EXPERIMENTAL_GRAY_BOX_HOST"
    }:
        raise GatewayError("invalid host classification")
    if obj["implementation_state"] not in {
        "CONTRACT_ONLY", "NOT_EXERCISED", "FIXTURE_READY", "LIVE_ADMITTED",
        "ABSENT", "SKIPPED_BY_POLICY",
    }:
        raise GatewayError("invalid host implementation_state")
    if obj["implementation_state"] == "FIXTURE_READY" and not fixture_scope:
        raise GatewayError("FIXTURE_READY is allowed only in FIXTURE_ONLY registries")
    if obj["trace_ceiling"] not in TRACE_ORDER:
        raise GatewayError("invalid trace ceiling")
    if obj["classification"] in GRAY_CLASSES and obj["trace_ceiling"] != "PROCESS_ONLY":
        raise GatewayError("gray-box hosts cannot claim internal trace completeness")

    adapter = require_exact_keys(
        obj["adapter"],
        {"kind", "binary", "version_argv", "argv_prefix",
         "supports_process_group_kill", "network_attestation", "filesystem_attestation"},
        set(), "host descriptor.adapter",
    )
    binary = require_string(adapter["binary"], "host descriptor.adapter.binary", maximum=100)
    if binary.lower() in SHELL_BINARIES or "/" in binary or "\\" in binary:
        raise GatewayError("adapter binary must be a registry-owned non-shell executable name")
    if adapter["kind"] == "FIXTURE_PROCESS" and not fixture_scope:
        raise GatewayError("fixture adapter outside FIXTURE_ONLY registry")
    if adapter["kind"] != "FIXTURE_PROCESS" and obj["implementation_state"] == "FIXTURE_READY":
        raise GatewayError("FIXTURE_READY requires FIXTURE_PROCESS adapter")
    for field in ("version_argv", "argv_prefix"):
        seq = adapter[field]
        if not isinstance(seq, list) or len(seq) > 16 or any(
            not isinstance(item, str) or len(item) > 1024 for item in seq
        ):
            raise GatewayError(f"invalid adapter {field}")
    for field in ("skill_discovery", "instruction_route"):
        seq = obj[field]
        if not isinstance(seq, list) or not seq or len(seq) != len(set(seq)):
            raise GatewayError(f"{field} must be non-empty unique strings")
    if obj["source_identity"] is not None:
        source = require_exact_keys(obj["source_identity"], {"repository", "commit"}, set(), "source_identity")
        if source["repository"].count("/") != 1 or not SHA_RE.fullmatch(source["commit"]):
            raise GatewayError("invalid source_identity")
    scan_secret(obj)
    return obj


def validate_registry(value: Any) -> dict[str, Any]:
    obj = require_exact_keys(value, {"schema_version", "evidence_scope", "hosts"}, set(), "host registry")
    if obj["schema_version"] != "loopx/worker-host-registry/v1":
        raise GatewayError("host registry schema_version mismatch")
    if obj["evidence_scope"] not in {"CONTRACT_ONLY", "FIXTURE_ONLY", "LIVE"}:
        raise GatewayError("invalid registry evidence_scope")
    hosts = obj["hosts"]
    if not isinstance(hosts, list) or len(hosts) != len(HOST_IDS):
        raise GatewayError("host registry must contain exactly six hosts")
    fixture = obj["evidence_scope"] == "FIXTURE_ONLY"
    checked = [validate_descriptor(item, fixture_scope=fixture) for item in hosts]
    ids = [item["host_id"] for item in checked]
    if sorted(ids) != sorted(HOST_IDS) or len(ids) != len(set(ids)):
        raise GatewayError("host registry must contain each canonical host exactly once")
    if obj["evidence_scope"] == "CONTRACT_ONLY" and any(
        item["implementation_state"] in {"FIXTURE_READY", "LIVE_ADMITTED"} for item in checked
    ):
        raise GatewayError("CONTRACT_ONLY registry cannot admit executable hosts")
    return obj


def validate_request(value: Any) -> dict[str, Any]:
    required = {
        "schema_version", "request_id", "subject", "host_id", "skill",
        "context_digest", "workspace", "invocation", "policy", "expected",
    }
    obj = require_exact_keys(value, required, set(), "worker request")
    if obj["schema_version"] != "loopx/worker-request/v1":
        raise GatewayError("worker request schema_version mismatch")
    if not ID_RE.fullmatch(require_string(obj["request_id"], "request_id", maximum=128)):
        raise GatewayError("request_id is invalid")
    validate_subject(obj["subject"])
    if obj["host_id"] not in HOST_IDS:
        raise GatewayError("unsupported host_id")
    skill = require_exact_keys(obj["skill"], {"name", "digest"}, set(), "skill")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", require_string(skill["name"], "skill.name", maximum=64)):
        raise GatewayError("skill.name is invalid")
    if not DIGEST_RE.fullmatch(require_string(skill["digest"], "skill.digest", maximum=71)):
        raise GatewayError("skill.digest is invalid")
    if not DIGEST_RE.fullmatch(require_string(obj["context_digest"], "context_digest", maximum=71)):
        raise GatewayError("context_digest is invalid")

    workspace = require_exact_keys(obj["workspace"], {"lease_id", "source_mode", "allow_reuse"}, set(), "workspace")
    if not ID_RE.fullmatch(require_string(workspace["lease_id"], "workspace.lease_id", maximum=128)):
        raise GatewayError("workspace.lease_id is invalid")
    if workspace["allow_reuse"] is not False:
        raise GatewayError("mutable/reusable Worker workspace is forbidden")
    if workspace["source_mode"] not in {"READ_ONLY_SNAPSHOT", "DISPOSABLE_COPY", "DISPOSABLE_WORKTREE"}:
        raise GatewayError("workspace.source_mode is invalid")

    invocation = require_exact_keys(obj["invocation"], {"args", "timeout_ms", "max_output_bytes", "stdin"}, set(), "invocation")
    args = invocation["args"]
    if not isinstance(args, list) or len(args) > 64 or any(
        not isinstance(item, str) or len(item) > 1024 for item in args
    ):
        raise GatewayError("invocation.args is invalid")
    for index, item in enumerate(args):
        if item.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", item) or "../" in item or item == "..":
            raise GatewayError(f"absolute/path-traversal argument at invocation.args[{index}]")
    if not isinstance(invocation["timeout_ms"], int) or not 50 <= invocation["timeout_ms"] <= 3_600_000:
        raise GatewayError("invocation.timeout_ms is invalid")
    if not isinstance(invocation["max_output_bytes"], int) or not 1024 <= invocation["max_output_bytes"] <= 16_777_216:
        raise GatewayError("invocation.max_output_bytes is invalid")
    stdin = require_exact_keys(invocation["stdin"], {"mode"}, set(), "invocation.stdin")
    if stdin["mode"] not in {"CLOSED", "EMPTY"}:
        raise GatewayError("unsupported stdin mode")

    policy = require_exact_keys(
        obj["policy"], {"network", "filesystem", "process", "env_allowlist", "credential_refs"}, set(), "policy"
    )
    if policy["network"] not in {"DENY", "ALLOWLIST", "HOST_POLICY"}:
        raise GatewayError("invalid network policy")
    filesystem = require_exact_keys(policy["filesystem"], {"read_only_paths", "writable_paths"}, set(), "filesystem policy")
    for field in ("read_only_paths", "writable_paths"):
        paths = filesystem[field]
        if not isinstance(paths, list) or len(paths) > 64 or len(paths) != len(set(paths)):
            raise GatewayError(f"{field} must be unique strings")
        for path in paths:
            if path != "." and not is_clean_relative_path(path):
                raise GatewayError(f"invalid relative path in {field}: {path!r}")
    process = require_exact_keys(policy["process"], {"kill_process_group", "max_children"}, set(), "process policy")
    if process["kill_process_group"] is not True:
        raise GatewayError("process-group kill is mandatory")
    if not isinstance(process["max_children"], int) or not 0 <= process["max_children"] <= 128:
        raise GatewayError("process.max_children is invalid")
    env_names = policy["env_allowlist"]
    if not isinstance(env_names, list) or len(env_names) > 64 or len(env_names) != len(set(env_names)):
        raise GatewayError("env_allowlist must be unique strings")
    if any(not isinstance(name, str) or not ENV_RE.fullmatch(name) for name in env_names):
        raise GatewayError("env_allowlist contains an invalid name")
    refs = policy["credential_refs"]
    if not isinstance(refs, list) or len(refs) > 16 or len(refs) != len(set(refs)):
        raise GatewayError("credential_refs must be unique references")

    expected = require_exact_keys(
        obj["expected"], {"minimum_trace", "loaded_skill_identity", "loaded_context_identity"}, set(), "expected"
    )
    if expected["minimum_trace"] not in TRACE_ORDER:
        raise GatewayError("invalid expected.minimum_trace")
    for field in ("loaded_skill_identity", "loaded_context_identity"):
        if expected[field] not in {"REQUIRED", "OPTIONAL", "UNOBSERVABLE"}:
            raise GatewayError(f"invalid expected.{field}")

    scan_secret(obj)
    scan_authority(obj)
    return obj


def host_by_id(registry: dict[str, Any], host_id: str) -> dict[str, Any]:
    for host in registry["hosts"]:
        if host["host_id"] == host_id:
            return host
    raise GatewayError(f"host absent from registry: {host_id}")


def validate_request_against_host(request: dict[str, Any], descriptor: dict[str, Any]) -> None:
    if request["host_id"] != descriptor["host_id"]:
        raise GatewayError("request/descriptor host mismatch")
    minimum = request["expected"]["minimum_trace"]
    if TRACE_ORDER[minimum] > TRACE_ORDER[descriptor["trace_ceiling"]]:
        raise GatewayError("requested trace completeness exceeds host ceiling")
    if descriptor["classification"] in GRAY_CLASSES and minimum != "PROCESS_ONLY":
        raise GatewayError("gray-box host cannot satisfy internal trace request")
    network = request["policy"]["network"]
    if network in {"DENY", "ALLOWLIST"} and descriptor["adapter"]["network_attestation"] != "ENFORCED":
        raise GatewayError("host adapter cannot attest requested network policy")
    if request["policy"]["credential_refs"] and descriptor["implementation_state"] == "FIXTURE_READY":
        raise GatewayError("fixture adapter cannot resolve credential references")
    if not descriptor["adapter"]["supports_process_group_kill"]:
        raise GatewayError("adapter cannot satisfy mandatory process-group cleanup")


def validate_event(event: Any, descriptor: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    obj = require_exact_keys(
        event,
        {"schema_version", "request_id", "host_id", "sequence", "observed_at",
         "kind", "trace_completeness", "payload"},
        set(), "worker event",
    )
    if obj["schema_version"] != "loopx/worker-event/v1":
        raise GatewayError("worker event schema_version mismatch")
    if obj["request_id"] != request["request_id"] or obj["host_id"] != request["host_id"]:
        raise GatewayError("worker event subject identity mismatch")
    if not isinstance(obj["sequence"], int) or obj["sequence"] < 0:
        raise GatewayError("worker event sequence invalid")
    if obj["kind"] in FORBIDDEN_EVENT_KINDS:
        raise GatewayError("Worker attempted an authoritative event")
    allowed = {
        "WORKER_STARTED", "STDOUT_OBSERVED", "STDERR_OBSERVED", "ARTIFACT_OBSERVED",
        "TOOL_EVENT_OBSERVED", "LOOP_EVENT_OBSERVED", "TIMEOUT_OBSERVED",
        "CANCELLATION_OBSERVED", "WORKER_EXITED", "CLEANUP_OBSERVED",
    }
    if obj["kind"] not in allowed:
        raise GatewayError(f"unknown Worker event kind: {obj['kind']!r}")
    trace = obj["trace_completeness"]
    if trace not in TRACE_ORDER or TRACE_ORDER[trace] > TRACE_ORDER[descriptor["trace_ceiling"]]:
        raise GatewayError("worker event exceeds descriptor trace ceiling")
    if descriptor["classification"] in GRAY_CLASSES and obj["kind"] in {
        "TOOL_EVENT_OBSERVED", "LOOP_EVENT_OBSERVED"
    }:
        raise GatewayError("gray-box adapter fabricated internal events")
    if not isinstance(obj["payload"], dict) or len(obj["payload"]) > 16:
        raise GatewayError("worker event payload invalid")
    scan_secret(obj["payload"], "worker_event.payload")
    scan_authority(obj["payload"], "worker_event.payload")
    return obj


def validate_receipt(receipt: Any, request: dict[str, Any], descriptor: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schema_version", "receipt_id", "request_id", "request_digest", "subject",
        "host", "skill_digest", "context_digest", "execution", "policy_attestation",
        "identity_observation", "events_digest", "artifacts", "cleanup", "authority",
        "state", "reasons",
    }
    obj = require_exact_keys(receipt, required, set(), "worker receipt")
    if obj["schema_version"] != "loopx/worker-receipt/v1":
        raise GatewayError("worker receipt schema_version mismatch")
    if obj["request_id"] != request["request_id"]:
        raise GatewayError("receipt/request ID mismatch")
    if obj["request_digest"] != digest_value(request):
        raise GatewayError("receipt request digest mismatch")
    if obj["subject"] != request["subject"]:
        raise GatewayError("receipt subject mismatch")
    host = require_exact_keys(
        obj["host"],
        {"host_id", "descriptor_digest", "classification", "trace_completeness"},
        set(), "receipt.host",
    )
    if host["host_id"] != descriptor["host_id"] or host["classification"] != descriptor["classification"]:
        raise GatewayError("receipt host identity mismatch")
    if host["descriptor_digest"] != digest_value(descriptor):
        raise GatewayError("receipt descriptor digest mismatch")
    if host["trace_completeness"] not in TRACE_ORDER:
        raise GatewayError("receipt trace completeness invalid")
    if descriptor["classification"] in GRAY_CLASSES and host["trace_completeness"] != "PROCESS_ONLY":
        raise GatewayError("gray-box receipt fabricated internal completeness")
    if obj["skill_digest"] != request["skill"]["digest"] or obj["context_digest"] != request["context_digest"]:
        raise GatewayError("receipt Skill/context digest mismatch")

    execution = require_exact_keys(
        obj["execution"],
        {"executed", "exit_code", "timed_out", "cancelled", "started_at", "finished_at"},
        set(), "receipt.execution",
    )
    cleanup = require_exact_keys(
        obj["cleanup"],
        {"state", "workspace_removed", "descendants_terminated", "residue_paths"},
        set(), "receipt.cleanup",
    )
    authority = require_exact_keys(
        obj["authority"],
        {"wrote_loopx_state", "wrote_gate_verdict", "performed_human_admit",
         "promoted_release", "waived_policy"},
        set(), "receipt.authority",
    )
    if any(authority.values()):
        raise GatewayError("Worker receipt claims forbidden authority")
    if cleanup["state"] not in {"PASS", "FAIL", "NOT_RUN"}:
        raise GatewayError("invalid cleanup state")
    if not isinstance(cleanup["residue_paths"], list):
        raise GatewayError("cleanup.residue_paths must be a list")
    state = obj["state"]
    if state not in {"PASS", "FAIL", "NOT_EXERCISED", "SKIPPED_BY_POLICY", "ABSENT"}:
        raise GatewayError("invalid receipt state")
    if not isinstance(obj["reasons"], list) or not obj["reasons"]:
        raise GatewayError("receipt reasons must be non-empty")

    identities = require_exact_keys(
        obj["identity_observation"], {"loaded_skill", "loaded_context"}, set(), "identity_observation"
    )
    if state == "PASS":
        if execution["executed"] is not True or execution["exit_code"] != 0:
            raise GatewayError("PASS requires an executed zero-exit process")
        if execution["timed_out"] or execution["cancelled"]:
            raise GatewayError("PASS cannot be timed out or cancelled")
        if cleanup["state"] != "PASS" or not cleanup["workspace_removed"] or not cleanup["descendants_terminated"]:
            raise GatewayError("PASS requires complete cleanup")
        if cleanup["residue_paths"]:
            raise GatewayError("PASS receipt contains residue")
        if request["expected"]["loaded_skill_identity"] == "REQUIRED" and identities["loaded_skill"] != "VERIFIED":
            raise GatewayError("PASS requires verified loaded Skill identity")
        if request["expected"]["loaded_context_identity"] == "REQUIRED" and identities["loaded_context"] != "VERIFIED":
            raise GatewayError("PASS requires verified loaded context identity")
    if state in {"NOT_EXERCISED", "ABSENT", "SKIPPED_BY_POLICY"} and execution["executed"]:
        raise GatewayError(f"{state} receipt cannot claim execution")
    scan_secret(obj)
    return obj
