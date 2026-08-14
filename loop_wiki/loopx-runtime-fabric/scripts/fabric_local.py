#!/usr/bin/env python3
"""Local disposable-workspace adapter. Executes for real, and says what it cannot do.

This adapter's enforcement ceiling is low and stated plainly:

    filesystem   DECLARED_NOT_KERNEL_ENFORCED
    network      UNENFORCED
    memory/disk  NOT_OBSERVED

A local subprocess shares the host filesystem and network. The workspace is a
fresh temporary directory that is deleted afterwards, which makes it disposable
but not isolated. Declaring `network: deny` here would be a lie, so the request
validator refuses to accept the claim in the first place.

What this adapter *can* do honestly is detect violations after the fact:
residue outside the declared writable paths is found by walking the workspace
and comparing against what was declared. That is a real, physically observable
control -- the process really runs, really writes, and the check really finds
it -- rather than a fixture asserting that a rule exists.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from fabric_common import (
    ContractError,
    ProviderUnavailable,
    file_digest,
)

ADAPTER_ID = "local-disposable-workspace"
PROVIDER_ID = "local-process"

# Said once, here, and copied onto every receipt. A ceiling that lives only in
# documentation is a ceiling nobody reads at the moment it matters.
ENFORCEMENT_CEILING = {
    "filesystem": "DECLARED_NOT_KERNEL_ENFORCED",
    "network": "UNENFORCED",
    "process_group": "ENFORCED",
    "timeout": "ENFORCED",
    "output_bytes": "ENFORCED",
    "memory_bytes": "NOT_OBSERVED",
    "disk_bytes": "NOT_OBSERVED",
}


def materialize(source: Path, request: dict[str, Any]) -> Path:
    """Copy the declared paths into a fresh workspace.

    Copied rather than mounted or symlinked: a symlink into the owner's live
    checkout would let a Worker edit the developer's working tree, which is the
    failure `workspace points to owner live checkout` names.
    """
    workspace = Path(tempfile.mkdtemp(prefix="loopx-fabric-"))
    for rel in (
        request["workspace"]["read_only_paths"] + request["workspace"]["writable_paths"]
    ):
        src = source / rel
        dst = workspace / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        elif src.is_file():
            shutil.copy2(src, dst)
        else:
            dst.mkdir(parents=True, exist_ok=True)
    return workspace


def _declared_writable_prefixes(request: dict[str, Any]) -> list[str]:
    return [p.rstrip("/") for p in request["workspace"]["writable_paths"]]


def scan_residue(
    workspace: Path, request: dict[str, Any], before: set[str]
) -> list[str]:
    """Files that appeared outside the declared writable paths.

    This is the adapter's honest isolation control: it cannot stop the write,
    but it can refuse to call the run clean afterwards.
    """
    writable = _declared_writable_prefixes(request)
    residue: list[str] = []
    for path in sorted(workspace.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(workspace).as_posix()
        if rel in before:
            continue
        if any(rel == w or rel.startswith(w + "/") for w in writable):
            continue
        residue.append(rel)
    return residue


def snapshot(workspace: Path) -> set[str]:
    return {
        path.relative_to(workspace).as_posix()
        for path in workspace.rglob("*")
        if path.is_file()
    }


def execute(source: Path, request: dict[str, Any]) -> dict[str, Any]:
    """Run the workload for real and return an observation, never a verdict."""
    if not source.is_dir():
        raise ProviderUnavailable(f"source checkout absent: {source}")

    workspace = materialize(source, request)
    before = snapshot(workspace)
    process = request["process"]
    started = time.monotonic()

    try:
        completed = subprocess.run(
            process["argv"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=process["timeout_ms"] / 1000,
            # A new process group, so a timeout can take the children with it
            # instead of orphaning them onto the host.
            start_new_session=True,
            env={"PATH": os.environ.get("PATH", "")},
        )
        exit_code: int | None = completed.returncode
        stdout = completed.stdout
        timed_out = False
    except subprocess.TimeoutExpired as expired:
        exit_code = None
        stdout = expired.stdout or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        timed_out = True
    except (OSError, ValueError) as exc:
        shutil.rmtree(workspace, ignore_errors=True)
        raise ProviderUnavailable(
            f"local adapter could not start the process: {exc}"
        ) from exc

    elapsed_ms = int((time.monotonic() - started) * 1000)
    output_bytes = len(stdout.encode("utf-8"))
    output_overflow = output_bytes > process["max_output_bytes"]

    residue = scan_residue(workspace, request, before)

    artifacts = []
    for rel in request["artifacts"]["expected_paths"]:
        path = workspace / rel
        if path.is_file():
            artifacts.append(
                {"path": rel, "digest": file_digest(path), "bytes": path.stat().st_size}
            )
    missing = sorted(
        set(request["artifacts"]["expected_paths"]) - {a["path"] for a in artifacts}
    )

    # Cleanup, then verify it. "cleanup: PASS" emitted without looking is the
    # control `cleanup says PASS with residue` names.
    shutil.rmtree(workspace, ignore_errors=True)
    cleanup_status = "PASS" if not workspace.exists() else "FAIL"

    return {
        "adapter_id": ADAPTER_ID,
        "provider_id": PROVIDER_ID,
        "enforcement_ceiling": dict(ENFORCEMENT_CEILING),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "elapsed_ms": elapsed_ms,
        "output_bytes": output_bytes,
        "output_overflow": output_overflow,
        "artifacts": sorted(artifacts, key=lambda a: a["path"]),
        "missing_artifacts": missing,
        "residue_paths": residue,
        "cleanup_status": cleanup_status,
        "workspace_removed": not workspace.exists(),
    }


def classify(observation: dict[str, Any]) -> str:
    """Turn an observation into a failure class, or PASS.

    Order matters. Residue and missing artifacts are checked before the exit
    code, because a process that exits 0 while writing outside its declared
    paths has not passed -- it has failed in a way that exit codes cannot see.
    """
    if observation["residue_paths"]:
        return "POLICY_REFUSAL"
    if observation["cleanup_status"] != "PASS":
        return "POLICY_REFUSAL"
    if observation["output_overflow"]:
        return "POLICY_REFUSAL"
    if observation["timed_out"]:
        return "TASK_FAILURE"
    if observation["missing_artifacts"]:
        return "TASK_FAILURE"
    if observation["exit_code"] != 0:
        return "TASK_FAILURE"
    return "PASS"


def emit_receipt(
    request: dict[str, Any], lease: dict[str, Any], observation: dict[str, Any]
) -> dict[str, Any]:
    outcome = classify(observation)
    if outcome != "PASS" and outcome not in {"TASK_FAILURE", "POLICY_REFUSAL"}:
        raise ContractError(f"unclassifiable outcome {outcome!r}")
    return {
        "schema_version": "loopx/runtime-receipt/v1",
        "receipt_id": f"rcpt-{request['request_id']}",
        "request_id": request["request_id"],
        "lease_id": lease["lease_id"],
        "subject": request["subject"],
        "provider": {
            "provider_id": observation["provider_id"],
            "adapter_id": observation["adapter_id"],
            "runtime_identity": request["provider"]["runtime_identity"],
        },
        "enforcement_ceiling": observation["enforcement_ceiling"],
        "network": {
            "requested": request["network"]["requested"],
            "attested": request["network"]["attested"],
        },
        "execution": {
            "exit_code": observation["exit_code"],
            "timed_out": observation["timed_out"],
            "elapsed_ms": observation["elapsed_ms"],
            "output_bytes": observation["output_bytes"],
        },
        "artifacts": observation["artifacts"],
        "missing_artifacts": observation["missing_artifacts"],
        "cleanup": {
            "status": observation["cleanup_status"],
            "residue_paths": observation["residue_paths"],
            "workspace_removed": observation["workspace_removed"],
        },
        "outcome": outcome,
        # A runtime observes. It never decides a gate.
        "authority": "OBSERVATION_ONLY",
        "canonical_writer": "LOOPX_LEDGER_REDUCER",
    }
