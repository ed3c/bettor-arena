#!/usr/bin/env python3
"""Execute one portable Skill request in a disposable Git worktree.

The runner is deterministic host code, not a model tool. It never accepts a raw
shell command, never trusts Worker prose as a verdict, and never writes LoopX
state. It emits a subject-bound receipt that a separate reducer may consume.

Exit codes:
  0  execution completed and every hard assertion passed
  2  checked request was refused, execution failed, or a hard assertion failed
 64  usage/input/tool failure that prevented a meaningful checked run
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from check_portable_execution_contract import (
    ContractError,
    load_json,
    validate_assertions,
    validate_request,
)

EXIT_OK = 0
EXIT_FAILED = 2
EXIT_USAGE = 64
SUPPORTED_ASSERTIONS = {
    "subject_match",
    "exit_code",
    "stderr_pattern",
    "stdout_json_schema",
    "file_exists",
    "file_hash",
    "file_content",
    "git_diff_allowlist",
    "lsp_diagnostics",
    "test_report",
    "artifact_digest",
}
SENSITIVE_ENV = re.compile(
    r"(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|COOKIE|SESSION)", re.I
)


def utc_now() -> str:
    return (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def digest_json(value: Any) -> str:
    return digest_bytes(canonical_bytes(value))


def directory_digest(root: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(
        item
        for item in root.rglob("*")
        if item.is_file()
        and "__pycache__" not in item.parts
        and not item.name.endswith(".pyc")
    )
    for item in files:
        digest.update(item.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def repo_relative(value: str, field: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise ContractError(
            f"{field} must be repository-relative without traversal: {value!r}"
        )
    return path


def inside(root: Path, relative: str, field: str) -> Path:
    rel = repo_relative(relative, field)
    candidate = root.joinpath(*rel.parts)
    resolved_root = root.resolve()
    try:
        resolved = candidate.resolve(strict=False)
        resolved.relative_to(resolved_root)
    except (OSError, ValueError) as exc:
        raise ContractError(
            f"{field} escapes the disposable worktree: {relative!r}"
        ) from exc
    return candidate


def run_git(
    repo: Path,
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if check and result.returncode != 0:
        raise ContractError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result


def normalize_repository(remote: str) -> str | None:
    value = remote.strip()
    patterns = (
        r"^(?:https?://|ssh://git@)github\.com/([^/]+/[^/]+?)(?:\.git)?$",
        r"^git@github\.com:([^/]+/[^/]+?)(?:\.git)?$",
    )
    for pattern in patterns:
        match = re.match(pattern, value)
        if match:
            return match.group(1)
    return None


def changed_paths(worktree: Path) -> list[str]:
    output = run_git(
        worktree,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    ).stdout
    paths: list[str] = []
    for line in output.splitlines():
        if len(line) < 4:
            continue
        name = line[3:]
        if " -> " in name:
            name = name.split(" -> ", 1)[1]
        paths.append(name.strip('"'))
    return sorted(set(paths))


def path_within(path: str, boundaries: Iterable[str]) -> bool:
    candidate = PurePosixPath(path)
    for boundary in boundaries:
        base = repo_relative(boundary, "path boundary")
        if candidate == base or base in candidate.parents:
            return True
    return False


def write_artifact(store: Path, data: bytes) -> str:
    digest = digest_bytes(data)
    target = store / digest.split(":", 1)[1]
    if not target.exists():
        target.write_bytes(data)
    return digest


def make_change_artifact(worktree: Path, paths: list[str]) -> bytes:
    patch = run_git(worktree, "diff", "--binary", "HEAD", check=False).stdout
    manifest: list[dict[str, Any]] = []
    for relative in paths:
        path = inside(worktree, relative, "changed path")
        entry: dict[str, Any] = {
            "path": relative,
            "exists": path.exists() or path.is_symlink(),
        }
        if path.is_file() and not path.is_symlink():
            entry["digest"] = digest_bytes(path.read_bytes())
            entry["size"] = path.stat().st_size
        manifest.append(entry)
    return canonical_bytes(
        {
            "schema_version": "skill-execution-change-artifact/v1",
            "paths": manifest,
            "patch": patch,
        }
    )


def parse_stdout_json(data: bytes) -> Any:
    return json.loads(data.decode("utf-8"))


def json_path_get(value: Any, path: str) -> Any:
    current = value
    if not path:
        return current
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            raise KeyError(path)
    return current


def evaluate_assertion(
    definition: dict[str, Any],
    *,
    worktree: Path,
    request: dict[str, Any],
    exit_code: int | None,
    stdout: bytes,
    stderr: bytes,
    changes: list[str],
    artifact_store: Path,
) -> tuple[str, list[str]]:
    kind = definition["type"]
    expected = definition.get("expected", {})
    evidence: list[str] = []
    try:
        if kind == "subject_match":
            head = run_git(worktree, "rev-parse", "HEAD").stdout.strip()
            tree = run_git(worktree, "rev-parse", "HEAD^{tree}").stdout.strip()
            passed = head == request["subject"]["commit"] and (
                "tree" not in request["subject"] or tree == request["subject"]["tree"]
            )
            evidence = [f"commit:{head}", f"tree:{tree}"]
        elif kind == "exit_code":
            passed = exit_code == expected.get("equals")
            evidence = [f"exit_code:{exit_code}"]
        elif kind == "stderr_pattern":
            text = stderr.decode("utf-8", errors="replace")
            if "absent" in expected:
                passed = re.search(str(expected["absent"]), text, re.MULTILINE) is None
            elif "matches" in expected:
                passed = (
                    re.search(str(expected["matches"]), text, re.MULTILINE) is not None
                )
            else:
                raise ContractError(
                    "stderr_pattern expected requires absent or matches"
                )
            evidence = [write_artifact(artifact_store, stderr)]
        elif kind == "stdout_json_schema":
            value = parse_stdout_json(stdout)
            passed = (
                isinstance(value, dict)
                if expected.get("type", "object") == "object"
                else True
            )
            for key in expected.get("required_keys", []):
                passed = passed and isinstance(value, dict) and key in value
            for path, wanted in expected.get("equals", {}).items():
                try:
                    passed = passed and json_path_get(value, path) == wanted
                except KeyError:
                    passed = False
            evidence = [write_artifact(artifact_store, stdout)]
        elif kind in {
            "file_exists",
            "file_hash",
            "file_content",
            "artifact_digest",
        }:
            relative = str(expected.get("path", ""))
            path = inside(
                worktree,
                relative,
                f"assertion {definition['id']} path",
            )
            if kind == "file_exists":
                wanted_kind = expected.get("kind", "file")
                passed = path.is_file() if wanted_kind == "file" else path.is_dir()
                evidence = [f"path:{relative}"]
            elif not path.is_file() or path.is_symlink():
                passed = False
                evidence = [f"path:{relative}:absent-or-not-regular"]
            else:
                data = path.read_bytes()
                observed = write_artifact(artifact_store, data)
                evidence = [observed]
                if kind in {"file_hash", "artifact_digest"}:
                    passed = observed == expected.get("digest")
                else:
                    text = data.decode("utf-8", errors="replace")
                    checks: list[bool] = []
                    if "equals" in expected:
                        checks.append(text == str(expected["equals"]))
                    if "contains" in expected:
                        checks.append(str(expected["contains"]) in text)
                    if "matches" in expected:
                        checks.append(
                            re.search(
                                str(expected["matches"]),
                                text,
                                re.MULTILINE,
                            )
                            is not None
                        )
                    if not checks:
                        raise ContractError(
                            "file_content expected requires equals, contains, or matches"
                        )
                    passed = all(checks)
        elif kind == "git_diff_allowlist":
            allowed = expected.get("paths", [])
            if not isinstance(allowed, list):
                raise ContractError(
                    "git_diff_allowlist expected.paths must be an array"
                )
            passed = all(
                path_within(path, [str(item) for item in allowed]) for path in changes
            )
            required = expected.get("required_paths", [])
            if isinstance(required, list):
                passed = passed and all(
                    any(path_within(path, [str(item)]) for path in changes)
                    for item in required
                )
            evidence = ["changed:" + ",".join(changes)]
        elif kind == "lsp_diagnostics":
            relative = str(expected.get("path", ""))
            path = inside(
                worktree,
                relative,
                f"assertion {definition['id']} path",
            )
            value = json.loads(path.read_text(encoding="utf-8"))
            diagnostics = (
                value.get("generalDiagnostics", value.get("diagnostics", []))
                if isinstance(value, dict)
                else value
            )
            if not isinstance(diagnostics, list):
                raise ContractError("lsp diagnostics artifact has no diagnostics array")
            errors = sum(
                1
                for item in diagnostics
                if isinstance(item, dict)
                and str(item.get("severity", "")).lower() in {"error", "1"}
            )
            passed = errors <= int(expected.get("max_errors", 0))
            evidence = [
                write_artifact(artifact_store, path.read_bytes()),
                f"lsp_errors:{errors}",
            ]
        elif kind == "test_report":
            relative = str(expected.get("path", ""))
            path = inside(
                worktree,
                relative,
                f"assertion {definition['id']} path",
            )
            root = ET.fromstring(path.read_bytes())
            failures = sum(
                int(node.attrib.get("failures", "0"))
                for node in root.iter()
                if node.tag.endswith("testsuite")
            )
            errors = sum(
                int(node.attrib.get("errors", "0"))
                for node in root.iter()
                if node.tag.endswith("testsuite")
            )
            passed = failures <= int(expected.get("max_failures", 0)) and errors <= int(
                expected.get("max_errors", 0)
            )
            evidence = [
                write_artifact(artifact_store, path.read_bytes()),
                f"tests_failures:{failures}",
                f"tests_errors:{errors}",
            ]
        else:
            raise ContractError(f"unsupported assertion type: {kind}")
        return ("PASS" if passed else "FAIL"), evidence
    except (
        ContractError,
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
        ET.ParseError,
    ) as exc:
        return "ERROR", [f"assertion_error:{type(exc).__name__}:{exc}"]


def result_rows(
    assertions: dict[str, Any],
    status: str = "NOT_RUN",
    reason: str | None = None,
) -> list[dict[str, Any]]:
    return [
        {
            "id": definition.get("id", "unknown"),
            "severity": definition.get("severity", "hard"),
            "status": status,
            "evidence": [] if reason is None else [reason],
        }
        for definition in assertions.get("assertions", [])
    ]


def build_receipt(
    *,
    request: dict[str, Any],
    assertions: list[dict[str, Any]],
    executed: bool,
    status: str,
    exit_code: int | None,
    started_at: str,
    ended_at: str,
    duration_ms: int,
    artifacts: dict[str, str | None],
    cleanup_status: str,
    residue: list[str],
    command_digest: str,
    network_mode: str,
) -> dict[str, Any]:
    return {
        "schema_version": "skill-execution-receipt/v1",
        "request_id": request["request_id"],
        "subject": request["subject"],
        "skill": request["skill"],
        "runner": {
            "id": "loopctl-local-process",
            "version": "1",
            "command_digest": command_digest,
        },
        "isolation": {
            "workspace": "detached-disposable-git-worktree",
            "process": "new-process-group-with-timeout",
            "environment": "explicit-allowlist",
            "network": network_mode,
            "filesystem": "post-run-diff-boundary-not-os-sandbox",
        },
        "executed": executed,
        "status": status,
        "exit_code": exit_code,
        "timing": {
            "started_at": started_at,
            "ended_at": ended_at,
            "duration_ms": duration_ms,
        },
        "artifacts": artifacts,
        "assertions": assertions,
        "cleanup": {"status": cleanup_status, "residue": residue},
        "human_admit_required": True,
    }


def write_receipt(
    output: Path,
    receipt: dict[str, Any],
    request: dict[str, Any],
    assertions: dict[str, Any],
) -> None:
    (output / "request.json").write_bytes(canonical_bytes(request) + b"\n")
    (output / "assertions.json").write_bytes(canonical_bytes(assertions) + b"\n")
    temp = output / "receipt.json.tmp"
    temp.write_bytes(
        json.dumps(
            receipt,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
        + b"\n"
    )
    temp.replace(output / "receipt.json")


def execute(
    request_path: Path,
    assertions_path: Path,
    repo: Path,
    output: Path,
) -> int:
    if output.exists():
        print(
            f"skill-execution FATAL: output already exists: {output}",
            file=sys.stderr,
        )
        return EXIT_USAGE
    try:
        request = load_json(request_path)
        assertions = load_json(assertions_path)
    except ContractError as exc:
        print(f"skill-execution FATAL: {exc}", file=sys.stderr)
        return EXIT_USAGE

    output.mkdir(parents=True, exist_ok=False)
    store = output / "artifacts"
    store.mkdir()
    started_at = utc_now()
    started_ns = time.monotonic_ns()
    diagnostics: list[str] = []
    worktree: Path | None = None
    executed = False
    exit_code: int | None = None
    assertion_rows = result_rows(assertions)
    cleanup_status = "PASS"
    residue: list[str] = []
    status = "ERROR"
    network_mode = str(request.get("sandbox", {}).get("network", "unknown"))
    command_digest = digest_json(request.get("command", {}))

    try:
        contract_errors = validate_request(request) + validate_assertions(assertions)
        if contract_errors:
            raise ContractError("; ".join(contract_errors))
        if request["assertion_set"]["id"] != assertions.get("id"):
            raise ContractError(
                "request assertion_set.id does not match assertion document"
            )
        observed_assertion_digest = digest_json(assertions)
        if request["assertion_set"]["digest"] != observed_assertion_digest:
            raise ContractError(
                "assertion set digest mismatch: "
                f"request={request['assertion_set']['digest']} "
                f"observed={observed_assertion_digest}"
            )
        unsupported = sorted(
            definition["type"]
            for definition in assertions["assertions"]
            if definition.get("type") not in SUPPORTED_ASSERTIONS
        )
        if unsupported:
            raise ContractError(f"unsupported assertion type(s): {unsupported}")
        if any(
            SENSITIVE_ENV.search(name) for name in request["command"]["env_allowlist"]
        ):
            raise ContractError(
                "secret-bearing environment names are not admitted by the local runner"
            )
        expected_artifacts = request.get("expected_artifacts", [])
        declared_exists = {
            item.get("expected", {}).get("path")
            for item in assertions["assertions"]
            if item.get("type") == "file_exists" and item.get("severity") == "hard"
        }
        missing_assertions = sorted(set(expected_artifacts) - declared_exists)
        if missing_assertions:
            raise ContractError(
                "expected artifacts lack hard file_exists assertions: "
                f"{missing_assertions}"
            )
        if network_mode != "inherit":
            status = "SKIPPED_BY_POLICY"
            diagnostics.append(
                f"local-process runner cannot attest network={network_mode}; "
                "use a physical sandbox adapter"
            )
            raise RuntimeError("POLICY_SKIP")
        if request["sandbox"]["cleanup"] != "required":
            raise ContractError("v1 public runner requires cleanup=required")

        repo = repo.resolve()
        if not (repo / ".git").exists():
            raise ContractError(f"repo is not a Git worktree: {repo}")
        remote = run_git(repo, "remote", "get-url", "origin").stdout.strip()
        observed_repository = normalize_repository(remote)
        if observed_repository != request["subject"]["repository"]:
            raise ContractError(
                "repository identity mismatch: "
                f"request={request['subject']['repository']} "
                f"observed={observed_repository or remote}"
            )
        commit = request["subject"]["commit"]
        run_git(repo, "cat-file", "-e", f"{commit}^{{commit}}")
        observed_tree = run_git(
            repo,
            "rev-parse",
            f"{commit}^{{tree}}",
        ).stdout.strip()
        if "tree" in request["subject"] and observed_tree != request["subject"]["tree"]:
            raise ContractError(
                "tree mismatch: "
                f"request={request['subject']['tree']} "
                f"observed={observed_tree}"
            )

        worktree = Path(
            tempfile.mkdtemp(
                prefix="skill-execution.",
                dir=str(output.parent.resolve()),
            )
        )
        worktree.rmdir()
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "worktree",
                "add",
                "--detach",
                "--force",
                str(worktree),
                commit,
            ],
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        if result.returncode != 0:
            raise ContractError(result.stderr.strip() or "git worktree add failed")
        head = run_git(worktree, "rev-parse", "HEAD").stdout.strip()
        tree = run_git(
            worktree,
            "rev-parse",
            "HEAD^{tree}",
        ).stdout.strip()
        if head != commit or tree != observed_tree:
            raise ContractError(
                "disposable worktree subject does not match requested commit/tree"
            )

        source = request["skill"]["canonical_source"]
        prefix = request["subject"]["repository"] + "/"
        if not source.startswith(prefix):
            raise ContractError(
                "skill.canonical_source must begin with subject.repository/"
            )
        skill_rel = source[len(prefix) :]
        skill_path = inside(
            worktree,
            skill_rel,
            "skill.canonical_source",
        )
        if not (skill_path / "SKILL.md").is_file():
            raise ContractError(f"canonical Skill is absent: {skill_rel}/SKILL.md")
        observed_skill_digest = directory_digest(skill_path)
        if observed_skill_digest != request["skill"]["content_digest"]:
            raise ContractError(
                "Skill digest mismatch: "
                f"request={request['skill']['content_digest']} "
                f"observed={observed_skill_digest}"
            )

        cwd = inside(
            worktree,
            request["command"]["cwd"],
            "command.cwd",
        )
        if not cwd.is_dir():
            raise ContractError(f"command.cwd is absent: {request['command']['cwd']}")
        executable_name = request["command"]["executable"]
        if "/" in executable_name:
            executable = inside(
                worktree,
                executable_name,
                "command.executable",
            )
            if not executable.is_file():
                raise ContractError(f"command executable is absent: {executable_name}")
            executable_value = str(executable)
        else:
            resolved = shutil.which(executable_name)
            if resolved is None:
                status = "ABSENT"
                raise FileNotFoundError(executable_name)
            executable_value = resolved

        env = {
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_NOSYSTEM": "1",
        }
        for name in request["command"]["env_allowlist"]:
            if name in os.environ:
                env[name] = os.environ[name]

        stdin_spec = request["command"]["stdin"]
        if stdin_spec["mode"] == "artifact":
            raise ContractError(
                "artifact stdin requires an admitted artifact resolver; "
                "v1 local runner refuses it"
            )
        stdin_value: int | None = subprocess.DEVNULL
        input_data: bytes | None = None
        if stdin_spec["mode"] == "literal":
            stdin_value = subprocess.PIPE
            input_data = str(stdin_spec.get("literal", "")).encode("utf-8")

        stdout_path = output / "stdout.raw"
        stderr_path = output / "stderr.raw"
        timeout_seconds = request["command"]["timeout_ms"] / 1000.0
        executed = True
        with (
            stdout_path.open("wb") as stdout_file,
            stderr_path.open("wb") as stderr_file,
        ):
            process = subprocess.Popen(
                [executable_value, *request["command"]["argv"]],
                cwd=cwd,
                env=env,
                stdin=stdin_value,
                stdout=stdout_file,
                stderr=stderr_file,
                shell=False,
                start_new_session=True,
            )
            try:
                if input_data is not None and process.stdin is not None:
                    process.stdin.write(input_data)
                    process.stdin.close()
                exit_code = process.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                diagnostics.append(
                    f"command timed out after {request['command']['timeout_ms']}ms"
                )
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                exit_code = None

        stdout = stdout_path.read_bytes()
        stderr = stderr_path.read_bytes()
        max_output = request["sandbox"]["max_output_bytes"]
        if len(stdout) > max_output or len(stderr) > max_output:
            diagnostics.append(
                "captured output exceeded "
                f"max_output_bytes={max_output}: "
                f"stdout={len(stdout)} stderr={len(stderr)}"
            )
        stdout_path.unlink(missing_ok=True)
        stderr_path.unlink(missing_ok=True)

        changes = changed_paths(worktree)
        writable = request["sandbox"]["writable_paths"]
        read_only = request["sandbox"]["read_only_paths"]
        illegal = [path for path in changes if not path_within(path, writable)]
        readonly_changes = [path for path in changes if path_within(path, read_only)]
        if illegal:
            diagnostics.append(f"changed path outside writable boundary: {illegal}")
        if readonly_changes:
            diagnostics.append(
                f"changed path inside read-only boundary: {readonly_changes}"
            )

        assertion_rows = []
        for definition in assertions["assertions"]:
            observed_status, evidence = evaluate_assertion(
                definition,
                worktree=worktree,
                request=request,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                changes=changes,
                artifact_store=store,
            )
            assertion_rows.append(
                {
                    "id": definition["id"],
                    "severity": definition["severity"],
                    "status": observed_status,
                    "evidence": evidence,
                }
            )
        hard_green = all(
            row["status"] == "PASS"
            for row in assertion_rows
            if row["severity"] == "hard"
        )
        if (
            illegal
            or readonly_changes
            or exit_code is None
            or len(stdout) > max_output
            or len(stderr) > max_output
        ):
            hard_green = False
        status = "PASS" if hard_green else "FAIL"

        artifacts: dict[str, str | None] = {
            "stdout": write_artifact(store, stdout),
            "stderr": write_artifact(store, stderr),
            "git_diff": write_artifact(
                store,
                make_change_artifact(worktree, changes),
            ),
            "test_report": None,
            "runner_diagnostics": write_artifact(
                store,
                ("\n".join(diagnostics) + ("\n" if diagnostics else "")).encode(
                    "utf-8"
                ),
            ),
        }
    except RuntimeError as exc:
        if str(exc) != "POLICY_SKIP":
            diagnostics.append(f"runtime error: {exc}")
        artifacts = {
            "stdout": None,
            "stderr": None,
            "git_diff": None,
            "test_report": None,
            "runner_diagnostics": write_artifact(
                store,
                ("\n".join(diagnostics) + "\n").encode("utf-8"),
            ),
        }
        assertion_rows = result_rows(
            assertions,
            "NOT_RUN",
            diagnostics[-1] if diagnostics else "not executed",
        )
    except FileNotFoundError as exc:
        diagnostics.append(f"required executable absent: {exc}")
        artifacts = {
            "stdout": None,
            "stderr": None,
            "git_diff": None,
            "test_report": None,
            "runner_diagnostics": write_artifact(
                store,
                ("\n".join(diagnostics) + "\n").encode("utf-8"),
            ),
        }
        assertion_rows = result_rows(
            assertions,
            "NOT_RUN",
            diagnostics[-1],
        )
    except (ContractError, OSError, KeyError, TypeError, ValueError) as exc:
        diagnostics.append(f"preflight/execution error: {exc}")
        status = "FAIL"
        artifacts = {
            "stdout": None,
            "stderr": None,
            "git_diff": None,
            "test_report": None,
            "runner_diagnostics": write_artifact(
                store,
                ("\n".join(diagnostics) + "\n").encode("utf-8"),
            ),
        }
        assertion_rows = result_rows(
            assertions,
            "NOT_RUN",
            diagnostics[-1],
        )

    if worktree is not None and worktree.exists():
        cleanup = subprocess.run(
            [
                "git",
                "-C",
                str(repo.resolve()),
                "worktree",
                "remove",
                "--force",
                str(worktree),
            ],
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        if cleanup.returncode != 0:
            cleanup_status = "FAIL"
            residue.append(str(worktree))
            diagnostics.append(cleanup.stderr.strip() or "git worktree remove failed")
        elif worktree.exists():
            cleanup_status = "FAIL"
            residue.append(str(worktree))
        else:
            cleanup_status = "PASS"
    if cleanup_status != "PASS":
        status = "FAIL"

    ended_at = utc_now()
    duration_ms = max(
        0,
        (time.monotonic_ns() - started_ns) // 1_000_000,
    )
    artifacts["runner_diagnostics"] = write_artifact(
        store,
        ("\n".join(diagnostics) + ("\n" if diagnostics else "")).encode("utf-8"),
    )
    receipt = build_receipt(
        request=request,
        assertions=assertion_rows,
        executed=executed,
        status=status,
        exit_code=exit_code,
        started_at=started_at,
        ended_at=ended_at,
        duration_ms=duration_ms,
        artifacts=artifacts,
        cleanup_status=cleanup_status,
        residue=residue,
        command_digest=command_digest,
        network_mode=network_mode,
    )
    write_receipt(output, receipt, request, assertions)
    if status == "PASS":
        print(f"PASS skill-execution receipt={output / 'receipt.json'}")
        return EXIT_OK
    print(
        f"RED skill-execution status={status} receipt={output / 'receipt.json'}",
        file=sys.stderr,
    )
    return EXIT_USAGE if status == "ABSENT" else EXIT_FAILED


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser(
        "run",
        help="execute one exact request",
    )
    run.add_argument("--request", type=Path, required=True)
    run.add_argument("--assertions", type=Path, required=True)
    run.add_argument("--repo", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    subparsers.add_parser(
        "selftest",
        help="run the synthetic positive and negative controls",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.command == "selftest":
        test = (
            Path(__file__).resolve().parent.parent
            / "tests"
            / "run-execution-selftest.py"
        )
        if not test.is_file():
            print(
                f"skill-execution FATAL: selftest missing: {test}",
                file=sys.stderr,
            )
            return EXIT_USAGE
        return subprocess.run(
            [sys.executable, str(test)],
            check=False,
        ).returncode
    return execute(
        args.request,
        args.assertions,
        args.repo,
        args.output,
    )


if __name__ == "__main__":
    raise SystemExit(main())
