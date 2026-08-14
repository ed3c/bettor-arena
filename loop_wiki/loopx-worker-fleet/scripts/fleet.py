#!/usr/bin/env python3
"""LoopX Worker Fleet public port. Exits 0 ok, 2 refused, 64 unusable input.

`cycle` schedules, leases and monitors. `gc` inventories orphan workspaces and
proposes; removing anything requires `--admit <path>` per workspace and
`--apply`, and a workspace that is leased, dirty or unreadable cannot be admitted
at all.

There is no subcommand that writes canonical task state, merges, ships, promotes
or rolls back. Those belong to LoopX and to a human, and a fleet controller with
a button for them is a fleet controller that will eventually press it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from wf_cleanup import execute, inventory, plan  # noqa: E402
from wf_common import (  # noqa: E402
    BAD,
    OK,
    USAGE,
    ContractError,
    InputError,
    load_json,
)
from wf_contract import check_contracts, run_contract_selftest  # noqa: E402
from wf_pipeline import run_cycle  # noqa: E402
from wf_receipt import validate_receipt  # noqa: E402
from wf_selftest import load_inputs, run_selftest  # noqa: E402

DEFAULT_ROOT = Path(__file__).resolve().parents[1]


class UsageParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"FATAL: {message}", file=sys.stderr)
        raise SystemExit(USAGE)


def build_parser() -> argparse.ArgumentParser:
    root = UsageParser(description=__doc__)
    sub = root.add_subparsers(dest="operation", required=True, parser_class=UsageParser)

    for name in ("check", "selftest"):
        parser = sub.add_parser(name)
        parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)

    cycle = sub.add_parser("cycle")
    cycle.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    cycle.add_argument("--now", default="2026-08-15T10:30:00Z")
    cycle.add_argument("--output", type=Path)

    gc = sub.add_parser("gc")
    gc.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    gc.add_argument("--workspaces", required=True, type=Path)
    gc.add_argument(
        "--admit",
        action="append",
        default=[],
        help="workspace a human admitted for removal; repeatable",
    )
    gc.add_argument(
        "--apply",
        action="store_true",
        help="actually remove admitted workspaces; omitting it is a dry run",
    )
    gc.add_argument("--output", type=Path)

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


def run(args: argparse.Namespace) -> int:
    op = args.operation
    if op == "check":
        schemas, fixtures = check_contracts(args.root.resolve())
        print(
            f"loopx-worker-fleet PASS: {schemas} schemas, {fixtures} positive fixtures"
        )
    elif op == "selftest":
        root = args.root.resolve()
        positive, controls = run_selftest(root)
        manifest_controls = run_contract_selftest(root)
        print(
            f"loopx-worker-fleet selftest PASS: {positive} positive, {controls} "
            f"controls, {manifest_controls} manifest mutations"
        )
    elif op == "cycle":
        inputs = load_inputs(args.root.resolve())
        _emit(
            run_cycle(
                inputs["fleet-queue"],
                inputs["leases"],
                set(),
                [],
                inputs["heartbeats"],
                args.now,
            ),
            args.output,
        )
    elif op == "gc":
        inputs = load_inputs(args.root.resolve())
        entries = inventory(
            args.workspaces.resolve(),
            inputs["leases"],
            inputs["fleet-queue"]["owner_checkout"],
        )
        proposal = plan(entries, args.admit)
        _emit(
            {**proposal, "execution": execute(proposal, apply=args.apply)}, args.output
        )
    elif op == "verify-receipt":
        validate_receipt(load_json(args.receipt))
        print("loopx-worker-fleet PASS: receipt observes and decides nothing")
    return OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ContractError as exc:
        print(f"loopx-worker-fleet RED: {exc}", file=sys.stderr)
        return BAD
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
