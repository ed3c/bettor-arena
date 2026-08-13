"""Shared deterministic helpers for knowledge-provider admission evals."""
from __future__ import annotations

import gzip
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
IDENT = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")
FAMILIES = {"symbol", "semantic", "graph", "memory"}
BASE = Path("docs/knowledge-providers")
EVALS = BASE / "evals"
AUTH_FALSE = {
    "advanced_state", "waived_gate", "marked_tested", "human_admit",
    "wrote_repository", "wrote_memory", "promoted_release",
}


class ContractError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def load(path: Path) -> Any:
    try:
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                return json.load(handle)
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"ABSENT: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"UNREADABLE_JSON: {path}: {exc}") from exc


def save(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def walk(value: Any, location: str = "$"):
    if isinstance(value, dict):
        for key, item in value.items():
            yield location, key, item
            yield from walk(item, f"{location}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk(item, f"{location}[{index}]")


def safe_path(value: str) -> bool:
    if not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and all(
        part not in {"", "."} for part in path.parts
    )


def common_safety(value: Any) -> None:
    path_keys = {"path", "path_scope", "source_refs", "residue", "manifest_path"}
    typed_refs = {"artifact", "receipt", "source", "issue", "pr", "memory"}
    for location, key, item in walk(value):
        if key not in path_keys:
            continue
        entries = item if isinstance(item, list) else [item]
        for entry in entries:
            if not isinstance(entry, str):
                continue
            if ":" in entry and entry.split(":", 1)[0] in typed_refs:
                continue
            require(safe_path(entry), f"PATH_ESCAPE: {location}.{key}: {entry}")


def validate_subject(value: Any, label: str) -> None:
    require(isinstance(value, dict), f"{label}: object required")
    require(REPO.fullmatch(str(value.get("repository", ""))) is not None, f"{label}: repository")
    require(SHA40.fullmatch(str(value.get("commit", ""))) is not None, f"{label}: commit")
    require(SHA40.fullmatch(str(value.get("tree", ""))) is not None, f"{label}: tree")
    require(not ({"branch", "ref", "tag"} & set(value)), f"{label}: mutable ref")
