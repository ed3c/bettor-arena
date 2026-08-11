#!/usr/bin/env python3
"""Complete tracked-path ownership classification for bettor-arena.

Module roots are authoritative.  Paths not owned by a module may be classified
only by the reviewed fallback classes in `.arena/ownership-classes.json`.
Every tracked path must resolve to exactly one subject and every fallback prefix
must classify at least one path.  Generated/evidence classes are forbidden from
absorbing implementation source.

Exit codes:
  0  ownership is complete
  2  contract violation
  64 usage, missing input, unreadable JSON, or unavailable Git metadata
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Iterable


CLASSES_SCHEMA = "bettor-arena/ownership-classes/v1"
SNAPSHOT_SCHEMA = "bettor-arena/ownership-snapshot/v1"
CLASS_KINDS = {"generated", "evidence", "documentation", "metadata"}
IMPLEMENTATION_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".go",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".mjs",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".sol",
    ".swift",
    ".ts",
    ".tsx",
}


class OwnershipError(ValueError):
    """A repository-owned ownership contract is invalid."""


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def digest_value(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise OwnershipError(f"missing JSON: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise OwnershipError(f"unreadable JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise OwnershipError(f"JSON root must be an object: {path}")
    return value


def valid_id(value: str) -> bool:
    return bool(value) and all(
        character.islower() or character.isdigit() or character in "-._"
        for character in value
    )


def normalize_prefix(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OwnershipError(f"{field} must be a non-empty string")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise OwnershipError(f"{field} must be repo-relative without '..': {value}")
    normalized = path.as_posix().rstrip("/")
    if not normalized or normalized == ".":
        raise OwnershipError(f"{field} may not own the repository root")
    return normalized


def path_matches(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(prefix + "/")


def load_classes(path: Path) -> dict[str, Any]:
    value = read_json(path)
    if set(value) != {"schema", "classes"}:
        raise OwnershipError(f"{path}: ownership-class fields drifted")
    if value["schema"] != CLASSES_SCHEMA:
        raise OwnershipError(f"{path}: schema must be {CLASSES_SCHEMA}")
    classes = value["classes"]
    if not isinstance(classes, list):
        raise OwnershipError(f"{path}: classes must be an array")

    seen_ids: set[str] = set()
    seen_prefixes: dict[str, str] = {}
    for entry in classes:
        if not isinstance(entry, dict) or set(entry) != {
            "id",
            "kind",
            "description",
            "paths",
        }:
            raise OwnershipError(f"{path}: malformed ownership class")
        class_id = entry["id"]
        if not isinstance(class_id, str) or not valid_id(class_id):
            raise OwnershipError(f"{path}: invalid class id: {class_id!r}")
        if class_id in seen_ids:
            raise OwnershipError(f"{path}: duplicate class id: {class_id}")
        seen_ids.add(class_id)
        if entry["kind"] not in CLASS_KINDS:
            raise OwnershipError(
                f"{path}: invalid class kind for {class_id}: {entry['kind']!r}"
            )
        if not isinstance(entry["description"], str) or not entry[
            "description"
        ].strip():
            raise OwnershipError(f"{path}: class description is required: {class_id}")
        paths = entry["paths"]
        if not isinstance(paths, list) or not paths:
            raise OwnershipError(f"{path}: class paths must be non-empty: {class_id}")
        normalized: list[str] = []
        for index, raw in enumerate(paths):
            prefix = normalize_prefix(raw, f"{class_id}.paths[{index}]")
            if prefix in seen_prefixes:
                raise OwnershipError(
                    f"{path}: fallback prefix {prefix!r} is declared by both "
                    f"{seen_prefixes[prefix]} and {class_id}"
                )
            seen_prefixes[prefix] = class_id
            normalized.append(prefix)
        if len(normalized) != len(set(normalized)):
            raise OwnershipError(f"{path}: duplicate class path: {class_id}")
        entry["paths"] = normalized
    return value


def git_tracked_paths(root: Path) -> list[str]:
    process = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=False,
        capture_output=True,
    )
    if process.returncode != 0:
        detail = process.stderr.decode("utf-8", errors="replace").strip()
        raise OwnershipError(f"git ls-files failed for {root}: {detail}")
    return sorted(
        item.decode("utf-8", errors="strict")
        for item in process.stdout.split(b"\0")
        if item
    )


def module_claims(modules: dict[str, dict[str, Any]]) -> list[tuple[str, str]]:
    claims: list[tuple[str, str]] = []
    for module_id, module in sorted(modules.items()):
        roots = module.get("roots")
        if not isinstance(roots, list):
            raise OwnershipError(f"module roots are malformed: {module_id}")
        for index, raw in enumerate(roots):
            claims.append(
                (module_id, normalize_prefix(raw, f"{module_id}.roots[{index}]"))
            )
    return claims


def classify(
    modules: dict[str, dict[str, Any]],
    classes_value: dict[str, Any],
    tracked_paths: Iterable[str],
) -> dict[str, Any]:
    paths = sorted(set(tracked_paths))
    if not paths:
        raise OwnershipError("tracked-path set is empty")

    claims = module_claims(modules)
    classes = classes_value["classes"]
    prefix_usage: dict[tuple[str, str], int] = {
        (entry["id"], prefix): 0 for entry in classes for prefix in entry["paths"]
    }
    assignments: list[dict[str, str]] = []
    errors: list[str] = []

    for tracked in paths:
        normalized = normalize_prefix(tracked, "tracked path")
        owners = sorted(
            {
                module_id
                for module_id, prefix in claims
                if path_matches(normalized, prefix)
            }
        )
        if len(owners) > 1:
            errors.append(
                f"MULTIPLY_OWNED {normalized}: modules={','.join(owners)}"
            )
            continue
        if len(owners) == 1:
            assignments.append(
                {"path": normalized, "type": "module", "subject": owners[0]}
            )
            continue

        matches: list[tuple[str, str, str]] = []
        for entry in classes:
            for prefix in entry["paths"]:
                if path_matches(normalized, prefix):
                    matches.append((entry["id"], entry["kind"], prefix))
        if not matches:
            errors.append(f"UNOWNED {normalized}")
            continue
        class_ids = sorted({match[0] for match in matches})
        if len(class_ids) > 1:
            errors.append(
                f"AMBIGUOUS_CLASS {normalized}: classes={','.join(class_ids)}"
            )
            continue

        class_id, kind, _ = matches[0]
        if kind in {"generated", "evidence"} and Path(normalized).suffix.lower() in (
            IMPLEMENTATION_SUFFIXES
        ):
            errors.append(
                f"IMPLEMENTATION_IN_{kind.upper()} {normalized}: class={class_id}"
            )
            continue
        for matched_class, _, prefix in matches:
            prefix_usage[(matched_class, prefix)] += 1
        assignments.append(
            {"path": normalized, "type": kind, "subject": class_id}
        )

    for (class_id, prefix), count in sorted(prefix_usage.items()):
        if count == 0:
            errors.append(f"STALE_CLASS_PATH {class_id}:{prefix}")

    if errors:
        raise OwnershipError("ownership coverage failed:\n" + "\n".join(errors))

    counts: dict[str, int] = {}
    for assignment in assignments:
        key = f"{assignment['type']}:{assignment['subject']}"
        counts[key] = counts.get(key, 0) + 1

    return {
        "schema": SNAPSHOT_SCHEMA,
        "tracked_files": len(assignments),
        "ownership_sha256": digest_value(assignments),
        "ownership_classes_sha256": digest_value(classes_value),
        "counts": dict(sorted(counts.items())),
        "assignments": assignments,
    }


def snapshot(
    root: Path,
    modules: dict[str, dict[str, Any]],
    classes_path: Path | None = None,
    tracked_paths: Iterable[str] | None = None,
) -> dict[str, Any]:
    path = classes_path or root / ".arena" / "ownership-classes.json"
    classes_value = load_classes(path)
    paths = list(tracked_paths) if tracked_paths is not None else git_tracked_paths(root)
    return classify(modules, classes_value, paths)


def selftest() -> None:
    modules = {
        "a": {"roots": ["a"]},
        "b": {"roots": ["b"]},
    }
    good_classes = {
        "schema": CLASSES_SCHEMA,
        "classes": [
            {
                "id": "docs",
                "kind": "documentation",
                "description": "fixture documentation",
                "paths": ["README.md"],
            },
            {
                "id": "evidence",
                "kind": "evidence",
                "description": "fixture evidence",
                "paths": ["data"],
            },
        ],
    }
    good_paths = ["a/main.py", "b/main.py", "README.md", "data/run.json"]
    first = classify(modules, json.loads(json.dumps(good_classes)), good_paths)
    second = classify(modules, json.loads(json.dumps(good_classes)), good_paths)
    if first["ownership_sha256"] != second["ownership_sha256"]:
        raise OwnershipError("deterministic ownership digest changed")

    changed = classify(
        modules,
        json.loads(json.dumps(good_classes)),
        good_paths + ["a/extra.txt"],
    )
    if first["ownership_sha256"] == changed["ownership_sha256"]:
        raise OwnershipError("added tracked path did not move ownership digest")

    cases: list[tuple[str, dict[str, Any], list[str]]] = [
        (
            "unowned",
            good_classes,
            good_paths + ["rogue.txt"],
        ),
        (
            "multiply-owned",
            {"schema": CLASSES_SCHEMA, "classes": []},
            ["a/file.txt"],
        ),
        (
            "stale-class",
            {
                "schema": CLASSES_SCHEMA,
                "classes": [
                    {
                        "id": "unused",
                        "kind": "metadata",
                        "description": "must be exercised",
                        "paths": ["unused.txt"],
                    }
                ],
            },
            ["a/file.txt"],
        ),
        (
            "implementation-as-evidence",
            {
                "schema": CLASSES_SCHEMA,
                "classes": [
                    {
                        "id": "evidence",
                        "kind": "evidence",
                        "description": "must not hide code",
                        "paths": ["data"],
                    }
                ],
            },
            ["data/evil.py"],
        ),
    ]
    for name, classes_value, paths in cases:
        case_modules = modules
        if name == "multiply-owned":
            case_modules = {
                "a": {"roots": ["a"]},
                "b": {"roots": ["a/file.txt"]},
            }
        try:
            classify(case_modules, json.loads(json.dumps(classes_value)), paths)
        except OwnershipError:
            pass
        else:
            raise OwnershipError(f"negative control accepted {name}")

    with tempfile.TemporaryDirectory(prefix="arena-ownership.") as temp:
        classes_path = Path(temp) / "classes.json"
        classes_path.write_text(json.dumps(good_classes), encoding="utf-8")
        loaded = load_classes(classes_path)
        if loaded["schema"] != CLASSES_SCHEMA:
            raise OwnershipError("ownership-class loader changed schema")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="arena_ownership.py")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.selftest:
            selftest()
            print("SELFTEST GREEN: tracked-path ownership")
            return 0
        parser.error("this module is consumed by arena_modules.py; use --selftest")
    except OwnershipError as exc:
        print(f"ownership RED: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"ownership FATAL: {exc}", file=sys.stderr)
        return 64
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
