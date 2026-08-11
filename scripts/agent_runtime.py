#!/usr/bin/env python3
"""Validate and exercise bettor-arena's aggregate Agent module set.

Offline validates portable desired/resolved closure. Adapter additionally proves
the two local skill discovery surfaces resolve to the pinned skill bytes. Strict
also requires a same-HEAD, same-binding live Claude/Codex canary receipt.

Exit: 0 selected level passed · 2 failed/incomplete · 64 usage/tool failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any


HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def canonical(document: dict[str, Any]) -> bytes:
    return json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def load_json(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"missing {relative}") from error
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"unreadable {relative}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{relative} must contain an object")
    return value


def verify_content_hash(document: dict[str, Any], label: str) -> list[str]:
    claimed = document.get("content_sha256")
    unsigned = dict(document)
    unsigned.pop("content_sha256", None)
    if not isinstance(claimed, str) or not HEX64.fullmatch(claimed):
        return [f"{label}: invalid content_sha256"]
    if sha256_bytes(canonical(unsigned)) != claimed:
        return [f"{label}: content_sha256 mismatch"]
    return []


def skill_digest(path: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(
        item
        for item in path.rglob("*")
        if item.is_file()
        and "__pycache__" not in item.parts
        and not item.name.endswith(".pyc")
    )
    for item in files:
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], text=True, capture_output=True, check=False
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git failed")
    return result.stdout.strip()


def validate_offline(root: Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    manifest = load_json(root, ".agents/module-set.json")
    if manifest.get("schema") != "bettor-arena/agent-module-set/v1":
        failures.append("module-set: unexpected schema")
    components = manifest.get("components")
    carriers = manifest.get("carriers")
    if not isinstance(components, dict) or set(components) != {
        "runtime_env",
        "shared_skills",
    }:
        failures.append("module-set: component set is not closed")
        return failures, manifest
    if not isinstance(carriers, dict) or set(carriers) != {
        "claude_code",
        "codex_cli",
    }:
        failures.append(
            "module-set: carrier set must contain Claude Code and Codex CLI"
        )
        return failures, manifest

    shared_paths = components["shared_skills"]
    runtime_paths = components["runtime_env"]
    shared_req = load_json(root, shared_paths["requirements"])
    shared = load_json(root, shared_paths["binding"])
    failures.extend(verify_content_hash(shared, "shared-skills binding"))
    if shared.get("schema") != "shared-skills/consumer-binding/v1":
        failures.append("shared-skills binding: unexpected schema")
    if shared.get("requirements_sha256") != sha256_bytes(
        (root / shared_paths["requirements"]).read_bytes()
    ):
        failures.append("shared-skills binding: requirements digest mismatch")
    resolved_names = [item.get("name") for item in shared.get("skills", [])]
    if resolved_names != sorted(shared_req.get("shared", [])):
        failures.append(
            "shared-skills binding: resolved names differ from requirements"
        )
    if shared.get("repo_owned") != sorted(shared_req.get("repo_owned", [])):
        failures.append("shared-skills binding: repo-owned rulings differ")
    if shared.get("surfaces") != shared_req.get("surfaces"):
        failures.append("shared-skills binding: carrier surfaces differ")
    for item in shared.get("skills", []):
        if not isinstance(item, dict) or set(item) != {
            "content_sha256",
            "entrypoint",
            "name",
        }:
            failures.append("shared-skills binding: malformed skill entry")
            continue
        if not HEX64.fullmatch(str(item["content_sha256"])):
            failures.append(f"shared-skills binding: invalid digest for {item['name']}")

    runtime_req = load_json(root, runtime_paths["requirements"])
    runtime = load_json(root, runtime_paths["binding"])
    failures.extend(verify_content_hash(runtime, "runtime-env binding"))
    if runtime.get("schema") != "runtime-env/consumer-binding/v2":
        failures.append("runtime-env binding: consumer-binding/v2 required")
    if runtime.get("requirements_sha256") != sha256_bytes(
        (root / runtime_paths["requirements"]).read_bytes()
    ):
        failures.append("runtime-env binding: requirements digest mismatch")
    if runtime.get("profile") != runtime_req.get("profile"):
        failures.append("runtime-env binding: profile differs from requirements")
    resolved_modules = [item.get("id") for item in runtime.get("modules", [])]
    if resolved_modules != runtime_req.get("required_modules"):
        failures.append("runtime-env binding: resolved module closure differs")
    for item in runtime.get("modules", []):
        if (
            not isinstance(item, dict)
            or item.get("interface_version") != "runtime-env/module/v1"
        ):
            failures.append("runtime-env binding: unsupported module interface")
        elif not HEX64.fullmatch(str(item.get("content_sha256", ""))):
            failures.append(f"runtime-env binding: invalid digest for {item.get('id')}")
    projections = runtime.get("projections", {})
    expected_policies = [
        f".runtime-env/policies/{name}.json" for name in runtime_req.get("policies", [])
    ]
    if projections.get("policies") != expected_policies:
        failures.append("runtime-env binding: policy closure differs")
    if projections.get("workload") != manifest.get("workload"):
        failures.append("runtime-env binding: workload projection differs")
    for relative in [manifest.get("workload"), *expected_policies]:
        if not isinstance(relative, str) or not (root / relative).is_file():
            failures.append(f"module-set: missing projection {relative}")
    for carrier, expected_policy in (
        ("claude_code", expected_policies[0] if expected_policies else None),
        ("codex_cli", expected_policies[1] if len(expected_policies) > 1 else None),
    ):
        value = carriers.get(carrier, {})
        if value.get("policy") != expected_policy:
            failures.append(
                f"module-set: {carrier} policy is not the resolved projection"
            )
        surface = value.get("skill_surface")
        if (
            not isinstance(surface, str)
            or Path(surface).is_absolute()
            or ".." in Path(surface).parts
        ):
            failures.append(f"module-set: {carrier} surface is not repo-relative")

    for binding in (shared, runtime):
        source = binding.get("source", {})
        if not HEX40.fullmatch(str(source.get("commit", ""))) or not HEX40.fullmatch(
            str(source.get("tree", ""))
        ):
            failures.append("module-set: source receipt has invalid Git ids")
        if not str(source.get("repository", "")).startswith(("https://", "http://")):
            failures.append("module-set: source repository identity is not a URL")
    return failures, manifest


def validate_adapter(root: Path, manifest: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    shared = load_json(root, manifest["components"]["shared_skills"]["binding"])
    expected = {item["name"]: item["content_sha256"] for item in shared["skills"]}
    for carrier, config in manifest["carriers"].items():
        surface = root / config["skill_surface"]
        for name, wanted in expected.items():
            skill = surface / name
            if not (skill / "SKILL.md").is_file():
                failures.append(f"adapter {carrier}: missing skill {name}")
                continue
            try:
                actual = skill_digest(skill)
            except OSError as error:
                failures.append(f"adapter {carrier}: unreadable skill {name}: {error}")
                continue
            if actual != wanted:
                failures.append(f"adapter {carrier}: skill {name} differs from binding")
    return failures


def validate_live(root: Path, manifest: dict[str, Any]) -> list[str]:
    relative = manifest.get("live_receipt")
    if not isinstance(relative, str):
        return ["live: receipt path is absent"]
    try:
        receipt = load_json(root, relative)
    except ValueError:
        return ["live: Claude/Codex canary receipt is NOT_EXERCISED"]
    shared = load_json(root, manifest["components"]["shared_skills"]["binding"])
    runtime = load_json(root, manifest["components"]["runtime_env"]["binding"])
    expected = {
        "commit": git(root, "rev-parse", "HEAD"),
        "module_set_sha256": sha256_bytes(
            (root / ".agents/module-set.json").read_bytes()
        ),
        "runtime_binding_sha256": runtime.get("content_sha256"),
        "shared_binding_sha256": shared.get("content_sha256"),
        "tree": git(root, "rev-parse", "HEAD^{tree}"),
    }
    failures = []
    if receipt.get("schema") != "bettor-arena/agent-runtime-live/v1":
        failures.append("live: unexpected receipt schema")
    if receipt.get("subject") != expected:
        failures.append("live: receipt is stale for this module set or commit")
    lanes = receipt.get("lanes", {})
    for lane in ("claude_code", "codex_cli"):
        if lanes.get(lane) != {"exit": 0, "reply_token_observed": True}:
            failures.append(f"live: {lane} did not complete a real canary")
    return failures


def check(root: Path, level: str) -> int:
    try:
        failures, manifest = validate_offline(root)
        if not failures and level in {"adapter", "strict"}:
            failures.extend(validate_adapter(root, manifest))
        if not failures and level == "strict":
            failures.extend(validate_live(root, manifest))
    except (ValueError, RuntimeError, KeyError, TypeError) as error:
        print(f"agent-runtime FATAL: {error}", file=sys.stderr)
        return 64
    for failure in failures:
        print(f"AGENT-RUNTIME-RED {failure}", file=sys.stderr)
    if failures:
        print(f"INCOMPLETE agent module set level={level}", file=sys.stderr)
        return 2
    print(f"PASS agent module set level={level}")
    if level == "offline":
        print("NOT_EXERCISED local adapter bytes and Claude/Codex live canaries")
    elif level == "adapter":
        print("NOT_EXERCISED Claude/Codex live canaries")
    return 0


def run_live(root: Path, force: bool) -> int:
    if check(root, "adapter") != 0:
        print(
            "agent-runtime: adapter must match the binding before spending model turns",
            file=sys.stderr,
        )
        return 2
    manifest = load_json(root, ".agents/module-set.json")
    receipt_path = root / manifest["live_receipt"]
    if receipt_path.exists() and not force:
        print(
            f"agent-runtime FATAL: receipt exists: {manifest['live_receipt']}",
            file=sys.stderr,
        )
        return 64
    base_env = dict(os.environ)
    claude_env = dict(base_env)
    for name in (
        "ANTHROPIC_API_KEY",
        "CODEX_ACCESS_TOKEN",
        "CODEX_API_KEY",
        "CODEX_HOME",
        "OPENAI_API_KEY",
    ):
        claude_env.pop(name, None)
    codex_env = dict(base_env)
    for name in (
        "ANTHROPIC_API_KEY",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "CLAUDE_CONFIG_DIR",
        "OPENAI_API_KEY",
    ):
        codex_env.pop(name, None)
    try:
        claude = subprocess.run(
            ["claude", "-p", "reply exactly OK", "--max-turns", "1"],
            cwd=root,
            env=claude_env,
            text=True,
            capture_output=True,
            timeout=180,
        )
        with tempfile.NamedTemporaryFile() as last:
            codex = subprocess.run(
                [
                    "codex",
                    "exec",
                    "-s",
                    "read-only",
                    "--ephemeral",
                    "reply exactly OK",
                    "-o",
                    last.name,
                ],
                cwd=root,
                env=codex_env,
                text=True,
                capture_output=True,
                timeout=180,
            )
            codex_reply = Path(last.name).read_text(encoding="utf-8")
    except FileNotFoundError as error:
        print(
            f"agent-runtime FATAL: carrier CLI absent: {error.filename}",
            file=sys.stderr,
        )
        return 64
    except subprocess.TimeoutExpired as error:
        print(
            f"agent-runtime RED: carrier canary timed out: {error.cmd[0]}",
            file=sys.stderr,
        )
        return 2
    shared = load_json(root, manifest["components"]["shared_skills"]["binding"])
    runtime = load_json(root, manifest["components"]["runtime_env"]["binding"])
    receipt = {
        "lanes": {
            "claude_code": {
                "exit": claude.returncode,
                "reply_token_observed": "OK" in claude.stdout,
            },
            "codex_cli": {
                "exit": codex.returncode,
                "reply_token_observed": "OK" in codex_reply,
            },
        },
        "schema": "bettor-arena/agent-runtime-live/v1",
        "subject": {
            "commit": git(root, "rev-parse", "HEAD"),
            "module_set_sha256": sha256_bytes(
                (root / ".agents/module-set.json").read_bytes()
            ),
            "runtime_binding_sha256": runtime["content_sha256"],
            "shared_binding_sha256": shared["content_sha256"],
            "tree": git(root, "rev-parse", "HEAD^{tree}"),
        },
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return check(root, "strict")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent_runtime.py")
    parser.add_argument("command", choices=("check", "live"))
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--adapter", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--force-receipt", action="store_true")
    args = parser.parse_args(argv)
    root = Path(git(Path(__file__).resolve().parent, "rev-parse", "--show-toplevel"))
    if args.command == "live":
        if args.offline or args.adapter:
            parser.error("live cannot be combined with a check level")
        return run_live(root, args.force_receipt)
    if args.force_receipt:
        parser.error("--force-receipt applies only to live")
    level = "offline" if args.offline else "adapter" if args.adapter else "strict"
    return check(root, level)


if __name__ == "__main__":
    raise SystemExit(main())
