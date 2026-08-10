#!/usr/bin/env python3
"""Render the pinned Codex/OpenShell provider block without reading credentials."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


POLICY_ID = "codex-openshell-chatgpt-placeholder"
EXPECTED_SETTINGS: dict[str, Any] = {
    "model_provider": "openshell_chatgpt",
    "model_providers.openshell_chatgpt.base_url": "https://chatgpt.com/backend-api/codex",
    "model_providers.openshell_chatgpt.env_http_headers.ChatGPT-Account-ID": "CODEX_AUTH_ACCOUNT_ID",
    "model_providers.openshell_chatgpt.env_key": "CODEX_AUTH_ACCESS_TOKEN",
    "model_providers.openshell_chatgpt.requires_openai_auth": False,
    "model_providers.openshell_chatgpt.supports_websockets": False,
    "model_providers.openshell_chatgpt.wire_api": "responses",
}


class Refusal(Exception):
    """The synchronized transport contract is missing or drifted."""


def validate_settings(settings: object) -> dict[str, Any]:
    if settings != EXPECTED_SETTINGS:
        raise Refusal("synchronized OpenShell model-provider settings drifted")
    assert isinstance(settings, dict)
    return settings


def load_settings(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise Refusal(f"cannot read synchronized policy: {error}") from error
    if document.get("schema") != "runtime-env/consumer-policy/v1":
        raise Refusal("synchronized policy has the wrong projection schema")
    policy = document.get("policy")
    if not isinstance(policy, dict) or policy.get("id") != POLICY_ID:
        raise Refusal(f"synchronized policy is not {POLICY_ID}")
    settings = validate_settings(policy.get("required_settings"))
    forbidden = policy.get("forbidden_environment")
    if not isinstance(forbidden, list) or "CODEX_AUTH_JSON" not in forbidden:
        raise Refusal("synchronized policy no longer forbids CODEX_AUTH_JSON")
    return settings


def render(settings: dict[str, Any]) -> str:
    return (
        "\n".join(
            (
                f'model_provider = "{settings["model_provider"]}"',
                "",
                "[model_providers.openshell_chatgpt]",
                'name = "ChatGPT via OpenShell"',
                f'base_url = "{settings["model_providers.openshell_chatgpt.base_url"]}"',
                f'env_key = "{settings["model_providers.openshell_chatgpt.env_key"]}"',
                f'wire_api = "{settings["model_providers.openshell_chatgpt.wire_api"]}"',
                "requires_openai_auth = false",
                "supports_websockets = false",
                "",
                "[model_providers.openshell_chatgpt.env_http_headers]",
                '"ChatGPT-Account-ID" = '
                f'"{settings["model_providers.openshell_chatgpt.env_http_headers.ChatGPT-Account-ID"]}"',
            )
        )
        + "\n"
    )


def selftest(settings: dict[str, Any]) -> None:
    output = render(settings)
    required = (
        'model_provider = "openshell_chatgpt"',
        'env_key = "CODEX_AUTH_ACCESS_TOKEN"',
        '"ChatGPT-Account-ID" = "CODEX_AUTH_ACCOUNT_ID"',
        "requires_openai_auth = false",
        "supports_websockets = false",
    )
    if not all(line in output for line in required):
        raise Refusal("renderer omitted a load-bearing placeholder setting")
    planted = dict(settings)
    planted["model_providers.openshell_chatgpt.env_key"] = "REAL_TOKEN"
    try:
        validate_settings(planted)
    except Refusal:
        pass
    else:
        raise Refusal("planted transport drift was not detected")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--selftest", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        settings = load_settings(arguments.policy)
        if arguments.selftest:
            selftest(settings)
            print("SELFTEST GREEN")
        else:
            print(render(settings), end="")
    except Refusal as error:
        print(f"FATAL: {error}", file=sys.stderr)
        return 64
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
