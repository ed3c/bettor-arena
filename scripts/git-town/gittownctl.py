#!/usr/bin/env python3
"""Git Town runtime admission port.

Exits 0 ok, 2 a checked invariant disagreed, 64 unusable input, 70 the executable
is not here.

    check      manifest, schemas and vocabulary
    selftest   positive properties, planted controls, manifest mutations
    probe      what is actually installed on this machine
    admit      combine a probe, a pin and a profile into an admission state
    argv       print the argv for an admitted mode, or refuse
    publish    whether a publication request may be made -- never make one

There is no subcommand that runs a sync, continues, skips, undoes, ships,
pushes or merges. `argv` prints what would run; running it is a separate act by
someone who read it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gt_admit import (  # noqa: E402
    admit,
    probe,
    require_mode_allowed,
)
from gt_common import (  # noqa: E402
    BAD,
    OK,
    PROVIDER,
    USAGE,
    ContractError,
    InputError,
    load_json,
)
from gt_contract import check_contracts, run_contract_selftest  # noqa: E402
from gt_publish import publication_decision  # noqa: E402
from gt_selftest import ADMISSION, PROFILE, run_selftest  # noqa: E402

DEFAULT_ROOT = Path(__file__).resolve().parents[2]


class UsageParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"FATAL: {message}", file=sys.stderr)
        raise SystemExit(USAGE)


def build_parser() -> argparse.ArgumentParser:
    root = UsageParser(description=__doc__)
    sub = root.add_subparsers(dest="operation", required=True, parser_class=UsageParser)
    for name in ("check", "selftest", "probe", "admit", "argv", "publish"):
        parser = sub.add_parser(name)
        parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
        parser.add_argument("--output", type=Path)
        if name in ("admit", "argv", "publish"):
            parser.add_argument("--admission", type=Path)
            parser.add_argument("--profile", type=Path)
            parser.add_argument("--reviewed", action="store_true")
        if name == "argv":
            parser.add_argument("--mode", required=True)
        if name == "publish":
            parser.add_argument("--local-head", required=True)
            parser.add_argument("--check-head", required=True)
    return root


def _emit(value: object, output: Path | None) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"WROTE {output}")


def current_admission(args: argparse.Namespace) -> dict:
    admission = load_json(args.admission) if args.admission else ADMISSION
    profile = load_json(args.profile) if args.profile else PROFILE
    return admit(probe(), admission, profile, live_local_reviewed=args.reviewed)


def run(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    op = args.operation

    if op == "check":
        schemas, files = check_contracts(root)
        print(f"git-town-runtime PASS: {schemas} schemas, {files} contract files")
    elif op == "selftest":
        positive, controls = run_selftest(root)
        mutations = run_contract_selftest(root)
        print(
            f"git-town-runtime selftest PASS: {positive} positive, {controls} controls, "
            f"{mutations} manifest mutations"
        )
    elif op == "probe":
        found = probe()
        _emit(found, args.output)
        if found["state"] == "EXECUTABLE_ABSENT":
            print(
                f"git-town-runtime EXECUTABLE_ABSENT: {found['reason']}",
                file=sys.stderr,
            )
            return PROVIDER
    elif op == "admit":
        result = current_admission(args)
        _emit(result, args.output)
        if result["state"] == "EXECUTABLE_ABSENT":
            print(
                f"git-town-runtime EXECUTABLE_ABSENT: {result['reason']}",
                file=sys.stderr,
            )
            return PROVIDER
    elif op == "argv":
        result = current_admission(args)
        if result["state"] == "EXECUTABLE_ABSENT":
            print(
                f"git-town-runtime EXECUTABLE_ABSENT: {result['reason']}",
                file=sys.stderr,
            )
            return PROVIDER
        _emit(
            {"mode": args.mode, "argv": require_mode_allowed(result, args.mode)},
            args.output,
        )
    elif op == "publish":
        result = current_admission(args)
        decision = publication_decision(result, args.local_head, args.check_head)
        _emit(decision, args.output)
        print(
            f"git-town-runtime PUBLICATION {'MAY_REQUEST' if decision['may_request'] else 'BLOCKED'}",
            file=sys.stderr,
        )
        if not decision["may_request"]:
            return BAD
    return OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ContractError as exc:
        print(f"git-town-runtime RED: {exc}", file=sys.stderr)
        return BAD
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
