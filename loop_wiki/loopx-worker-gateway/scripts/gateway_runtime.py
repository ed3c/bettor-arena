#!/usr/bin/env python3
"""Trusted-host execution and normalization for LoopX Worker Gateway v1."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
from typing import Any

from gateway_common import *
from gateway_contract import validate_adapter, validate_event, validate_receipt, validate_request

AUTHORITY_FALSE = {
    "wrote_loopx_state": False,
    "submitted_gate_verdict": False,
    "performed_human_admit": False,
    "promoted_release": False,
    "wrote_durable_memory": False,
}

def run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        env={"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"},
    )
    if check and result.returncode != 0:
        raise InputError(f"git {' '.join(args)} failed: {result.stderr[-500:]}")
    return result

def copy_artifact(data: bytes, output: Path, artifact_id: str, kind: str, producer: str, media_type: str) -> dict[str, Any]:
    artifacts = output / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha256(data).hexdigest()
    path = artifacts / name
    if not path.exists():
        path.write_bytes(data)
    return make_artifact(path, output, artifact_id, kind, producer, media_type)

def nonexecution_receipt(
    request: dict[str, Any],
    descriptor: dict[str, Any],
    output: Path,
    status: str,
    receipt_id: str,
    reason: str,
) -> dict[str, Any]:
    events = b""
    events_ref = copy_artifact(events, output, "worker-events", "WORKER_EVENT", "worker-gateway", "application/x-ndjson")
    receipt = {
        "schema_version": "loopx/worker-receipt/v1",
        "receipt_id": receipt_id,
        "request_id": request["request_id"],
        "subject": copy.deepcopy(request["subject"]),
        "adapter": {
            "adapter_id": descriptor["adapter_id"],
            "host_id": descriptor["host_id"],
            "descriptor_digest": descriptor["content_digest"],
            "binary_identity": None,
            "implementation_state": descriptor["implementation_state"],
        },
        "skill": {"name": request["skill"]["name"], "digest": request["skill"]["digest"]},
        "context": {"digest": request["context"]["digest"]},
        "status": status,
        "executed": False,
        "process": {
            "exit_code": None,
            "timed_out": False,
            "cancelled": False,
            "process_group_killed": False,
        },
        "trace": {
            "completeness": "PROCESS_ONLY",
            "events_digest": events_ref["digest"],
            "event_count": 0,
            "opaque_segments": [reason],
        },
        "artifacts": [events_ref],
        "cleanup": {"state": "NOT_RUN", "residue_paths": []},
        "authority": copy.deepcopy(AUTHORITY_FALSE),
        "content_digest": None,
    }
    raw = copy.deepcopy(receipt)
    raw.pop("content_digest")
    receipt["content_digest"] = digest(raw)
    validate_receipt(receipt, request, descriptor)
    return receipt

def ensure_request_subject(repo: Path, request: dict[str, Any]) -> None:
    if not (repo / ".git").exists() and run_git(repo, "rev-parse", "--git-dir", check=False).returncode != 0:
        raise InputError(f"not a Git repository: {repo}")
    commit = run_git(repo, "rev-parse", request["subject"]["commit"]).stdout.strip()
    tree = run_git(repo, "rev-parse", f"{request['subject']['commit']}^{{tree}}").stdout.strip()
    if commit != request["subject"]["commit"] or tree != request["subject"]["tree"]:
        raise ContractError("request subject does not match the source repository")
    prompt_path = repo / request["task"]["prompt_ref"]["path"]
    if not prompt_path.is_file() or file_digest(prompt_path) != request["task"]["prompt_ref"]["digest"]:
        raise ContractError("prompt artifact is absent or digest-mismatched")
    for entry in request["context"]["entry_files"]:
        if not (repo / entry).is_file():
            raise ContractError(f"context entry file is absent: {entry}")
    skill_path = repo / request["skill"]["source_ref"]
    if not skill_path.is_file():
        raise ContractError("Skill source is absent")
    if file_digest(skill_path) != request["skill"]["digest"]:
        raise ContractError("Skill digest mismatch")

def changed_paths(worktree: Path) -> list[str]:
    result = run_git(worktree, "status", "--porcelain=v1", "-z")
    entries = result.stdout.split("\0")
    paths: list[str] = []
    for item in entries:
        if not item:
            continue
        value = item[3:] if len(item) >= 4 else item
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        paths.append(value)
    return sorted(set(paths))

def within_roots(path: str, roots: list[str]) -> bool:
    candidate = Path(path).as_posix()
    for root in roots:
        normalized = Path(root).as_posix().rstrip("/")
        if candidate == normalized or candidate.startswith(normalized + "/"):
            return True
    return False

def run_fixture_or_implemented(
    request: dict[str, Any],
    descriptor: dict[str, Any],
    repo: Path,
    module_root: Path,
    output: Path,
    receipt_id: str,
    allow_fixture: bool,
) -> tuple[dict[str, Any], int]:
    if descriptor["implementation_state"] != "IMPLEMENTED":
        status = "ABSENT" if descriptor["implementation_state"] == "ABSENT" else (
            "SKIPPED_BY_POLICY" if descriptor["implementation_state"] == "SKIPPED_BY_POLICY" else "NOT_EXERCISED"
        )
        receipt = nonexecution_receipt(
            request, descriptor, output, status, receipt_id,
            f"adapter state is {descriptor['implementation_state']}; no live host execution was performed",
        )
        write_json_atomic(output / "receipt.json", receipt)
        return receipt, BAD
    if descriptor["host_id"] == "fixture-host" and not allow_fixture:
        raise ContractError("fixture adapter requires explicit --allow-fixture-adapter")
    if request["policy"]["network"] != "HOST_POLICY":
        receipt = nonexecution_receipt(
            request, descriptor, output, "SKIPPED_BY_POLICY", receipt_id,
            "local gateway cannot attest requested network isolation; physical runtime adapter required",
        )
        write_json_atomic(output / "receipt.json", receipt)
        return receipt, BAD

    ensure_request_subject(repo, request)
    output.mkdir(parents=True, exist_ok=False)
    canonical_request = output / "request.json"
    descriptor_path = output / "adapter.json"
    write_json_atomic(canonical_request, request)
    write_json_atomic(descriptor_path, descriptor)

    adapter_entry = module_root / descriptor["adapter_entry"]
    if not adapter_entry.is_file():
        raise ContractError(f"adapter entry is absent: {descriptor['adapter_entry']}")

    with tempfile.TemporaryDirectory(prefix=f"loopx-worker-{request['host_id']}.") as temp:
        temp_root = Path(temp)
        workspace = temp_root / "workspace"
        events_path = output / "events.jsonl"
        adapter_output = output / "adapter-output"
        adapter_output.mkdir(parents=True)
        run_git(repo, "worktree", "add", "--detach", str(workspace), request["subject"]["commit"])
        timed_out = False
        cancelled = False
        killed = False
        stdout = b""
        stderr = b""
        exit_code: int | None = None
        try:
            env = {
                "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
                "PYTHONUNBUFFERED": "1",
            }
            for key in request["policy"]["env_allowlist"]:
                if key in os.environ:
                    env[key] = os.environ[key]
            argv = [
                sys.executable,
                str(adapter_entry),
                "--request", str(canonical_request),
                "--workspace", str(workspace),
                "--events", str(events_path),
                "--output", str(adapter_output),
            ]
            process = subprocess.Popen(
                argv,
                cwd=workspace,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
            try:
                stdout, stderr = process.communicate(timeout=request["policy"]["timeout_ms"] / 1000)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                killed = True
                os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()
                exit_code = process.returncode
            maximum = request["policy"]["max_output_bytes"]
            if len(stdout) + len(stderr) > maximum:
                raise ContractError("Worker output exceeded the request budget")
            changes = changed_paths(workspace)
            if request["task"]["mode"] == "READ_ONLY" and changes:
                raise ContractError(f"read-only Worker changed paths: {changes}")
            unauthorized = [path for path in changes if not within_roots(path, request["workspace"]["writable_paths"])]
            if unauthorized:
                raise ContractError(f"Worker changed paths outside writable roots: {unauthorized}")

            events: list[dict[str, Any]] = []
            if events_path.exists():
                for index, line in enumerate(events_path.read_text(encoding="utf-8").splitlines()):
                    if not line.strip():
                        continue
                    value = json.loads(line)
                    events.append(validate_event(value, request, descriptor, index))
            if not events or events[-1]["kind"] != "PROCESS_EXIT":
                raise ContractError("Worker event stream lacks a terminal PROCESS_EXIT event")
            if events[-1]["payload"]["exit_code"] != exit_code:
                raise ContractError("Worker event exit code disagrees with the OS")

            stdout_ref = copy_artifact(stdout, output, "worker-stdout", "STDOUT", "worker-gateway", "text/plain")
            stderr_ref = copy_artifact(stderr, output, "worker-stderr", "STDERR", "worker-gateway", "text/plain")
            events_ref = copy_artifact(events_path.read_bytes(), output, "worker-events", "WORKER_EVENT", "worker-gateway", "application/x-ndjson")
            diff = run_git(workspace, "diff", "--binary", "HEAD", check=False).stdout.encode("utf-8")
            diff_ref = copy_artifact(diff, output, "worker-diff", "GIT_DIFF", "worker-gateway", "text/x-diff")
            artifacts = [stdout_ref, stderr_ref, events_ref, diff_ref]
            status = "PASS" if exit_code == 0 and not timed_out else "FAIL"
        finally:
            run_git(repo, "worktree", "remove", "--force", str(workspace), check=False)
            shutil.rmtree(workspace, ignore_errors=True)
        cleanup_state = "PASS" if not workspace.exists() else "FAIL"
        residue = [] if cleanup_state == "PASS" else ["workspace"]

    completeness = descriptor["trace_ceiling"]
    opaque = [] if completeness == "SOURCE_VERIFIED_INTERNAL" else ["hidden host/model internals remain UNKNOWN"]
    receipt = {
        "schema_version": "loopx/worker-receipt/v1",
        "receipt_id": receipt_id,
        "request_id": request["request_id"],
        "subject": copy.deepcopy(request["subject"]),
        "adapter": {
            "adapter_id": descriptor["adapter_id"],
            "host_id": descriptor["host_id"],
            "descriptor_digest": descriptor["content_digest"],
            "binary_identity": f"{descriptor['binary']} fixture-adapter" if descriptor["host_id"] == "fixture-host" else descriptor["binary"],
            "implementation_state": descriptor["implementation_state"],
        },
        "skill": {"name": request["skill"]["name"], "digest": request["skill"]["digest"]},
        "context": {"digest": request["context"]["digest"]},
        "status": status,
        "executed": True,
        "process": {
            "exit_code": exit_code,
            "timed_out": timed_out,
            "cancelled": cancelled,
            "process_group_killed": killed,
        },
        "trace": {
            "completeness": completeness,
            "events_digest": events_ref["digest"],
            "event_count": len(events),
            "opaque_segments": opaque,
        },
        "artifacts": artifacts,
        "cleanup": {"state": cleanup_state, "residue_paths": residue},
        "authority": copy.deepcopy(AUTHORITY_FALSE),
        "content_digest": None,
    }
    raw = copy.deepcopy(receipt)
    raw.pop("content_digest")
    receipt["content_digest"] = digest(raw)
    validate_receipt(receipt, request, descriptor)
    write_json_atomic(output / "receipt.json", receipt)
    return receipt, OK if status == "PASS" else BAD
