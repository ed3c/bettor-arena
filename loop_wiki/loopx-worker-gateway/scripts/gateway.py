#!/usr/bin/env python3
"""Run or inspect a LoopX Worker Gateway v1 request."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from gateway_common import BAD, OK, USAGE, ContractError, InputError, load_json
from gateway_contract import validate_adapter, validate_request
from gateway_runtime import run_fixture_or_implemented

class UsageParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"FATAL: {message}", file=sys.stderr)
        raise SystemExit(USAGE)

def build_parser() -> argparse.ArgumentParser:
    parser = UsageParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True, parser_class=UsageParser)
    run = sub.add_parser("run")
    run.add_argument("--request", required=True, type=Path)
    run.add_argument("--adapter", required=True, type=Path)
    run.add_argument("--repo", required=True, type=Path)
    run.add_argument("--output", required=True, type=Path)
    run.add_argument("--receipt-id", required=True)
    run.add_argument("--allow-fixture-adapter", action="store_true")
    return parser

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    module_root = Path(__file__).resolve().parents[1]
    try:
        descriptor = validate_adapter(
            load_json(args.adapter),
            allow_fixture=args.allow_fixture_adapter,
        )
        request = validate_request(
            load_json(args.request),
            {descriptor["adapter_id"]: descriptor},
        )
        _, code = run_fixture_or_implemented(
            request,
            descriptor,
            args.repo.resolve(),
            module_root,
            args.output.resolve(),
            args.receipt_id,
            args.allow_fixture_adapter,
        )
        return code
    except ContractError as exc:
        print(f"loopx-worker-gateway RED: {exc}", file=sys.stderr)
        return BAD
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE

if __name__ == "__main__":
    raise SystemExit(main())
