#!/usr/bin/env python3
"""Validate the technical-equivalence actor × browser-transport contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile


class ContractError(ValueError):
    pass


def load_matrix(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot load carrier matrix: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError("carrier matrix must be a JSON object")
    return value


def validate(value: dict) -> None:
    if set(value) != {
        "schema_version",
        "actors",
        "browser_transports",
        "acceptance_cases",
        "official_sources",
    }:
        raise ContractError("carrier matrix top-level fields drifted")
    if value["schema_version"] != "technical-equivalence-carrier-capabilities@1.0.0":
        raise ContractError("unsupported carrier matrix schema")

    actors = value["actors"]
    transports = value["browser_transports"]
    cases = value["acceptance_cases"]
    if not isinstance(actors, dict) or not actors:
        raise ContractError("actors must be a non-empty object")
    if not isinstance(transports, dict) or not transports:
        raise ContractError("browser_transports must be a non-empty object")
    for actor_id, actor in actors.items():
        if set(actor) != {"kind", "native_browser", "capabilities"}:
            raise ContractError(f"actor fields drifted: {actor_id}")
        if not isinstance(actor["native_browser"], bool):
            raise ContractError(f"native_browser must be boolean: {actor_id}")
        if not actor["capabilities"] or len(actor["capabilities"]) != len(
            set(actor["capabilities"])
        ):
            raise ContractError(f"actor capabilities invalid: {actor_id}")
    for transport_id, transport in transports.items():
        if set(transport) != {"host", "engine", "capabilities", "contract_path"}:
            raise ContractError(f"browser transport fields drifted: {transport_id}")
        if not transport["capabilities"] or len(transport["capabilities"]) != len(
            set(transport["capabilities"])
        ):
            raise ContractError(
                f"browser transport capabilities invalid: {transport_id}"
            )

    if not isinstance(cases, list) or not cases:
        raise ContractError("acceptance_cases must be a non-empty array")
    seen: set[str] = set()
    for case in cases:
        if set(case) != {"id", "actor", "transport", "status", "assurance", "reason"}:
            raise ContractError("acceptance case fields drifted")
        case_id = case["id"]
        if case_id in seen:
            raise ContractError(f"duplicate acceptance case: {case_id}")
        seen.add(case_id)
        if case["actor"] not in actors:
            raise ContractError(f"unknown actor in case: {case_id}")
        if case["transport"] is not None and case["transport"] not in transports:
            raise ContractError(f"unknown transport in case: {case_id}")
        if case["status"] not in {"supported", "unsupported", "control-only"}:
            raise ContractError(f"invalid status in case: {case_id}")
        if case["assurance"] not in {"declared", "offline-exercised", "live-exercised"}:
            raise ContractError(f"invalid assurance in case: {case_id}")
        if not isinstance(case["reason"], str) or not case["reason"].strip():
            raise ContractError(f"missing reason in case: {case_id}")

    required = {
        "agy--gemini-dr-browser": "unsupported",
        "claude-code--claude-in-chrome": "supported",
        "codex-cli--chatgpt-chrome-extension": "unsupported",
        "codex-cli--playwright-cdp": "supported",
    }
    actual = {case["id"]: case["status"] for case in cases}
    if any(actual.get(case_id) != status for case_id, status in required.items()):
        raise ContractError("required fail-closed carrier decisions drifted")
    if any(case["assurance"] == "live-exercised" for case in cases):
        raise ContractError(
            "live-exercised requires an immutable live receipt contract"
        )

    sources = value["official_sources"]
    if (
        not isinstance(sources, dict)
        or not sources
        or any(
            not isinstance(url, str) or not url.startswith("https://")
            for url in sources.values()
        )
    ):
        raise ContractError("official_sources must be non-empty HTTPS URLs")


def selftest(value: dict) -> None:
    broken = json.loads(json.dumps(value))
    for case in broken["acceptance_cases"]:
        if case["id"] == "codex-cli--chatgpt-chrome-extension":
            case["status"] = "supported"
    try:
        validate(broken)
    except ContractError:
        pass
    else:
        raise ContractError("negative control accepted native Codex CLI Browser")

    with tempfile.TemporaryDirectory(prefix="carrier-contract.") as root:
        missing = Path(root) / "missing.json"
        try:
            load_matrix(missing)
        except ContractError:
            pass
        else:
            raise ContractError("negative control accepted missing matrix")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    try:
        value = load_matrix(args.matrix)
        validate(value)
        if args.selftest:
            selftest(value)
        print("PASS: carrier contract validated")
        return 0
    except ContractError as exc:
        print(f"carrier contract RED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
