#!/usr/bin/env python3
"""LoopX Skill Evolution public port. Exits 0 ok, 2 refused, 64 unusable input.

`evaluate` runs the experiment and reaches CANDIDATE, REJECTED or INCONCLUSIVE.
`receipt` turns a decision into a candidate release proposal. Neither writes a
Skill body, and there is no subcommand that does -- admitting a release is
`skills-shared`'s, and rebinding Bettor to it is a separate leaf.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from se_common import (  # noqa: E402
    BAD,
    OK,
    USAGE,
    ContractError,
    InputError,
    load_json,
)
from se_contract import check_contracts, run_contract_selftest  # noqa: E402
from se_pipeline import evaluate  # noqa: E402
from se_release import build_receipt, validate_receipt  # noqa: E402
from se_selftest import load_inputs, run_selftest  # noqa: E402

DEFAULT_ROOT = Path(__file__).resolve().parents[1]


class UsageParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"FATAL: {message}", file=sys.stderr)
        raise SystemExit(USAGE)


def build_parser() -> argparse.ArgumentParser:
    root = UsageParser(description=__doc__)
    sub = root.add_subparsers(dest="operation", required=True, parser_class=UsageParser)

    for name in ("check", "selftest", "evaluate"):
        parser = sub.add_parser(name)
        parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
        if name == "evaluate":
            parser.add_argument("--output", type=Path)

    receipt = sub.add_parser("receipt")
    receipt.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    receipt.add_argument(
        "--evidence-kind", required=True, choices=["FIXTURE_ONLY", "LIVE_EXERCISED"]
    )
    receipt.add_argument("--at", required=True)
    receipt.add_argument("--output", type=Path)

    verify = sub.add_parser("verify-receipt")
    verify.add_argument("--receipt", required=True, type=Path)
    return root


def _emit(value: object, output: Path | None) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"WROTE {output}")


def _evaluate(root: Path) -> tuple[dict, dict]:
    inputs = load_inputs(root)
    return inputs, evaluate(
        inputs["experiment"],
        inputs["dev-cases"],
        inputs["mutation-cases"],
        inputs["holdout-cases"],
        inputs["dev-runs"],
        inputs["mutation-runs"],
        inputs["holdout-runs"],
        inputs["cross-host"],
    )


def run(args: argparse.Namespace) -> int:
    op = args.operation
    if op == "check":
        schemas, fixtures = check_contracts(args.root.resolve())
        print(
            f"loopx-skill-evolution PASS: {schemas} schemas, {fixtures} positive fixtures"
        )
    elif op == "selftest":
        root = args.root.resolve()
        positive, controls = run_selftest(root)
        manifest_controls = run_contract_selftest(root)
        print(
            f"loopx-skill-evolution selftest PASS: {positive} positive, {controls} "
            f"controls, {manifest_controls} manifest mutations"
        )
    elif op == "evaluate":
        _, result = _evaluate(args.root.resolve())
        _emit(result, args.output)
    elif op == "receipt":
        root = args.root.resolve()
        inputs, result = _evaluate(root)
        _emit(
            build_receipt(
                inputs["experiment"],
                result["decision"],
                args.evidence_kind,
                inputs["host-projections"],
                args.at,
            ),
            args.output,
        )
    elif op == "verify-receipt":
        validate_receipt(load_json(args.receipt))
        print(
            "loopx-skill-evolution PASS: receipt proposes a release and mutates nothing"
        )
    return OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ContractError as exc:
        print(f"loopx-skill-evolution RED: {exc}", file=sys.stderr)
        return BAD
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
