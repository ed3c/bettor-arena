#!/usr/bin/env python3
"""Validate Bettor's immutable shared-Skills source pin and generated binding.

The source pin is authored policy. The consumer binding is generated only by the
canonical `skills-shared` synchronizer. This gate reconciles the two without
copying the shared Skill bodies into the consumer repository.

Exit codes:
  0  declared source/binding subject passed
  2  readable subject was evaluated and refused
  64 required input was absent, unreadable, or malformed
  70 checker implementation failure
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PIN = ROOT / ".agents" / "shared-skills.source.json"
DEFAULT_REQUIREMENTS = ROOT / ".agents" / "shared-skills.requirements.json"
DEFAULT_BINDING = ROOT / ".agents" / "bindings" / "bettor-arena.json"

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
INTERFACE_ID = re.compile(r"^[A-Z][A-Z0-9-]*-V[0-9]+$")
FORBIDDEN_PATH_PREFIXES = ("file:", "/Users/", "/home/", "~/")
MUTABLE_REFS = {"main", "master", "latest", "head", "origin/main", "refs/heads/main"}


class Unusable(RuntimeError):
    """The declared subject cannot be read, which is not a policy refusal."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise Unusable(f"unreadable JSON {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise Unusable(f"malformed JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise Unusable(f"JSON root must be an object: {path}")
    return value


def canonical_json(document: dict[str, Any]) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise Unusable(f"unreadable file {path}: {error}") from error


def safe_relative(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = Path(value)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and not value.startswith(FORBIDDEN_PATH_PREFIXES)
    )


def _add(problems: list[str], condition: bool, code: str, message: str) -> None:
    if not condition:
        problems.append(f"{code}: {message}")


def validate_pin(pin: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    expected_top = {"schema", "source", "interfaces", "generator", "consumer"}
    _add(problems, set(pin) == expected_top, "PIN_FIELDS", f"pin fields must be exactly {sorted(expected_top)}")
    _add(problems, pin.get("schema") == "shared-skills/source-pin/v1", "PIN_SCHEMA", "schema must be shared-skills/source-pin/v1")

    source = pin.get("source")
    if not isinstance(source, dict):
        problems.append("PIN_SOURCE: source must be an object")
        source = {}
    _add(problems, set(source) == {"repository", "commit", "tree"}, "PIN_SOURCE_FIELDS", "source must contain exactly repository, commit, and tree")
    repository = source.get("repository")
    _add(
        problems,
        isinstance(repository, str)
        and repository.startswith("https://github.com/")
        and not repository.endswith(".git")
        and "@" not in repository.split("://", 1)[-1].split("/", 1)[0],
        "PIN_REPOSITORY",
        "repository must be a credential-free canonical GitHub URL without .git",
    )
    commit = source.get("commit")
    tree = source.get("tree")
    _add(problems, isinstance(commit, str) and SHA40.fullmatch(commit) is not None, "PIN_COMMIT", "source commit must be an exact lowercase 40-hex SHA")
    _add(problems, isinstance(tree, str) and SHA40.fullmatch(tree) is not None, "PIN_TREE", "source tree must be an exact lowercase 40-hex SHA")
    for field, value in source.items():
        if isinstance(value, str):
            _add(problems, value.lower() not in MUTABLE_REFS, "PIN_MUTABLE_REF", f"source.{field} cannot use mutable ref {value!r}")

    interfaces = pin.get("interfaces")
    if not isinstance(interfaces, list) or not interfaces:
        problems.append("PIN_INTERFACES: interfaces must be a non-empty array")
        interfaces = []
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for index, item in enumerate(interfaces):
        label = f"interfaces[{index}]"
        if not isinstance(item, dict):
            problems.append(f"PIN_INTERFACE_SHAPE: {label} must be an object")
            continue
        _add(problems, set(item) == {"id", "path", "blob"}, "PIN_INTERFACE_FIELDS", f"{label} must contain exactly id, path, and blob")
        interface_id = item.get("id")
        path = item.get("path")
        blob = item.get("blob")
        _add(problems, isinstance(interface_id, str) and INTERFACE_ID.fullmatch(interface_id) is not None, "PIN_INTERFACE_ID", f"{label}.id must be a stable versioned interface ID")
        _add(problems, safe_relative(path), "PIN_INTERFACE_PATH", f"{label}.path must be a safe repository-relative path")
        _add(problems, isinstance(blob, str) and SHA40.fullmatch(blob) is not None, "PIN_INTERFACE_BLOB", f"{label}.blob must be an exact Git blob SHA")
        if isinstance(interface_id, str):
            _add(problems, interface_id not in seen_ids, "PIN_INTERFACE_DUPLICATE", f"duplicate interface ID {interface_id}")
            seen_ids.add(interface_id)
        if isinstance(path, str):
            _add(problems, path not in seen_paths, "PIN_INTERFACE_PATH_DUPLICATE", f"duplicate interface path {path}")
            seen_paths.add(path)

    generator = pin.get("generator")
    if not isinstance(generator, dict):
        problems.append("PIN_GENERATOR: generator must be an object")
        generator = {}
    _add(problems, set(generator) == {"path", "blob"}, "PIN_GENERATOR_FIELDS", "generator must contain exactly path and blob")
    _add(problems, safe_relative(generator.get("path")), "PIN_GENERATOR_PATH", "generator.path must be a safe repository-relative path")
    _add(problems, isinstance(generator.get("blob"), str) and SHA40.fullmatch(generator.get("blob", "")) is not None, "PIN_GENERATOR_BLOB", "generator.blob must be an exact Git blob SHA")

    consumer = pin.get("consumer")
    if not isinstance(consumer, dict):
        problems.append("PIN_CONSUMER: consumer must be an object")
        consumer = {}
    _add(problems, set(consumer) == {"requirements", "binding"}, "PIN_CONSUMER_FIELDS", "consumer must contain exactly requirements and binding")
    for field in ("requirements", "binding"):
        _add(problems, safe_relative(consumer.get(field)), "PIN_CONSUMER_PATH", f"consumer.{field} must be a safe repository-relative path")
    _add(problems, consumer.get("requirements") != consumer.get("binding"), "PIN_CONSUMER_PATH_COLLISION", "requirements and binding paths must be different")
    return problems


def validate_requirements(requirements: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    expected = {"schema", "binding", "shared", "repo_owned", "surfaces"}
    _add(problems, set(requirements) == expected, "REQ_FIELDS", f"requirements fields must be exactly {sorted(expected)}")
    _add(problems, requirements.get("schema") == "shared-skills/consumer-requirements/v1", "REQ_SCHEMA", "requirements schema is not supported")
    binding = requirements.get("binding")
    _add(problems, isinstance(binding, str) and bool(binding) and all(ch in "abcdefghijklmnopqrstuvwxyz0123456789-" for ch in binding), "REQ_BINDING", "binding must use lowercase letters, digits, and hyphens")
    for field in ("shared", "repo_owned"):
        values = requirements.get(field)
        _add(problems, isinstance(values, list) and all(isinstance(value, str) and value for value in values), "REQ_NAMES", f"{field} must be an array of non-empty names")
        if isinstance(values, list):
            _add(problems, len(values) == len(set(values)), "REQ_DUPLICATE", f"{field} names must be unique")
    if isinstance(requirements.get("shared"), list) and isinstance(requirements.get("repo_owned"), list):
        overlap = sorted(set(requirements["shared"]).intersection(requirements["repo_owned"]))
        _add(problems, not overlap, "REQ_OVERLAP", f"names cannot be shared and repo-owned: {', '.join(overlap)}")
    surfaces = requirements.get("surfaces")
    _add(problems, isinstance(surfaces, dict) and set(surfaces) == {"claude", "codex"}, "REQ_SURFACES", "surfaces must contain exactly claude and codex")
    if isinstance(surfaces, dict):
        for carrier, path in surfaces.items():
            _add(problems, safe_relative(path), "REQ_SURFACE_PATH", f"{carrier} surface must be a safe repository-relative path")
    return problems


def validate_binding_shape(binding: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    expected = {"binding", "content_sha256", "registry_sha256", "requirements_sha256", "repo_owned", "schema", "skills", "source", "surfaces"}
    _add(problems, set(binding) == expected, "BINDING_FIELDS", f"binding fields must be exactly {sorted(expected)}")
    _add(problems, binding.get("schema") == "shared-skills/consumer-binding/v1", "BINDING_SCHEMA", "binding schema is not supported")
    for field in ("content_sha256", "registry_sha256", "requirements_sha256"):
        _add(problems, isinstance(binding.get(field), str) and SHA64.fullmatch(binding.get(field, "")) is not None, "BINDING_DIGEST", f"{field} must be a lowercase SHA-256")
    source = binding.get("source")
    _add(problems, isinstance(source, dict) and set(source) == {"repository", "commit", "tree"}, "BINDING_SOURCE", "binding source must contain exactly repository, commit, and tree")
    if isinstance(source, dict):
        _add(problems, isinstance(source.get("commit"), str) and SHA40.fullmatch(source.get("commit", "")) is not None, "BINDING_SOURCE_COMMIT", "binding source commit must be exact")
        _add(problems, isinstance(source.get("tree"), str) and SHA40.fullmatch(source.get("tree", "")) is not None, "BINDING_SOURCE_TREE", "binding source tree must be exact")
    skills = binding.get("skills")
    if not isinstance(skills, list):
        problems.append("BINDING_SKILLS: skills must be an array")
        skills = []
    names: list[str] = []
    for index, skill in enumerate(skills):
        label = f"skills[{index}]"
        if not isinstance(skill, dict):
            problems.append(f"BINDING_SKILL_SHAPE: {label} must be an object")
            continue
        _add(problems, set(skill) == {"name", "entrypoint", "content_sha256"}, "BINDING_SKILL_FIELDS", f"{label} fields drifted")
        name = skill.get("name")
        entrypoint = skill.get("entrypoint")
        _add(problems, isinstance(name, str) and bool(name), "BINDING_SKILL_NAME", f"{label}.name must be non-empty")
        _add(problems, isinstance(name, str) and entrypoint == f"skills/{name}/SKILL.md", "BINDING_ENTRYPOINT", f"{label}.entrypoint must resolve the canonical Skill entrypoint")
        _add(problems, isinstance(skill.get("content_sha256"), str) and SHA64.fullmatch(skill.get("content_sha256", "")) is not None, "BINDING_SKILL_DIGEST", f"{label}.content_sha256 must be a SHA-256")
        if isinstance(name, str):
            names.append(name)
    _add(problems, names == sorted(names), "BINDING_SKILL_ORDER", "binding skills must use stable sorted order")
    _add(problems, len(names) == len(set(names)), "BINDING_SKILL_DUPLICATE", "binding skill names must be unique")
    return problems


def validate_relation(pin: dict[str, Any], requirements: dict[str, Any], binding: dict[str, Any], *, requirements_digest: str) -> list[str]:
    problems: list[str] = []
    source = pin.get("source") if isinstance(pin.get("source"), dict) else {}
    binding_source = binding.get("source") if isinstance(binding.get("source"), dict) else {}
    _add(problems, binding_source == source, "REL_SOURCE", "generated binding source must equal the authored immutable source pin")
    _add(problems, binding.get("binding") == requirements.get("binding"), "REL_BINDING_NAME", "binding name must equal requirements.binding")
    _add(problems, binding.get("requirements_sha256") == requirements_digest, "REL_REQUIREMENTS_DIGEST", "binding requirements digest must equal the current requirements bytes")
    _add(problems, binding.get("repo_owned") == sorted(requirements.get("repo_owned", [])), "REL_REPO_OWNED", "binding repo_owned set must equal the sorted requirements set")
    _add(problems, binding.get("surfaces") == requirements.get("surfaces"), "REL_SURFACES", "binding surfaces must equal requirements surfaces")
    requested = sorted(requirements.get("shared", []))
    observed = [skill.get("name") for skill in binding.get("skills", []) if isinstance(skill, dict)]
    _add(problems, observed == requested, "REL_SHARED_SKILLS", "binding selected Skill names must equal the requirements set")
    unsigned = copy.deepcopy(binding)
    declared = unsigned.pop("content_sha256", None)
    measured = hashlib.sha256(canonical_json(unsigned).encode("utf-8")).hexdigest()
    _add(problems, declared == measured, "REL_BINDING_DIGEST", "binding content_sha256 must be recomputed from the generated document")
    consumer = pin.get("consumer") if isinstance(pin.get("consumer"), dict) else {}
    _add(problems, consumer.get("requirements") == ".agents/shared-skills.requirements.json", "REL_REQUIREMENTS_ROUTE", "source pin must name the canonical Bettor requirements route")
    _add(problems, consumer.get("binding") == ".agents/bindings/bettor-arena.json", "REL_BINDING_ROUTE", "source pin must name the canonical Bettor binding route")
    return problems


def git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(["git", "-C", str(root), *arguments], capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git failed"
        raise Unusable(f"git {' '.join(arguments)} failed in {root}: {detail}")
    return completed.stdout.strip()


def normalize_repository(value: str) -> str:
    value = value.strip()
    if value.startswith("git@") and ":" in value:
        host, path = value[4:].split(":", 1)
        value = f"https://{host}/{path}"
    return value.removesuffix(".git")


def tracked_blob(root: Path, path: str) -> str:
    output = git(root, "ls-files", "-s", "--", path)
    rows = [line for line in output.splitlines() if line.strip()]
    if len(rows) != 1:
        raise Unusable(f"expected one tracked entry for {path}, found {len(rows)}")
    fields = rows[0].split(maxsplit=3)
    if len(fields) != 4:
        raise Unusable(f"cannot parse tracked entry for {path}")
    return fields[1]


def validate_shared_root(pin: dict[str, Any], shared_root: Path) -> list[str]:
    problems: list[str] = []
    if not shared_root.is_dir():
        raise Unusable(f"shared root does not exist: {shared_root}")
    source = pin["source"]
    head = git(shared_root, "rev-parse", "HEAD")
    tree = git(shared_root, "rev-parse", "HEAD^{tree}")
    status = git(shared_root, "status", "--porcelain", "--untracked-files=all")
    _add(problems, head == source["commit"], "SOURCE_COMMIT", f"shared checkout HEAD {head} does not equal pin {source['commit']}")
    _add(problems, tree == source["tree"], "SOURCE_TREE", f"shared checkout tree {tree} does not equal pin {source['tree']}")
    _add(problems, status == "", "SOURCE_DIRTY", "shared checkout must be clean before canonical generation")
    remote = normalize_repository(git(shared_root, "remote", "get-url", "origin"))
    _add(problems, remote == source["repository"], "SOURCE_REPOSITORY", f"shared checkout origin {remote!r} does not equal pin")
    for interface in pin["interfaces"]:
        observed = tracked_blob(shared_root, interface["path"])
        _add(problems, observed == interface["blob"], "SOURCE_INTERFACE_BLOB", f"{interface['id']} blob {observed} does not equal pin {interface['blob']}")
        try:
            body = (shared_root / interface["path"]).read_text(encoding="utf-8")
        except OSError as error:
            raise Unusable(f"cannot read interface {interface['path']}: {error}") from error
        _add(problems, f"Document ID: `{interface['id']}`" in body, "SOURCE_INTERFACE_ID", f"{interface['path']} does not declare {interface['id']}")
        _add(problems, "Document Role: `CANONICAL_METHOD`" in body, "SOURCE_INTERFACE_ROLE", f"{interface['path']} is not the canonical method")
        _add(problems, "Repository Plane: `INSTRUCTION`" in body, "SOURCE_INTERFACE_PLANE", f"{interface['path']} is not in the Instruction plane")
    generator = pin["generator"]
    observed_generator = tracked_blob(shared_root, generator["path"])
    _add(problems, observed_generator == generator["blob"], "SOURCE_GENERATOR_BLOB", "canonical generator blob does not equal the authored pin")
    return problems


def evaluate(*, pin_path: Path, requirements_path: Path, binding_path: Path, shared_root: Path | None, source_only: bool) -> list[str]:
    pin = load_json(pin_path)
    problems = validate_pin(pin)
    if shared_root is not None and not problems:
        problems.extend(validate_shared_root(pin, shared_root))
    if source_only:
        return problems
    requirements = load_json(requirements_path)
    binding = load_json(binding_path)
    problems.extend(validate_requirements(requirements))
    problems.extend(validate_binding_shape(binding))
    problems.extend(validate_relation(pin, requirements, binding, requirements_digest=sha256_file(requirements_path)))
    return problems


def _valid_documents() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    requirements = {
        "binding": "bettor-arena",
        "repo_owned": ["local"],
        "schema": "shared-skills/consumer-requirements/v1",
        "shared": ["alpha", "beta"],
        "surfaces": {"claude": ".claude/skills", "codex": ".agents/skills"},
    }
    pin = {
        "schema": "shared-skills/source-pin/v1",
        "source": {"repository": "https://github.com/ed3c/skills-shared", "commit": "1" * 40, "tree": "2" * 40},
        "interfaces": [{"id": "DOMAIN-DECOUPLING-V1", "path": "docs/architecture/DOMAIN_DECOUPLING.md", "blob": "3" * 40}],
        "generator": {"path": "skills/shared-skills-infra/scripts/shared_skills.py", "blob": "4" * 40},
        "consumer": {"requirements": ".agents/shared-skills.requirements.json", "binding": ".agents/bindings/bettor-arena.json"},
    }
    requirements_bytes = json.dumps(requirements, indent=2, sort_keys=True) + "\n"
    binding: dict[str, Any] = {
        "binding": "bettor-arena",
        "registry_sha256": "5" * 64,
        "requirements_sha256": hashlib.sha256(requirements_bytes.encode()).hexdigest(),
        "repo_owned": ["local"],
        "schema": "shared-skills/consumer-binding/v1",
        "skills": [
            {"name": "alpha", "entrypoint": "skills/alpha/SKILL.md", "content_sha256": "6" * 64},
            {"name": "beta", "entrypoint": "skills/beta/SKILL.md", "content_sha256": "7" * 64},
        ],
        "source": copy.deepcopy(pin["source"]),
        "surfaces": copy.deepcopy(requirements["surfaces"]),
    }
    binding["content_sha256"] = hashlib.sha256(canonical_json(binding).encode()).hexdigest()
    return pin, requirements, binding


def selftest() -> int:
    pin, requirements, binding = _valid_documents()
    expected = {
        "mutable-ref": "PIN_COMMIT",
        "absolute-interface-path": "PIN_INTERFACE_PATH",
        "wrong-source": "REL_SOURCE",
        "stale-requirements": "REL_REQUIREMENTS_DIGEST",
        "missing-skill": "REL_SHARED_SKILLS",
        "wrong-entrypoint": "BINDING_ENTRYPOINT",
        "stale-binding-digest": "REL_BINDING_DIGEST",
        "unsafe-surface": "REQ_SURFACE_PATH",
    }
    mutations: dict[str, tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = {}
    p, r, b = copy.deepcopy((pin, requirements, binding)); p["source"]["commit"] = "main"; mutations["mutable-ref"] = (p, r, b)
    p, r, b = copy.deepcopy((pin, requirements, binding)); p["interfaces"][0]["path"] = "/Users/example/private.md"; mutations["absolute-interface-path"] = (p, r, b)
    p, r, b = copy.deepcopy((pin, requirements, binding)); b["source"]["commit"] = "8" * 40; mutations["wrong-source"] = (p, r, b)
    p, r, b = copy.deepcopy((pin, requirements, binding)); b["requirements_sha256"] = "9" * 64; mutations["stale-requirements"] = (p, r, b)
    p, r, b = copy.deepcopy((pin, requirements, binding)); b["skills"] = b["skills"][:-1]; mutations["missing-skill"] = (p, r, b)
    p, r, b = copy.deepcopy((pin, requirements, binding)); b["skills"][0]["entrypoint"] = "copied/SKILL.md"; mutations["wrong-entrypoint"] = (p, r, b)
    p, r, b = copy.deepcopy((pin, requirements, binding)); b["content_sha256"] = "a" * 64; mutations["stale-binding-digest"] = (p, r, b)
    p, r, b = copy.deepcopy((pin, requirements, binding)); r["surfaces"]["codex"] = "/home/user/.agents/skills"; mutations["unsafe-surface"] = (p, r, b)

    req_bytes = json.dumps(requirements, indent=2, sort_keys=True) + "\n"
    good = validate_pin(pin) + validate_requirements(requirements) + validate_binding_shape(binding) + validate_relation(pin, requirements, binding, requirements_digest=hashlib.sha256(req_bytes.encode()).hexdigest())
    if good:
        print("SELFTEST RED: positive fixture failed", file=sys.stderr)
        return 2
    for name, (candidate_pin, candidate_req, candidate_binding) in mutations.items():
        candidate_req_bytes = json.dumps(candidate_req, indent=2, sort_keys=True) + "\n"
        problems = validate_pin(candidate_pin) + validate_requirements(candidate_req) + validate_binding_shape(candidate_binding) + validate_relation(candidate_pin, candidate_req, candidate_binding, requirements_digest=hashlib.sha256(candidate_req_bytes.encode()).hexdigest())
        marker = expected[name]
        if not any(problem.startswith(marker + ":") for problem in problems):
            print(f"SELFTEST RED: {name} did not trigger expected {marker}", file=sys.stderr)
            return 2
    print(f"SELFTEST GREEN: positive fixture passed; {len(mutations)} mutations refused")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pin", type=Path, default=DEFAULT_PIN)
    parser.add_argument("--requirements", type=Path, default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--binding", type=Path, default=DEFAULT_BINDING)
    parser.add_argument("--shared-root", type=Path)
    parser.add_argument("--source-only", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    try:
        problems = evaluate(pin_path=args.pin, requirements_path=args.requirements, binding_path=args.binding, shared_root=args.shared_root, source_only=args.source_only)
    except Unusable as error:
        print(f"SHARED-SKILLS-BINDING-UNUSABLE: {error}", file=sys.stderr)
        return 64
    except Exception as error:
        print(f"SHARED-SKILLS-BINDING-INTERNAL: {type(error).__name__}: {error}", file=sys.stderr)
        return 70
    if problems:
        for problem in problems:
            print(f"SHARED-SKILLS-BINDING-RED: {problem}", file=sys.stderr)
        return 2
    mode = "source+binding" if not args.source_only else "source"
    print(f"SHARED-SKILLS-BINDING-GREEN: {mode} contract verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
