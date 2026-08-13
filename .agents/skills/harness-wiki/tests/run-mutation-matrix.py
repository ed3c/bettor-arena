#!/usr/bin/env python3
"""Run each planted portable-execution mutation independently.

This prevents a compound negative fixture from passing merely because one
unrelated defect was detected. The production validator remains standard-library
only; this runner imports it from the Skill package and checks the expected
failure signal for every mutation.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def load_validator(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("portable_execution_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    here = Path(__file__).resolve().parent
    skill_root = here.parent
    validator = load_validator(skill_root / "scripts" / "check_portable_execution_contract.py")
    good = validator.load_json(here / "fixtures" / "good" / "case.json")
    failures: list[str] = []
    mutation_files = sorted((here / "fixtures" / "mutations").glob("*.json"))
    if not mutation_files:
        print("mutation matrix: no cases", file=sys.stderr)
        return 64

    for mutation_file in mutation_files:
        spec = json.loads(mutation_file.read_text(encoding="utf-8"))
        candidate = validator.apply_mutations(good, mutation_file)
        errors = validator.validate_case(candidate, mutation_file.name)
        joined = "\n".join(errors)
        expected = spec.get("expected_errors", [])
        if not errors:
            failures.append(f"{mutation_file.name}: planted mutation was not killed")
            continue
        for needle in expected:
            if needle not in joined:
                failures.append(
                    f"{mutation_file.name}: expected error {needle!r} not found; got {errors}"
                )

    if failures:
        print("portable execution mutation matrix: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 2

    print(f"portable execution mutation matrix: PASS ({len(mutation_files)} controls)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
