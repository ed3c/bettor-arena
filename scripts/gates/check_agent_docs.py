#!/usr/bin/env python3
"""Validate bettor-arena's native Agent entry documents.

The gate is repo-contained and zero-network. It verifies that AGENTS.md and
CLAUDE.md both route to the same canonical engineering and modular-integration
documents, carry the mandatory host-specific markers, and contain no live
machine paths. It intentionally does not read a sibling skills-shared checkout.

Exit codes:
  0  checked-clean
  2  contract violation
  64 missing/unreadable contract or usage failure
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any


SCHEMA = "bettor-arena/agent-entrypoints/v1"


class ContractError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"missing contract: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"unreadable contract: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError("agent-entrypoint contract must be an object")
    return value


def validate_contract(contract: dict[str, Any], path: Path) -> None:
    if set(contract) != {
        "schema",
        "canonical_documents",
        "forbidden_patterns",
        "entrypoints",
    }:
        raise ContractError(f"{path}: top-level fields drifted")
    if contract["schema"] != SCHEMA:
        raise ContractError(f"{path}: schema must be {SCHEMA}")
    docs = contract["canonical_documents"]
    if (
        not isinstance(docs, list)
        or not docs
        or len(docs) != len(set(docs))
        or any(not isinstance(item, str) or not item for item in docs)
    ):
        raise ContractError(f"{path}: canonical_documents must be unique strings")
    patterns = contract["forbidden_patterns"]
    if (
        not isinstance(patterns, list)
        or any(not isinstance(item, str) or not item for item in patterns)
    ):
        raise ContractError(f"{path}: forbidden_patterns must be strings")
    for pattern in patterns:
        try:
            re.compile(pattern)
        except re.error as exc:
            raise ContractError(f"{path}: invalid forbidden regex {pattern!r}: {exc}") from exc

    entrypoints = contract["entrypoints"]
    if not isinstance(entrypoints, dict) or set(entrypoints) != {
        "AGENTS.md",
        "CLAUDE.md",
    }:
        raise ContractError(
            f"{path}: entrypoints must contain exactly AGENTS.md and CLAUDE.md"
        )
    for filename, spec in entrypoints.items():
        if not isinstance(spec, dict) or set(spec) != {"role", "required_markers"}:
            raise ContractError(f"{path}: malformed entrypoint spec: {filename}")
        if spec["role"] not in {"codex-cross-host", "claude-code"}:
            raise ContractError(f"{path}: invalid role for {filename}")
        markers = spec["required_markers"]
        if (
            not isinstance(markers, list)
            or not markers
            or len(markers) != len(set(markers))
            or any(not isinstance(item, str) or not item for item in markers)
        ):
            raise ContractError(f"{path}: required_markers invalid for {filename}")


def check(root: Path, contract_path: Path) -> list[str]:
    failures: list[str] = []
    contract = load_json(contract_path)
    validate_contract(contract, contract_path)

    for relative in contract["canonical_documents"]:
        path = root / relative
        if not path.is_file():
            failures.append(f"MISSING-CANONICAL {relative}")

    compiled = [re.compile(pattern) for pattern in contract["forbidden_patterns"]]
    for filename, spec in contract["entrypoints"].items():
        path = root / filename
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            failures.append(f"MISSING-ENTRYPOINT {filename}")
            continue
        except OSError as exc:
            failures.append(f"UNREADABLE-ENTRYPOINT {filename}: {exc}")
            continue
        for marker in spec["required_markers"]:
            if marker not in text:
                failures.append(f"MISSING-MARKER {filename}: {marker}")
        for pattern in compiled:
            match = pattern.search(text)
            if match:
                failures.append(
                    f"FORBIDDEN-PATH {filename}: {match.group(0)!r} "
                    f"matched /{pattern.pattern}/"
                )

    agents = root / "AGENTS.md"
    claude = root / "CLAUDE.md"
    if agents.is_file() and claude.is_file():
        agent_text = agents.read_text(encoding="utf-8")
        claude_text = claude.read_text(encoding="utf-8")
        for relative in contract["canonical_documents"]:
            if relative not in agent_text or relative not in claude_text:
                failures.append(
                    f"ASYMMETRIC-CANONICAL-POINTER {relative}: "
                    "both entrypoints must name it"
                )
    return failures


def write_fixture(root: Path) -> Path:
    (root / "docs/architecture").mkdir(parents=True)
    (root / "docs/agent-runtime-integration.md").write_text("current\n", encoding="utf-8")
    (root / "docs/architecture/modular-integration-requirements.md").write_text(
        "target\n", encoding="utf-8"
    )
    (root / "ARCHITECTURE.md").write_text("ssot\n", encoding="utf-8")
    contract = {
        "schema": SCHEMA,
        "canonical_documents": [
            "ARCHITECTURE.md",
            "docs/architecture/modular-integration-requirements.md",
            "docs/agent-runtime-integration.md",
        ],
        "forbidden_patterns": [r"/Users/", r"(?<![A-Za-z0-9_.-])~/"],
        "entrypoints": {
            "AGENTS.md": {
                "role": "codex-cross-host",
                "required_markers": ["## Mandatory read order", "## Completion contract"],
            },
            "CLAUDE.md": {
                "role": "claude-code",
                "required_markers": [
                    "## Mandatory modular-integration read order",
                    "Claude Code 不得",
                ],
            },
        },
    }
    contract_path = root / "docs/architecture/agent-entrypoints.contract.json"
    contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    pointer_block = (
        "ARCHITECTURE.md\n"
        "docs/architecture/modular-integration-requirements.md\n"
        "docs/agent-runtime-integration.md\n"
    )
    (root / "AGENTS.md").write_text(
        pointer_block + "## Mandatory read order\n## Completion contract\n",
        encoding="utf-8",
    )
    (root / "CLAUDE.md").write_text(
        pointer_block
        + "## Mandatory modular-integration read order\n"
        + "Claude Code 不得\n",
        encoding="utf-8",
    )
    return contract_path


def selftest() -> None:
    with tempfile.TemporaryDirectory(prefix="agent-docs.") as temp:
        root = Path(temp)
        contract = write_fixture(root)
        failures = check(root, contract)
        if failures:
            raise ContractError(f"positive fixture failed: {failures}")

        (root / "AGENTS.md").write_text(
            (root / "AGENTS.md")
            .read_text(encoding="utf-8")
            .replace("## Completion contract", ""),
            encoding="utf-8",
        )
        failures = check(root, contract)
        if not any(item.startswith("MISSING-MARKER AGENTS.md") for item in failures):
            raise ContractError("negative control accepted a missing mandatory marker")

        (root / "AGENTS.md").write_text(
            (root / "AGENTS.md").read_text(encoding="utf-8") + "/Users/example/repo\n",
            encoding="utf-8",
        )
        failures = check(root, contract)
        if not any(item.startswith("FORBIDDEN-PATH AGENTS.md") for item in failures):
            raise ContractError("negative control accepted a machine-specific path")


def default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check_agent_docs.py")
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("docs/architecture/agent-entrypoints.contract.json"),
    )
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.selftest:
            selftest()
            print("SELFTEST GREEN: agent entrypoints")
            return 0
        root = args.root.resolve()
        contract = args.contract if args.contract.is_absolute() else root / args.contract
        failures = check(root, contract)
        if failures:
            for failure in failures:
                print(f"AGENT-DOCS-RED {failure}", file=sys.stderr)
            return 2
        print("PASS agent entrypoints checked from repo-contained contract")
        return 0
    except ContractError as exc:
        print(f"agent-docs FATAL: {exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
