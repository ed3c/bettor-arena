#!/usr/bin/env python3
"""Trusted process adapter for LoopX Worker Gateway v1."""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from gateway_common import (
    GatewayError,
    GatewayFatal,
    canonical_bytes,
    digest_bytes,
    digest_value,
    host_by_id,
    utc_now,
    validate_descriptor,
    validate_event,
    validate_receipt,
    validate_registry,
    validate_request,
    validate_request_against_host,
    write_json_exclusive,
)


def _artifact(output: Path, kind: str, data: bytes, media_type: str) -> dict[str, Any]:
    digest = digest_bytes(data)
    path = output / "artifacts" / digest.removeprefix("sha256:")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        if path.read_bytes() != data:
            raise GatewayFatal(f"artifact digest collision: {path}")
    except OSError as exc:
        raise GatewayFatal(f"cannot write artifact: {path}: {exc}") from exc
    return {"kind": kind, "digest": digest, "bytes": len(data), "media_type": media_type}


def _resolve_command(descriptor: dict[str, Any], root: Path, args: list[str]) -> list[str]:
    binary = shutil.which(descriptor["adapter"]["binary"])
    if binary is None:
        raise GatewayFatal(f"adapter binary absent: {descriptor['adapter']['binary']}")
    prefix: list[str] = []
    for item in descriptor["adapter"]["argv_prefix"]:
        candidate = root / item
        if item and not Path(item).is_absolute() and candidate.is_file():
            prefix.append(str(candidate.resolve()))
        else:
            prefix.append(item)
    return [binary, *prefix, *args]


def _minimal_env(request: dict[str, Any], workspace: Path) -> dict[str, str]:
    env: dict[str, str] = {"PATH": os.environ.get("PATH", "")}
    for name in request["policy"]["env_allowlist"]:
        if name in os.environ:
            env[name] = os.environ[name]
    env.update(
        {
            "LOOPX_REQUEST_ID": request["request_id"],
            "LOOPX_HOST_ID": request["host_id"],
            "LOOPX_REPOSITORY": request["subject"]["repository"],
            "LOOPX_COMMIT": request["subject"]["commit"],
            "LOOPX_TREE": request["subject"]["tree"],
            "LOOPX_TASK_ID": request["subject"]["task_id"],
            "LOOPX_SKILL_DIGEST": request["skill"]["digest"],
            "LOOPX_CONTEXT_DIGEST": request["context_digest"],
            "LOOPX_WORKSPACE": str(workspace),
        }
    )
    return env


def _identity_observation(stdout: bytes, request: dict[str, Any]) -> dict[str, str]:
    found: dict[str, Any] | None = None
    for raw in stdout.decode("utf-8", errors="replace").splitlines():
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("schema_version") == "loopx/fixture-worker-observation/v1":
            found = value
    if found is None:
        return {"loaded_skill": "UNOBSERVABLE", "loaded_context": "UNOBSERVABLE"}
    return {
        "loaded_skill": "VERIFIED"
        if found.get("skill_digest") == request["skill"]["digest"]
        else "MISMATCH",
        "loaded_context": "VERIFIED"
        if found.get("context_digest") == request["context_digest"]
        else "MISMATCH",
    }


def _attestation(value: str) -> str:
    return {"NONE": "NOT_ATTESTED", "REQUEST_ONLY": "REQUEST_ONLY", "ENFORCED": "ENFORCED"}[value]


def _non_execution_receipt(
    request: dict[str, Any], descriptor: dict[str, Any], state: str, reason: str
) -> dict[str, Any]:
    now = utc_now()
    events: list[dict[str, Any]] = []
    return {
        "schema_version": "loopx/worker-receipt/v1",
        "receipt_id": request["request_id"] + "-receipt",
        "request_id": request["request_id"],
        "request_digest": digest_value(request),
        "subject": request["subject"],
        "host": {
            "host_id": descriptor["host_id"],
            "descriptor_digest": digest_value(descriptor),
            "classification": descriptor["classification"],
            "trace_completeness": "PROCESS_ONLY",
        },
        "skill_digest": request["skill"]["digest"],
        "context_digest": request["context_digest"],
        "execution": {
            "executed": False,
            "exit_code": None,
            "timed_out": False,
            "cancelled": False,
            "started_at": now,
            "finished_at": now,
        },
        "policy_attestation": {
            "network": _attestation(descriptor["adapter"]["network_attestation"]),
            "filesystem": _attestation(descriptor["adapter"]["filesystem_attestation"]),
            "process_group": "NOT_ATTESTED",
        },
        "identity_observation": {"loaded_skill": "NOT_RUN", "loaded_context": "NOT_RUN"},
        "events_digest": digest_value(events),
        "artifacts": [],
        "cleanup": {
            "state": "NOT_RUN",
            "workspace_removed": True,
            "descendants_terminated": True,
            "residue_paths": [],
        },
        "authority": {
            "wrote_loopx_state": False,
            "wrote_gate_verdict": False,
            "performed_human_admit": False,
            "promoted_release": False,
            "waived_policy": False,
        },
        "state": state,
        "reasons": [reason],
    }


def execute(
    *,
    root: Path,
    registry: dict[str, Any],
    request: dict[str, Any],
    output: Path,
) -> tuple[int, dict[str, Any]]:
    registry = validate_registry(registry)
    request = validate_request(request)
    descriptor = validate_descriptor(
        host_by_id(registry, request["host_id"]),
        fixture_scope=registry["evidence_scope"] == "FIXTURE_ONLY",
    )
    validate_request_against_host(request, descriptor)

    if output.exists():
        raise GatewayFatal(f"output path already exists: {output}")
    output.mkdir(parents=True)
    write_json_exclusive(output / "request.json", request)
    write_json_exclusive(output / "host-descriptor.json", descriptor)

    state = descriptor["implementation_state"]
    if state not in {"FIXTURE_READY", "LIVE_ADMITTED"}:
        receipt_state = {
            "ABSENT": "ABSENT",
            "SKIPPED_BY_POLICY": "SKIPPED_BY_POLICY",
            "CONTRACT_ONLY": "NOT_EXERCISED",
            "NOT_EXERCISED": "NOT_EXERCISED",
        }.get(state, "NOT_EXERCISED")
        receipt = _non_execution_receipt(
            request, descriptor, receipt_state, f"host implementation state is {state}"
        )
        validate_receipt(receipt, request, descriptor)
        write_json_exclusive(output / "receipt.json", receipt)
        return 2, receipt

    command = _resolve_command(descriptor, root, request["invocation"]["args"])
    workspace = Path(tempfile.mkdtemp(prefix=f"loopx-worker-{request['host_id']}-"))
    started = utc_now()
    events: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    process: subprocess.Popen[bytes] | None = None
    stdout = b""
    stderr = b""
    timed_out = False
    cancelled = False
    descendants_terminated = False
    output_overflow = False

    def add_event(kind: str, payload: dict[str, Any]) -> None:
        event = {
            "schema_version": "loopx/worker-event/v1",
            "request_id": request["request_id"],
            "host_id": request["host_id"],
            "sequence": len(events),
            "observed_at": utc_now(),
            "kind": kind,
            "trace_completeness": "PROCESS_ONLY",
            "payload": payload,
        }
        validate_event(event, descriptor, request)
        events.append(event)

    try:
        add_event("WORKER_STARTED", {"argv_digest": digest_value(command), "workspace_lease": request["workspace"]["lease_id"]})
        try:
            process = subprocess.Popen(
                command,
                cwd=workspace,
                env=_minimal_env(request, workspace),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                start_new_session=True,
            )
        except OSError as exc:
            raise GatewayFatal(f"cannot start host adapter: {exc}") from exc

        try:
            stdout, stderr = process.communicate(timeout=request["invocation"]["timeout_ms"] / 1000)
        except subprocess.TimeoutExpired:
            timed_out = True
            add_event("TIMEOUT_OBSERVED", {"timeout_ms": request["invocation"]["timeout_ms"]})
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except OSError as exc:
                raise GatewayFatal(f"cannot kill timed-out process group: {exc}") from exc
            stdout, stderr = process.communicate()
        if process.poll() is None:
            descendants_terminated = False
        else:
            try:
                os.killpg(process.pid, 0)
            except ProcessLookupError:
                descendants_terminated = True
            except (PermissionError, OSError):
                descendants_terminated = False
            else:
                descendants_terminated = False

        limit = request["invocation"]["max_output_bytes"]
        if len(stdout) + len(stderr) > limit:
            output_overflow = True
            remaining = limit
            stdout = stdout[:remaining]
            remaining -= len(stdout)
            stderr = stderr[:max(0, remaining)]

        if stdout:
            artifact = _artifact(output, "STDOUT", stdout, "text/plain; charset=utf-8")
            artifacts.append(artifact)
            add_event("STDOUT_OBSERVED", {"digest": artifact["digest"], "bytes": artifact["bytes"]})
        if stderr:
            artifact = _artifact(output, "STDERR", stderr, "text/plain; charset=utf-8")
            artifacts.append(artifact)
            add_event("STDERR_OBSERVED", {"digest": artifact["digest"], "bytes": artifact["bytes"]})
        add_event(
            "WORKER_EXITED",
            {
                "exit_code": process.returncode,
                "timed_out": timed_out,
                "cancelled": cancelled,
                "output_overflow": output_overflow,
            },
        )
    finally:
        try:
            shutil.rmtree(workspace)
        except OSError:
            pass
        workspace_removed = not workspace.exists()
        residue = [] if workspace_removed else [str(workspace)]
        add_event(
            "CLEANUP_OBSERVED",
            {
                "workspace_removed": workspace_removed,
                "descendants_terminated": descendants_terminated,
                "residue_count": len(residue),
            },
        )

    event_bytes = b"".join(canonical_bytes(item) + b"\n" for item in events)
    event_artifact = _artifact(output, "WORKER_EVENT_STREAM", event_bytes, "application/x-ndjson")
    artifacts.append(event_artifact)
    finished = utc_now()
    identity = _identity_observation(stdout, request)
    cleanup_state = "PASS" if workspace_removed and descendants_terminated and not residue else "FAIL"
    exit_code = None if process is None else process.returncode
    reasons: list[str] = []
    if timed_out:
        reasons.append("process exceeded timeout and its process group was killed")
    if output_overflow:
        reasons.append("combined stdout/stderr exceeded the bounded output budget")
    if exit_code != 0:
        reasons.append(f"host process exited with {exit_code}")
    if cleanup_state != "PASS":
        reasons.append("workspace or process cleanup failed")
    if request["expected"]["loaded_skill_identity"] == "REQUIRED" and identity["loaded_skill"] != "VERIFIED":
        reasons.append("loaded Skill digest was not verified")
    if request["expected"]["loaded_context_identity"] == "REQUIRED" and identity["loaded_context"] != "VERIFIED":
        reasons.append("loaded context digest was not verified")
    if not reasons:
        reasons.append("process, identity and cleanup checks passed")
    result_state = "PASS" if not timed_out and not output_overflow and exit_code == 0 and cleanup_state == "PASS" and all(
        [
            request["expected"]["loaded_skill_identity"] != "REQUIRED" or identity["loaded_skill"] == "VERIFIED",
            request["expected"]["loaded_context_identity"] != "REQUIRED" or identity["loaded_context"] == "VERIFIED",
        ]
    ) else "FAIL"

    receipt = {
        "schema_version": "loopx/worker-receipt/v1",
        "receipt_id": request["request_id"] + "-receipt",
        "request_id": request["request_id"],
        "request_digest": digest_value(request),
        "subject": request["subject"],
        "host": {
            "host_id": descriptor["host_id"],
            "descriptor_digest": digest_value(descriptor),
            "classification": descriptor["classification"],
            "trace_completeness": "PROCESS_ONLY",
        },
        "skill_digest": request["skill"]["digest"],
        "context_digest": request["context_digest"],
        "execution": {
            "executed": True,
            "exit_code": exit_code,
            "timed_out": timed_out,
            "cancelled": cancelled,
            "started_at": started,
            "finished_at": finished,
        },
        "policy_attestation": {
            "network": _attestation(descriptor["adapter"]["network_attestation"]),
            "filesystem": _attestation(descriptor["adapter"]["filesystem_attestation"]),
            "process_group": "ENFORCED" if descriptor["adapter"]["supports_process_group_kill"] else "NOT_ATTESTED",
        },
        "identity_observation": identity,
        "events_digest": digest_value(events),
        "artifacts": artifacts,
        "cleanup": {
            "state": cleanup_state,
            "workspace_removed": workspace_removed,
            "descendants_terminated": descendants_terminated,
            "residue_paths": residue,
        },
        "authority": {
            "wrote_loopx_state": False,
            "wrote_gate_verdict": False,
            "performed_human_admit": False,
            "promoted_release": False,
            "waived_policy": False,
        },
        "state": result_state,
        "reasons": reasons,
    }
    validate_receipt(receipt, request, descriptor)
    write_json_exclusive(output / "receipt.json", receipt)
    return (0 if result_state == "PASS" else 2), receipt


def probe(registry: dict[str, Any]) -> dict[str, Any]:
    registry = validate_registry(registry)
    observations = []
    for descriptor in registry["hosts"]:
        path = shutil.which(descriptor["adapter"]["binary"])
        observations.append(
            {
                "host_id": descriptor["host_id"],
                "implementation_state": descriptor["implementation_state"],
                "binary_state": "PRESENT" if path else "ABSENT",
                "execution_state": "NOT_EXERCISED",
                "classification": descriptor["classification"],
                "trace_ceiling": descriptor["trace_ceiling"],
            }
        )
    return {
        "schema_version": "loopx/worker-probe-report/v1",
        "evidence_scope": "HOST_PROBE_ONLY",
        "observed_at": utc_now(),
        "hosts": observations,
        "admission": "NOT_PERFORMED",
    }
