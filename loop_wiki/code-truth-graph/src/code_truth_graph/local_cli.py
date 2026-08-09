#!/usr/bin/env python3
"""Trusted-local manifest ingress for the generic CTG build mechanism.

This surface intentionally stays outside MCP: it may read subject-owned host paths.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from .build import build_graph, load_manifest
from .identity import RUNTIME_REF, SURFACE_VERSION
from .java_ast import JavaAstError
from .util import write_json


def absolute_fresh(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise ValueError(f"{label} must be absolute")
    resolved = path.resolve()
    if label == "output" and resolved.exists():
        raise ValueError(f"output must not already exist: {resolved}")
    return resolved


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def subject_root(manifest: Path) -> Path:
    return Path(git(manifest.parent, "rev-parse", "--show-toplevel")).resolve()


def require_within(
    root: Path, path: Path, label: str, *, allow_root: bool = False
) -> Path:
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} must stay inside subject root") from exc
    if (not relative.parts and not allow_root) or (
        relative.parts and relative.parts[0] == ".git"
    ):
        raise ValueError(f"{label} must not target the subject root or .git")
    return relative


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runner_identity() -> dict[str, object]:
    root = Path(__file__).resolve().parents[4]
    try:
        commit = git(root, "rev-parse", "HEAD")
        tree = git(root, "rev-parse", "HEAD^{tree}")
        dirty = bool(git(root, "status", "--porcelain", "--untracked-files=all"))
    except ValueError:
        commit = "UNVERIFIED_RELOCATED"
        tree = "UNVERIFIED_RELOCATED"
        dirty = None
    return {
        "repo_commit": commit,
        "repo_tree": tree,
        "dirty_before_run": dirty,
        "runtime_ref": RUNTIME_REF,
        "surface_version": SURFACE_VERSION,
    }


def validate_local_inputs(root: Path, manifest_path: Path) -> list[Path]:
    manifest = load_manifest(manifest_path)
    base = Path(manifest["_base_dir"])
    require_within(root, base, "path_base", allow_root=True)

    static = manifest.get("static") or {}
    if not isinstance(static, dict):
        raise ValueError("static must be an object")
    if static.get("classpath") not in {None, ""}:
        raise ValueError(
            "static.classpath is forbidden in trusted-local mode; use a pinned tool profile"
        )
    sandbox = manifest.get("sandbox") or {}
    production = manifest.get("production") or {}
    sessions = manifest.get("sessions") or []
    if not isinstance(sandbox, dict):
        raise ValueError("sandbox must be an object")
    if not isinstance(production, dict):
        raise ValueError("production must be an object")
    if not isinstance(sessions, list):
        raise ValueError("sessions must be an array")
    logs = production.get("logs", [])
    if not isinstance(logs, list) or not all(isinstance(item, dict) for item in logs):
        raise ValueError("production.logs must be an array of objects")
    sandbox_receipts = sandbox.get("receipts", [])
    production_receipts = production.get("receipts", [])
    source_globs = static.get("source_globs", ["**/*.java"])
    consumed: set[Path] = set()
    for values, label in (
        (sandbox_receipts, "sandbox.receipts"),
        (production_receipts, "production.receipts"),
        (source_globs, "static.source_globs"),
    ):
        if not isinstance(values, list) or not all(
            isinstance(value, str) for value in values
        ):
            raise ValueError(f"{label} must be an array of strings")
    path_specs: list[tuple[object, str, bool]] = [
        (static.get("root"), "static.root", True),
        (sandbox.get("jacoco"), "sandbox.jacoco", False),
    ]
    path_specs.extend(
        (value, "sandbox.receipts[]", False) for value in sandbox_receipts
    )
    path_specs.extend(
        (item.get("path"), "production.logs[].path", False) for item in logs
    )
    path_specs.extend(
        (value, "production.receipts[]", False) for value in production_receipts
    )
    for item in sessions:
        if not isinstance(item, dict):
            raise ValueError("sessions entries must be objects")
        path_specs.extend(
            (
                (item.get("path"), "sessions[].path", False),
                (item.get("root"), "sessions[].root", True),
            )
        )
    for value, label, allow_root in path_specs:
        if not value:
            continue
        path = Path(str(value)).expanduser()
        resolved = path.resolve() if path.is_absolute() else (base / path).resolve()
        require_within(root, resolved, label, allow_root=allow_root)
        if resolved.is_file():
            consumed.add(resolved)
    static_root_value = static.get("root")
    if static_root_value:
        static_root_path = Path(str(static_root_value)).expanduser()
        static_root = (
            static_root_path.resolve()
            if static_root_path.is_absolute()
            else (base / static_root_path).resolve()
        )
        for pattern in source_globs:
            for match in glob.glob(str(static_root / str(pattern)), recursive=True):
                path = Path(match)
                if path.is_file():
                    resolved = path.resolve()
                    require_within(root, resolved, "static source")
                    consumed.add(resolved)
    return sorted(consumed)


def input_records(root: Path, paths: list[Path]) -> list[dict[str, str]]:
    return [
        {"input_ref": path.relative_to(root).as_posix(), "sha256": sha256(path)}
        for path in paths
    ]


def closure_sha256(records: list[dict[str, str]]) -> str:
    payload = json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def write_receipt(
    *,
    output: Path,
    root: Path,
    manifest: Path,
    report: dict[str, object],
    dirty: bool,
    consumed_inputs: list[Path],
) -> None:
    artifacts = []
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        artifacts.append(
            {
                "artifact_ref": path.relative_to(output).as_posix(),
                "sha256": sha256(path),
            }
        )
    inputs = input_records(root, consumed_inputs)
    receipt = {
        "schema_version": "ctg-local-build-receipt@1.0.0",
        "runner": runner_identity(),
        "subject": {
            "repo_commit": git(root, "rev-parse", "HEAD"),
            "repo_tree": git(root, "rev-parse", "HEAD^{tree}"),
            "dirty_before_run": dirty,
            "manifest_ref": manifest.relative_to(root).as_posix(),
            "manifest_sha256": sha256(manifest),
            "input_files": inputs,
            "input_closure_sha256": closure_sha256(inputs),
        },
        "artifacts": artifacts,
        "overall": {"state": "PASSED" if report.get("ok") else "FAILED"},
        "claim_boundary": "trusted-local artifacts remain subject-owned and are not MCP-deliverable",
    }
    write_json(output / "ctg-local-build-receipt.json", receipt)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(prog="code-truth-graph-local")
    value.add_argument("--manifest", required=True, type=Path)
    value.add_argument("--output", required=True, type=Path)
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        manifest = absolute_fresh(args.manifest, "manifest")
        output = absolute_fresh(args.output, "output")
        if not manifest.is_file():
            raise ValueError(f"manifest is not a file: {manifest}")
        root = subject_root(manifest)
        require_within(root, manifest, "manifest")
        require_within(root, output, "output")
        consumed_inputs = validate_local_inputs(root, manifest)
        dirty = bool(git(root, "status", "--porcelain", "--untracked-files=all"))
        report = build_graph(manifest, output_dir=output)
        write_receipt(
            output=output,
            root=root,
            manifest=manifest,
            report=report,
            dirty=dirty,
            consumed_inputs=consumed_inputs,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ctg local FATAL: {exc}", file=sys.stderr)
        return 64
    except JavaAstError as exc:
        print(f"ctg local FAILED: {exc}", file=sys.stderr)
        return 2
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
