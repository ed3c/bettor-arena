#!/usr/bin/env python3
"""Validate the sealed disposable controlled-language projection materializer.

Exit 0: the projection contract, one materialized body, and carrier parity pass.
Exit 2: input was readable but violated the contract.
Exit 64: usage or input was absent, unreadable, or malformed.
Exit 70: the evaluator itself could not complete.

Without --source the positive lane materializes a synthetic Git fixture, so a
green result is mechanism evidence only; the real private upstream checkout and
both physical carriers stay NOT_EXERCISED in the receipt.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from controlled_language_binding.model import BadInput, BadUsage, Red
from controlled_language_binding.projection import run_projection, run_selftest


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise BadUsage(message)


def main(argv: Sequence[str] | None = None) -> int:
    parser = Parser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--source", type=Path, default=None)
    parser.add_argument("--target", type=Path, default=None)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--json", action="store_true")

    try:
        args = parser.parse_args(argv)
        if (args.source is None) != (args.target is None):
            raise BadUsage("--source and --target must be given together")
        receipt: dict[str, Any] = run_projection(
            args.root.resolve(),
            args.source.resolve() if args.source else None,
            args.target.resolve() if args.target else None,
        )
        control_count = run_selftest(args.root.resolve()) if args.selftest else None
    except BadUsage as error:
        print(f"CTL PROJECTION USAGE: {error}", file=sys.stderr)
        return 64
    except BadInput as error:
        print(f"CTL PROJECTION INPUT: {error}", file=sys.stderr)
        return 64
    except Red as error:
        print(f"CTL PROJECTION RED: {error}", file=sys.stderr)
        return 2
    except Exception as error:  # pragma: no cover - forced in unit test
        print(
            f"CTL PROJECTION EVALUATOR: {type(error).__name__}: {error}",
            file=sys.stderr,
        )
        return 70

    receipt["selftest_controls_refused"] = (
        control_count if control_count is not None else "NOT_EXERCISED"
    )
    receipt["status"] = "PASS"
    if args.json:
        print(json.dumps(receipt, sort_keys=True))
    else:
        detail = f" and {control_count} controls" if control_count is not None else ""
        print(
            f"CTL PROJECTION GREEN: {receipt['projected']['file_count']} sealed files"
            f"{detail} passed ({receipt['source_class']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
