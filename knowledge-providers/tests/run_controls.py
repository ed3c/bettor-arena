#!/usr/bin/env python3
"""Independent positive, hollow, and mutation controls for provider contracts."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def run(command: list[str], expected: int, label: str) -> None:
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != expected:
        raise AssertionError(
            f"{label}: expected exit {expected}, got {result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def select(value: object, path: str) -> tuple[object, str | int]:
    parts = path.split(".")
    current = value
    for raw in parts[:-1]:
        key: str | int = int(raw) if raw.isdigit() else raw
        current = current[key]  # type: ignore[index]
    tail = parts[-1]
    return current, int(tail) if tail.isdigit() else tail


def mutate(value: object, mutations: list[dict[str, object]]) -> object:
    result = copy.deepcopy(value)
    for mutation in mutations:
        parent, key = select(result, str(mutation["path"]))
        operation = mutation["op"]
        if operation == "set":
            parent[key] = mutation["value"]  # type: ignore[index]
        elif operation == "remove":
            if isinstance(parent, list):
                parent.pop(int(key))
            else:
                parent.pop(str(key))  # type: ignore[union-attr]
        else:
            raise AssertionError(f"unknown mutation operation: {operation}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    validator = root / "scripts" / "check_knowledge_providers.py"
    fixtures = root / "tests" / "fixtures"

    run(
        [
            sys.executable,
            str(validator),
            "pair",
            "--root",
            str(root),
            "--request",
            str(fixtures / "good" / "request.json"),
            "--receipt",
            str(fixtures / "good" / "receipt.json"),
        ],
        0,
        "good request/receipt pair",
    )
    run(
        [
            sys.executable,
            str(validator),
            "memory",
            "--root",
            str(root),
            "--proposal",
            str(fixtures / "good" / "memory-proposal.json"),
        ],
        0,
        "good memory proposal",
    )
    run(
        [
            sys.executable,
            str(validator),
            "pair",
            "--root",
            str(root),
            "--request",
            str(fixtures / "missing-request.json"),
            "--receipt",
            str(fixtures / "good" / "receipt.json"),
        ],
        64,
        "unreadable input",
    )

    cases = json.loads((fixtures / "cases.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="knowledge-provider-controls-") as temp:
        temp_root = Path(temp)
        for case in cases:
            mode = case["mode"]
            command = [sys.executable, str(validator), mode, "--root", str(root)]
            if mode == "pair":
                source = fixtures / case.get("receipt", "good/receipt.json")
                value = json.loads(source.read_text(encoding="utf-8"))
                target = temp_root / f"{case['id']}.json"
                target.write_text(
                    json.dumps(mutate(value, case.get("mutations", [])), indent=2)
                    + "\n",
                    encoding="utf-8",
                )
                command.extend(
                    [
                        "--request",
                        str(fixtures / "good" / "request.json"),
                        "--receipt",
                        str(target),
                    ]
                )
            elif mode == "memory":
                source = fixtures / "good" / "memory-proposal.json"
                value = json.loads(source.read_text(encoding="utf-8"))
                target = temp_root / f"{case['id']}.json"
                target.write_text(
                    json.dumps(mutate(value, case.get("mutations", [])), indent=2)
                    + "\n",
                    encoding="utf-8",
                )
                command.extend(["--proposal", str(target)])
            elif mode == "check":
                command.extend(["--registry", str(fixtures / case["registry"])])
            run(command, 2, case["id"])

    print(
        f"PASS knowledge-provider controls: 2 positive + {len(cases)} contract negatives + 1 unreadable input"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
