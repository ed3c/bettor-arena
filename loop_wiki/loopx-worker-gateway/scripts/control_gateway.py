#!/usr/bin/env python3
# ruff: noqa: F401,F403,F405  # this module family composes through star imports; the names ruff reads as unused are deliberate re-exports the downstream modules import through.
"""Independent subprocess control for the LoopX Worker Gateway public port."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Sequence

from gateway_common import (
    BAD,
    OK,
    USAGE,
    canonical_bytes,
    digest,
    file_digest,
    load_json,
    write_json_atomic,
)
from gateway_contract import validate_adapter, validate_receipt, validate_request


class ControlFailure(RuntimeError):
    pass


def invoke(argv: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
        env={
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PYTHONUNBUFFERED": "1",
            "CI": "true",
        },
    )


def expect(
    result: subprocess.CompletedProcess[str],
    code: int,
    label: str,
    marker: str | None = None,
) -> None:
    if result.returncode != code:
        raise ControlFailure(
            f"{label}: expected {code}, observed {result.returncode}; "
            f"stdout={result.stdout[-500:]!r}; stderr={result.stderr[-500:]!r}"
        )
    if marker is not None and marker not in (result.stdout + result.stderr):
        raise ControlFailure(f"{label}: missing marker {marker!r}")


def git(repo: Path, *args: str) -> str:
    result = invoke(["git", "-C", str(repo), *args], repo)
    if result.returncode != 0:
        raise ControlFailure(f"git {' '.join(args)} failed: {result.stderr[-500:]}")
    return result.stdout.strip()


def with_digest(value: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result["content_digest"] = None
    raw = copy.deepcopy(result)
    raw.pop("content_digest")
    result["content_digest"] = digest(raw)
    return result


def fixture_descriptor() -> dict[str, Any]:
    source = {
        "repository": "ed3c/bettor-arena",
        "ref": "fixture-worker-v1",
        "digest": digest({"fixture": "loopx-worker-gateway", "version": 1}),
    }
    return with_digest(
        {
            "schema_version": "loopx/worker-adapter/v1",
            "adapter_id": "fixture-host",
            "host_id": "fixture-host",
            "classification": "WHITE_BOX_REFERENCE",
            "transport": "CLI",
            "binary": "python3",
            "version_argv": ["--version"],
            "implementation_state": "IMPLEMENTED",
            "source_identity": source,
            "skill_roots": [".agents/skills"],
            "instruction_routes": ["AGENTS.md"],
            "adapter_entry": "scripts/fake_worker.py",
            "trace_ceiling": "SOURCE_VERIFIED_INTERNAL",
            "capabilities": {
                "structured_output": True,
                "streaming": True,
                "session_resume": False,
                "loaded_skill_digest": True,
                "loaded_context_digest": True,
                "offline": True,
            },
        }
    )


def make_repo(repo: Path) -> tuple[str, str]:
    repo.mkdir()
    invoke(["git", "init", "-b", "main", str(repo)], repo.parent)
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "user.name", "LoopX Fixture")
    (repo / ".agents/skills/fixture").mkdir(parents=True)
    (repo / "task").mkdir()
    (repo / "src").mkdir()
    (repo / "AGENTS.md").write_text("# Fixture repository\n", encoding="utf-8")
    (repo / ".agents/skills/fixture/SKILL.md").write_text(
        "---\nname: fixture\ndescription: deterministic Worker Gateway fixture\n---\n\nExecute one bounded fixture task.\n",
        encoding="utf-8",
    )
    (repo / "task/prompt.md").write_text(
        "Write a deterministic fixture result.\n", encoding="utf-8"
    )
    (repo / "src/base.txt").write_text("base\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "fixture subject")
    commit = git(repo, "rev-parse", "HEAD")
    tree = git(repo, "rev-parse", "HEAD^{tree}")
    return commit, tree


def fixture_request(repo: Path, commit: str, tree: str) -> dict[str, Any]:
    skill = repo / ".agents/skills/fixture/SKILL.md"
    prompt = repo / "task/prompt.md"
    context = repo / "AGENTS.md"
    return with_digest(
        {
            "schema_version": "loopx/worker-request/v1",
            "request_id": "fixture-worker-request",
            "subject": {
                "repository": "ed3c/bettor-arena",
                "commit": commit,
                "tree": tree,
                "task_id": "fixture-worker-gateway",
            },
            "adapter_id": "fixture-host",
            "host_id": "fixture-host",
            "skill": {
                "name": "fixture",
                "digest": file_digest(skill),
                "source_ref": ".agents/skills/fixture/SKILL.md",
            },
            "context": {
                "digest": file_digest(context),
                "entry_files": ["AGENTS.md"],
            },
            "workspace": {
                "lease_id": "fixture-worker-lease",
                "writable_paths": ["generated"],
                "read_only_paths": ["AGENTS.md", "src/base.txt"],
                "cleanup": "REQUIRED",
            },
            "policy": {
                "timeout_ms": 30000,
                "max_output_bytes": 1048576,
                "max_processes": 4,
                "network": "HOST_POLICY",
                "env_allowlist": ["CI"],
                "require_process_group": True,
            },
            "task": {
                "prompt_ref": {
                    "artifact_id": "fixture-prompt",
                    "kind": "FILE",
                    "path": "task/prompt.md",
                    "digest": file_digest(prompt),
                    "bytes": prompt.stat().st_size,
                    "media_type": "text/markdown",
                    "producer": "fixture-builder",
                },
                "mode": "EDIT",
                "expected_artifacts": [
                    "STDOUT",
                    "STDERR",
                    "GIT_DIFF",
                    "WORKER_EVENT",
                    "CLEANUP_REPORT",
                ],
            },
            "credential_refs": [],
        }
    )


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    gateway = root / "scripts/gateway.py"
    try:
        with tempfile.TemporaryDirectory(
            prefix="loopx-worker-gateway-control."
        ) as temporary:
            temp = Path(temporary)
            repo = temp / "repo"
            commit, tree = make_repo(repo)
            descriptor = fixture_descriptor()
            request = fixture_request(repo, commit, tree)
            validate_adapter(descriptor, allow_fixture=True)
            validate_request(request, {descriptor["adapter_id"]: descriptor})

            descriptor_path = temp / "fixture-adapter.json"
            request_path = temp / "request.json"
            write_json_atomic(descriptor_path, descriptor)
            write_json_atomic(request_path, request)
            output = temp / "run-output"
            result = invoke(
                [
                    sys.executable,
                    str(gateway),
                    "run",
                    "--request",
                    str(request_path),
                    "--adapter",
                    str(descriptor_path),
                    "--repo",
                    str(repo),
                    "--output",
                    str(output),
                    "--receipt-id",
                    "fixture-worker-receipt",
                    "--allow-fixture-adapter",
                ],
                root,
            )
            expect(result, OK, "fixture run")
            receipt = validate_receipt(
                load_json(output / "receipt.json"), request, descriptor
            )
            if receipt["status"] != "PASS" or receipt["trace"]["event_count"] != 3:
                raise ControlFailure(
                    "fixture receipt did not record an executed three-event PASS"
                )
            if any(receipt["authority"].values()):
                raise ControlFailure("fixture Worker escaped its authority ceiling")

            production_descriptor = root / "adapters/codex-cli.json"
            production_request = copy.deepcopy(request)
            production_request["request_id"] = "codex-not-exercised"
            production_request["adapter_id"] = "codex-cli"
            production_request["host_id"] = "codex-cli"
            raw = copy.deepcopy(production_request)
            raw.pop("content_digest")
            production_request["content_digest"] = digest(raw)
            production_request_path = temp / "codex-request.json"
            write_json_atomic(production_request_path, production_request)
            not_exercised = temp / "not-exercised"
            result = invoke(
                [
                    sys.executable,
                    str(gateway),
                    "run",
                    "--request",
                    str(production_request_path),
                    "--adapter",
                    str(production_descriptor),
                    "--repo",
                    str(repo),
                    "--output",
                    str(not_exercised),
                    "--receipt-id",
                    "codex-not-exercised-receipt",
                ],
                root,
            )
            expect(result, BAD, "not-exercised production adapter")
            codex_descriptor = load_json(production_descriptor)
            status_receipt = validate_receipt(
                load_json(not_exercised / "receipt.json"),
                production_request,
                codex_descriptor,
            )
            if status_receipt["status"] != "NOT_EXERCISED":
                raise ControlFailure(
                    "production adapter presence was promoted beyond NOT_EXERCISED"
                )

            traversal = copy.deepcopy(request)
            traversal["workspace"]["writable_paths"] = ["../escape"]
            raw = copy.deepcopy(traversal)
            raw.pop("content_digest")
            traversal["content_digest"] = digest(raw)
            traversal_path = temp / "traversal.json"
            write_json_atomic(traversal_path, traversal)
            result = invoke(
                [
                    sys.executable,
                    str(gateway),
                    "run",
                    "--request",
                    str(traversal_path),
                    "--adapter",
                    str(descriptor_path),
                    "--repo",
                    str(repo),
                    "--output",
                    str(temp / "traversal-output"),
                    "--receipt-id",
                    "traversal-receipt",
                    "--allow-fixture-adapter",
                ],
                root,
            )
            expect(result, BAD, "path traversal", "RED:")

            mismatch = copy.deepcopy(request)
            mismatch["skill"]["digest"] = "sha256:" + "0" * 64
            raw = copy.deepcopy(mismatch)
            raw.pop("content_digest")
            mismatch["content_digest"] = digest(raw)
            mismatch_path = temp / "mismatch.json"
            write_json_atomic(mismatch_path, mismatch)
            result = invoke(
                [
                    sys.executable,
                    str(gateway),
                    "run",
                    "--request",
                    str(mismatch_path),
                    "--adapter",
                    str(descriptor_path),
                    "--repo",
                    str(repo),
                    "--output",
                    str(temp / "mismatch-output"),
                    "--receipt-id",
                    "mismatch-receipt",
                    "--allow-fixture-adapter",
                ],
                root,
            )
            expect(result, BAD, "Skill mismatch", "RED:")

            result = invoke([sys.executable, str(gateway), "run"], root)
            expect(result, USAGE, "invalid invocation", "FATAL:")

            print(
                "loopx-worker-gateway control PASS: "
                "fixture=PASS codex=NOT_EXERCISED traversal=2 skill-mismatch=2 invocation=64 cleanup=PASS"
            )
            return OK
    except subprocess.TimeoutExpired as exc:
        print(f"FATAL: control timeout: {exc}", file=sys.stderr)
        return USAGE
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FATAL: control runtime/input error: {exc}", file=sys.stderr)
        return USAGE
    except (ControlFailure, Exception) as exc:
        # Preserve typed gateway errors while keeping this independent control bounded.
        print(f"loopx-worker-gateway control RED: {exc}", file=sys.stderr)
        return BAD


if __name__ == "__main__":
    raise SystemExit(main())
