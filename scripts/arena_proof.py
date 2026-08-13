#!/usr/bin/env python3
"""Module-scoped proof identity and receipt validation for bettor-arena.

A module subject is keyed by:
- Git path/mode/blob identity for the module implementation closure;
- the module manifest and proof specification;
- selected shared/repo-owned Skill identities;
- selected runtime projection identity; and
- direct capability-provider closure digests.

Generated composition projections and versioned evidence remain release-level
inputs, so an isolated implementation change in module A does not invalidate an
unrelated module B.  PASS, FAIL, ABSENT, and NOT_EXERCISED remain distinct.

Exit codes:
  0  valid / command completed
  2  contract violation
  64 usage, missing input, unreadable JSON, or unavailable Git metadata
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

import arena_index
import arena_lock
import arena_modules
import arena_ownership


SUBJECT_SCHEMA = "bettor-arena/module-subject-lock/v1"
EVIDENCE_SCHEMA = "bettor-arena/module-evidence-receipt/v1"
RELEASE_SCHEMA = "bettor-arena/module-release-receipt/v1"
EVIDENCE_KINDS = ("proof", "control", "mutation")
EVIDENCE_STATES = {"PASS", "FAIL", "ABSENT", "NOT_EXERCISED"}
RELEASE_PROJECTION_PREFIXES = (
    ".arena/compositions",
    ".arena/contexts.lock.json",
    ".arena/locks",
    ".arena/presets",
)


class ProofError(ValueError):
    """A module proof subject or receipt is invalid."""


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def digest_value(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def default_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict[str, Any]:
    return arena_modules.load_json(path)


def manifest_owner(path: str, selected: set[str]) -> str | None:
    parts = Path(path).parts
    if (
        len(parts) == 4
        and parts[:2] == (".arena", "modules")
        and parts[3] == "module.json"
    ):
        module_id = parts[2]
        return module_id if module_id in selected else None
    return None


def release_projection(path: str) -> bool:
    return any(
        path == prefix or path.startswith(prefix + "/")
        for prefix in RELEASE_PROJECTION_PREFIXES
    )


def projected_module_paths(
    modules: dict[str, dict[str, Any]],
    ownership: dict[str, Any],
    selected: set[str],
) -> dict[str, list[str]]:
    result = {module_id: [] for module_id in selected}
    for assignment in ownership["assignments"]:
        path = assignment["path"]
        implicit = manifest_owner(path, selected)
        if implicit is not None:
            result[implicit].append(path)
            continue
        if release_projection(path):
            continue
        if assignment["type"] == "module" and assignment["subject"] in selected:
            result[assignment["subject"]].append(path)
    return {key: sorted(set(value)) for key, value in result.items()}


def path_entry_digest(entries: dict[str, dict[str, str]], paths: list[str]) -> str:
    selected: list[dict[str, str]] = []
    for path in paths:
        entry = entries.get(path)
        if entry is None:
            raise ProofError(f"owned path is not in the Git index: {path}")
        selected.append(entry)
    return digest_value(selected)


def load_shared_skills(root: Path) -> dict[str, str]:
    path = root / ".agents" / "bindings" / "bettor-arena.json"
    if not path.is_file():
        return {}
    value = read_json(path)
    skills = value.get("skills", [])
    if not isinstance(skills, list):
        raise ProofError(f"{path}: skills must be an array")
    result: dict[str, str] = {}
    for item in skills:
        if not isinstance(item, dict):
            raise ProofError(f"{path}: malformed skill binding")
        name = item.get("name")
        digest = item.get("content_sha256")
        if isinstance(name, str) and isinstance(digest, str):
            result[name] = digest
    return result


def entries_under(
    entries: dict[str, dict[str, str]], prefix: str
) -> list[dict[str, str]]:
    return [
        entries[path]
        for path in sorted(entries)
        if path == prefix or path.startswith(prefix + "/")
    ]


def repo_owned_skill_input(
    name: str,
    entries: dict[str, dict[str, str]],
) -> dict[str, Any]:
    candidates = [
        f".agents/skills/{name}",
        f".claude/skills/{name}",
    ]
    if name == "openwiki-port":
        candidates.append("kb-ingest/skill")
    matched: list[dict[str, str]] = []
    for prefix in candidates:
        matched.extend(entries_under(entries, prefix))
    unique = {entry["path"]: entry for entry in matched}
    if not unique:
        return {"name": name, "scope": "repo-owned", "state": "ABSENT", "sha256": None}
    values = [unique[path] for path in sorted(unique)]
    return {
        "name": name,
        "scope": "repo-owned",
        "state": "PRESENT",
        "sha256": digest_value(values),
    }


def skill_inputs(
    module: dict[str, Any],
    shared: dict[str, str],
    entries: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for name in sorted(module["skills"]["required"]):
        digest = shared.get(name)
        result.append(
            {
                "name": name,
                "scope": "shared",
                "state": "PRESENT" if digest else "ABSENT",
                "sha256": digest,
            }
        )
    for name in sorted(module["skills"]["optional"]):
        digest = shared.get(name)
        if digest:
            result.append(
                {
                    "name": name,
                    "scope": "shared-optional",
                    "state": "PRESENT",
                    "sha256": digest,
                }
            )
    for name in sorted(module["skills"]["repo_owned"]):
        result.append(repo_owned_skill_input(name, entries))
    return result


def runtime_input(
    module: dict[str, Any],
    entries: dict[str, dict[str, str]],
) -> dict[str, Any]:
    profiles = sorted(module["runtime"]["profiles"])
    if not profiles:
        return {"profiles": [], "state": "NOT_REQUIRED", "sha256": None}
    runtime_entries = entries_under(entries, ".runtime-env")
    return {
        "profiles": profiles,
        "state": "PRESENT" if runtime_entries else "ABSENT",
        "sha256": digest_value(runtime_entries) if runtime_entries else None,
    }


def local_subjects(
    root: Path,
    modules: dict[str, dict[str, Any]],
    selected: set[str],
    entries: dict[str, dict[str, str]],
    ownership: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    paths_by_module = projected_module_paths(modules, ownership, selected)
    shared = load_shared_skills(root)
    result: dict[str, dict[str, Any]] = {}
    for module_id in sorted(selected):
        module = modules[module_id]
        paths = paths_by_module[module_id]
        files = [entries[path] for path in paths]
        skills = skill_inputs(module, shared, entries)
        runtime = runtime_input(module, entries)
        proof_sha = digest_value(module["proof"])
        unsigned: dict[str, Any] = {
            "id": module_id,
            "interface_version": module["interface_version"],
            "owned_files": len(files),
            "files_sha256": digest_value(files),
            "manifest_sha256": digest_value(module),
            "proof_spec_sha256": proof_sha,
            "skills": skills,
            "runtime": runtime,
        }
        unsigned["local_sha256"] = digest_value(unsigned)
        result[module_id] = unsigned
    return result


def dependency_map(
    modules: dict[str, dict[str, Any]],
    selected: set[str],
) -> dict[str, list[dict[str, str]]]:
    providers = arena_modules.validate_capabilities(modules)
    result: dict[str, list[dict[str, str]]] = {}
    for module_id in sorted(selected):
        dependencies: list[dict[str, str]] = []
        for capability in sorted(modules[module_id]["requires"]):
            if capability.startswith("external:"):
                dependencies.append({"capability": capability, "provider": "EXTERNAL"})
                continue
            provider = providers.get(capability)
            if provider is None or provider not in selected:
                raise ProofError(
                    f"{module_id} proof subject cannot resolve capability {capability}"
                )
            dependencies.append({"capability": capability, "provider": provider})
        result[module_id] = dependencies
    return result


def close_subjects(
    local: dict[str, dict[str, Any]],
    dependencies: dict[str, list[dict[str, str]]],
) -> dict[str, dict[str, Any]]:
    resolved: dict[str, dict[str, Any]] = {}
    visiting: set[str] = set()

    def visit(module_id: str) -> dict[str, Any]:
        if module_id in resolved:
            return resolved[module_id]
        if module_id in visiting:
            raise ProofError(f"module dependency cycle reaches {module_id}")
        visiting.add(module_id)
        closed_dependencies: list[dict[str, str]] = []
        for dependency in dependencies[module_id]:
            provider = dependency["provider"]
            if provider == "EXTERNAL":
                closed_dependencies.append(
                    {
                        "capability": dependency["capability"],
                        "provider": provider,
                        "closure_sha256": digest_value(dependency),
                    }
                )
            else:
                provider_subject = visit(provider)
                closed_dependencies.append(
                    {
                        "capability": dependency["capability"],
                        "provider": provider,
                        "closure_sha256": provider_subject["closure_sha256"],
                    }
                )
        unsigned = dict(local[module_id])
        unsigned["dependencies"] = closed_dependencies
        unsigned["closure_sha256"] = digest_value(unsigned)
        resolved[module_id] = unsigned
        visiting.remove(module_id)
        return unsigned

    for module_id in sorted(local):
        visit(module_id)
    return resolved


def subject_lock(
    root: Path,
    entries: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    modules, _ = arena_modules.load_modules(root)
    composition_lock = read_json(root / ".arena" / "locks" / "bettor-arena.lock.json")
    selected = {item["id"] for item in composition_lock["modules"]}
    missing = selected - set(modules)
    if missing:
        raise ProofError(f"composition selects missing modules: {sorted(missing)}")
    entries = entries if entries is not None else arena_index.git_entries(root)
    ownership = arena_ownership.snapshot(root, modules, tracked_paths=entries.keys())
    local = local_subjects(root, modules, selected, entries, ownership)
    dependencies = dependency_map(modules, selected)
    closed = close_subjects(local, dependencies)
    unsigned: dict[str, Any] = {
        "schema": SUBJECT_SCHEMA,
        "composition": composition_lock["composition"],
        "composition_lock_sha256": digest_bytes(
            (root / ".arena" / "locks" / "bettor-arena.lock.json").read_bytes()
        ),
        "modules": [closed[module_id] for module_id in sorted(closed)],
    }
    unsigned["content_sha256"] = digest_value(unsigned)
    return unsigned


def validate_evidence(
    receipt: dict[str, Any],
    subject: dict[str, Any],
    kind: str,
) -> None:
    required = {
        "schema",
        "module",
        "interface_version",
        "closure_sha256",
        "kind",
        "status",
        "command",
        "exit",
        "evidence_sha256",
        "note",
    }
    if set(receipt) != required:
        raise ProofError(f"evidence receipt fields drifted: {receipt.get('module')}")
    if receipt["schema"] != EVIDENCE_SCHEMA:
        raise ProofError("unsupported evidence receipt schema")
    if receipt["module"] != subject["id"]:
        raise ProofError("evidence receipt module does not match subject")
    if receipt["interface_version"] != subject["interface_version"]:
        raise ProofError("evidence receipt interface does not match subject")
    if receipt["closure_sha256"] != subject["closure_sha256"]:
        raise ProofError("evidence receipt closure is stale")
    if receipt["kind"] != kind:
        raise ProofError("evidence receipt kind does not match its slot")
    if receipt["status"] not in EVIDENCE_STATES:
        raise ProofError(f"invalid evidence status: {receipt['status']}")
    if receipt["status"] == "PASS":
        if receipt["exit"] != 0 or not isinstance(receipt["evidence_sha256"], str):
            raise ProofError("PASS evidence requires exit 0 and evidence sha256")
    if receipt["status"] == "NOT_EXERCISED":
        if receipt["exit"] is not None or receipt["evidence_sha256"] is not None:
            raise ProofError("NOT_EXERCISED may not carry fake execution evidence")


def release_receipt(
    root: Path,
    subjects: dict[str, Any],
    evidence_root: Path,
) -> dict[str, Any]:
    module_entries: list[dict[str, Any]] = []
    overall = "PASS"
    for subject in subjects["modules"]:
        evidence: dict[str, str] = {}
        for kind in EVIDENCE_KINDS:
            path = evidence_root / subject["id"] / f"{kind}.json"
            if path.is_file():
                receipt = read_json(path)
                validate_evidence(receipt, subject, kind)
                state = receipt["status"]
            else:
                state = "NOT_EXERCISED"
            evidence[kind] = state
            if state != "PASS":
                overall = (
                    "NOT_EXERCISED"
                    if state == "NOT_EXERCISED" and overall == "PASS"
                    else overall
                )
                if state in {"FAIL", "ABSENT"}:
                    overall = "FAIL"
        module_entries.append(
            {
                "id": subject["id"],
                "interface_version": subject["interface_version"],
                "closure_sha256": subject["closure_sha256"],
                "evidence": evidence,
            }
        )
    unsigned: dict[str, Any] = {
        "schema": RELEASE_SCHEMA,
        "composition": subjects["composition"],
        "composition_lock_sha256": subjects["composition_lock_sha256"],
        "subject_lock_sha256": digest_value(subjects),
        "status": overall,
        "modules": module_entries,
    }
    unsigned["content_sha256"] = digest_value(unsigned)
    return unsigned


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def check(
    root: Path,
    subjects_path: Path,
    release_path: Path,
    entries: dict[str, dict[str, str]] | None = None,
) -> None:
    expected_subjects = subject_lock(root, entries=entries)
    actual_subjects = read_json(subjects_path)
    if actual_subjects != expected_subjects:
        raise ProofError(
            f"{subjects_path}: stale module subjects; run `python3 scripts/arena_proof.py subjects --output {subjects_path.relative_to(root)}`"
        )
    expected_release = release_receipt(
        root,
        expected_subjects,
        root / "data" / "module-proof" / "evidence",
    )
    actual_release = read_json(release_path)
    if actual_release != expected_release:
        raise ProofError(
            f"{release_path}: stale release receipt; run `python3 scripts/arena_proof.py release --output {release_path.relative_to(root)}`"
        )


def selftest() -> None:
    local = {
        "a": {"id": "a", "interface_version": "1", "local_sha256": "a1"},
        "b": {"id": "b", "interface_version": "1", "local_sha256": "b1"},
        "c": {"id": "c", "interface_version": "1", "local_sha256": "c1"},
    }
    dependencies = {
        "a": [],
        "b": [],
        "c": [{"capability": "a/v1", "provider": "a"}],
    }
    first = close_subjects(local, dependencies)
    changed_local = json.loads(json.dumps(local))
    changed_local["a"]["local_sha256"] = "a2"
    second = close_subjects(changed_local, dependencies)
    if first["b"]["closure_sha256"] != second["b"]["closure_sha256"]:
        raise ProofError("unrelated module B was invalidated by module A")
    if first["a"]["closure_sha256"] == second["a"]["closure_sha256"]:
        raise ProofError("changed module A retained its closure")
    if first["c"]["closure_sha256"] == second["c"]["closure_sha256"]:
        raise ProofError("dependent module C ignored provider A change")

    subject = {
        "id": "a",
        "interface_version": "1",
        "closure_sha256": first["a"]["closure_sha256"],
    }
    not_run = {
        "schema": EVIDENCE_SCHEMA,
        "module": "a",
        "interface_version": "1",
        "closure_sha256": subject["closure_sha256"],
        "kind": "proof",
        "status": "NOT_EXERCISED",
        "command": ["false"],
        "exit": None,
        "evidence_sha256": None,
        "note": "fixture",
    }
    validate_evidence(not_run, subject, "proof")
    broken = dict(not_run)
    broken["status"] = "PASS"
    try:
        validate_evidence(broken, subject, "proof")
    except ProofError:
        pass
    else:
        raise ProofError("negative control accepted PASS without execution evidence")
    broken = dict(not_run)
    broken["closure_sha256"] = "0" * 64
    try:
        validate_evidence(broken, subject, "proof")
    except ProofError:
        pass
    else:
        raise ProofError("negative control accepted stale evidence closure")

    with tempfile.TemporaryDirectory(prefix="arena-proof.") as temp:
        path = Path(temp) / "receipt.json"
        write_json(path, not_run)
        if read_json(path) != not_run:
            raise ProofError("receipt writer changed receipt semantics")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="arena_proof.py")
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--index-manifest", type=Path)
    parser.add_argument("--selftest", action="store_true")
    subparsers = parser.add_subparsers(dest="command")

    subjects_parser = subparsers.add_parser("subjects")
    subjects_parser.add_argument("--output", type=Path)

    release_parser = subparsers.add_parser("release")
    release_parser.add_argument(
        "--subjects", type=Path, default=Path("data/module-proof/subjects.lock.json")
    )
    release_parser.add_argument("--output", type=Path)

    check_parser = subparsers.add_parser("check")
    check_parser.add_argument(
        "--subjects", type=Path, default=Path("data/module-proof/subjects.lock.json")
    )
    check_parser.add_argument(
        "--release", type=Path, default=Path("data/module-proof/release-receipt.json")
    )

    args = parser.parse_args(argv)
    try:
        if args.selftest:
            if args.command is not None:
                parser.error("--selftest cannot be combined with a command")
            selftest()
            print("SELFTEST GREEN: module proof identity")
            return 0
        if args.command is None:
            parser.error("a command is required")
        root = args.root.resolve()
        entries = (
            arena_index.load_entries(args.index_manifest)
            if args.index_manifest
            else None
        )
        if args.command == "subjects":
            value = subject_lock(root, entries=entries)
            if args.output:
                output = (
                    args.output if args.output.is_absolute() else root / args.output
                )
                write_json(output, value)
                print(f"WROTE {output}")
            else:
                print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))
            return 0
        if args.command == "release":
            subjects_path = (
                args.subjects if args.subjects.is_absolute() else root / args.subjects
            )
            subjects = read_json(subjects_path)
            value = release_receipt(
                root,
                subjects,
                root / "data" / "module-proof" / "evidence",
            )
            if args.output:
                output = (
                    args.output if args.output.is_absolute() else root / args.output
                )
                write_json(output, value)
                print(f"WROTE {output}")
            else:
                print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))
            return 0
        if args.command == "check":
            subjects_path = (
                args.subjects if args.subjects.is_absolute() else root / args.subjects
            )
            release_path = (
                args.release if args.release.is_absolute() else root / args.release
            )
            check(root, subjects_path, release_path, entries=entries)
            print("PASS module proof subjects and release receipt")
            return 0
        parser.error(f"unknown command: {args.command}")
    except (
        ProofError,
        arena_index.IndexError,
        arena_modules.ContractError,
        arena_ownership.OwnershipError,
        arena_lock.LockError,
    ) as exc:
        print(f"module proof RED: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"module proof FATAL: {exc}", file=sys.stderr)
        return 64
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
