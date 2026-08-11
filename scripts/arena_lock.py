#!/usr/bin/env python3
"""Composition lock v1 with complete tracked-path ownership.

The Phase 0 manifest resolver remains in `arena_modules.py`.  This layer adds the
Phase 1 repository ownership subject without duplicating manifest or capability
resolution.  The checked-in composition lock is valid only when both the module
selection and the full `git ls-files` ownership assignment are unchanged.

Exit codes:
  0  valid / command completed
  2  contract violation
  64 usage, missing input, unreadable JSON, or unavailable Git metadata
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

import arena_modules
import arena_ownership


LOCK_SCHEMA = "bettor-arena/composition-lock/v1"


class LockError(ValueError):
    """The augmented composition lock is invalid or stale."""


def default_root() -> Path:
    return Path(__file__).resolve().parents[1]


def augment(base: dict[str, Any], ownership: dict[str, Any]) -> dict[str, Any]:
    value = dict(base)
    value.pop("content_sha256", None)
    value["tracked_files"] = ownership["tracked_files"]
    value["ownership_sha256"] = ownership["ownership_sha256"]
    value["ownership_classes_sha256"] = ownership["ownership_classes_sha256"]
    value["content_sha256"] = arena_modules.digest_value(value)
    return value


def resolve(
    root: Path,
    requirements_path: Path,
    tracked_paths: list[str] | None = None,
) -> dict[str, Any]:
    modules, module_paths = arena_modules.load_modules(root)
    base = arena_modules.resolve(root, modules, module_paths, requirements_path)
    ownership = arena_ownership.snapshot(
        root,
        modules,
        tracked_paths=tracked_paths,
    )
    return augment(base, ownership)


def check(root: Path, requirements_path: Path, lock_path: Path) -> None:
    expected = resolve(root, requirements_path)
    actual = arena_modules.load_json(lock_path)
    if actual.get("schema") != LOCK_SCHEMA:
        raise LockError(f"{lock_path}: schema must be {LOCK_SCHEMA}")
    if actual != expected:
        raise LockError(
            f"{lock_path}: stale composition lock; run "
            f"`python3 scripts/arena_lock.py resolve "
            f"--requirements {requirements_path.relative_to(root)} "
            f"--output {lock_path.relative_to(root)}`"
        )


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def selftest() -> None:
    arena_ownership.selftest()

    base = {
        "schema": LOCK_SCHEMA,
        "composition": "fixture",
        "requirements_sha256": "a" * 64,
        "modules": [],
        "capabilities": {},
        "content_sha256": "obsolete",
    }
    ownership = {
        "tracked_files": 2,
        "ownership_sha256": "b" * 64,
        "ownership_classes_sha256": "c" * 64,
    }
    first = augment(base, ownership)
    second = augment(base, ownership)
    if first != second:
        raise LockError("augmented lock is not deterministic")
    if first["content_sha256"] == "obsolete":
        raise LockError("augmented lock retained the Phase 0 digest")

    moved = dict(ownership)
    moved["tracked_files"] = 3
    changed = augment(base, moved)
    if changed["content_sha256"] == first["content_sha256"]:
        raise LockError("ownership change did not invalidate composition lock")

    with tempfile.TemporaryDirectory(prefix="arena-lock.") as temp:
        output = Path(temp) / "lock.json"
        write_json(output, first)
        loaded = arena_modules.load_json(output)
        if loaded != first:
            raise LockError("composition-lock writer changed bytes semantically")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="arena_lock.py")
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--selftest", action="store_true")
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check")
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

    resolve_parser = subparsers.add_parser("resolve")
    resolve_parser.add_argument("--requirements", type=Path, required=True)
    resolve_parser.add_argument("--output", type=Path)

    subparsers.add_parser("ownership")

    args = parser.parse_args(argv)
    try:
        if args.selftest:
            if args.command is not None:
                parser.error("--selftest cannot be combined with a command")
            selftest()
            print("SELFTEST GREEN: composition ownership lock")
            return 0
        if args.command is None:
            parser.error("a command is required")

        root = args.root.resolve()
        if args.command == "check":
            requirements = (
                args.requirements
                if args.requirements.is_absolute()
                else root / args.requirements
            )
            lock_path = args.lock if args.lock.is_absolute() else root / args.lock
            check(root, requirements, lock_path)
            ownership = arena_ownership.snapshot(
                root,
                arena_modules.load_modules(root)[0],
            )
            print(
                "PASS module catalog and ownership "
                f"({ownership['tracked_files']} tracked paths, "
                f"digest={ownership['ownership_sha256'][:12]})"
            )
            return 0
        if args.command == "resolve":
            requirements = (
                args.requirements
                if args.requirements.is_absolute()
                else root / args.requirements
            )
            value = resolve(root, requirements)
            if args.output:
                output = args.output if args.output.is_absolute() else root / args.output
                write_json(output, value)
                print(f"WROTE {output}")
            else:
                print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))
            return 0
        if args.command == "ownership":
            modules = arena_modules.load_modules(root)[0]
            value = arena_ownership.snapshot(root, modules)
            print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))
            return 0
        parser.error(f"unknown command: {args.command}")
    except (arena_modules.ContractError, arena_ownership.OwnershipError, LockError) as exc:
        print(f"composition lock RED: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"composition lock FATAL: {exc}", file=sys.stderr)
        return 64
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
