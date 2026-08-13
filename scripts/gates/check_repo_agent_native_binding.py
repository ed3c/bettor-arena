#!/usr/bin/env python3
"""Validate the Bettor consumer binding for the shared repo-agent-native Skill."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

BINDING_REL = Path(".skill-bindings/repo-agent-native/binding.json")
BINDING_DIR_REL = BINDING_REL.parent
DOCS_AGENT_REL = Path("docs/agents")
MCP_JSON_REL = Path(".mcp.json")
CODEX_TOML_REL = Path(".codex/config.toml")
EVIDENCE_STATES = {
    "PASS",
    "FAIL",
    "ABSENT",
    "NOT_IMPLEMENTED",
    "NOT_EXERCISED",
    "SKIPPED_BY_POLICY",
}
CONFIG_STATES = {"BUILT_IN", "CONFIGURED", "NOT_CONFIGURED"}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
MACOS_HOME_ROOT = "/Use" + "rs/"
LINUX_HOME_ROOT = "/ho" + "me/"
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "token-like value": re.compile(
        r"(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|secret)\s*[:=]\s*[\"']?"
        r"(?:sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9]{12,}|[A-Za-z0-9+/]{24,}={0,2})"
    ),
    "macOS absolute user path": re.compile(re.escape(MACOS_HOME_ROOT) + r"[^/\s`]+/"),
    "Linux absolute home path": re.compile(re.escape(LINUX_HOME_ROOT) + r"[^/\s`]+/"),
}
REQUIRED_DOC_HEADINGS = {
    DOCS_AGENT_REL / "README.md": {
        "## Document authority",
        "## Mandatory route",
        "## Change contract",
    },
    DOCS_AGENT_REL / "domain.md": {
        "## Read order",
        "## Context documents",
        "## ADR policy",
        "## Evidence boundary",
        "## Change contract",
    },
    DOCS_AGENT_REL / "issue-tracker.md": {
        "## System of record",
        "## Read and write policy",
        "## Traceability",
        "## Change contract",
    },
}


class BindingError(Exception):
    pass


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BindingError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise BindingError(f"{path}: top level must be an object")
    return value


def load_toml(path: Path) -> dict:
    try:
        value = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise BindingError(f"{path}: invalid TOML: {exc}") from exc
    if not isinstance(value, dict):
        raise BindingError(f"{path}: top level must be a table")
    return value


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def inside(root: Path, raw: str, *, label: str) -> Path:
    if not nonempty(raw):
        raise BindingError(f"{label}: path must be a non-empty string")
    if Path(raw).is_absolute():
        raise BindingError(f"{label}: absolute path is forbidden: {raw}")
    path = (root / raw).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise BindingError(f"{label}: path escapes repository: {raw}") from exc
    return path


def git_mode(root: Path, raw: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-s", "--", raw],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise BindingError(f"git ls-files failed for {raw}: {result.stderr.strip()}")
    line = result.stdout.strip().splitlines()
    if not line:
        return None
    return line[0].split(maxsplit=1)[0]


def serialized(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def validate_docs(root: Path, errors: list[str]) -> None:
    for relative, required in REQUIRED_DOC_HEADINGS.items():
        path = root / relative
        if not path.is_file():
            errors.append(f"missing Agent policy document: {relative}")
            continue
        headings = set(path.read_text(encoding="utf-8").splitlines())
        missing = sorted(required - headings)
        if missing:
            errors.append(f"{relative}: missing headings: {', '.join(missing)}")


def validate_no_sensitive_material(root: Path, errors: list[str]) -> None:
    paths: list[Path] = []
    for base in (root / BINDING_DIR_REL, root / DOCS_AGENT_REL):
        if base.is_dir():
            paths.extend(p for p in base.rglob("*") if p.is_file())
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"{path.relative_to(root)}: binding docs must be UTF-8 text")
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{path.relative_to(root)}: forbidden {label}")


def validate(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    try:
        binding = load_json(root / BINDING_REL)
        mcp_json = load_json(root / MCP_JSON_REL)
        codex_toml = load_toml(root / CODEX_TOML_REL)
    except BindingError as exc:
        return [str(exc)]

    if binding.get("schema_version") != "repo-agent-native-binding/v1":
        errors.append("binding.json: unsupported schema_version")

    consumer = binding.get("consumer")
    if (
        not isinstance(consumer, dict)
        or consumer.get("repository") != "ed3c/bettor-arena"
    ):
        errors.append("binding.json: consumer.repository must be ed3c/bettor-arena")

    skill = binding.get("skill")
    if not isinstance(skill, dict):
        errors.append("binding.json: skill must be an object")
        skill = {}
    if skill.get("name") != "repo-agent-native":
        errors.append("binding.json: skill.name mismatch")
    if skill.get("canonical_repository") != "ed3c/skills-shared":
        errors.append("binding.json: canonical_repository mismatch")
    if not SHA40.fullmatch(str(skill.get("candidate_commit", ""))):
        errors.append(
            "binding.json: skill.candidate_commit must be a lowercase 40-hex SHA"
        )
    if skill.get("candidate_state") not in EVIDENCE_STATES:
        errors.append("binding.json: skill.candidate_state is unsupported")

    projection_paths = skill.get("projection_paths")
    if not isinstance(projection_paths, list) or not projection_paths:
        errors.append("binding.json: skill.projection_paths must be a non-empty array")
        projection_paths = []
    for raw in projection_paths:
        if not nonempty(raw):
            errors.append("binding.json: projection paths must be non-empty strings")
            continue
        try:
            relative = Path(raw)
            if relative.is_absolute() or ".." in relative.parts:
                raise BindingError(
                    f"projection: path must stay lexically inside repository: {raw}"
                )
            mode = git_mode(root, raw)
        except BindingError as exc:
            errors.append(str(exc))
            continue
        if mode != "120000":
            errors.append(
                f"{raw}: shared Skill projection must be a tracked Git symlink, got mode {mode or 'ABSENT'}"
            )

    routes = binding.get("routes")
    if not isinstance(routes, list) or not routes:
        errors.append("binding.json: routes must be a non-empty array")
        routes = []
    seen_routes: set[str] = set()
    for index, route in enumerate(routes):
        label = f"routes[{index}]"
        if not isinstance(route, dict):
            errors.append(f"{label}: must be an object")
            continue
        raw = route.get("path")
        if not nonempty(raw):
            errors.append(f"{label}.path is required")
            continue
        if raw in seen_routes:
            errors.append(f"{label}: duplicate route {raw}")
        seen_routes.add(raw)
        try:
            path = inside(root, raw, label=label)
        except BindingError as exc:
            errors.append(str(exc))
            continue
        kind = route.get("kind")
        if kind not in {"file", "directory"}:
            errors.append(f"{label}.kind must be file or directory")
            continue
        required = route.get("required")
        if not isinstance(required, bool):
            errors.append(f"{label}.required must be boolean")
            continue
        if required:
            exists = path.is_file() if kind == "file" else path.is_dir()
            if not exists:
                errors.append(f"{label}: required route is ABSENT: {raw}")

    output = binding.get("output")
    if (
        not isinstance(output, dict)
        or output.get("schema_version") != "repo-agent-native-output/v2"
    ):
        errors.append("binding.json: output schema must be repo-agent-native-output/v2")

    evidence_states = binding.get("evidence_states")
    if not isinstance(evidence_states, list) or set(evidence_states) != EVIDENCE_STATES:
        errors.append(
            "binding.json: evidence_states must contain the exact six-state vocabulary"
        )

    human_admit = binding.get("human_admit")
    if (
        not isinstance(human_admit, list)
        or not human_admit
        or any(not nonempty(x) for x in human_admit)
    ):
        errors.append("binding.json: human_admit must be a non-empty string array")

    claude_servers = mcp_json.get("mcpServers")
    if not isinstance(claude_servers, dict):
        errors.append(".mcp.json: mcpServers must be an object")
        claude_servers = {}
    codex_servers = codex_toml.get("mcp_servers")
    if not isinstance(codex_servers, dict):
        errors.append(".codex/config.toml: mcp_servers must be a table")
        codex_servers = {}

    capabilities = binding.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        errors.append("binding.json: capabilities must be a non-empty array")
        capabilities = []
    seen_capabilities: set[str] = set()
    for index, capability in enumerate(capabilities):
        label = f"capabilities[{index}]"
        if not isinstance(capability, dict):
            errors.append(f"{label}: must be an object")
            continue
        capability_id = capability.get("id")
        if not nonempty(capability_id):
            errors.append(f"{label}.id is required")
            continue
        if capability_id in seen_capabilities:
            errors.append(f"{label}: duplicate capability id {capability_id}")
        seen_capabilities.add(capability_id)
        config_state = capability.get("config_state")
        runtime_state = capability.get("runtime_state")
        if config_state not in CONFIG_STATES:
            errors.append(f"{label}.config_state is unsupported")
        if runtime_state not in EVIDENCE_STATES:
            errors.append(f"{label}.runtime_state is unsupported")
        if not nonempty(capability.get("authority_ceiling")):
            errors.append(f"{label}.authority_ceiling is required")
        if runtime_state != "PASS" and not nonempty(capability.get("fallback")):
            errors.append(f"{label}: non-PASS runtime state requires fallback")
        if runtime_state == "PASS":
            receipt = capability.get("receipt")
            if not nonempty(receipt):
                errors.append(f"{label}: PASS requires a subject-bound receipt")
            else:
                try:
                    receipt_path = inside(root, receipt, label=f"{label}.receipt")
                    if not receipt_path.is_file():
                        errors.append(f"{label}: PASS receipt is ABSENT: {receipt}")
                except BindingError as exc:
                    errors.append(str(exc))

        server = capability.get("mcp_server")
        if config_state in {"CONFIGURED", "NOT_CONFIGURED"}:
            if not nonempty(server):
                errors.append(f"{label}: {config_state} capability requires mcp_server")
                continue
            in_claude = server in claude_servers
            in_codex = server in codex_servers
            if config_state == "CONFIGURED" and not (in_claude and in_codex):
                errors.append(
                    f"{label}: configured server {server!r} must appear in both .mcp.json and .codex/config.toml"
                )
            if config_state == "NOT_CONFIGURED" and (in_claude or in_codex):
                errors.append(
                    f"{label}: unadmitted server {server!r} is present in project MCP configuration"
                )

        provider_commit = capability.get("provider_commit")
        if nonempty(provider_commit):
            if not SHA40.fullmatch(provider_commit):
                errors.append(f"{label}.provider_commit must be a lowercase 40-hex SHA")
            elif nonempty(server):
                for surface_name, surface in (
                    (".mcp.json", claude_servers.get(server, {})),
                    (".codex/config.toml", codex_servers.get(server, {})),
                ):
                    if provider_commit not in serialized(surface):
                        errors.append(
                            f"{label}: provider_commit is not pinned in {surface_name}"
                        )

    validate_docs(root, errors)
    validate_no_sensitive_material(root, errors)
    return sorted(set(errors))


def write_placeholder(path: Path, *, directory: bool) -> None:
    if directory:
        path.mkdir(parents=True, exist_ok=True)
        (path / ".keep").write_text("fixture\n", encoding="utf-8")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# fixture\n", encoding="utf-8")


def initialise_git(root: Path) -> None:
    subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
    subprocess.run(
        ["git", "-C", str(root), "config", "user.email", "fixture@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(root), "config", "user.name", "Fixture"], check=True
    )
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)


def restage(root: Path) -> None:
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)


def make_fixture(source_root: Path, destination: Path) -> None:
    binding = load_json(source_root / BINDING_REL)
    shutil.copytree(source_root / BINDING_DIR_REL, destination / BINDING_DIR_REL)
    shutil.copytree(source_root / DOCS_AGENT_REL, destination / DOCS_AGENT_REL)
    for relative in (MCP_JSON_REL, CODEX_TOML_REL):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_root / relative, target)

    for route in binding["routes"]:
        path = destination / route["path"]
        if path.exists():
            continue
        if route["required"]:
            write_placeholder(path, directory=route["kind"] == "directory")

    for raw in binding["skill"]["projection_paths"]:
        path = destination / raw
        path.parent.mkdir(parents=True, exist_ok=True)
        os.symlink("/tmp/canonical/repo-agent-native", path)

    initialise_git(destination)


def assert_mutation_fails(source_root: Path, label: str, mutate) -> None:
    with tempfile.TemporaryDirectory(prefix="repo-agent-native-binding-") as tmp:
        root = Path(tmp)
        make_fixture(source_root, root)
        mutate(root)
        restage(root)
        errors = validate(root)
        if not errors:
            raise AssertionError(f"{label}: planted mutation unexpectedly passed")


def selftest(source_root: Path) -> int:
    base_errors = validate(source_root)
    if base_errors:
        for error in base_errors:
            print(f"SELFTEST BASE FAIL {error}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(
        prefix="repo-agent-native-binding-positive-"
    ) as tmp:
        fixture = Path(tmp)
        make_fixture(source_root, fixture)
        positive_errors = validate(fixture)
        if positive_errors:
            for error in positive_errors:
                print(f"SELFTEST POSITIVE FAIL {error}", file=sys.stderr)
            return 1

    def copied_projection(root: Path) -> None:
        path = root / ".agents/skills/repo-agent-native"
        path.unlink()
        path.mkdir()
        (path / "SKILL.md").write_text("# shadow copy\n", encoding="utf-8")

    def missing_route(root: Path) -> None:
        (root / "docs/agents/domain.md").unlink()

    def unadmitted_graph(root: Path) -> None:
        path = root / MCP_JSON_REL
        value = load_json(path)
        value["mcpServers"]["code-graph-rag"] = {
            "type": "stdio",
            "command": "code-graph-rag",
            "args": ["mcp-server"],
        }
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def missing_fallback(root: Path) -> None:
        path = root / BINDING_REL
        value = load_json(path)
        for capability in value["capabilities"]:
            if capability["id"] == "project-memory":
                capability["fallback"] = ""
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def secret_injection(root: Path) -> None:
        path = root / BINDING_DIR_REL / "provider-map.md"
        path.write_text(
            path.read_text(encoding="utf-8") + '\napi_key = "sk-test-secret-value"\n',
            encoding="utf-8",
        )

    def home_path_injection(root: Path) -> None:
        path = root / BINDING_DIR_REL / "provider-map.md"
        planted = MACOS_HOME_ROOT + "fixture/project"
        path.write_text(
            path.read_text(encoding="utf-8") + f"\nlocal index: {planted}\n",
            encoding="utf-8",
        )

    for label, mutation in (
        ("copied-projection", copied_projection),
        ("missing-route", missing_route),
        ("unadmitted-graph", unadmitted_graph),
        ("missing-fallback", missing_fallback),
        ("secret-injection", secret_injection),
        ("home-path-injection", home_path_injection),
    ):
        assert_mutation_fails(source_root, label, mutation)

    print(
        "PASS repo-agent-native Bettor binding selftest: 1 positive + 6 planted negatives"
    )
    return 0


def emit(root: Path, errors: list[str]) -> None:
    report = {
        "schema_version": "repo-agent-native-binding-check/v1",
        "repository": "ed3c/bettor-arena",
        "state": "PASS" if not errors else "FAIL",
        "errors": errors,
    }
    stream = sys.stdout if not errors else sys.stderr
    print(json.dumps(report, indent=2, sort_keys=True), file=stream)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.selftest:
        return selftest(root)
    errors = validate(root)
    emit(root, errors)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
