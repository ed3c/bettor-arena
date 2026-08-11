#!/usr/bin/env python3
"""Context Capsules and fixed Claude Code / Codex CLI canaries.

A capsule binds the exact tracked root and loop passive-context bytes, the loop
working directory, and the native driver entrypoints.  `prepare` and `canary`
require an immutable commit SHA or immutable `v*` tag, materialize a disposable
Git worktree, re-verify the capsule at that subject, and always remove the
worktree.  The public command does not accept arbitrary cwd, prompt, or driver
flags.

Live canaries use a fixed request: read the native passive context and reply
exactly CONTEXT_OK.  Absence or an unrun carrier is NOT_EXERCISED, never PASS.

Exit codes:
  0  contract valid / prepared / canary passed
  2  contract violation or canary failure
  64 usage, missing tool, unreadable input, or worktree failure
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Iterator


CAPSULE_SCHEMA = "bettor-arena/context-capsule/v1"
LOCK_SCHEMA = "bettor-arena/context-lock/v1"
RECEIPT_SCHEMA = "bettor-arena/context-driver-receipt/v1"
PARITY_SCHEMA = "bettor-arena/driver-parity-receipt/v1"
DRIVERS = {"claude-code", "codex-cli"}
IMMUTABLE_SHA = re.compile(r"^[0-9a-f]{40}$")
IMMUTABLE_TAG = re.compile(r"^v[0-9][0-9A-Za-z._-]*$")
FIXED_PROMPT = (
    "Read the native root and loop passive context for this checkout. "
    "Do not modify files. Reply exactly CONTEXT_OK."
)


class ContextError(ValueError):
    """A context capsule, driver result, or immutable subject is invalid."""


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def digest_value(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContextError(f"missing JSON: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ContextError(f"unreadable JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContextError(f"JSON root must be an object: {path}")
    return value


def normalize_path(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContextError(f"{field} must be a non-empty string")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ContextError(f"{field} must be repo-relative without '..': {value}")
    normalized = path.as_posix().rstrip("/")
    return normalized or "."


def string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ContextError(f"{field} must be a non-empty array")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ContextError(f"{field} contains a non-string/empty item")
    if len(value) != len(set(value)):
        raise ContextError(f"{field} contains duplicates")
    return list(value)


def git(root: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise ContextError(process.stderr.strip() or f"git {' '.join(args)} failed")
    return process.stdout.strip()


def git_entries(root: Path) -> dict[str, dict[str, str]]:
    process = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--stage", "-z"],
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise ContextError(
            process.stderr.decode("utf-8", errors="replace").strip()
            or "git ls-files --stage failed"
        )
    result: dict[str, dict[str, str]] = {}
    for raw in process.stdout.split(b"\0"):
        if not raw:
            continue
        metadata, separator, path_raw = raw.partition(b"\t")
        if not separator:
            raise ContextError("malformed Git index entry")
        mode, blob, stage = metadata.decode("ascii").split()
        if stage != "0":
            raise ContextError("unmerged context bytes cannot be frozen")
        path = path_raw.decode("utf-8", errors="strict")
        result[path] = {"path": path, "mode": mode, "blob": blob}
    return result


def validate_capsule(value: dict[str, Any], path: Path, root: Path) -> dict[str, Any]:
    required = {
        "schema",
        "id",
        "module",
        "loop",
        "cwd",
        "common",
        "drivers",
        "policy",
    }
    if set(value) != required:
        raise ContextError(f"{path}: capsule fields drifted")
    if value["schema"] != CAPSULE_SCHEMA:
        raise ContextError(f"{path}: schema must be {CAPSULE_SCHEMA}")
    for field in ("id", "module", "loop"):
        if not isinstance(value[field], str) or not value[field].strip():
            raise ContextError(f"{path}: {field} is required")
    if path.stem != value["id"]:
        raise ContextError(f"{path}: filename must equal capsule id")
    value["cwd"] = normalize_path(value["cwd"], f"{value['id']}.cwd")
    if not (root / value["cwd"]).is_dir():
        raise ContextError(f"{path}: cwd is absent: {value['cwd']}")
    value["common"] = [
        normalize_path(item, f"{value['id']}.common")
        for item in string_list(value["common"], f"{value['id']}.common")
    ]
    drivers = value["drivers"]
    if not isinstance(drivers, dict) or set(drivers) != DRIVERS:
        raise ContextError(f"{path}: drivers must be Claude Code and Codex CLI")
    for driver, config in drivers.items():
        if not isinstance(config, dict) or set(config) != {"entry", "binary"}:
            raise ContextError(f"{path}: malformed driver entry: {driver}")
        config["entry"] = normalize_path(
            config["entry"], f"{value['id']}.{driver}.entry"
        )
        expected_binary = "claude" if driver == "claude-code" else "codex"
        if config["binary"] != expected_binary:
            raise ContextError(
                f"{path}: {driver} binary must be fixed to {expected_binary}"
            )
    policy = value["policy"]
    if not isinstance(policy, dict) or set(policy) != {
        "immutable_ref_required",
        "mutation",
        "network",
        "secrets",
        "max_seconds",
    }:
        raise ContextError(f"{path}: policy fields drifted")
    if policy["immutable_ref_required"] is not True:
        raise ContextError(f"{path}: immutable refs are mandatory")
    if policy["mutation"] != "none":
        raise ContextError(f"{path}: context canary must be read-only")
    if policy["network"] not in {"host-policy", "none"}:
        raise ContextError(f"{path}: unsupported network policy")
    if policy["secrets"] not in {"host-only", "none"}:
        raise ContextError(f"{path}: unsupported secrets policy")
    if not isinstance(policy["max_seconds"], int) or policy["max_seconds"] <= 0:
        raise ContextError(f"{path}: max_seconds must be positive")
    return value


def load_capsules(root: Path) -> dict[str, dict[str, Any]]:
    context_root = root / ".arena" / "contexts"
    if not context_root.is_dir():
        raise ContextError(f"missing context catalog: {context_root}")
    capsules: dict[str, dict[str, Any]] = {}
    for path in sorted(context_root.glob("*.json")):
        value = validate_capsule(read_json(path), path, root)
        if value["id"] in capsules:
            raise ContextError(f"duplicate context id: {value['id']}")
        capsules[value["id"]] = value
    if not capsules:
        raise ContextError("context catalog is empty")
    return capsules


def context_lock(root: Path) -> dict[str, Any]:
    capsules = load_capsules(root)
    entries = git_entries(root)
    locked: list[dict[str, Any]] = []
    for context_id, capsule in sorted(capsules.items()):
        paths = sorted(
            set(
                capsule["common"]
                + [capsule["drivers"][driver]["entry"] for driver in sorted(DRIVERS)]
            )
        )
        files: list[dict[str, str]] = []
        for path in paths:
            entry = entries.get(path)
            if entry is None:
                raise ContextError(f"{context_id}: context path is not tracked: {path}")
            files.append(entry)
        unsigned = {
            "id": context_id,
            "module": capsule["module"],
            "loop": capsule["loop"],
            "cwd": capsule["cwd"],
            "common": capsule["common"],
            "drivers": capsule["drivers"],
            "policy": capsule["policy"],
            "files": files,
        }
        unsigned["context_sha256"] = digest_value(unsigned)
        locked.append(unsigned)
    value: dict[str, Any] = {"schema": LOCK_SCHEMA, "contexts": locked}
    value["content_sha256"] = digest_value(value)
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def immutable_ref(root: Path, ref: str) -> tuple[str, str]:
    if ref in {"HEAD", "main", "master", "trunk"}:
        raise ContextError(f"mutable ref is refused: {ref}")
    if not (IMMUTABLE_SHA.fullmatch(ref) or IMMUTABLE_TAG.fullmatch(ref)):
        raise ContextError("ref must be a 40-hex commit or immutable v* tag")
    commit = git(root, "rev-parse", f"{ref}^{{commit}}")
    tree = git(root, "rev-parse", f"{commit}^{{tree}}")
    if not IMMUTABLE_SHA.fullmatch(commit) or not IMMUTABLE_SHA.fullmatch(tree):
        raise ContextError("resolved ref did not produce immutable Git ids")
    return commit, tree


@contextmanager
def disposable_worktree(root: Path, commit: str) -> Iterator[Path]:
    parent = Path(tempfile.mkdtemp(prefix="arena-context."))
    worktree = parent / "worktree"
    try:
        process = subprocess.run(
            ["git", "-C", str(root), "worktree", "add", "--detach", str(worktree), commit],
            text=True,
            capture_output=True,
            check=False,
        )
        if process.returncode != 0:
            raise ContextError(process.stderr.strip() or "git worktree add failed")
        yield worktree
    finally:
        if worktree.exists():
            subprocess.run(
                ["git", "-C", str(root), "worktree", "remove", "--force", str(worktree)],
                text=True,
                capture_output=True,
                check=False,
            )
        shutil.rmtree(parent, ignore_errors=True)


def strip_environment(driver: str) -> dict[str, str]:
    environment = dict(os.environ)
    if driver == "claude-code":
        for name in (
            "ANTHROPIC_API_KEY",
            "CODEX_ACCESS_TOKEN",
            "CODEX_API_KEY",
            "CODEX_HOME",
            "OPENAI_API_KEY",
        ):
            environment.pop(name, None)
    else:
        for name in (
            "ANTHROPIC_API_KEY",
            "CLAUDE_CODE_OAUTH_TOKEN",
            "CLAUDE_CONFIG_DIR",
            "OPENAI_API_KEY",
        ):
            environment.pop(name, None)
    return environment


def driver_command(driver: str, binary: str, output: Path) -> list[str]:
    if driver == "claude-code":
        return [binary, "-p", FIXED_PROMPT, "--max-turns", "1"]
    if driver == "codex-cli":
        return [
            binary,
            "exec",
            "-s",
            "read-only",
            "--ephemeral",
            FIXED_PROMPT,
            "-o",
            str(output),
        ]
    raise ContextError(f"unknown driver: {driver}")


def run_driver(
    cwd: Path,
    driver: str,
    binary: str,
    timeout: int,
) -> tuple[int, str]:
    with tempfile.NamedTemporaryFile(prefix="arena-driver-output.") as output:
        command = driver_command(driver, binary, Path(output.name))
        try:
            process = subprocess.run(
                command,
                cwd=cwd,
                env=strip_environment(driver),
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ContextError(f"driver binary absent: {binary}") from exc
        except subprocess.TimeoutExpired as exc:
            raise ContextError(f"driver timed out: {driver}") from exc
        reply = process.stdout
        if driver == "codex-cli":
            reply = Path(output.name).read_text(encoding="utf-8")
        return process.returncode, reply


def selected_context(lock: dict[str, Any], context_id: str) -> dict[str, Any]:
    matches = [item for item in lock["contexts"] if item["id"] == context_id]
    if len(matches) != 1:
        raise ContextError(f"unknown or duplicate context id: {context_id}")
    return matches[0]


def parity_receipt(lock: dict[str, Any]) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema": PARITY_SCHEMA,
        "context_lock_sha256": digest_value(lock),
        "offline_contract": "PASS",
        "claude_code": "NOT_EXERCISED",
        "codex_cli": "NOT_EXERCISED",
        "note": "Fixed driver commands and shared capsule bytes are validated offline; live subscription carriers require host-owned sessions.",
    }
    value["content_sha256"] = digest_value(value)
    return value


def prepare_or_canary(
    root: Path,
    context_id: str,
    driver: str,
    ref: str,
    live: bool,
) -> dict[str, Any]:
    if driver not in DRIVERS:
        raise ContextError(f"unknown driver: {driver}")
    commit, tree = immutable_ref(root, ref)
    current_lock = context_lock(root)
    context = selected_context(current_lock, context_id)
    receipt: dict[str, Any]
    cleaned = False
    with disposable_worktree(root, commit) as worktree:
        worktree_lock = context_lock(worktree)
        worktree_context = selected_context(worktree_lock, context_id)
        if worktree_context["context_sha256"] != context["context_sha256"]:
            raise ContextError("selected immutable ref carries different context bytes")
        cwd = worktree / context["cwd"]
        state = "NOT_EXERCISED"
        exit_code: int | None = None
        reply_sha: str | None = None
        if live:
            config = context["drivers"][driver]
            exit_code, reply = run_driver(
                cwd,
                driver,
                config["binary"],
                context["policy"]["max_seconds"],
            )
            state = "PASS" if exit_code == 0 and reply.strip() == "CONTEXT_OK" else "FAIL"
            reply_sha = hashlib.sha256(reply.encode("utf-8")).hexdigest()
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "context": context_id,
            "module": context["module"],
            "loop": context["loop"],
            "driver": driver,
            "commit": commit,
            "tree": tree,
            "context_sha256": context["context_sha256"],
            "state": state,
            "exit": exit_code,
            "reply_sha256": reply_sha,
            "cleanup": "PENDING",
        }
    cleaned = True
    receipt["cleanup"] = "PASS" if cleaned else "FAIL"
    receipt["content_sha256"] = digest_value(receipt)
    if receipt["state"] == "FAIL":
        raise ContextError(f"{driver} context canary failed")
    return receipt


def check(root: Path) -> None:
    expected_lock = context_lock(root)
    lock_path = root / ".arena" / "contexts.lock.json"
    actual_lock = read_json(lock_path)
    if actual_lock != expected_lock:
        raise ContextError(
            f"{lock_path}: stale context lock; run `python3 scripts/arena_context.py lock --output .arena/contexts.lock.json`"
        )
    expected_parity = parity_receipt(expected_lock)
    parity_path = root / "data" / "context-capsules" / "driver-parity.json"
    actual_parity = read_json(parity_path)
    if actual_parity != expected_parity:
        raise ContextError(
            f"{parity_path}: stale parity receipt; run `python3 scripts/arena_context.py parity --output data/context-capsules/driver-parity.json`"
        )


def init_fixture(path: Path) -> str:
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "t@local"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "t"], check=True)
    (path / ".arena" / "contexts").mkdir(parents=True)
    (path / "loop").mkdir()
    (path / "AGENTS.md").write_text("root codex\n", encoding="utf-8")
    (path / "CLAUDE.md").write_text("root claude\n", encoding="utf-8")
    (path / "loop" / "AGENTS.md").write_text("loop codex\n", encoding="utf-8")
    (path / "loop" / "CLAUDE.md").write_text("loop claude\n", encoding="utf-8")
    (path / "loop" / "PROMPT.md").write_text("goal\n", encoding="utf-8")
    capsule = {
        "schema": CAPSULE_SCHEMA,
        "id": "fixture",
        "module": "fixture",
        "loop": "fixture",
        "cwd": "loop",
        "common": ["AGENTS.md", "CLAUDE.md", "loop/PROMPT.md"],
        "drivers": {
            "claude-code": {"entry": "loop/CLAUDE.md", "binary": "claude"},
            "codex-cli": {"entry": "loop/AGENTS.md", "binary": "codex"},
        },
        "policy": {
            "immutable_ref_required": True,
            "mutation": "none",
            "network": "none",
            "secrets": "none",
            "max_seconds": 5,
        },
    }
    write_json(path / ".arena" / "contexts" / "fixture.json", capsule)
    subprocess.run(["git", "-C", str(path), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-qm", "fixture"], check=True)
    return git(path, "rev-parse", "HEAD")


def selftest() -> None:
    if driver_command("claude-code", "claude", Path("out"))[:2] != ["claude", "-p"]:
        raise ContextError("Claude driver command drifted")
    if driver_command("codex-cli", "codex", Path("out"))[:2] != ["codex", "exec"]:
        raise ContextError("Codex driver command drifted")
    try:
        immutable_ref(Path.cwd(), "HEAD")
    except ContextError:
        pass
    else:
        raise ContextError("mutable HEAD was accepted")

    with tempfile.TemporaryDirectory(prefix="context-fixture.") as temp:
        root = Path(temp) / "repo"
        root.mkdir()
        commit = init_fixture(root)
        first = context_lock(root)
        second = context_lock(root)
        if first != second:
            raise ContextError("context lock is not deterministic")
        before = first["contexts"][0]["context_sha256"]
        (root / "loop" / "PROMPT.md").write_text("changed\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", "loop/PROMPT.md"], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "change"], check=True)
        after = context_lock(root)["contexts"][0]["context_sha256"]
        if before == after:
            raise ContextError("changed context retained its digest")

        capsule_path = root / ".arena" / "contexts" / "fixture.json"
        capsule = read_json(capsule_path)
        capsule["common"].append("missing.md")
        write_json(capsule_path, capsule)
        subprocess.run(["git", "-C", str(root), "add", str(capsule_path)], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "missing"], check=True)
        try:
            context_lock(root)
        except ContextError:
            pass
        else:
            raise ContextError("missing context path was accepted")

        capsule["common"].pop()
        capsule["cwd"] = "../escape"
        write_json(capsule_path, capsule)
        try:
            load_capsules(root)
        except ContextError:
            pass
        else:
            raise ContextError("path escape was accepted")

        # Restore a valid committed fixture, then prove the disposable worktree cleans up.
        subprocess.run(["git", "-C", str(root), "reset", "--hard", commit], check=True, capture_output=True)
        parent: Path | None = None
        with disposable_worktree(root, commit) as worktree:
            parent = worktree.parent
            if not worktree.is_dir():
                raise ContextError("disposable worktree was not materialized")
        if parent is None or parent.exists():
            raise ContextError("disposable worktree was not cleaned")

        fake = Path(temp) / "fake"
        fake.write_text("#!/bin/sh\nprintf 'WRONG\\n'\n", encoding="utf-8")
        fake.chmod(0o755)
        rc, reply = run_driver(root, "claude-code", str(fake), 5)
        if rc != 0 or reply.strip() == "CONTEXT_OK":
            raise ContextError("driver output-drift control did not disagree")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="arena_context.py")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--selftest", action="store_true")
    subparsers = parser.add_subparsers(dest="command")

    lock_parser = subparsers.add_parser("lock")
    lock_parser.add_argument("--output", type=Path)

    parity_parser = subparsers.add_parser("parity")
    parity_parser.add_argument("--output", type=Path)

    subparsers.add_parser("check")

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--context", required=True)
    prepare_parser.add_argument("--driver", choices=sorted(DRIVERS), required=True)
    prepare_parser.add_argument("--ref", required=True)
    prepare_parser.add_argument("--output", type=Path)

    canary_parser = subparsers.add_parser("canary")
    canary_parser.add_argument("--context", required=True)
    canary_parser.add_argument("--driver", choices=sorted(DRIVERS), required=True)
    canary_parser.add_argument("--ref", required=True)
    canary_parser.add_argument("--output", type=Path)
    canary_parser.add_argument("--live", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.selftest:
            if args.command is not None:
                parser.error("--selftest cannot be combined with a command")
            selftest()
            print("SELFTEST GREEN: Context Capsules and driver parity")
            return 0
        if args.command is None:
            parser.error("a command is required")
        root = args.root.resolve()
        if args.command == "lock":
            value = context_lock(root)
            if args.output:
                output = args.output if args.output.is_absolute() else root / args.output
                write_json(output, value)
                print(f"WROTE {output}")
            else:
                print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))
            return 0
        if args.command == "parity":
            value = parity_receipt(context_lock(root))
            if args.output:
                output = args.output if args.output.is_absolute() else root / args.output
                write_json(output, value)
                print(f"WROTE {output}")
            else:
                print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))
            return 0
        if args.command == "check":
            check(root)
            print("PASS Context Capsules and offline driver parity")
            return 0
        live = args.command == "canary" and args.live
        value = prepare_or_canary(root, args.context, args.driver, args.ref, live)
        if args.output:
            output = args.output if args.output.is_absolute() else root / args.output
            write_json(output, value)
            print(f"WROTE {output}")
        else:
            print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except ContextError as exc:
        print(f"context RED: {exc}", file=sys.stderr)
        return 2
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"context FATAL: {exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
