#!/usr/bin/env python3
"""Trusted-local manifest ingress for the generic CTG build mechanism.

This surface intentionally stays outside MCP: it may read subject-owned host paths.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

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


def _schema_type_matches(value: object, declared: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "boolean": isinstance(value, bool),
        "null": value is None,
        "integer": isinstance(value, int) and not isinstance(value, bool),
    }.get(declared, False)


def _validate_schema(
    value: object, schema: dict[str, Any], root: dict[str, Any], path: str = "$"
) -> None:
    reference = schema.get("$ref")
    if reference:
        if not isinstance(reference, str) or not reference.startswith("#/"):
            raise ValueError(f"{path}: only local schema references are supported")
        target: object = root
        for part in reference[2:].split("/"):
            if not isinstance(target, dict) or part not in target:
                raise ValueError(f"{path}: unresolved schema reference {reference}")
            target = target[part]
        if not isinstance(target, dict):
            raise ValueError(f"{path}: schema reference does not resolve to an object")
        _validate_schema(value, target, root, path)
        return
    if "const" in schema and value != schema["const"]:
        raise ValueError(f"{path}: value differs from schema const")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path}: value is outside schema enum")
    declared = schema.get("type")
    if declared is not None:
        types = declared if isinstance(declared, list) else [declared]
        if not any(_schema_type_matches(value, item) for item in types):
            raise ValueError(f"{path}: value does not match schema type {declared}")
    if isinstance(value, dict):
        required = schema.get("required", [])
        missing = sorted(set(required) - set(value))
        if missing:
            raise ValueError(f"{path}: missing required keys {missing}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                raise ValueError(f"{path}: unknown keys {extra}")
        for key, item in value.items():
            child_schema = properties.get(key)
            if isinstance(child_schema, dict):
                _validate_schema(item, child_schema, root, f"{path}.{key}")
    elif isinstance(value, list):
        if len(value) < int(schema.get("minItems", 0)):
            raise ValueError(f"{path}: array has fewer than minItems")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_schema(item, item_schema, root, f"{path}[{index}]")
    elif isinstance(value, str):
        if len(value) < int(schema.get("minLength", 0)):
            raise ValueError(f"{path}: string has fewer than minLength characters")
        pattern = schema.get("pattern")
        if pattern and re.fullmatch(str(pattern), value) is None:
            raise ValueError(f"{path}: string does not match schema pattern")


def validate_local_receipt(receipt: dict[str, object]) -> None:
    schema_path = (
        Path(__file__).resolve().parents[2]
        / "schemas/ctg-local-build-receipt.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if not isinstance(schema, dict):
        raise ValueError("local receipt schema must be a JSON object")
    _validate_schema(receipt, schema, schema)


def write_receipt(
    *,
    output: Path,
    root: Path,
    manifest: Path,
    manifest_sha256: str,
    report: dict[str, object],
    dirty: bool,
    consumed_inputs: list[dict[str, str]],
    subject_commit: str,
    subject_tree: str,
    runner: dict[str, object],
) -> None:
    artifacts = []
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        artifacts.append(
            {
                "artifact_ref": path.relative_to(output).as_posix(),
                "sha256": sha256(path),
            }
        )
    receipt = {
        "schema_version": "ctg-local-build-receipt@1.0.0",
        "runner": runner,
        "subject": {
            "repo_commit": subject_commit,
            "repo_tree": subject_tree,
            "dirty_before_run": dirty,
            "manifest_ref": manifest.relative_to(root).as_posix(),
            "manifest_sha256": manifest_sha256,
            "input_files": consumed_inputs,
            "input_closure_sha256": closure_sha256(consumed_inputs),
        },
        "artifacts": artifacts,
        "overall": {"state": "PASSED" if report.get("ok") else "FAILED"},
        "claim_boundary": "trusted-local artifacts remain subject-owned and are not MCP-deliverable",
    }
    validate_local_receipt(receipt)
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
        manifest_digest = sha256(manifest)
        consumed_inputs = input_records(root, validate_local_inputs(root, manifest))
        subject_commit = git(root, "rev-parse", "HEAD")
        subject_tree = git(root, "rev-parse", "HEAD^{tree}")
        dirty = bool(git(root, "status", "--porcelain", "--untracked-files=all"))
        runner = runner_identity()
        report = build_graph(manifest, output_dir=output)
        after_manifest_digest = sha256(manifest)
        after_inputs = input_records(root, validate_local_inputs(root, manifest))
        if manifest_digest != after_manifest_digest or consumed_inputs != after_inputs:
            raise ValueError(
                "manifest or consumed input closure changed during local build; result is not publishable"
            )
        if subject_commit != git(root, "rev-parse", "HEAD") or subject_tree != git(
            root, "rev-parse", "HEAD^{tree}"
        ):
            raise ValueError("subject Git identity changed during local build")
        write_receipt(
            output=output,
            root=root,
            manifest=manifest,
            manifest_sha256=manifest_digest,
            report=report,
            dirty=dirty,
            consumed_inputs=consumed_inputs,
            subject_commit=subject_commit,
            subject_tree=subject_tree,
            runner=runner,
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
