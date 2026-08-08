#!/usr/bin/env python3
"""Profile-driven, fail-closed migration for repository MCP configuration.

The engine owns migration mechanics only.  Repository profiles remain the
policy source of truth, and human host approval is deliberately not automated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SECRET_KEY = re.compile(r"(?:api[_-]?key|token|secret|password)", re.IGNORECASE)
SAFE_SECRET_REFERENCE = re.compile(
    r"^(?:\$\{?[A-Za-z_][A-Za-z0-9_]*\}?|env:[A-Za-z_][A-Za-z0-9_]*)$"
)
TEXT_SECRET_ASSIGNMENT = re.compile(
    r"(?im)^\s*(?:--)?[A-Za-z0-9_-]*(?:api[_-]?key|token|secret|password)"
    r"[A-Za-z0-9_-]*\s*(?:=|:)\s*"
    r"[\"']?([^\s\"']+)"
)
TEXT_SECRET_ARGUMENT = re.compile(
    r"(?im)(?:^|\s)--[A-Za-z0-9_-]*(?:api[_-]?key|token|secret|password)"
    r"[A-Za-z0-9_-]*\s+"
    r"[\"']?([^\s\"']+)"
)
PROFILE_REQUIRED = {
    "schema_version",
    "repo_id",
    "engine_sha256",
    "managed_files",
    "mirrors",
    "capabilities",
    "probes",
    "human_gates",
}
PROFILE_FIELDS = PROFILE_REQUIRED | {
    "protected_branches",
    "receipt_dir",
    "backup_dir",
    "forbidden_paths",
}
MANAGED_FILE_FIELDS = {"path", "format", "contains", "secret_scan"}
MIRROR_FIELDS = {"source", "target", "comparison"}
CAPABILITY_FIELDS = {
    "id",
    "registration",
    "surface_residency",
    "payload_residency",
    "heavy_executor",
}
PROBE_FIELDS = {"id", "argv", "cwd", "timeout_sec", "env"}
HUMAN_GATE_FIELDS = {"id", "description"}


class MigrationError(RuntimeError):
    """A fail-closed migration or verification error with a useful diagnosis."""


@dataclass(frozen=True)
class Profile:
    root: Path
    path: Path
    payload: dict[str, Any]


@dataclass(frozen=True)
class PlanItem:
    source: str
    target: str
    comparison: str
    status: str
    source_sha256: str
    target_sha256: str | None


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise MigrationError(message)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _repo_path(root: Path, relative: str, *, must_exist: bool = False) -> Path:
    _require(
        isinstance(relative, str) and relative not in {"", "."},
        "profile path must be non-empty",
    )
    candidate = root / relative
    resolved = candidate.resolve(strict=must_exist)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise MigrationError(f"profile path escapes repository: {relative}") from exc
    _require(
        not candidate.is_symlink(), f"profile path must not be a symlink: {relative}"
    )
    return resolved


def _git(
    root: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            check=check,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = (
            exc.stderr.strip()
            if isinstance(exc, subprocess.CalledProcessError)
            else str(exc)
        )
        raise MigrationError(f"git {' '.join(args)} failed: {detail}") from exc


def _git_info(root: Path) -> dict[str, Any]:
    commit = _git(root, "rev-parse", "HEAD").stdout.strip()
    branch = _git(root, "branch", "--show-current").stdout.strip()
    dirty = bool(_git(root, "status", "--porcelain").stdout.strip())
    return {"commit": commit, "branch": branch or None, "dirty": dirty}


def _validate_residency(capabilities: Any) -> None:
    _require(isinstance(capabilities, list), "capabilities must be a list")
    seen: set[str] = set()
    for capability in capabilities:
        _require(isinstance(capability, dict), "each capability must be an object")
        capability_id = capability.get("id")
        _require(
            isinstance(capability_id, str) and capability_id,
            "capability id is required",
        )
        _require(capability_id not in seen, f"duplicate capability id: {capability_id}")
        seen.add(capability_id)
        registration = capability.get("registration")
        surface = capability.get("surface_residency")
        payload = capability.get("payload_residency")
        _require(
            registration in {"always", "project_scoped", "on_demand"},
            f"invalid registration policy for {capability_id}: {registration}",
        )
        _require(
            surface in {"resident", "session_scoped", "on_demand"},
            f"invalid surface residency for {capability_id}: {surface}",
        )
        _require(
            payload in {"demand_pull", "on_demand", "session_scoped", "resident"},
            f"invalid payload residency for {capability_id}: {payload}",
        )
        if capability.get("heavy_executor") is True:
            _require(
                payload != "resident",
                f"heavy executor payload must not be resident: {capability_id}",
            )


def load_profile(repo_root: Path, profile_path: Path) -> Profile:
    root = repo_root.resolve(strict=True)
    _require((root / ".git").exists(), f"repository root has no .git entry: {root}")
    try:
        raw_path = profile_path if profile_path.is_absolute() else root / profile_path
        resolved_path = raw_path.resolve(strict=True)
        path = _repo_path(root, str(resolved_path.relative_to(root)), must_exist=True)
    except ValueError as exc:
        raise MigrationError(
            f"profile path escapes repository: {profile_path}"
        ) from exc
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MigrationError(f"cannot parse migration profile {path}: {exc}") from exc
    _require(isinstance(payload, dict), "migration profile must be a JSON object")
    missing_fields = sorted(PROFILE_REQUIRED - set(payload))
    unknown_fields = sorted(set(payload) - PROFILE_FIELDS)
    _require(not missing_fields, f"missing required profile fields: {missing_fields}")
    _require(not unknown_fields, f"unknown profile fields: {unknown_fields}")
    _require(
        payload.get("schema_version") == SCHEMA_VERSION,
        "unsupported migration profile schema",
    )
    _require(
        isinstance(payload.get("repo_id"), str) and payload["repo_id"],
        "repo_id is required",
    )
    engine_sha256 = payload.get("engine_sha256")
    _require(
        isinstance(engine_sha256, str) and re.fullmatch(r"[0-9a-f]{64}", engine_sha256),
        "engine_sha256 must be a lowercase SHA-256",
    )
    _require(
        engine_sha256 == _sha256_file(Path(__file__).resolve()),
        "migration engine hash mismatch",
    )
    _require(
        isinstance(payload.get("protected_branches", []), list),
        "protected_branches must be a list",
    )
    _repo_path(root, payload.get("receipt_dir", "mcp/production/receipts"))
    _repo_path(root, payload.get("backup_dir", ".mcp-production/backups"))

    managed = payload.get("managed_files", [])
    _require(isinstance(managed, list), "managed_files must be a list")
    for item in managed:
        _require(isinstance(item, dict), "each managed file must be an object")
        _require(
            not (set(item) - MANAGED_FILE_FIELDS),
            f"unknown managed file fields: {sorted(set(item) - MANAGED_FILE_FIELDS)}",
        )
        _require(
            {"path", "format"} <= set(item), "managed file requires path and format"
        )
        _repo_path(root, item.get("path", ""))
        _require(
            item.get("format", "text") in {"json", "toml", "text"},
            "unsupported file format",
        )
        contains = item.get("contains", [])
        _require(
            isinstance(contains, list)
            and all(isinstance(value, str) for value in contains),
            "contains must be a string list",
        )
        _require(
            isinstance(item.get("secret_scan", True), bool),
            "secret_scan must be boolean",
        )

    mirrors = payload.get("mirrors", [])
    _require(isinstance(mirrors, list), "mirrors must be a list")
    for item in mirrors:
        _require(isinstance(item, dict), "each mirror must be an object")
        _require(
            set(item) == MIRROR_FIELDS,
            f"mirror fields must be exactly: {sorted(MIRROR_FIELDS)}",
        )
        _repo_path(root, item.get("source", ""))
        _repo_path(root, item.get("target", ""))
        _require(
            item.get("comparison", "bytes") in {"bytes", "json"},
            "unsupported mirror comparison",
        )

    forbidden = payload.get("forbidden_paths", [])
    _require(isinstance(forbidden, list), "forbidden_paths must be a list")
    for relative in forbidden:
        _repo_path(root, relative)

    probes = payload.get("probes", [])
    _require(isinstance(probes, list), "probes must be a list")
    probe_ids: set[str] = set()
    for probe in probes:
        _require(isinstance(probe, dict), "each probe must be an object")
        _require(
            not (set(probe) - PROBE_FIELDS),
            f"unknown probe fields: {sorted(set(probe) - PROBE_FIELDS)}",
        )
        _require(
            {"id", "argv", "cwd", "timeout_sec"} <= set(probe),
            "probe is missing required fields",
        )
        probe_id = probe.get("id")
        argv = probe.get("argv")
        _require(isinstance(probe_id, str) and probe_id, "probe id is required")
        _require(probe_id not in probe_ids, f"duplicate probe id: {probe_id}")
        probe_ids.add(probe_id)
        _require(
            isinstance(argv, list)
            and argv
            and all(isinstance(value, str) for value in argv),
            f"probe argv must be a non-empty string list: {probe_id}",
        )
        _repo_path(
            root,
            probe.get("cwd", ".")
            if probe.get("cwd", ".") != "."
            else "__root_marker__",
        )
        timeout = probe.get("timeout_sec")
        _require(
            isinstance(timeout, (int, float)) and 0 < timeout <= 3600,
            f"invalid probe timeout: {probe_id}",
        )

    gates = payload.get("human_gates", [])
    _require(isinstance(gates, list), "human_gates must be a list")
    gate_ids: set[str] = set()
    for gate in gates:
        _require(
            isinstance(gate, dict) and isinstance(gate.get("id"), str),
            "human gate id is required",
        )
        _require(
            set(gate) == HUMAN_GATE_FIELDS,
            f"human gate fields must be exactly: {sorted(HUMAN_GATE_FIELDS)}",
        )
        _require(gate["id"] not in gate_ids, f"duplicate human gate id: {gate['id']}")
        gate_ids.add(gate["id"])

    for capability in payload.get("capabilities", []):
        _require(
            isinstance(capability, dict) and set(capability) == CAPABILITY_FIELDS,
            f"capability fields must be exactly: {sorted(CAPABILITY_FIELDS)}",
        )
    _validate_residency(payload.get("capabilities", []))
    _scan_secret_literals(payload)
    return Profile(root=root, path=path, payload=payload)


def _equivalent(source: Path, target: Path, comparison: str) -> bool:
    if not target.exists():
        return False
    if comparison == "bytes":
        return source.read_bytes() == target.read_bytes()
    try:
        return json.loads(source.read_text(encoding="utf-8")) == json.loads(
            target.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as exc:
        raise MigrationError(
            f"cannot compare JSON mirror {source} -> {target}: {exc}"
        ) from exc


def build_plan(profile: Profile) -> list[PlanItem]:
    plan: list[PlanItem] = []
    for mirror in profile.payload.get("mirrors", []):
        source = _repo_path(profile.root, mirror["source"], must_exist=True)
        target = _repo_path(profile.root, mirror["target"])
        comparison = mirror.get("comparison", "bytes")
        plan.append(
            PlanItem(
                source=mirror["source"],
                target=mirror["target"],
                comparison=comparison,
                status="in_sync"
                if _equivalent(source, target, comparison)
                else "drift",
                source_sha256=_sha256_file(source),
                target_sha256=_sha256_file(target) if target.exists() else None,
            )
        )
    return plan


def _assert_mutation_branch(profile: Profile) -> None:
    branch = _git_info(profile.root)["branch"]
    protected = set(profile.payload.get("protected_branches", []))
    _require(branch is not None, "apply and rollback require a named Git branch")
    _require(
        branch not in protected, f"refusing mutation on protected branch: {branch}"
    )


def _assert_clean_destination(profile: Profile, relative: str) -> None:
    status = _git(profile.root, "status", "--porcelain", "--", relative).stdout.strip()
    _require(not status, f"refusing to overwrite dirty destination: {relative}")


def _open_parent_dir(repo_root: Path, path: Path) -> tuple[int, str]:
    root = repo_root.resolve(strict=True)
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise MigrationError(f"write path escapes repository: {path}") from exc
    _require(relative.name not in {"", ".", ".."}, f"invalid write path: {path}")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    directory_fd = os.open("/", flags)
    try:
        for component in root.parts[1:]:
            next_fd = os.open(component, flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        for component in relative.parts[:-1]:
            try:
                os.mkdir(component, 0o755, dir_fd=directory_fd)
            except FileExistsError:
                pass
            next_fd = os.open(component, flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
    except OSError as exc:
        os.close(directory_fd)
        raise MigrationError(
            f"write directory contains a symlink or is unsafe: {path.parent}"
        ) from exc
    return directory_fd, relative.name


def _atomic_write(repo_root: Path, path: Path, payload: bytes) -> str:
    directory_fd, target_name = _open_parent_dir(repo_root, path)
    directory_identity = os.fstat(directory_fd)
    temp_name = f".mcp-migrate-{os.getpid()}-{time.time_ns()}"
    try:
        file_fd = os.open(
            temp_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=directory_fd,
        )
        with os.fdopen(file_fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(
            temp_name,
            target_name,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
        os.fsync(directory_fd)
        _assert_parent_binding(repo_root, path, directory_identity, target_name)
        target_fd = os.open(
            target_name,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=directory_fd,
        )
        with os.fdopen(target_fd, "rb") as handle:
            written = handle.read()
        _require(written == payload, f"atomic write verification failed: {path}")
        return _sha256_bytes(written)
    finally:
        try:
            os.unlink(temp_name, dir_fd=directory_fd)
        except FileNotFoundError:
            pass
        os.close(directory_fd)


def _assert_parent_binding(
    repo_root: Path,
    path: Path,
    expected_identity: os.stat_result,
    expected_name: str,
) -> None:
    try:
        verification_fd, verification_name = _open_parent_dir(repo_root, path)
    except MigrationError as exc:
        raise MigrationError(
            f"write namespace changed during publication: {path}"
        ) from exc
    try:
        verification_identity = os.fstat(verification_fd)
        _require(
            (expected_identity.st_dev, expected_identity.st_ino)
            == (verification_identity.st_dev, verification_identity.st_ino),
            f"write namespace changed during publication: {path}",
        )
        _require(verification_name == expected_name, f"write target changed: {path}")
    finally:
        os.close(verification_fd)


def _exclusive_write(repo_root: Path, path: Path, payload: bytes, mode: int) -> None:
    directory_fd, target_name = _open_parent_dir(repo_root, path)
    directory_identity = os.fstat(directory_fd)
    temp_name = f".mcp-receipt-{os.getpid()}-{time.time_ns()}.tmp"
    temp_created = False
    published = False
    try:
        file_fd = os.open(
            temp_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            mode,
            dir_fd=directory_fd,
        )
        temp_created = True
        with os.fdopen(file_fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        _assert_parent_binding(repo_root, path, directory_identity, target_name)
        try:
            os.link(
                temp_name,
                target_name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
                follow_symlinks=False,
            )
        except FileExistsError as exc:
            raise MigrationError(f"append-only receipt collision: {path}") from exc
        published = True
        os.unlink(temp_name, dir_fd=directory_fd)
        temp_created = False
        os.fsync(directory_fd)
        _assert_parent_binding(repo_root, path, directory_identity, target_name)
    except BaseException:
        cleanup_errors: list[str] = []
        if published:
            try:
                os.unlink(target_name, dir_fd=directory_fd)
            except OSError as cleanup_exc:
                cleanup_errors.append(str(cleanup_exc))
        if temp_created:
            try:
                os.unlink(temp_name, dir_fd=directory_fd)
            except OSError as cleanup_exc:
                cleanup_errors.append(str(cleanup_exc))
        try:
            os.fsync(directory_fd)
        except OSError as cleanup_exc:
            cleanup_errors.append(str(cleanup_exc))
        if cleanup_errors:
            raise MigrationError(
                f"incomplete receipt cleanup failed: {path}: {cleanup_errors}"
            )
        raise
    finally:
        os.close(directory_fd)


def _new_run_id(action: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    suffix = _sha256_bytes(f"{action}:{time.time_ns()}:{os.getpid()}".encode())[:10]
    return f"{stamp}-{action}-{suffix}"


def write_receipt(profile: Profile, action: str, details: dict[str, Any]) -> Path:
    _assert_mutation_branch(profile)
    receipt_dir = _repo_path(
        profile.root,
        profile.payload.get("receipt_dir", "mcp/production/receipts"),
    )
    receipt_dir.mkdir(parents=True, exist_ok=True)
    _require(not receipt_dir.is_symlink(), "receipt directory must not be a symlink")
    existing = sorted(receipt_dir.glob("*.json"))
    previous = _sha256_file(existing[-1]) if existing else None
    run_id = _new_run_id(action)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "action": action,
        "repo_id": profile.payload["repo_id"],
        "git": _git_info(profile.root),
        "profile_path": str(profile.path.relative_to(profile.root)),
        "profile_sha256": _sha256_file(profile.path),
        "previous_receipt_sha256": previous,
        "details": details,
    }
    path = receipt_dir / f"{run_id}.json"
    encoded = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _exclusive_write(profile.root, path, encoded, 0o444)
    return path


def check_receipt_chain(profile: Profile) -> dict[str, Any]:
    receipt_dir = _repo_path(
        profile.root,
        profile.payload.get("receipt_dir", "mcp/production/receipts"),
    )
    if not receipt_dir.exists():
        return {"status": "pass", "receipt_count": 0, "tip_sha256": None}
    previous: str | None = None
    count = 0
    for path in sorted(receipt_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise MigrationError(f"invalid receipt {path}: {exc}") from exc
        _require(
            payload.get("previous_receipt_sha256") == previous,
            f"broken receipt chain at {path.name}",
        )
        _require(
            payload.get("repo_id") == profile.payload["repo_id"],
            f"receipt repo mismatch: {path.name}",
        )
        previous = _sha256_file(path)
        count += 1
    return {"status": "pass", "receipt_count": count, "tip_sha256": previous}


def apply_plan(profile: Profile) -> list[PlanItem]:
    _assert_mutation_branch(profile)
    initial_plan = build_plan(profile)
    changes = [item for item in initial_plan if item.status == "drift"]
    for item in changes:
        _assert_clean_destination(profile, item.target)

    run_id = _new_run_id("backup")
    backup_root = (
        _repo_path(
            profile.root,
            profile.payload.get("backup_dir", ".mcp-production/backups"),
        )
        / run_id
    )
    prepared: list[dict[str, Any]] = []
    for item in changes:
        source = _repo_path(profile.root, item.source, must_exist=True)
        target = _repo_path(profile.root, item.target)
        before_exists = target.exists()
        before_content = target.read_bytes() if before_exists else b""
        backup_relative: str | None = None
        if before_exists:
            backup = backup_root / item.target
            _atomic_write(profile.root, backup, before_content)
            backup_relative = str(backup.relative_to(profile.root))
        prepared.append(
            {
                "item": item,
                "source_content": source.read_bytes(),
                "target": target,
                "before_exists": before_exists,
                "before_content": before_content,
                "backup": backup_relative,
            }
        )

    receipt_changes: list[dict[str, Any]] = []
    applied: list[PlanItem] = []
    written: list[dict[str, Any]] = []
    prepared_by_target = {entry["item"].target: entry for entry in prepared}
    try:
        for item in initial_plan:
            if item.status != "drift":
                applied.append(item)
                continue
            entry = prepared_by_target[item.target]
            target = entry["target"]
            after_sha = _atomic_write(profile.root, target, entry["source_content"])
            written.append(entry)
            receipt_changes.append(
                {
                    "target": item.target,
                    "before_exists": entry["before_exists"],
                    "before_sha256": item.target_sha256,
                    "after_sha256": after_sha,
                    "backup": entry["backup"],
                }
            )
            applied.append(
                PlanItem(
                    source=item.source,
                    target=item.target,
                    comparison=item.comparison,
                    status="applied",
                    source_sha256=item.source_sha256,
                    target_sha256=after_sha,
                )
            )
        write_receipt(profile, "apply", {"changes": receipt_changes})
    except Exception as exc:
        restore_errors: list[str] = []
        for entry in reversed(written):
            try:
                if entry["before_exists"]:
                    _atomic_write(
                        profile.root, entry["target"], entry["before_content"]
                    )
                else:
                    entry["target"].unlink(missing_ok=True)
            except OSError as restore_exc:
                restore_errors.append(f"{entry['item'].target}: {restore_exc}")
        if restore_errors:
            raise MigrationError(
                f"apply transaction failed ({exc}); restoration also failed: {restore_errors}"
            ) from exc
        raise MigrationError(
            f"apply transaction failed and was restored: {exc}"
        ) from exc
    return applied


def _scan_secret_literals(value: Any, location: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location}.{key}"
            if SECRET_KEY.search(str(key)) and isinstance(child, str) and child:
                _require(
                    SAFE_SECRET_REFERENCE.fullmatch(child) is not None,
                    f"secret-like literal is forbidden at {child_location}",
                )
            _scan_secret_literals(child, child_location)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            if (
                isinstance(child, str)
                and SECRET_KEY.search(child.lstrip("-"))
                and index + 1 < len(value)
                and isinstance(value[index + 1], str)
                and not value[index + 1].startswith("-")
            ):
                _require(
                    SAFE_SECRET_REFERENCE.fullmatch(value[index + 1]) is not None,
                    f"secret-like literal is forbidden at {location}[{index + 1}]",
                )
            _scan_secret_literals(child, f"{location}[{index}]")


def _scan_text_secret_literals(text: str, location: str) -> None:
    for pattern in (TEXT_SECRET_ASSIGNMENT, TEXT_SECRET_ARGUMENT):
        for match in pattern.finditer(text):
            value = match.group(1)
            _require(
                SAFE_SECRET_REFERENCE.fullmatch(value) is not None,
                f"secret-like literal is forbidden at {location}",
            )


def _validate_managed_file(profile: Profile, item: dict[str, Any]) -> dict[str, Any]:
    path = _repo_path(profile.root, item["path"], must_exist=True)
    _require(path.is_file(), f"managed path is not a file: {item['path']}")
    text = path.read_text(encoding="utf-8")
    file_format = item.get("format", "text")
    parsed: Any = text
    try:
        if file_format == "json":
            parsed = json.loads(text)
        elif file_format == "toml":
            parsed = tomllib.loads(text)
    except (json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        raise MigrationError(
            f"invalid {file_format} file {item['path']}: {exc}"
        ) from exc
    if file_format in {"json", "toml"} and item.get("secret_scan", True):
        _scan_secret_literals(parsed)
    elif file_format == "text" and item.get("secret_scan", True):
        _scan_text_secret_literals(text, item["path"])
    for required_text in item.get("contains", []):
        _require(
            required_text in text,
            f"managed file {item['path']} is missing required text: {required_text}",
        )
    return {"path": item["path"], "sha256": _sha256_file(path), "status": "pass"}


def _expand(value: str, profile: Profile) -> str:
    return value.replace("{repo_root}", str(profile.root)).replace(
        "{python}", sys.executable
    )


def _run_probe(profile: Profile, probe: dict[str, Any]) -> dict[str, Any]:
    argv = [_expand(value, profile) for value in probe["argv"]]
    cwd_value = probe.get("cwd", ".")
    cwd = (
        profile.root
        if cwd_value == "."
        else _repo_path(profile.root, cwd_value, must_exist=True)
    )
    env = os.environ.copy()
    for key, value in probe.get("env", {}).items():
        _require(
            isinstance(key, str) and isinstance(value, str),
            f"invalid probe env: {probe['id']}",
        )
        _require(
            not SECRET_KEY.search(key),
            f"probe profile must not carry secret env: {key}",
        )
        env[key] = _expand(value, profile)
    started = time.monotonic()
    try:
        result = subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            capture_output=True,
            check=False,
            timeout=float(probe["timeout_sec"]),
        )
    except subprocess.TimeoutExpired:
        return {
            "id": probe["id"],
            "status": "fail",
            "reason": "timeout",
            "duration_ms": round((time.monotonic() - started) * 1000),
        }
    except OSError as exc:
        return {
            "id": probe["id"],
            "status": "fail",
            "reason": f"start failed: {exc}",
            "duration_ms": round((time.monotonic() - started) * 1000),
        }
    return {
        "id": probe["id"],
        "status": "pass" if result.returncode == 0 else "fail",
        "returncode": result.returncode,
        "stdout_sha256": _sha256_bytes(result.stdout),
        "stderr_sha256": _sha256_bytes(result.stderr),
        "duration_ms": round((time.monotonic() - started) * 1000),
    }


def verify_profile(profile: Profile, *, run_probes: bool) -> dict[str, Any]:
    forbidden_present = [
        relative
        for relative in profile.payload.get("forbidden_paths", [])
        if _repo_path(profile.root, relative).exists()
    ]
    _require(not forbidden_present, f"forbidden MCP paths exist: {forbidden_present}")
    files = [
        _validate_managed_file(profile, item)
        for item in profile.payload.get("managed_files", [])
    ]
    plan = build_plan(profile)
    drift = [item.target for item in plan if item.status != "in_sync"]
    _require(not drift, f"MCP configuration mirror drift: {drift}")
    chain = check_receipt_chain(profile)
    probes = (
        [_run_probe(profile, probe) for probe in profile.payload.get("probes", [])]
        if run_probes
        else []
    )
    probe_failed = any(item["status"] != "pass" for item in probes)
    post_probe_files: list[dict[str, Any]] = []
    post_probe_plan: list[PlanItem] = []
    post_probe_error = ""
    post_probe_forbidden: list[str] = []
    post_probe_chain = chain
    if run_probes:
        try:
            post_probe_files = [
                _validate_managed_file(profile, item)
                for item in profile.payload.get("managed_files", [])
            ]
            post_probe_plan = build_plan(profile)
        except (
            MigrationError,
            OSError,
            json.JSONDecodeError,
            tomllib.TOMLDecodeError,
        ) as exc:
            post_probe_error = str(exc)
        post_probe_forbidden = [
            relative
            for relative in profile.payload.get("forbidden_paths", [])
            if _repo_path(profile.root, relative).exists()
        ]
        try:
            post_probe_chain = check_receipt_chain(profile)
        except MigrationError as exc:
            post_probe_chain = {"status": "fail", "error": str(exc)}
    post_probe_failed = (
        bool(post_probe_error)
        or bool(post_probe_forbidden)
        or post_probe_chain.get("status") != "pass"
        or any(item.status != "in_sync" for item in post_probe_plan)
    )
    gates = [
        {
            "id": gate["id"],
            "description": gate.get("description", ""),
            "status": "pending",
            "automatable": False,
        }
        for gate in profile.payload.get("human_gates", [])
    ]
    if not run_probes and profile.payload.get("probes"):
        status = "not_run"
    elif probe_failed or post_probe_failed:
        status = "fail"
    elif gates:
        status = "technical_pass_human_pending"
    else:
        status = "technical_pass"
    return {
        "status": status,
        "repo_id": profile.payload["repo_id"],
        "git": _git_info(profile.root),
        "managed_files": files,
        "mirrors": [item.__dict__ for item in plan],
        "capabilities": profile.payload.get("capabilities", []),
        "probes": probes,
        "post_probe_managed_files": post_probe_files,
        "post_probe_mirrors": [item.__dict__ for item in post_probe_plan],
        "post_probe_error": post_probe_error or None,
        "post_probe_forbidden_paths": post_probe_forbidden,
        "post_probe_receipt_chain": post_probe_chain,
        "human_gates": gates,
        "receipt_chain": chain,
    }


def rollback(profile: Profile, receipt_path: Path) -> Path:
    _assert_mutation_branch(profile)
    raw_path = (
        receipt_path if receipt_path.is_absolute() else profile.root / receipt_path
    )
    try:
        resolved_path = raw_path.resolve(strict=True)
        path = _repo_path(
            profile.root,
            str(resolved_path.relative_to(profile.root)),
            must_exist=True,
        )
    except ValueError as exc:
        raise MigrationError(
            f"rollback receipt escapes repository: {receipt_path}"
        ) from exc
    receipt_dir = _repo_path(
        profile.root,
        profile.payload.get("receipt_dir", "mcp/production/receipts"),
    )
    _require(
        path.parent == receipt_dir,
        "rollback receipt is outside the configured receipt directory",
    )
    _require(
        path in sorted(receipt_dir.glob("*.json")),
        "rollback receipt is not in the receipt chain",
    )
    check_receipt_chain(profile)
    payload = json.loads(path.read_text(encoding="utf-8"))
    _require(payload.get("action") == "apply", "rollback requires an apply receipt")
    _require(
        payload.get("repo_id") == profile.payload["repo_id"],
        "rollback receipt repo mismatch",
    )
    _require(
        payload.get("profile_sha256") == _sha256_file(profile.path),
        "rollback receipt profile hash mismatch",
    )
    restored: list[dict[str, Any]] = []
    for change in payload.get("details", {}).get("changes", []):
        target = _repo_path(profile.root, change["target"])
        _require(target.exists(), f"rollback target is missing: {change['target']}")
        _require(
            _sha256_file(target) == change["after_sha256"],
            f"rollback target changed after apply: {change['target']}",
        )
        if change["before_exists"]:
            backup_value = change.get("backup")
            _require(
                isinstance(backup_value, str),
                f"rollback backup missing: {change['target']}",
            )
            backup = _repo_path(profile.root, backup_value, must_exist=True)
            _require(
                _sha256_file(backup) == change["before_sha256"],
                f"rollback backup hash mismatch: {change['target']}",
            )
            _atomic_write(profile.root, target, backup.read_bytes())
        else:
            target.unlink()
        restored.append(
            {"target": change["target"], "restored_sha256": change["before_sha256"]}
        )
    return write_receipt(
        profile,
        "rollback",
        {"apply_receipt": str(path.relative_to(profile.root)), "restored": restored},
    )


def _profile_from_args(args: argparse.Namespace) -> Profile:
    root = Path(args.repo_root).resolve()
    profile_path = Path(args.profile)
    if not profile_path.is_absolute():
        profile_path = root / profile_path
    return load_profile(root, profile_path)


def _print(payload: Any) -> None:
    print(
        json.dumps(
            payload, indent=2, sort_keys=True, default=lambda value: value.__dict__
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--profile", default="mcp/production/profile.json")
    subparsers = parser.add_subparsers(dest="action", required=True)
    subparsers.add_parser("plan")
    subparsers.add_parser("check")
    subparsers.add_parser("apply")
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--no-probes", action="store_true")
    verify_parser.add_argument("--receipt", action="store_true")
    subparsers.add_parser("check-receipts")
    rollback_parser = subparsers.add_parser("rollback")
    rollback_parser.add_argument("receipt")
    args = parser.parse_args(argv)

    try:
        profile = _profile_from_args(args)
        if args.action == "plan":
            _print([item.__dict__ for item in build_plan(profile)])
            return 0
        if args.action == "check":
            plan = build_plan(profile)
            _print([item.__dict__ for item in plan])
            return 1 if any(item.status != "in_sync" for item in plan) else 0
        if args.action == "apply":
            _print([item.__dict__ for item in apply_plan(profile)])
            return 0
        if args.action == "verify":
            report = verify_profile(profile, run_probes=not args.no_probes)
            if args.receipt:
                report["receipt"] = str(
                    write_receipt(profile, "verify", report).relative_to(profile.root)
                )
            _print(report)
            return 0 if report["status"].startswith("technical_pass") else 1
        if args.action == "check-receipts":
            _print(check_receipt_chain(profile))
            return 0
        if args.action == "rollback":
            _print(
                {
                    "receipt": str(
                        rollback(profile, Path(args.receipt)).relative_to(profile.root)
                    )
                }
            )
            return 0
    except (MigrationError, OSError, json.JSONDecodeError) as exc:
        print(f"MCP production migration failed: {exc}", file=sys.stderr)
        return 2
    raise AssertionError(f"unhandled action: {args.action}")


if __name__ == "__main__":
    raise SystemExit(main())
