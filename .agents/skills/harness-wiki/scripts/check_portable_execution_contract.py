#!/usr/bin/env python3
"""Deterministic semantic checks for the portable Skill execution contract.

Exit codes follow bettor-arena public CLI convention:
  0  valid subject / expected selftest outcome
  2  checked subject failed
  64 invalid usage, unreadable input, or missing required file
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

EXIT_OK = 0
EXIT_FAILED = 2
EXIT_USAGE = 64
KNOWN_ASSERTIONS = {
    "exit_code",
    "stdout_json_schema",
    "stderr_pattern",
    "file_exists",
    "file_hash",
    "file_content",
    "git_diff_allowlist",
    "ast_query",
    "lsp_diagnostics",
    "test_report",
    "artifact_digest",
    "subject_match",
}
FORBIDDEN_KEYS = {
    "shell",
    "command_string",
    "raw_command",
    "api_key",
    "token",
    "secret",
    "credential",
}
SHELL_META = re.compile(r"[;&|`$<>\n\r]")
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ContractError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ContractError(f"top-level JSON must be an object: {path}")
    return data


def walk_forbidden(value: Any, location: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                errors.append(f"forbidden key {location}.{key}")
            errors.extend(walk_forbidden(child, f"{location}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(walk_forbidden(child, f"{location}[{index}]"))
    return errors


def relative_path(value: Any, field: str) -> str | None:
    if not isinstance(value, str) or not value:
        return f"{field} must be a non-empty string"
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        return f"{field} must be repository-relative without traversal: {value!r}"
    return None


def expect(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_request(data: dict[str, Any]) -> list[str]:
    errors = walk_forbidden(data)
    expect(
        data.get("schema_version") == "skill-execution-request/v1",
        "wrong request schema_version",
        errors,
    )
    subject = data.get("subject")
    expect(isinstance(subject, dict), "request subject must be an object", errors)
    if isinstance(subject, dict):
        expect(
            bool(COMMIT.fullmatch(str(subject.get("commit", "")))),
            "subject.commit must be a 40-character lowercase SHA",
            errors,
        )
        if "tree" in subject:
            expect(
                bool(COMMIT.fullmatch(str(subject["tree"]))),
                "subject.tree must be a 40-character lowercase SHA",
                errors,
            )
        if "context_digest" in subject:
            expect(
                bool(SHA256.fullmatch(str(subject["context_digest"]))),
                "subject.context_digest must be sha256:<64 hex>",
                errors,
            )

    skill = data.get("skill")
    expect(isinstance(skill, dict), "request skill must be an object", errors)
    if isinstance(skill, dict):
        name = str(skill.get("name", ""))
        expect(
            bool(SKILL_NAME.fullmatch(name)) and len(name) <= 64,
            "skill.name must be portable lower-kebab-case",
            errors,
        )
        expect(
            bool(SHA256.fullmatch(str(skill.get("content_digest", "")))),
            "skill.content_digest must be sha256:<64 hex>",
            errors,
        )

    command = data.get("command")
    expect(isinstance(command, dict), "request command must be an object", errors)
    if isinstance(command, dict):
        executable = command.get("executable")
        expect(
            isinstance(executable, str) and bool(executable),
            "command.executable must be a non-empty string",
            errors,
        )
        if isinstance(executable, str):
            expect(
                not SHELL_META.search(executable),
                "command.executable contains shell metacharacters",
                errors,
            )
            expect(
                not executable.strip().startswith(
                    ("bash -c", "sh -c", "zsh -c", "cmd /c", "powershell -command")
                ),
                "command.executable must not embed a shell command",
                errors,
            )
        argv = command.get("argv")
        expect(
            isinstance(argv, list) and all(isinstance(item, str) for item in argv),
            "command.argv must be an array of strings",
            errors,
        )
        cwd_error = relative_path(command.get("cwd"), "command.cwd")
        if cwd_error:
            errors.append(cwd_error)
        stdin = command.get("stdin")
        expect(
            isinstance(stdin, dict)
            and stdin.get("mode") in {"closed", "artifact", "literal"},
            "command.stdin.mode is invalid",
            errors,
        )
        env = command.get("env_allowlist")
        expect(
            isinstance(env, list)
            and all(
                isinstance(item, str) and re.fullmatch(r"[A-Z_][A-Z0-9_]*", item)
                for item in env
            ),
            "command.env_allowlist must contain environment variable names only",
            errors,
        )
        timeout = command.get("timeout_ms")
        expect(
            isinstance(timeout, int) and 1 <= timeout <= 900_000,
            "command.timeout_ms is out of range",
            errors,
        )

    sandbox = data.get("sandbox")
    expect(isinstance(sandbox, dict), "request sandbox must be an object", errors)
    if isinstance(sandbox, dict):
        expect(
            sandbox.get("network") in {"deny", "allowlisted", "inherit"},
            "sandbox.network is invalid",
            errors,
        )
        expect(
            sandbox.get("process_group") is True,
            "sandbox.process_group must be true",
            errors,
        )
        for field in ("writable_paths", "read_only_paths"):
            values = sandbox.get(field)
            expect(
                isinstance(values, list), f"sandbox.{field} must be an array", errors
            )
            if isinstance(values, list):
                for index, value in enumerate(values):
                    path_error = relative_path(value, f"sandbox.{field}[{index}]")
                    if path_error:
                        errors.append(path_error)
        if sandbox.get("network") == "allowlisted":
            allowlist = sandbox.get("network_allowlist")
            expect(
                isinstance(allowlist, list) and bool(allowlist),
                "allowlisted network requires network_allowlist",
                errors,
            )

    assertion_set = data.get("assertion_set")
    expect(
        isinstance(assertion_set, dict),
        "request assertion_set must be an object",
        errors,
    )
    if isinstance(assertion_set, dict):
        expect(
            bool(SHA256.fullmatch(str(assertion_set.get("digest", "")))),
            "assertion_set.digest must be sha256:<64 hex>",
            errors,
        )
    return errors


def validate_assertions(data: dict[str, Any]) -> list[str]:
    errors = walk_forbidden(data)
    expect(
        data.get("schema_version") == "skill-assertion-set/v1",
        "wrong assertion schema_version",
        errors,
    )
    expect(
        data.get("subject_policy") == "exact-request-subject",
        "assertion subject_policy must be exact-request-subject",
        errors,
    )
    assertions = data.get("assertions")
    expect(
        isinstance(assertions, list) and bool(assertions),
        "assertions must be a non-empty array",
        errors,
    )
    if not isinstance(assertions, list):
        return errors
    ids: set[str] = set()
    hard = 0
    for index, assertion in enumerate(assertions):
        if not isinstance(assertion, dict):
            errors.append(f"assertions[{index}] must be an object")
            continue
        assertion_id = assertion.get("id")
        expect(
            isinstance(assertion_id, str) and bool(assertion_id),
            f"assertions[{index}].id missing",
            errors,
        )
        if isinstance(assertion_id, str):
            expect(
                assertion_id not in ids,
                f"duplicate assertion id: {assertion_id}",
                errors,
            )
            ids.add(assertion_id)
        expect(
            assertion.get("type") in KNOWN_ASSERTIONS,
            f"unknown assertion type at index {index}",
            errors,
        )
        severity = assertion.get("severity")
        expect(
            severity in {"hard", "advisory"},
            f"invalid assertion severity at index {index}",
            errors,
        )
        if severity == "hard":
            hard += 1
        expect(
            isinstance(assertion.get("expected"), dict),
            f"assertions[{index}].expected must be an object",
            errors,
        )
    expect(hard > 0, "assertion set must contain at least one hard assertion", errors)
    return errors


def validate_receipt(
    data: dict[str, Any], request: dict[str, Any], assertion_set: dict[str, Any]
) -> list[str]:
    errors = walk_forbidden(data)
    expect(
        data.get("schema_version") == "skill-execution-receipt/v1",
        "wrong receipt schema_version",
        errors,
    )
    expect(
        data.get("request_id") == request.get("request_id"),
        "receipt request_id does not match request",
        errors,
    )
    expect(
        data.get("subject") == request.get("subject"),
        "receipt subject does not match request",
        errors,
    )
    expect(
        data.get("skill") == request.get("skill"),
        "receipt skill does not match request",
        errors,
    )
    status = data.get("status")
    allowed = {
        "NOT_RUN",
        "PASS",
        "FAIL",
        "ERROR",
        "ABSENT",
        "NOT_EXERCISED",
        "SKIPPED_BY_POLICY",
    }
    expect(status in allowed, "receipt status is invalid", errors)
    executed = data.get("executed")
    expect(isinstance(executed, bool), "receipt executed must be boolean", errors)
    if status == "PASS":
        expect(executed is True, "PASS requires executed=true", errors)
        expect(
            isinstance(data.get("exit_code"), int),
            "PASS requires an observed integer exit_code",
            errors,
        )
        artifacts = data.get("artifacts")
        expect(isinstance(artifacts, dict), "PASS requires artifacts", errors)
        if isinstance(artifacts, dict):
            expect(
                bool(SHA256.fullmatch(str(artifacts.get("stdout", "")))),
                "PASS requires stdout artifact digest",
                errors,
            )
            expect(
                bool(SHA256.fullmatch(str(artifacts.get("stderr", "")))),
                "PASS requires stderr artifact digest",
                errors,
            )
        cleanup = data.get("cleanup")
        expect(
            isinstance(cleanup, dict) and cleanup.get("status") == "PASS",
            "PASS requires cleanup PASS",
            errors,
        )
    if status in {"NOT_RUN", "NOT_EXERCISED", "ABSENT", "SKIPPED_BY_POLICY"}:
        expect(executed is False, f"{status} requires executed=false", errors)

    expected = {
        item.get("id"): item
        for item in assertion_set.get("assertions", [])
        if isinstance(item, dict)
    }
    results = data.get("assertions")
    expect(isinstance(results, list), "receipt assertions must be an array", errors)
    result_map: dict[str, dict[str, Any]] = {}
    if isinstance(results, list):
        for index, result in enumerate(results):
            if not isinstance(result, dict):
                errors.append(f"receipt assertions[{index}] must be an object")
                continue
            result_id = result.get("id")
            if isinstance(result_id, str):
                expect(
                    result_id not in result_map,
                    f"duplicate receipt assertion id: {result_id}",
                    errors,
                )
                result_map[result_id] = result
            expect(
                isinstance(result.get("evidence"), list),
                f"receipt assertions[{index}].evidence must be an array",
                errors,
            )

    for assertion_id, definition in expected.items():
        result = result_map.get(assertion_id)
        expect(
            result is not None,
            f"missing receipt result for assertion: {assertion_id}",
            errors,
        )
        if result is None:
            continue
        expect(
            result.get("severity") == definition.get("severity"),
            f"severity mismatch for assertion: {assertion_id}",
            errors,
        )
        if status == "PASS" and definition.get("severity") == "hard":
            expect(
                result.get("status") == "PASS",
                f"PASS receipt has non-PASS hard assertion: {assertion_id}",
                errors,
            )
            expect(
                bool(result.get("evidence")),
                f"PASS hard assertion lacks evidence: {assertion_id}",
                errors,
            )
    return errors


def validate_case(case: dict[str, Any], source: str) -> list[str]:
    request = case.get("request")
    assertions = case.get("assertions")
    receipt = case.get("receipt")
    if (
        not isinstance(request, dict)
        or not isinstance(assertions, dict)
        or not isinstance(receipt, dict)
    ):
        raise ContractError(
            f"case must contain request, assertions and receipt objects: {source}"
        )
    errors = []
    errors.extend(f"request: {error}" for error in validate_request(request))
    errors.extend(f"assertions: {error}" for error in validate_assertions(assertions))
    errors.extend(
        f"receipt: {error}" for error in validate_receipt(receipt, request, assertions)
    )
    return errors


def validate_root(root: Path) -> list[str]:
    return validate_case(load_json(root / "case.json"), str(root / "case.json"))


def apply_mutations(case: dict[str, Any], mutation_file: Path) -> dict[str, Any]:
    candidate = copy.deepcopy(case)
    spec = load_json(mutation_file)
    mutations = spec.get("mutations")
    if not isinstance(mutations, list) or not mutations:
        raise ContractError(
            f"mutation file requires a non-empty mutations array: {mutation_file}"
        )
    for index, mutation in enumerate(mutations):
        if (
            not isinstance(mutation, dict)
            or not isinstance(mutation.get("path"), str)
            or "value" not in mutation
        ):
            raise ContractError(f"invalid mutation at {mutation_file}:{index}")
        parts = mutation["path"].split(".")
        target: Any = candidate
        for part in parts[:-1]:
            if isinstance(target, list):
                try:
                    target = target[int(part)]
                except (ValueError, IndexError) as exc:
                    raise ContractError(
                        f"invalid list path in {mutation_file}: {mutation['path']}"
                    ) from exc
            elif isinstance(target, dict):
                if part not in target:
                    raise ContractError(
                        f"missing mutation path in {mutation_file}: {mutation['path']}"
                    )
                target = target[part]
            else:
                raise ContractError(
                    f"non-container mutation path in {mutation_file}: {mutation['path']}"
                )
        leaf = parts[-1]
        if isinstance(target, list):
            try:
                target[int(leaf)] = mutation["value"]
            except (ValueError, IndexError) as exc:
                raise ContractError(
                    f"invalid list leaf in {mutation_file}: {mutation['path']}"
                ) from exc
        elif isinstance(target, dict):
            target[leaf] = mutation["value"]
        else:
            raise ContractError(
                f"non-container mutation leaf in {mutation_file}: {mutation['path']}"
            )
    return candidate


def run_selftest(script_root: Path) -> list[str]:
    fixtures = script_root.parent / "tests" / "fixtures"
    failures: list[str] = []
    try:
        good = load_json(fixtures / "good" / "case.json")
        good_errors = validate_case(good, "good/case.json")
        if good_errors:
            failures.append(
                f"selftest good: expected PASS, observed errors={good_errors}"
            )
        for name in ("hollow", "mutation"):
            candidate = apply_mutations(good, fixtures / name / "mutation.json")
            errors = validate_case(candidate, f"{name}/mutation.json")
            if not errors:
                failures.append(f"selftest {name}: planted negative was not killed")
    except ContractError as exc:
        failures.append(str(exc))
    return failures


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        help="directory containing case.json with request, assertions and receipt objects",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="run positive, hollow and mutation fixtures",
    )
    args = parser.parse_args(argv)
    if not args.selftest and args.root is None:
        parser.error("one of --selftest or --root is required")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.selftest:
            failures = run_selftest(Path(__file__).resolve().parent)
            if failures:
                print("portable execution contract selftest: FAIL", file=sys.stderr)
                for failure in failures:
                    print(f"- {failure}", file=sys.stderr)
                return EXIT_FAILED
            print("portable execution contract selftest: PASS")
        if args.root is not None:
            errors = validate_root(args.root)
            if errors:
                print("portable execution contract: FAIL", file=sys.stderr)
                for error in errors:
                    print(f"- {error}", file=sys.stderr)
                return EXIT_FAILED
            print("portable execution contract: PASS")
        return EXIT_OK
    except ContractError as exc:
        print(f"portable execution contract: USAGE/INPUT ERROR: {exc}", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
