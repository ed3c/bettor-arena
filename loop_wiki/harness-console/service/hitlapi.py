#!/usr/bin/env python3
"""Harness Console HITL port. Exits 0 ok, 2 refused, 64 unusable input.

    check      manifest, schemas and vocabulary
    selftest   positive properties, planted controls, manifest mutations
    project    reduce canonical events into the read-only projection
    views      build the eight bounded views from a projection
    draft      draft a decision request against a projection
    sign       attach a signature (the key is read from an env var, never a flag)
    submit     hand a signed request to LoopX; it accepts or rejects

There is no subcommand that mutates task state, writes a ledger event, marks a
gate PASS, merges, promotes or rolls back. The console asks; LoopX answers.

The signer key is read from HITL_SIGNER_KEY. Not a flag, because a flag lands in
a shell history, a process list and a CI log, and all three outlive the request.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "contracts"))
sys.path.insert(0, str(HERE.parents[0] / "app"))

from hc_contract import check_contracts, run_contract_selftest  # noqa: E402
from hc_vocab import BAD, OK, USAGE, ContractError, InputError, load_json  # noqa: E402
from hc_views import render  # noqa: E402
from hitl_reducer import reduce  # noqa: E402
from hitl_request import accept, draft, sign_request  # noqa: E402
from hitl_selftest import run_selftest  # noqa: E402

DEFAULT_ROOT = HERE.parents[2]
KEY_ENV = "HITL_SIGNER_KEY"


class UsageParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"FATAL: {message}", file=sys.stderr)
        raise SystemExit(USAGE)


def build_parser() -> argparse.ArgumentParser:
    root = UsageParser(description=__doc__)
    sub = root.add_subparsers(dest="operation", required=True, parser_class=UsageParser)
    for name in ("check", "selftest", "project", "views", "draft", "sign", "submit"):
        parser = sub.add_parser(name)
        parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
        parser.add_argument("--output", type=Path)
        if name == "project":
            parser.add_argument("--events", type=Path, required=True)
            parser.add_argument("--head", required=True)
        if name in ("views", "draft", "submit"):
            parser.add_argument("--projection", type=Path, required=True)
        if name == "draft":
            parser.add_argument("--request", type=Path, required=True)
        if name in ("sign", "submit"):
            parser.add_argument("--in", dest="source", type=Path, required=True)
        if name == "sign":
            parser.add_argument("--key-id", required=True)
        if name == "submit":
            parser.add_argument("--seen", type=Path)
    return root


def _emit(value: object, output: Path | None) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"WROTE {output}")


def signer_key() -> bytes:
    raw = os.environ.get(KEY_ENV)
    if not raw:
        # Absent, not refused. A missing key is an unconfigured operator, not a
        # decision that disagreed, and exit 2 would say the request was wrong.
        raise InputError(
            f"{KEY_ENV} is not set. The signer key is Human-held; it is never stored in "
            "this repository, passed as a flag, or written into a receipt"
        )
    return raw.encode("utf-8")


def run(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    op = args.operation

    if op == "check":
        schemas, files = check_contracts(root)
        print(f"harness-console PASS: {schemas} schemas, {files} contract files")
    elif op == "selftest":
        positive, controls = run_selftest(root)
        mutations = run_contract_selftest(root)
        print(
            f"harness-console selftest PASS: {positive} positive, {controls} controls, "
            f"{mutations} manifest mutations"
        )
    elif op == "project":
        _emit(reduce(load_json(args.events), args.head), args.output)
    elif op == "views":
        _emit(render(load_json(args.projection)), args.output)
    elif op == "draft":
        _emit(draft(load_json(args.request), load_json(args.projection)), args.output)
    elif op == "sign":
        _emit(
            sign_request(load_json(args.source), signer_key(), args.key_id), args.output
        )
    elif op == "submit":
        seen = set(load_json(args.seen)) if args.seen and args.seen.exists() else set()
        outcome = accept(
            load_json(args.source), load_json(args.projection), signer_key(), seen
        )
        _emit(outcome, args.output)
        print(f"harness-console {outcome['outcome']}", file=sys.stderr)
        if outcome["outcome"] != "ACCEPTED":
            return BAD
    return OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ContractError as exc:
        print(f"harness-console RED: {exc}", file=sys.stderr)
        return BAD
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
