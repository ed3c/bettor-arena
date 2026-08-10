#!/usr/bin/env python3
"""Validate a per-request transmission admit, then call the fixed live loop."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from typing import Any


RISK_ACKNOWLEDGEMENT = (
    "I approve transmitting this digest-bound request, internal runtime/security "
    "architecture, and local path metadata to the logged-in Gemini service."
)


class ApprovalError(ValueError):
    pass


def canonical_digest(document: dict[str, Any], field: str) -> str:
    unsigned = dict(document)
    unsigned.pop(field, None)
    raw = json.dumps(
        unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def private_json(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ApprovalError(f"cannot inspect {label}: {exc.strerror}") from exc
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        raise ApprovalError(f"{label} must be a regular file, not a symlink")
    if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != 0o600:
        raise ApprovalError(f"{label} must be user-owned with mode 0600")
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ApprovalError(f"{label} is invalid JSON") from exc
    if not isinstance(value, dict):
        raise ApprovalError(f"{label} must be a JSON object")
    return value, raw


def validate_approval(request_path: Path, approval_path: Path) -> dict[str, Any]:
    request, request_raw = private_json(request_path, "equivalence request")
    approval, _ = private_json(approval_path, "external-transmission approval")
    if request.get("schema_version") != "technical-equivalence-request@1.0.0":
        raise ApprovalError("unsupported equivalence request schema")
    if request.get("request_digest") != canonical_digest(request, "request_digest"):
        raise ApprovalError("equivalence request digest mismatch")
    required = {
        "schema",
        "decision",
        "destination",
        "request_digest",
        "request_sha256",
        "risk_acknowledgement",
        "decided_by",
        "approved_at",
        "expires_at",
        "receipt_digest",
    }
    if set(approval) != required:
        raise ApprovalError("approval fields do not match the exact contract")
    expected = {
        "schema": "runtime-env/external-transmission-admit/v1",
        "decision": "APPROVE_EXTERNAL_TRANSMISSION",
        "destination": "https://gemini.google.com/",
        "request_digest": request["request_digest"],
        "request_sha256": "sha256:" + hashlib.sha256(request_raw).hexdigest(),
        "risk_acknowledgement": RISK_ACKNOWLEDGEMENT,
    }
    mismatches = [key for key, value in expected.items() if approval.get(key) != value]
    if (
        not isinstance(approval.get("decided_by"), str)
        or not approval["decided_by"].strip()
    ):
        mismatches.append("decided_by")
    if approval.get("receipt_digest") != canonical_digest(approval, "receipt_digest"):
        mismatches.append("receipt_digest")
    try:
        expires_at = datetime.fromisoformat(
            str(approval["expires_at"]).replace("Z", "+00:00")
        )
        approved_at = datetime.fromisoformat(
            str(approval["approved_at"]).replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ApprovalError("approval timestamps must be ISO-8601") from exc
    now = datetime.now(timezone.utc)
    if approved_at.tzinfo is None or expires_at.tzinfo is None:
        mismatches.append("timestamp-timezone")
    elif not approved_at <= now < expires_at:
        mismatches.append("approval-window")
    if mismatches:
        raise ApprovalError("approval mismatch: " + ", ".join(sorted(set(mismatches))))
    return request


def required_path(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        raise ApprovalError(f"{name} is required")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ApprovalError(f"{name} must be absolute")
    return path


def main() -> int:
    try:
        request_path = required_path("EQUIVALENCE_REQUEST_PATH")
        approval_path = required_path("EQUIVALENCE_APPROVAL_RECEIPT_PATH")
        run_root = required_path("EQUIVALENCE_RUN_ROOT")
        source_peer = required_path("ANTIGRAVITY_PEER")
        target_peer = required_path("SKILL_BETTOR_PEER")
        request = validate_approval(request_path, approval_path)
        run_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        metadata = run_root.stat()
        if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != 0o700:
            raise ApprovalError(
                "EQUIVALENCE_RUN_ROOT must be user-owned with mode 0700"
            )
        arena = Path(__file__).resolve().parents[2]
        command = [
            "sh",
            str(arena / "loopctl" / "loopctl.sh"),
            "equivalence",
            "run",
            "--request",
            str(request_path),
            "--target-peer",
            str(target_peer),
            "--source-peer",
            str(source_peer),
            "--execute-gemini",
            "--json",
        ]
        environment = dict(os.environ)
        environment["EQUIVALENCE_RUN_ROOT"] = str(run_root)
        result = subprocess.run(
            command,
            cwd=arena,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        envelope = json.loads(result.stdout) if result.stdout.strip() else {}
        summary = {
            "schema": "runtime-env/equivalence-live-receipt/v1",
            "status": "passed" if result.returncode == 0 else "failed",
            "exit": result.returncode,
            "request_digest": request["request_digest"],
            "destination": "https://gemini.google.com/",
            "artifacts": envelope.get("artifacts", []),
            "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
        }
        print(json.dumps(summary, sort_keys=True))
        return result.returncode
    except (ApprovalError, json.JSONDecodeError) as exc:
        print(f"equivalence live FATAL: {exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
