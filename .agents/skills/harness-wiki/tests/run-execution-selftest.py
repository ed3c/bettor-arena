#!/usr/bin/env python3
"""Synthetic positive and negative controls for portable Skill execution."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
RUNNER = ROOT.parent / "scripts" / "run_portable_skill.py"


def canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def digest_json(value: Any) -> str:
    return digest_bytes(canonical(value))


def directory_digest(root: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and not path.name.endswith(".pyc")
    )
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def run(*args: object, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(arg) for arg in args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def git(repo: Path, *args: str) -> str:
    result = run("git", "-C", repo, *args)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def fixture(base: Path) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    repo = base / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "fixture@example.com")
    git(repo, "config", "user.name", "Fixture")
    git(
        repo,
        "remote",
        "add",
        "origin",
        "https://github.com/fixture/portable-skill-execution.git",
    )

    skill = repo / "skills" / "fixture-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: fixture-skill\n"
        "description: deterministic fixture\n"
        "---\n\n"
        "Run the checked script.\n",
        encoding="utf-8",
    )
    (repo / "scripts").mkdir()
    (repo / "src").mkdir()
    (repo / "src" / "input.txt").write_text("source\n", encoding="utf-8")
    (repo / "scripts" / "write_result.py").write_text(
        "from pathlib import Path\n"
        "import json\n"
        "p = Path('artifacts/result.json')\n"
        "p.parent.mkdir(parents=True, exist_ok=True)\n"
        "p.write_text(json.dumps({'ok': True, 'value': 7}, sort_keys=True) + '\\n')\n"
        "print(json.dumps({'ok': True, 'value': 7}, sort_keys=True))\n",
        encoding="utf-8",
    )
    (repo / "scripts" / "fail.py").write_text(
        "import sys\nprint('failed', file=sys.stderr)\nsys.exit(7)\n",
        encoding="utf-8",
    )
    (repo / "scripts" / "sleep.py").write_text(
        "import time\ntime.sleep(2)\n",
        encoding="utf-8",
    )
    (repo / "scripts" / "write_outside.py").write_text(
        "from pathlib import Path\nPath('src/forbidden.txt').write_text('bad')\n",
        encoding="utf-8",
    )
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "fixture")
    commit = git(repo, "rev-parse", "HEAD")
    tree = git(repo, "rev-parse", "HEAD^{tree}")

    assertions: dict[str, Any] = {
        "schema_version": "skill-assertion-set/v1",
        "id": "fixture-execution",
        "subject_policy": "exact-request-subject",
        "assertions": [
            {
                "id": "subject-exact",
                "type": "subject_match",
                "severity": "hard",
                "expected": {"request": True},
                "evidence_required": ["subject"],
            },
            {
                "id": "exit-zero",
                "type": "exit_code",
                "severity": "hard",
                "expected": {"equals": 0},
                "evidence_required": ["exit_code"],
            },
            {
                "id": "result-exists",
                "type": "file_exists",
                "severity": "hard",
                "expected": {
                    "path": "artifacts/result.json",
                    "kind": "file",
                },
                "evidence_required": ["artifact_digest"],
            },
            {
                "id": "result-content",
                "type": "file_content",
                "severity": "hard",
                "expected": {
                    "path": "artifacts/result.json",
                    "contains": '"ok": true',
                },
                "evidence_required": ["artifact_digest"],
            },
            {
                "id": "stdout-json",
                "type": "stdout_json_schema",
                "severity": "hard",
                "expected": {
                    "type": "object",
                    "required_keys": ["ok", "value"],
                    "equals": {"ok": True, "value": 7},
                },
                "evidence_required": ["stdout"],
            },
            {
                "id": "diff-bounded",
                "type": "git_diff_allowlist",
                "severity": "hard",
                "expected": {
                    "paths": ["artifacts"],
                    "required_paths": ["artifacts/result.json"],
                },
                "evidence_required": ["git_diff"],
            },
        ],
    }
    request: dict[str, Any] = {
        "schema_version": "skill-execution-request/v1",
        "request_id": "req-fixture-execution",
        "subject": {
            "repository": "fixture/portable-skill-execution",
            "commit": commit,
            "tree": tree,
        },
        "skill": {
            "name": "fixture-skill",
            "canonical_source": (
                "fixture/portable-skill-execution/skills/fixture-skill"
            ),
            "content_digest": directory_digest(skill),
            "host_projection": "loopctl",
        },
        "command": {
            "executable": "python3",
            "argv": ["scripts/write_result.py"],
            "cwd": ".",
            "stdin": {"mode": "closed"},
            "env_allowlist": [],
            "timeout_ms": 5000,
        },
        "sandbox": {
            "network": "inherit",
            "writable_paths": ["artifacts"],
            "read_only_paths": ["src", "scripts", "skills"],
            "max_output_bytes": 65536,
            "process_group": True,
            "cleanup": "required",
        },
        "assertion_set": {
            "id": "fixture-execution",
            "digest": digest_json(assertions),
        },
        "expected_artifacts": ["artifacts/result.json"],
    }
    return repo, request, assertions


def execute_case(
    base: Path,
    repo: Path,
    request: dict[str, Any],
    assertions: dict[str, Any],
    name: str,
    loopctl: Path | None,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any] | None, Path]:
    request_path = base / f"{name}.request.json"
    assertion_path = base / f"{name}.assertions.json"
    output = base / f"{name}.out"
    write_json(request_path, request)
    write_json(assertion_path, assertions)
    if loopctl is None:
        argv: list[object] = [sys.executable, RUNNER, "run"]
    else:
        argv = ["sh", loopctl, "skill-execution", "run"]
    argv.extend(
        [
            "--request",
            request_path,
            "--assertions",
            assertion_path,
            "--repo",
            repo,
            "--output",
            output,
        ]
    )
    result = run(*argv)
    receipt_path = output / "receipt.json"
    receipt = (
        json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt_path.exists()
        else None
    )
    return result, receipt, output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--loopctl",
        type=Path,
        help="exercise the public loopctl port instead of the runner directly",
    )
    args = parser.parse_args(argv)
    failures: list[object] = []

    with tempfile.TemporaryDirectory(prefix="skill-exec-selftest.") as temporary:
        base = Path(temporary)
        repo, request, assertions = fixture(base)
        result, receipt, _ = execute_case(
            base,
            repo,
            request,
            assertions,
            "good",
            args.loopctl,
        )
        if (
            result.returncode != 0
            or receipt is None
            or receipt["status"] != "PASS"
            or receipt["cleanup"]["status"] != "PASS"
        ):
            failures.append(("good", result.returncode, result.stderr, receipt))

        cases: list[
            tuple[
                str,
                dict[str, Any],
                dict[str, Any],
                int,
                str,
            ]
        ] = []
        candidate = copy.deepcopy(request)
        candidate["sandbox"]["network"] = "deny"
        cases.append(
            (
                "network-deny",
                candidate,
                assertions,
                2,
                "SKIPPED_BY_POLICY",
            )
        )
        candidate = copy.deepcopy(request)
        candidate["assertion_set"]["digest"] = "sha256:" + "0" * 64
        cases.append(("assertion-digest", candidate, assertions, 2, "FAIL"))
        candidate = copy.deepcopy(request)
        candidate["skill"]["content_digest"] = "sha256:" + "0" * 64
        cases.append(("skill-digest", candidate, assertions, 2, "FAIL"))
        candidate = copy.deepcopy(request)
        candidate["subject"]["tree"] = "0" * 40
        cases.append(("tree-mismatch", candidate, assertions, 2, "FAIL"))
        candidate = copy.deepcopy(request)
        candidate["command"]["argv"] = ["scripts/fail.py"]
        cases.append(("exit-fail", candidate, assertions, 2, "FAIL"))
        candidate = copy.deepcopy(request)
        candidate["command"]["argv"] = ["scripts/sleep.py"]
        candidate["command"]["timeout_ms"] = 50
        cases.append(("timeout", candidate, assertions, 2, "FAIL"))
        candidate = copy.deepcopy(request)
        candidate["command"]["argv"] = ["scripts/write_outside.py"]
        candidate["expected_artifacts"] = []
        changed_assertions = copy.deepcopy(assertions)
        changed_assertions["assertions"] = [
            item
            for item in changed_assertions["assertions"]
            if item["id"] not in {"result-exists", "result-content", "stdout-json"}
        ]
        candidate["assertion_set"]["digest"] = digest_json(changed_assertions)
        cases.append(
            (
                "diff-boundary",
                candidate,
                changed_assertions,
                2,
                "FAIL",
            )
        )
        candidate = copy.deepcopy(request)
        changed_assertions = copy.deepcopy(assertions)
        changed_assertions["assertions"].append(
            {
                "id": "unsupported",
                "type": "ast_query",
                "severity": "hard",
                "expected": {},
                "evidence_required": [],
            }
        )
        candidate["assertion_set"]["digest"] = digest_json(changed_assertions)
        cases.append(
            (
                "unsupported",
                candidate,
                changed_assertions,
                2,
                "FAIL",
            )
        )
        candidate = copy.deepcopy(request)
        candidate["shell"] = True
        cases.append(("raw-shell", candidate, assertions, 2, "FAIL"))

        for name, candidate, assertion_set, expected_rc, expected_status in cases:
            result, receipt, _ = execute_case(
                base,
                repo,
                candidate,
                assertion_set,
                name,
                args.loopctl,
            )
            if (
                result.returncode != expected_rc
                or receipt is None
                or receipt["status"] != expected_status
            ):
                failures.append((name, result.returncode, result.stderr, receipt))

        request_path = base / "collision.request.json"
        assertion_path = base / "collision.assertions.json"
        output = base / "collision.out"
        write_json(request_path, request)
        write_json(assertion_path, assertions)
        if args.loopctl is None:
            collision_argv: list[object] = [
                sys.executable,
                RUNNER,
                "run",
            ]
        else:
            collision_argv = [
                "sh",
                args.loopctl,
                "skill-execution",
                "run",
            ]
        collision_argv.extend(
            [
                "--request",
                request_path,
                "--assertions",
                assertion_path,
                "--repo",
                repo,
                "--output",
                output,
            ]
        )
        first = run(*collision_argv)
        before = (output / "receipt.json").read_bytes()
        second = run(*collision_argv)
        if (
            first.returncode != 0
            or second.returncode != 64
            or (output / "receipt.json").read_bytes() != before
        ):
            failures.append(
                (
                    "append-only",
                    first.returncode,
                    second.returncode,
                    second.stderr,
                )
            )

    if failures:
        print("portable skill execution selftest: FAIL", file=sys.stderr)
        for failure in failures:
            print(repr(failure), file=sys.stderr)
        return 2
    print(
        "portable skill execution selftest: PASS (1 positive, 10 independent negatives)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
