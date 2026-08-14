#!/usr/bin/env python3
"""LoopX Observability public port. Exits 0 ok, 2 refused, 64 unusable input.

Projects ledger events into redacted, OpenTelemetry-shaped envelopes and admits
signed console requests. It never writes canonical state; every output it
produces says so on its face.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from obs_action import admit_request, validate_request
from obs_common import BAD, OK, USAGE, ContractError, InputError, load_json
from obs_contract import check_contracts, run_contract_selftest
from obs_envelope import project, rebuild_matches
from obs_redaction import validate_policy
from obs_selftest import run_selftest


class UsageParser(argparse.ArgumentParser):
    """Map argparse's own errors onto the repository's 64, not its default 2."""

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

    proj = sub.add_parser("project")
    proj.add_argument("--ledger", required=True, type=Path)
    proj.add_argument("--policy", required=True, type=Path)
    proj.add_argument("--output", type=Path)

    rebuild = sub.add_parser("rebuild")
    rebuild.add_argument("--ledger", required=True, type=Path)
    rebuild.add_argument("--policy", required=True, type=Path)
    rebuild.add_argument("--projection", required=True, type=Path)
    rebuild.add_argument("--output", type=Path)

    admit = sub.add_parser("admit-request")
    admit.add_argument("--request", required=True, type=Path)
    admit.add_argument("--state", required=True, type=Path)
    admit.add_argument("--projection", required=True, type=Path)
    admit.add_argument("--output", type=Path)

    vpolicy = sub.add_parser("validate-policy")
    vpolicy.add_argument("--policy", required=True, type=Path)

    vrequest = sub.add_parser("validate-request")
    vrequest.add_argument("--request", required=True, type=Path)
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
            f"loopx-observability PASS: {schemas} schemas, {fixtures} positive fixtures"
        )
    elif op == "selftest":
        root = args.root.resolve()
        positive, controls = run_selftest(root)
        # The manifest mutations run here too. They were written and imported but
        # never called -- six controls that existed in the file and nowhere in the
        # execution path, which is the same as not having them. ruff's
        # unused-import warning is what surfaced it.
        manifest_controls = run_contract_selftest(root)
        print(
            f"loopx-observability selftest PASS: {positive} positive, "
            f"{controls} controls, {manifest_controls} manifest mutations"
        )
    elif op == "project":
        _emit(project(load_json(args.ledger), load_json(args.policy)), args.output)
    elif op == "rebuild":
        _emit(
            rebuild_matches(
                load_json(args.ledger),
                load_json(args.policy),
                load_json(args.projection),
            ),
            args.output,
        )
    elif op == "admit-request":
        _emit(
            admit_request(
                load_json(args.request),
                load_json(args.state),
                load_json(args.projection),
            ),
            args.output,
        )
    elif op == "validate-policy":
        policy = validate_policy(load_json(args.policy))
        print(f"loopx-observability PASS: policy {policy['policy_version']} admissible")
    elif op == "validate-request":
        request = validate_request(load_json(args.request))
        print(
            f"loopx-observability PASS: {request['requested_action']} request is a "
            "proposal, not a command"
        )
    return OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ContractError as exc:
        print(f"loopx-observability RED: {exc}", file=sys.stderr)
        return BAD
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
