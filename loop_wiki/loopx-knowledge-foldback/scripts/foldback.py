#!/usr/bin/env python3
"""LoopX Knowledge Fold-back public port. Exits 0 ok, 2 refused, 64 unusable input.

`fold-back` compiles a candidate bundle and stops. `admit` is a separate
subcommand that requires an explicit decision file, because a single call that
compiled and admitted in one pass would make the Human Admit boundary depend on
which arguments happened to be supplied.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fb_bundle import validate_receipt  # noqa: E402
from fb_common import (  # noqa: E402
    BAD,
    OK,
    USAGE,
    ContractError,
    InputError,
    load_json,
)
from fb_contract import check_contracts, run_contract_selftest  # noqa: E402
from fb_history import rollback as rollback_history  # noqa: E402
from fb_pipeline import admit_bundle, fold_back  # noqa: E402
from fb_selftest import load_bundle_inputs, run_selftest  # noqa: E402

DEFAULT_ROOT = Path(__file__).resolve().parents[1]


class UsageParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"FATAL: {message}", file=sys.stderr)
        raise SystemExit(USAGE)


def build_parser() -> argparse.ArgumentParser:
    root = UsageParser(description=__doc__)
    sub = root.add_subparsers(dest="operation", required=True, parser_class=UsageParser)

    check = sub.add_parser("check")
    check.add_argument("--root", type=Path, default=DEFAULT_ROOT)

    selftest = sub.add_parser("selftest")
    selftest.add_argument("--root", type=Path, default=DEFAULT_ROOT)

    fold = sub.add_parser("fold-back")
    fold.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    fold.add_argument("--output", type=Path)

    admit = sub.add_parser("admit")
    admit.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    admit.add_argument("--decisions", type=Path)
    admit.add_argument("--output", type=Path)

    verify = sub.add_parser("verify-receipt")
    verify.add_argument("--receipt", required=True, type=Path)

    roll = sub.add_parser("rollback")
    roll.add_argument("--history", required=True, type=Path)
    roll.add_argument("--revision", required=True)
    roll.add_argument("--actor", required=True)
    roll.add_argument("--at", required=True)
    roll.add_argument("--output", type=Path)
    return root


def _emit(value: object, output: Path | None) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"WROTE {output}")


def run(args: argparse.Namespace) -> int:
    op = args.operation
    if op == "check":
        schemas, fixtures = check_contracts(args.root.resolve())
        print(
            f"loopx-knowledge-foldback PASS: {schemas} schemas, {fixtures} positive "
            "fixtures"
        )
    elif op == "selftest":
        root = args.root.resolve()
        positive, controls = run_selftest(root)
        manifest_controls = run_contract_selftest(root)
        print(
            f"loopx-knowledge-foldback selftest PASS: {positive} positive, {controls} "
            f"controls, {manifest_controls} manifest mutations"
        )
    elif op == "fold-back":
        inputs = load_bundle_inputs(args.root.resolve())
        _emit(
            fold_back(
                inputs["change-delta"],
                inputs["cards"],
                inputs["patches"],
                inputs["similarity"],
                inputs["revision-history"],
            ),
            args.output,
        )
    elif op == "admit":
        inputs = load_bundle_inputs(args.root.resolve())
        decisions = (
            load_json(args.decisions)
            if args.decisions is not None
            else inputs["decisions"]
        )
        folded = fold_back(
            inputs["change-delta"],
            inputs["cards"],
            inputs["patches"],
            inputs["similarity"],
            inputs["revision-history"],
        )
        _emit(
            admit_bundle(
                folded["bundle"], inputs["revision-history"], decisions, inputs["cards"]
            ),
            args.output,
        )
    elif op == "verify-receipt":
        validate_receipt(load_json(args.receipt))
        print("loopx-knowledge-foldback PASS: receipt records a human decision")
    elif op == "rollback":
        _emit(
            rollback_history(
                load_json(args.history), args.revision, args.actor, args.at
            ),
            args.output,
        )
    return OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ContractError as exc:
        print(f"loopx-knowledge-foldback RED: {exc}", file=sys.stderr)
        return BAD
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
