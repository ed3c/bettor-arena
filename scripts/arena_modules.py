#!/usr/bin/env python3
"""Module catalog and composition resolver for bettor-arena.

This is the first executable slice of the modular-integration target contract.
It validates module manifests, rejects overlapping ownership roots, resolves
capability dependencies, and verifies a checked-in deterministic composition
lock. It is intentionally zero-network and standard-library only.

Exit codes:
  0  valid / command completed
  2  contract violation
  64 usage, missing input, or unreadable JSON
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any


MODULE_SCHEMA = "bettor-arena/module/v1"
REQ_SCHEMA = "bettor-arena/composition-requirements/v1"
LOCK_SCHEMA = "bettor-arena/composition-lock/v1"


class ContractError(ValueError):
    """A user- or repository-owned contract is invalid."""


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def digest_value(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"missing JSON: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"unreadable JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"JSON root must be an object: {path}")
    return value


def rel_path(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{field} must be a non-empty string")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ContractError(f"{field} must be repo-relative without '..': {value}")
    return path.as_posix().rstrip("/")


def string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise ContractError(f"{field} must be an array of non-empty strings")
    if len(value) != len(set(value)):
        raise ContractError(f"{field} contains duplicates")
    return list(value)


def validate_module(module: dict[str, Any], path: Path, root: Path) -> None:
    required = {
        "schema",
        "id",
        "interface_version",
        "summary",
        "roots",
        "components",
        "provides",
        "requires",
        "conflicts",
        "loops",
        "skills",
        "runtime",
        "proof",
        "external_policy",
    }
    if set(module) != required:
        missing = sorted(required - set(module))
        extra = sorted(set(module) - required)
        raise ContractError(
            f"{path}: module fields drifted; missing={missing}, extra={extra}"
        )
    if module["schema"] != MODULE_SCHEMA:
        raise ContractError(f"{path}: schema must be {MODULE_SCHEMA}")
    module_id = module["id"]
    if not isinstance(module_id, str) or not re_id(module_id):
        raise ContractError(f"{path}: invalid module id: {module_id!r}")
    if path.parent.name != module_id:
        raise ContractError(
            f"{path}: directory name {path.parent.name!r} must equal module id"
        )
    if (
        not isinstance(module["interface_version"], str)
        or not module["interface_version"]
    ):
        raise ContractError(f"{path}: interface_version is required")
    if not isinstance(module["summary"], str) or not module["summary"].strip():
        raise ContractError(f"{path}: summary is required")

    roots = string_list(module["roots"], f"{module_id}.roots")
    if not roots:
        raise ContractError(f"{path}: roots must not be empty")
    for index, value in enumerate(roots):
        relative = rel_path(value, f"{module_id}.roots[{index}]")
        if not (root / relative).exists():
            raise ContractError(f"{path}: owned root is absent: {relative}")

    components = module["components"]
    if not isinstance(components, dict) or not components:
        raise ContractError(f"{path}: components must be a non-empty object")
    for name, component in components.items():
        if not re_id(name) or not isinstance(component, dict):
            raise ContractError(f"{path}: invalid component {name!r}")
        if set(component) != {"required", "paths"}:
            raise ContractError(f"{path}: component fields drifted: {name}")
        if not isinstance(component["required"], bool):
            raise ContractError(f"{path}: component.required must be boolean: {name}")
        paths = string_list(component["paths"], f"{module_id}.components.{name}.paths")
        for index, value in enumerate(paths):
            relative = rel_path(value, f"{module_id}.components.{name}.paths[{index}]")
            if not (root / relative).exists():
                raise ContractError(
                    f"{path}: component path is absent: {name}: {relative}"
                )

    for field in ("provides", "requires", "conflicts"):
        string_list(module[field], f"{module_id}.{field}")
    if module_id in module["conflicts"]:
        raise ContractError(f"{path}: a module cannot conflict with itself")

    loops = module["loops"]
    if not isinstance(loops, list):
        raise ContractError(f"{path}: loops must be an array")
    loop_ids: set[str] = set()
    for loop in loops:
        if not isinstance(loop, dict) or set(loop) != {
            "id",
            "class",
            "interface_version",
            "public_port",
            "external_policy",
        }:
            raise ContractError(f"{path}: malformed loop declaration")
        if loop["id"] in loop_ids:
            raise ContractError(f"{path}: duplicate loop id: {loop['id']}")
        loop_ids.add(loop["id"])
        if loop["class"] not in {"macro", "micro", "core", "provider", "aggregate"}:
            raise ContractError(f"{path}: invalid loop class: {loop['class']}")
        if loop["external_policy"] not in {
            "denied",
            "allowlisted",
            "control-only",
        }:
            raise ContractError(
                f"{path}: invalid loop external_policy: {loop['external_policy']}"
            )

    skills = module["skills"]
    if not isinstance(skills, dict) or set(skills) != {
        "required",
        "optional",
        "repo_owned",
    }:
        raise ContractError(f"{path}: skills fields drifted")
    for field in skills:
        string_list(skills[field], f"{module_id}.skills.{field}")

    runtime = module["runtime"]
    if not isinstance(runtime, dict) or set(runtime) != {"profiles", "tools"}:
        raise ContractError(f"{path}: runtime fields drifted")
    for field in runtime:
        string_list(runtime[field], f"{module_id}.runtime.{field}")

    proof = module["proof"]
    if not isinstance(proof, dict) or set(proof) != {
        "verify",
        "selftest",
        "control",
        "mutation",
    }:
        raise ContractError(f"{path}: proof fields drifted")
    for field in proof:
        command = proof[field]
        if command is not None and (
            not isinstance(command, list)
            or not command
            or any(not isinstance(part, str) or not part for part in command)
        ):
            raise ContractError(f"{path}: proof.{field} must be null or argv array")

    external = module["external_policy"]
    if not isinstance(external, dict) or set(external) != {
        "exposed",
        "mutation",
        "network",
        "secrets",
    }:
        raise ContractError(f"{path}: external_policy fields drifted")
    if not isinstance(external["exposed"], bool):
        raise ContractError(f"{path}: external_policy.exposed must be boolean")
    if external["mutation"] not in {
        "none",
        "disposable-worktree",
        "workspace",
        "external-system",
    }:
        raise ContractError(f"{path}: invalid external mutation class")
    if external["network"] not in {"none", "optional", "required", "broker-only"}:
        raise ContractError(f"{path}: invalid external network class")
    if external["secrets"] not in {"none", "broker-only", "host-only"}:
        raise ContractError(f"{path}: invalid external secrets class")


def re_id(value: str) -> bool:
    return bool(value) and all(
        ch.islower() or ch.isdigit() or ch in "-._" for ch in value
    )


def load_modules(root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Path]]:
    module_root = root / ".arena" / "modules"
    if not module_root.is_dir():
        raise ContractError(f"missing module catalog: {module_root}")
    modules: dict[str, dict[str, Any]] = {}
    paths: dict[str, Path] = {}
    for path in sorted(module_root.glob("*/module.json")):
        module = load_json(path)
        validate_module(module, path, root)
        module_id = module["id"]
        if module_id in modules:
            raise ContractError(f"duplicate module id: {module_id}")
        modules[module_id] = module
        paths[module_id] = path
    if not modules:
        raise ContractError("module catalog is empty")
    validate_ownership(modules)
    validate_capabilities(modules)
    return modules, paths


def path_parts(value: str) -> tuple[str, ...]:
    return Path(value.rstrip("/")).parts


def owns_overlap(left: str, right: str) -> bool:
    a, b = path_parts(left), path_parts(right)
    return a == b[: len(a)] or b == a[: len(b)]


def validate_ownership(modules: dict[str, dict[str, Any]]) -> None:
    claims: list[tuple[str, str]] = []
    for module_id, module in modules.items():
        for owned in module["roots"]:
            claims.append((module_id, owned.rstrip("/")))
    conflicts: list[str] = []
    for index, (left_id, left) in enumerate(claims):
        for right_id, right in claims[index + 1 :]:
            if left_id != right_id and owns_overlap(left, right):
                conflicts.append(f"{left_id}:{left} <-> {right_id}:{right}")
    if conflicts:
        raise ContractError("overlapping module ownership: " + "; ".join(conflicts))


def validate_capabilities(modules: dict[str, dict[str, Any]]) -> dict[str, str]:
    providers: dict[str, str] = {}
    for module_id, module in modules.items():
        for capability in module["provides"]:
            if capability in providers:
                raise ContractError(
                    f"capability has multiple providers: {capability}: "
                    f"{providers[capability]}, {module_id}"
                )
            providers[capability] = module_id
    return providers


def validate_requirements(value: dict[str, Any], path: Path) -> None:
    if set(value) != {"schema", "id", "preset", "modules"}:
        raise ContractError(f"{path}: requirements fields drifted")
    if value["schema"] != REQ_SCHEMA:
        raise ContractError(f"{path}: schema must be {REQ_SCHEMA}")
    if not isinstance(value["id"], str) or not re_id(value["id"]):
        raise ContractError(f"{path}: invalid composition id")
    if value["preset"] is not None and (
        not isinstance(value["preset"], str) or not re_id(value["preset"])
    ):
        raise ContractError(f"{path}: preset must be null or an id")
    if not isinstance(value["modules"], list) or not value["modules"]:
        raise ContractError(f"{path}: modules must be a non-empty array")
    seen: set[str] = set()
    for entry in value["modules"]:
        if not isinstance(entry, dict) or set(entry) != {"id", "components"}:
            raise ContractError(f"{path}: malformed module selection")
        if not isinstance(entry["id"], str) or not re_id(entry["id"]):
            raise ContractError(f"{path}: invalid selected module id")
        if entry["id"] in seen:
            raise ContractError(f"{path}: duplicate selected module: {entry['id']}")
        seen.add(entry["id"])
        string_list(entry["components"], f"{path}:{entry['id']}.components")


def resolve(
    root: Path,
    modules: dict[str, dict[str, Any]],
    module_paths: dict[str, Path],
    requirements_path: Path,
) -> dict[str, Any]:
    requirements = load_json(requirements_path)
    validate_requirements(requirements, requirements_path)
    providers = validate_capabilities(modules)

    requested_components: dict[str, set[str]] = {}
    queue: list[str] = []
    for entry in requirements["modules"]:
        module_id = entry["id"]
        if module_id not in modules:
            raise ContractError(f"unknown selected module: {module_id}")
        requested_components[module_id] = set(entry["components"])
        queue.append(module_id)

    selected: set[str] = set()
    while queue:
        module_id = queue.pop(0)
        if module_id in selected:
            continue
        selected.add(module_id)
        module = modules[module_id]
        for capability in module["requires"]:
            if capability.startswith("external:"):
                continue
            provider = providers.get(capability)
            if provider is None:
                raise ContractError(
                    f"{module_id} requires unprovided capability: {capability}"
                )
            if provider not in selected:
                queue.append(provider)

    for module_id in sorted(selected):
        module = modules[module_id]
        selected_conflicts = selected.intersection(module["conflicts"])
        if selected_conflicts:
            raise ContractError(
                f"{module_id} conflicts with selected modules: "
                f"{', '.join(sorted(selected_conflicts))}"
            )
        requested = requested_components.get(module_id)
        if requested is None:
            requested = {
                name
                for name, component in module["components"].items()
                if component["required"]
            }
        unknown = requested - set(module["components"])
        if unknown:
            raise ContractError(
                f"{module_id} requests unknown components: {', '.join(sorted(unknown))}"
            )
        missing_required = {
            name
            for name, component in module["components"].items()
            if component["required"]
        } - requested
        if missing_required:
            raise ContractError(
                f"{module_id} omits required components: "
                f"{', '.join(sorted(missing_required))}"
            )
        requested_components[module_id] = requested

    resolved_modules: list[dict[str, Any]] = []
    capability_map: dict[str, str] = {}
    for module_id in sorted(selected):
        module = modules[module_id]
        manifest = load_json(module_paths[module_id])
        manifest_sha = digest_value(manifest)
        for capability in module["provides"]:
            capability_map[capability] = module_id
        resolved_modules.append(
            {
                "id": module_id,
                "interface_version": module["interface_version"],
                "manifest_sha256": manifest_sha,
                "components": sorted(requested_components[module_id]),
                "provides": sorted(module["provides"]),
            }
        )

    unsigned: dict[str, Any] = {
        "schema": LOCK_SCHEMA,
        "composition": requirements["id"],
        "requirements_sha256": digest_bytes(requirements_path.read_bytes()),
        "modules": resolved_modules,
        "capabilities": dict(sorted(capability_map.items())),
    }
    unsigned["content_sha256"] = digest_value(unsigned)
    return unsigned


def check_lock(root: Path, requirements: Path, lock_path: Path) -> None:
    modules, paths = load_modules(root)
    expected = resolve(root, modules, paths, requirements)
    actual = load_json(lock_path)
    if actual.get("schema") != LOCK_SCHEMA:
        raise ContractError(f"{lock_path}: schema must be {LOCK_SCHEMA}")
    if actual != expected:
        raise ContractError(
            f"{lock_path}: stale composition lock; run "
            f"`python3 scripts/arena_modules.py resolve "
            f"--requirements {requirements.relative_to(root)} "
            f"--output {lock_path.relative_to(root)}`"
        )


def catalog(modules: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": "bettor-arena/module-catalog/v1",
        "modules": [
            {
                "id": module_id,
                "interface_version": module["interface_version"],
                "summary": module["summary"],
                "provides": sorted(module["provides"]),
                "requires": sorted(module["requires"]),
                "external_exposed": module["external_policy"]["exposed"],
            }
            for module_id, module in sorted(modules.items())
        ],
    }


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def build_fixture(root: Path) -> tuple[Path, Path]:
    fixture_paths = (
        "a",
        "b",
        ".arena/modules/a",
        ".arena/modules/b",
        ".arena/compositions",
        ".arena/locks",
    )
    for relative in fixture_paths:
        (root / relative).mkdir(parents=True, exist_ok=True)
    module_a = {
        "schema": MODULE_SCHEMA,
        "id": "a",
        "interface_version": "1.0.0",
        "summary": "provider",
        "roots": ["a"],
        "components": {"runtime": {"required": True, "paths": ["a"]}},
        "provides": ["cap.a/v1"],
        "requires": [],
        "conflicts": [],
        "loops": [],
        "skills": {"required": [], "optional": [], "repo_owned": []},
        "runtime": {"profiles": [], "tools": []},
        "proof": {"verify": None, "selftest": None, "control": None, "mutation": None},
        "external_policy": {
            "exposed": False,
            "mutation": "none",
            "network": "none",
            "secrets": "none",
        },
    }
    module_b = {
        **module_a,
        "id": "b",
        "summary": "consumer",
        "roots": ["b"],
        "components": {"client": {"required": True, "paths": ["b"]}},
        "provides": ["cap.b/v1"],
        "requires": ["cap.a/v1"],
    }
    write_json(root / ".arena/modules/a/module.json", module_a)
    write_json(root / ".arena/modules/b/module.json", module_b)
    requirements = {
        "schema": REQ_SCHEMA,
        "id": "fixture",
        "preset": None,
        "modules": [{"id": "b", "components": ["client"]}],
    }
    req_path = root / ".arena/compositions/fixture.requirements.json"
    lock_path = root / ".arena/locks/fixture.lock.json"
    write_json(req_path, requirements)
    modules, paths = load_modules(root)
    write_json(lock_path, resolve(root, modules, paths, req_path))
    return req_path, lock_path


def selftest() -> None:
    with tempfile.TemporaryDirectory(prefix="arena-modules.") as temp:
        root = Path(temp)
        req, lock = build_fixture(root)
        check_lock(root, req, lock)

        broken = load_json(root / ".arena/modules/b/module.json")
        broken["requires"] = ["missing/v1"]
        write_json(root / ".arena/modules/b/module.json", broken)
        try:
            check_lock(root, req, lock)
        except ContractError:
            pass
        else:
            raise ContractError("negative control accepted missing capability provider")

    with tempfile.TemporaryDirectory(prefix="arena-modules-overlap.") as temp:
        root = Path(temp)
        req, lock = build_fixture(root)
        broken = load_json(root / ".arena/modules/b/module.json")
        broken["roots"] = ["a/child"]
        (root / "a/child").mkdir(parents=True)
        broken["components"]["client"]["paths"] = ["a/child"]
        write_json(root / ".arena/modules/b/module.json", broken)
        try:
            load_modules(root)
        except ContractError:
            pass
        else:
            raise ContractError("negative control accepted overlapping ownership")


def default_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="arena_modules.py")
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--selftest", action="store_true")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("catalog")

    check_parser = sub.add_parser("check")
    check_parser.add_argument(
        "--requirements",
        type=Path,
        default=Path(".arena/compositions/bettor-arena.requirements.json"),
    )
    check_parser.add_argument(
        "--lock",
        type=Path,
        default=Path(".arena/locks/bettor-arena.lock.json"),
    )

    resolve_parser = sub.add_parser("resolve")
    resolve_parser.add_argument("--requirements", type=Path, required=True)
    resolve_parser.add_argument("--output", type=Path)

    args = parser.parse_args(argv)
    try:
        if args.selftest:
            if args.command is not None:
                parser.error("--selftest cannot be combined with a command")
            selftest()
            print("SELFTEST GREEN: module catalog")
            return 0
        if args.command is None:
            parser.error("a command is required")

        root = args.root.resolve()
        modules, paths = load_modules(root)
        if args.command == "catalog":
            print(json.dumps(catalog(modules), ensure_ascii=False, indent=2))
            return 0
        if args.command == "check":
            requirements = (
                args.requirements
                if args.requirements.is_absolute()
                else root / args.requirements
            )
            lock = args.lock if args.lock.is_absolute() else root / args.lock
            check_lock(root, requirements, lock)
            print(
                f"PASS module catalog ({len(modules)} modules), "
                f"composition={requirements.name}"
            )
            return 0
        if args.command == "resolve":
            requirements = (
                args.requirements
                if args.requirements.is_absolute()
                else root / args.requirements
            )
            value = resolve(root, modules, paths, requirements)
            if args.output:
                output = (
                    args.output if args.output.is_absolute() else root / args.output
                )
                write_json(output, value)
                print(f"WROTE {output}")
            else:
                print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))
            return 0
        parser.error(f"unknown command: {args.command}")
    except ContractError as exc:
        print(f"module catalog RED: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"module catalog FATAL: {exc}", file=sys.stderr)
        return 64
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
