#!/usr/bin/env python3
"""Public CLI for LoopX Worker Gateway v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gateway_common import (
    GatewayError,
    GatewayFatal,
    host_by_id,
    load_json,
    validate_registry,
    validate_request,
    validate_request_against_host,
    write_json_exclusive,
)
from gateway_engine import execute, probe


class StrictParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise GatewayFatal(message)


def module_root() -> Path:
    return Path(__file__).resolve().parents[3]


def command_validate(args: argparse.Namespace) -> int:
    registry = validate_registry(load_json(args.registry))
    request = validate_request(load_json(args.request))
    descriptor = host_by_id(registry, request["host_id"])
    validate_request_against_host(request, descriptor)
    print(f"loopx-worker-gateway VALID request={request['request_id']} host={request['host_id']}")
    return 0


def command_probe(args: argparse.Namespace) -> int:
    report = probe(load_json(args.registry))
    write_json_exclusive(args.output / "probe-report.json", report)
    print(f"loopx-worker-gateway PROBE hosts={len(report['hosts'])} admission=NOT_PERFORMED")
    return 0


def command_run(args: argparse.Namespace) -> int:
    rc, receipt = execute(
        root=args.root.resolve(),
        registry=load_json(args.registry),
        request=load_json(args.request),
        output=args.output.resolve(),
    )
    if args.json:
        print(json.dumps(receipt, sort_keys=True))
    else:
        print(
            f"loopx-worker-gateway {receipt['state']} "
            f"request={receipt['request_id']} host={receipt['host']['host_id']}"
        )
    return rc


def command_selftest(_: argparse.Namespace) -> int:
    from gateway_selftest import selftest

    selftest(module_root())
    print("loopx-worker-gateway selftest PASS: positive, hollow and planted mutations")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = StrictParser(prog="loopx-worker-gateway")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("--registry", type=Path, required=True)
    validate.add_argument("--request", type=Path, required=True)
    validate.set_defaults(func=command_validate)

    probe_parser = sub.add_parser("probe")
    probe_parser.add_argument("--registry", type=Path, required=True)
    probe_parser.add_argument("--output", type=Path, required=True)
    probe_parser.set_defaults(func=command_probe)

    run = sub.add_parser("run")
    run.add_argument("--registry", type=Path, required=True)
    run.add_argument("--request", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--root", type=Path, default=module_root())
    run.add_argument("--json", action="store_true")
    run.set_defaults(func=command_run)

    selftest_parser = sub.add_parser("selftest")
    selftest_parser.set_defaults(func=command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        return int(args.func(args))
    except GatewayError as exc:
        print(f"loopx-worker-gateway RED: {exc}", file=sys.stderr)
        return 2
    except GatewayFatal as exc:
        print(f"loopx-worker-gateway FATAL: {exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
