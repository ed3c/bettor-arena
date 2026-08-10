#!/usr/bin/env python3
"""Run fixed carrier status commands and emit only bounded classifications."""

from __future__ import annotations

import json
import os
import subprocess
import sys


def forbidden_present(names: tuple[str, ...]) -> list[str]:
    return sorted(name for name in names if os.environ.get(name))


def check_claude() -> int:
    forbidden = forbidden_present(
        (
            "ANTHROPIC_API_KEY",
            "CLAUDE_CONFIG_DIR",
            "CODEX_ACCESS_TOKEN",
            "CODEX_API_KEY",
            "CODEX_HOME",
            "OPENAI_API_KEY",
        )
    )
    if forbidden:
        print(
            "carrier status RED: Claude default-login environment is contaminated",
            file=sys.stderr,
        )
        return 2
    result = subprocess.run(
        ["claude", "auth", "status", "--json"],
        check=False,
        capture_output=True,
        text=True,
    )
    try:
        status = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("carrier status RED: Claude status was not JSON", file=sys.stderr)
        return 2
    if result.returncode != 0 or status.get("loggedIn") is not True:
        print(
            "carrier status RED: Claude default login is unavailable", file=sys.stderr
        )
        return 2
    print("PASS: claude-code default-login authenticated; identity fields redacted")
    return 0


def check_codex() -> int:
    forbidden = forbidden_present(
        ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CONFIG_DIR")
    )
    if forbidden:
        print("carrier status RED: Codex environment is contaminated", file=sys.stderr)
        return 2
    if not os.environ.get("CODEX_HOME"):
        print("carrier status RED: CODEX_HOME is absent", file=sys.stderr)
        return 2
    result = subprocess.run(
        ["codex", "login", "status"], check=False, capture_output=True, text=True
    )
    if result.returncode != 0:
        print("carrier status RED: Codex login is unavailable", file=sys.stderr)
        return 2
    print("PASS: codex-cli authenticated; identity fields redacted")
    return 0


def check_agy() -> int:
    model = os.environ.get("AGY_MODEL") or "gemini-3.6-flash-high"
    effort = os.environ.get("AGY_EFFORT") or "high"
    if model != "gemini-3.6-flash-high" or effort != "high":
        print(
            "carrier status RED: agy model or effort contract drifted", file=sys.stderr
        )
        return 2
    result = subprocess.run(
        ["agy", "models"], check=False, capture_output=True, text=True
    )
    inventory = result.stdout + result.stderr
    if result.returncode != 0 or model not in inventory:
        print("carrier status RED: exact agy model is unavailable", file=sys.stderr)
        return 2
    print("PASS: agy exact model present; inventory redacted")
    return 0


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"claude", "codex", "agy"}:
        print("usage: check-carrier-status.py <claude|codex|agy>", file=sys.stderr)
        return 64
    return {"claude": check_claude, "codex": check_codex, "agy": check_agy}[
        sys.argv[1]
    ]()


if __name__ == "__main__":
    raise SystemExit(main())
