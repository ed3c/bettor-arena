#!/usr/bin/env python3
"""One-shot, secret-free host handoff for Bettor #161 runtime-env rebind.

This entrypoint never launches Workers, Git Town, Forgejo, merge, ship, or push.
It only executes the exact runtime-env sync transaction and then asks the
repository-owned #161 admission gate whether the consumer became admissible.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "scripts/gates/check_issue_161_runtime_admission.py"
RUNTIME_COMMIT = "77dca3584a4adb1c463c815bdb5ab603eae32b23"
PROFILE = "bettor-arena-tech-lead-local"
BINDING = "bettor-arena-local"
WORKLOAD = "bettor-arena-proof"
POLICIES = (
    "claude-code-native-isolation",
    "codex-cli-native-isolation",
    "codex-openshell-chatgpt-placeholder",
)


def run(argv: list[str], cwd: Path | None = None) -> dict[str, Any]:
    proc = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "argv": argv,
        "exit_code": proc.returncode,
        "stdout_sha256": hashlib.sha256(proc.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(proc.stderr.encode()).hexdigest(),
    }


def git_value(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed for {repo}")
    return proc.stdout.strip()


def validate_runtime_root(runtime_root: Path) -> dict[str, str]:
    runtime_root = runtime_root.resolve()
    cli = runtime_root / "runtime-env"
    if not cli.is_file():
        raise RuntimeError("runtime-env entrypoint missing")
    head = git_value(runtime_root, "rev-parse", "HEAD")
    if head != RUNTIME_COMMIT:
        raise RuntimeError(f"runtime-env exact subject mismatch: {head}")
    dirty = git_value(runtime_root, "status", "--porcelain")
    if dirty:
        raise RuntimeError("runtime-env checkout must be clean")
    return {"root": str(runtime_root), "commit": head, "cli": str(cli)}


def sync_argv(runtime_cli: Path, mode: str) -> list[str]:
    argv = [
        str(runtime_cli), "sync",
        "--profile", PROFILE,
        "--binding", BINDING,
        "--workload", WORKLOAD,
    ]
    for policy in POLICIES:
        argv += ["--policy", policy]
    argv += ["--target-root", str(ROOT)]
    if mode == "apply":
        argv.append("--apply")
    elif mode == "check":
        argv.append("--check")
    return argv


def validate_contract() -> list[str]:
    errors: list[str] = []
    if len(RUNTIME_COMMIT) != 40:
        errors.append("runtime commit must be SHA-40")
    if PROFILE != "bettor-arena-tech-lead-local":
        errors.append("profile drifted")
    if BINDING != "bettor-arena-local" or WORKLOAD != "bettor-arena-proof":
        errors.append("consumer binding/workload drifted")
    if POLICIES != (
        "claude-code-native-isolation",
        "codex-cli-native-isolation",
        "codex-openshell-chatgpt-placeholder",
    ):
        errors.append("policy closure drifted")
    probe = sync_argv(Path("/runtime-env"), "plan")
    if "--apply" in probe or "--check" in probe:
        errors.append("plan must remain dry-run")
    if "multi-worker-scheduler" in probe:
        errors.append("module must arrive through profile composition, not argv injection")
    return errors


def selftest() -> list[str]:
    failures = validate_contract()
    apply = sync_argv(Path("/runtime-env"), "apply")
    check = sync_argv(Path("/runtime-env"), "check")
    if apply.count("--apply") != 1 or "--check" in apply:
        failures.append("apply mode is not explicit and singular")
    if check.count("--check") != 1 or "--apply" in check:
        failures.append("check mode is not read-only")
    wrong = list(apply)
    wrong[wrong.index(PROFILE)] = "bettor-arena-runtime-local"
    if wrong == apply:
        failures.append("wrong-profile control failed to disagree")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-env-root", type=Path)
    parser.add_argument("--mode", choices=("plan", "apply", "check"), default="plan")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        failures = selftest()
        if failures:
            for failure in failures:
                print(f"FAIL: {failure}")
            return 1
        print("PASS: issue #166 host rebind handoff controls")
        return 0

    contract_errors = validate_contract()
    if contract_errors:
        for error in contract_errors:
            print(f"FAIL: {error}")
        return 2
    if args.runtime_env_root is None:
        print("FAIL: --runtime-env-root is required outside --selftest")
        return 2

    receipt: dict[str, Any] = {
        "schema": "bettor-arena/issue-161-host-rebind/v1",
        "runtime_env": {"required_commit": RUNTIME_COMMIT, "profile": PROFILE},
        "consumer": {"binding": BINDING, "workload": WORKLOAD},
        "mode": args.mode,
        "worker_launch": "FORBIDDEN",
        "git_town": "NOT_EXERCISED",
        "forgejo": "NOT_EXERCISED",
        "canary": "NOT_EXERCISED",
    }
    try:
        runtime = validate_runtime_root(args.runtime_env_root)
        receipt["runtime_env"].update({"observed_commit": runtime["commit"]})
        sync = run(sync_argv(Path(runtime["cli"]), args.mode), cwd=args.runtime_env_root)
        receipt["sync"] = sync
        if sync["exit_code"] != 0:
            receipt["state"] = "SYNC_BLOCKED"
            exit_code = 3
        elif args.mode != "apply":
            receipt["state"] = "DRY_RUN_COMPLETE" if args.mode == "plan" else "BINDING_CURRENT"
            exit_code = 0
        else:
            gate = run([sys.executable, str(GATE)], cwd=ROOT)
            receipt["admission_gate"] = gate
            if gate["exit_code"] != 0:
                receipt["state"] = "APPLY_NOT_ADMITTED"
                exit_code = 4
            else:
                gate_text = subprocess.run(
                    [sys.executable, str(GATE)], cwd=ROOT, text=True,
                    capture_output=True, check=False,
                ).stdout
                receipt["state"] = (
                    "READY_FOR_LOCAL_CANARY"
                    if "READY_FOR_LOCAL_CANARY" in gate_text
                    else "APPLY_NOT_ADMITTED"
                )
                exit_code = 0 if receipt["state"] == "READY_FOR_LOCAL_CANARY" else 4
    except Exception as exc:
        receipt["state"] = "REFUSED"
        receipt["error_type"] = type(exc).__name__
        exit_code = 2

    payload = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
