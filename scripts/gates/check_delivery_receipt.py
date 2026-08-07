#!/usr/bin/env python3
"""T0 gate: every materialized repo on a delivery line must carry its receipt.

Zero network by contract. Reads the delivery registry (line ↔ repo ↔ milestone ↔
issues SSOT) and, for each line whose materialized_path exists on disk, requires
<path>/delivery.json with every required_receipt_fields key non-empty.

Three outcomes that must never be confused, which is the whole point:
  * materialized + complete receipt      -> pass, named
  * materialized + missing/holed receipt -> FAIL, named per line and per field
  * not materialized yet (null or absent path) -> SKIP, named

"Delivered" is therefore a fact on disk, not a memory of having done it. The gate
never asks the forge whether the issues are real — that is an explicit audit
(`/delivery`), not a commit-time dependency, the same split resolve-refs uses.

Usage:
  python3 scripts/gates/check_delivery_receipt.py             # gate over all lines
  python3 scripts/gates/check_delivery_receipt.py --line ID   # print one line's context
  python3 scripts/gates/check_delivery_receipt.py --selftest  # good/hollow controls

Exit codes: 0 pass · 2 receipt violation · 64 usage or unknown line.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from _gate_common import repo_root  # noqa: E402

REGISTRY_REL = ".skill-bindings/forgejo-delivery-loop/registry.json"


def load_registry(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("lines"), list) or not data["lines"]:
        print(f"FATAL registry-malformed: {path} has no lines[]", file=sys.stderr)
        raise SystemExit(64)
    return data


def check_line(line: dict, required: list[str], root: Path) -> list[str]:
    failures: list[str] = []
    line_id = line.get("line", "?")
    materialized = line.get("materialized_path")
    if not materialized:
        print(f"  SKIP  {line_id}: nothing materialized yet (registry says null)")
        return failures
    target = root / materialized
    if not target.is_dir():
        print(f"  SKIP  {line_id}: materialized_path not on disk ({materialized})")
        return failures
    receipt_path = target / "delivery.json"
    if not receipt_path.is_file():
        failures.append(
            f"FAIL receipt-missing: {line_id}: {materialized}/delivery.json "
            f"— materialized a repo but left no delivery receipt"
        )
        return failures
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        failures.append(f"FAIL receipt-unreadable: {line_id}: {err}")
        return failures
    for field in required:
        if receipt.get(field) in (None, "", []):
            failures.append(
                f"FAIL receipt-field-missing: {line_id}: delivery.json lacks '{field}'"
            )
    if not failures:
        print(
            f"  pass  {line_id}: receipt ok → pr={receipt.get('pr')} "
            f"issues={len(receipt.get('issues', []))}"
        )
    return failures


def run_gate(root: Path, registry_path: Path) -> int:
    data = load_registry(registry_path)
    required = data.get("required_receipt_fields", [])
    failures: list[str] = []
    for line in data["lines"]:
        failures.extend(check_line(line, required, root))
    if failures:
        for line in failures:
            print(line, file=sys.stderr)
        return 2
    print("PASS: delivery receipts hold for every materialized line")
    return 0


def show_line(line_id: str, root: Path) -> int:
    data = load_registry(root / REGISTRY_REL)
    for line in data["lines"]:
        if line.get("line") == line_id:
            print(json.dumps(line, ensure_ascii=False, indent=2))
            return 0
    print(
        f"FATAL unknown-line: {line_id} is not in the registry — register it before starting work",
        file=sys.stderr,
    )
    return 64


# ---------------------------------------------------------------- selftest


def _fixture(root: Path, receipt: dict | None, materialized: bool = True) -> Path:
    target = root / "materialized/demo"
    if materialized:
        target.mkdir(parents=True, exist_ok=True)
        if receipt is not None:
            (target / "delivery.json").write_text(json.dumps(receipt), encoding="utf-8")
    registry = root / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "required_receipt_fields": [
                    "line",
                    "repo",
                    "issues",
                    "pr",
                    "milestone_url",
                    "synced_at_commit",
                ],
                "lines": [
                    {
                        "line": "demo",
                        "materialized_path": "materialized/demo"
                        if materialized
                        else None,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return registry


def _selftest() -> int:
    complete = {
        "line": "demo",
        "repo": "neon/x",
        "issues": ["u"],
        "pr": "u",
        "milestone_url": "u",
        "synced_at_commit": "abc1234",
    }
    cases = []
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        cases.append(
            ("materialized-without-receipt", run_gate(root, _fixture(root, None)), 2)
        )
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        holed = {k: v for k, v in complete.items() if k != "synced_at_commit"}
        cases.append(
            ("receipt-missing-a-field", run_gate(root, _fixture(root, holed)), 2)
        )
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        cases.append(("complete-receipt", run_gate(root, _fixture(root, complete)), 0))
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        cases.append(
            (
                "not-materialized-is-skip-not-fail",
                run_gate(root, _fixture(root, None, materialized=False)),
                0,
            )
        )

    red = [
        f"{name}: got {got}, want {want}" for name, got, want in cases if got != want
    ]
    for line in red:
        print(f"SELFTEST case failed — {line}", file=sys.stderr)
    print("SELFTEST " + ("GREEN" if not red else "RED"))
    return 0 if not red else 1


def main(argv: list[str]) -> int:
    root = repo_root(Path(__file__).resolve().parent)
    if argv == ["--selftest"]:
        return _selftest()
    if root is None:
        print("check_delivery_receipt: not inside a git work tree", file=sys.stderr)
        return 64
    if len(argv) == 2 and argv[0] == "--line":
        return show_line(argv[1], root)
    if argv:
        print(__doc__.strip(), file=sys.stderr)
        return 64
    print(f"check_delivery_receipt: scanning repo root {root}")
    return run_gate(root, root / REGISTRY_REL)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
