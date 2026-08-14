#!/usr/bin/env python3
"""LoopX Knowledge Compiler public port. Exits 0 ok, 2 refused, 64 unusable input.

`compile` runs the forward half of the abstraction ladder against a pinned notes
subject and stops at CANDIDATE_RECEIPT. There is no `apply`, no `merge` and no
`promote` subcommand, because none of those are this module's to reach.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kc_common import (  # noqa: E402
    BAD,
    OK,
    USAGE,
    ContractError,
    InputError,
    load_json,
)
from kc_compile import compile_subject  # noqa: E402
from kc_contract import check_contracts, run_contract_selftest  # noqa: E402
from kc_scaffold import validate_receipt  # noqa: E402
from kc_selftest import run_selftest  # noqa: E402

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

    compile_ = sub.add_parser("compile")
    compile_.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    compile_.add_argument("--output-root", type=Path)
    compile_.add_argument("--output", type=Path)

    verify = sub.add_parser("verify-receipt")
    verify.add_argument("--receipt", required=True, type=Path)
    return root


def _fixtures(root: Path) -> tuple[dict, dict, dict, dict, dict]:
    good = root / "tests/fixtures/good"
    return (
        load_json(good / "source-manifest.json"),
        load_json(good / "assertion-graph.json"),
        load_json(good / "grouping.json"),
        load_json(good / "system-spec.json"),
        load_json(good / "codeop-plan.json"),
    )


def run(args: argparse.Namespace) -> int:
    op = args.operation
    if op == "check":
        schemas, fixtures = check_contracts(args.root.resolve())
        print(
            f"loopx-knowledge-compiler PASS: {schemas} schemas, {fixtures} positive "
            "fixtures"
        )
    elif op == "selftest":
        root = args.root.resolve()
        positive, controls = run_selftest(root)
        manifest_controls = run_contract_selftest(root)
        print(
            f"loopx-knowledge-compiler selftest PASS: {positive} positive, {controls} "
            f"controls, {manifest_controls} manifest mutations"
        )
    elif op == "compile":
        manifest, graph, grouping, spec, plan = _fixtures(args.root.resolve())
        if args.output_root is not None:
            result = compile_subject(
                manifest, graph, grouping, spec, plan, args.output_root
            )
        else:
            # A disposable tree by default. A compile that wrote into the caller's
            # cwd unless told otherwise would eventually be run from a checkout.
            with tempfile.TemporaryDirectory(prefix="loopx-kc-") as tmp:
                result = compile_subject(
                    manifest, graph, grouping, spec, plan, Path(tmp) / "candidate"
                )
        text = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output is None:
            sys.stdout.write(text)
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
            print(f"WROTE {args.output}")
    elif op == "verify-receipt":
        validate_receipt(load_json(args.receipt))
        print("loopx-knowledge-compiler PASS: receipt is a candidate awaiting admit")
    return OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ContractError as exc:
        print(f"loopx-knowledge-compiler RED: {exc}", file=sys.stderr)
        return BAD
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
