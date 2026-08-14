#!/usr/bin/env python3
"""LoopX Runtime Fabric public port. Exits 0 ok, 2 refused, 64 unusable, 70 provider.

The fourth exit is the one this module needs and the others did not: a provider
that will not start has told you nothing about the task. Folding that into 2
would record a verdict about code that never ran.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from fabric_common import (
    BAD,
    OK,
    USAGE,
    ContractError,
    InputError,
    ProviderUnavailable,
    load_json,
)
from fabric_contract import check_contracts, run_contract_selftest
from fabric_lease import admit_lease, gc_candidates, validate_lease
from fabric_local import emit_receipt, execute
from fabric_parity import build_matrix, validate_matrix
from fabric_request import validate_request
from fabric_selftest import run_selftest

PROVIDER = 70


class UsageParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"FATAL: {message}", file=sys.stderr)
        raise SystemExit(USAGE)


DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    root = UsageParser(description=__doc__)
    sub = root.add_subparsers(dest="operation", required=True, parser_class=UsageParser)

    check = sub.add_parser("check")
    check.add_argument("--root", type=Path, default=DEFAULT_ROOT)

    selftest = sub.add_parser("selftest")
    selftest.add_argument("--root", type=Path, default=DEFAULT_ROOT)

    vreq = sub.add_parser("validate-request")
    vreq.add_argument("--request", required=True, type=Path)

    vlease = sub.add_parser("validate-lease")
    vlease.add_argument("--lease", required=True, type=Path)

    admit = sub.add_parser("admit-lease")
    admit.add_argument("--lease", required=True, type=Path)
    admit.add_argument("--now", required=True)
    admit.add_argument("--revision", required=True, type=int)
    admit.add_argument("--output", type=Path)

    run_ = sub.add_parser("run")
    run_.add_argument("--request", required=True, type=Path)
    run_.add_argument("--lease", required=True, type=Path)
    run_.add_argument("--source", required=True, type=Path)
    run_.add_argument("--output", type=Path)

    gc = sub.add_parser("gc")
    gc.add_argument("--leases", required=True, type=Path)
    gc.add_argument("--now", required=True)
    gc.add_argument("--output", type=Path)

    parity = sub.add_parser("parity")
    parity.add_argument("--reference", required=True)
    parity.add_argument("--receipts", required=True, type=Path)
    parity.add_argument("--declared", required=True, type=Path)
    parity.add_argument("--output", type=Path)
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
            f"loopx-runtime-fabric PASS: {schemas} schemas, {fixtures} positive fixtures"
        )
    elif op == "selftest":
        root = args.root.resolve()
        positive, controls = run_selftest(root)
        manifest_controls = run_contract_selftest(root)
        print(
            f"loopx-runtime-fabric selftest PASS: {positive} positive, {controls} "
            f"controls, {manifest_controls} manifest mutations"
        )
    elif op == "validate-request":
        validate_request(load_json(args.request))
        print("loopx-runtime-fabric PASS: request claims only what its adapter attests")
    elif op == "validate-lease":
        validate_lease(load_json(args.lease))
        print("loopx-runtime-fabric PASS: lease has one owner and a real expiry")
    elif op == "admit-lease":
        _emit(admit_lease(load_json(args.lease), args.now, args.revision), args.output)
    elif op == "run":
        request = validate_request(load_json(args.request))
        lease = validate_lease(load_json(args.lease))
        observation = execute(args.source.resolve(), request)
        _emit(emit_receipt(request, lease, observation), args.output)
    elif op == "gc":
        _emit(gc_candidates(load_json(args.leases), args.now), args.output)
    elif op == "parity":
        matrix = build_matrix(
            args.reference, load_json(args.receipts), load_json(args.declared)
        )
        validate_matrix(matrix)
        _emit(matrix, args.output)
    return OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ContractError as exc:
        print(f"loopx-runtime-fabric RED: {exc}", file=sys.stderr)
        return BAD
    except ProviderUnavailable as exc:
        # Not 2. Nothing about the task was observed, so nothing about the task
        # may be concluded -- including that it failed.
        print(f"loopx-runtime-fabric PROVIDER_UNAVAILABLE: {exc}", file=sys.stderr)
        return PROVIDER
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
