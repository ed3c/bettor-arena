#!/usr/bin/env python3
# ruff: noqa: F401,F403,F405  # this module family composes through star imports; the names ruff reads as unused are deliberate re-exports the downstream modules import through.
"""Operate the LoopX append-only ledger with deterministic 0/2/64 exits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from ledger_common import BAD, OK, USAGE, BusyError, ContractError, InputError
from ledger_cli import append_event, initialize, recover_store, replay_to, verify_store
from ledger_selftest import run_selftest


class UsageParser(argparse.ArgumentParser):
    """Map CLI contract/usage errors to the repository-standard exit 64."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"FATAL: {message}", file=sys.stderr)
        raise SystemExit(USAGE)


def parser() -> argparse.ArgumentParser:
    root = UsageParser(description=__doc__)
    sub = root.add_subparsers(dest="operation", required=True, parser_class=UsageParser)
    init = sub.add_parser("init")
    init.add_argument("--contract", required=True, type=Path)
    init.add_argument("--store", required=True, type=Path)
    init.add_argument("--created-at", required=True)
    init.add_argument("--receipt", required=True, type=Path)
    init.add_argument("--operation-id", required=True)
    append = sub.add_parser("append")
    append.add_argument("--store", required=True, type=Path)
    append.add_argument("--request", required=True, type=Path)
    append.add_argument("--receipt", required=True, type=Path)
    append.add_argument("--operation-id", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--store", required=True, type=Path)
    verify.add_argument("--receipt", required=True, type=Path)
    verify.add_argument("--operation-id", required=True)
    replay = sub.add_parser("replay")
    replay.add_argument("--store", required=True, type=Path)
    replay.add_argument("--snapshot-out", required=True, type=Path)
    replay.add_argument("--receipt", required=True, type=Path)
    replay.add_argument("--operation-id", required=True)
    recover = sub.add_parser("recover")
    recover.add_argument("--store", required=True, type=Path)
    recover.add_argument("--apply", action="store_true")
    recover.add_argument("--receipt", required=True, type=Path)
    recover.add_argument("--operation-id", required=True)
    test = sub.add_parser("selftest")
    test.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.operation == "init":
            initialize(
                args.contract.resolve(),
                args.store.resolve(),
                args.created_at,
                args.receipt.resolve(),
                args.operation_id,
            )
        elif args.operation == "append":
            append_event(
                args.store.resolve(),
                args.request.resolve(),
                args.receipt.resolve(),
                args.operation_id,
            )
        elif args.operation == "verify":
            verify_store(
                args.store.resolve(), args.receipt.resolve(), args.operation_id
            )
        elif args.operation == "replay":
            replay_to(
                args.store.resolve(),
                args.snapshot_out.resolve(),
                args.receipt.resolve(),
                args.operation_id,
            )
        elif args.operation == "recover":
            _, code = recover_store(
                args.store.resolve(),
                args.apply,
                args.receipt.resolve(),
                args.operation_id,
            )
            return code
        elif args.operation == "selftest":
            run_selftest(args.root.resolve())
        else:
            raise InputError(f"unknown operation: {args.operation}")
        return OK
    except BusyError as exc:
        print(f"loopx-ledger RED: {exc}", file=sys.stderr)
        return BAD
    except ContractError as exc:
        print(f"loopx-ledger RED: {exc}", file=sys.stderr)
        return BAD
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
