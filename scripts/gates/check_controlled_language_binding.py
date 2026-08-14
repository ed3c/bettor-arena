#!/usr/bin/env python3
"""Validate the immutable Bettor controlled-language consumer binding.

Exit 0: the exact offline binding and declared controls pass.
Exit 2: input was readable but violated the contract.
Exit 64: usage or input was absent, unreadable, or malformed.
Exit 70: the evaluator itself could not complete.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from controlled_language_binding.constants import CANDIDATE, ROLLBACK
from controlled_language_binding.model import BadInput, BadUsage, Red, load_bundle
from controlled_language_binding.mutations import run_selftest
from controlled_language_binding.validate import validate_bundle


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise BadUsage(message)


def receipt(selftest_count: int | None) -> dict[str, Any]:
    return {
        "candidate_commit": CANDIDATE["commit"],
        "candidate_skill_tree": CANDIDATE["skill_tree"],
        "consumer": "ed3c/bettor-arena",
        "evidence_boundary": {
            "claude_physical_carrier": "NOT_EXERCISED",
            "codex_physical_carrier": "NOT_EXERCISED",
            "official_compliance": "NOT_CLAIMED",
            "projection": "NOT_IMPLEMENTED",
            "production_termbase": "ABSENT",
        },
        "rollback_commit": ROLLBACK["commit"],
        "schema_version": "controlled-language-binding-verdict/v1",
        "selftest_mutations_refused": selftest_count
        if selftest_count is not None
        else "NOT_EXERCISED",
        "status": "PASS",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = Parser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--json", action="store_true")

    try:
        args = parser.parse_args(argv)
        root = args.root.resolve()
        documents = load_bundle(root)
        validate_bundle(documents, root)
        mutation_count = run_selftest(root) if args.selftest else None
    except BadUsage as error:
        print(f"CTL BINDING USAGE: {error}", file=sys.stderr)
        return 64
    except BadInput as error:
        print(f"CTL BINDING INPUT: {error}", file=sys.stderr)
        return 64
    except Red as error:
        print(f"CTL BINDING RED: {error}", file=sys.stderr)
        return 2
    except Exception as error:  # pragma: no cover - forced in unit test
        print(
            f"CTL BINDING EVALUATOR: {type(error).__name__}: {error}",
            file=sys.stderr,
        )
        return 70

    result = receipt(mutation_count)
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        detail = (
            f" and {mutation_count} mutations"
            if mutation_count is not None
            else ""
        )
        print(f"CTL BINDING GREEN: exact consumer binding{detail} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
