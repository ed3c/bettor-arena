#!/usr/bin/env python3
"""LoopX Decision Memory runtime public port. Exits 0 ok, 2 refused, 64 unusable.

`admit` runs a proposal through the lifecycle and appends only on a HUMAN ADMIT.
`delete` tombstones a memory: content unretrievable, history intact. `rebuild`
derives the projection from events alone.

There is no subcommand that writes a memory without a decision, and no branch
that could: `admit` returns REJECTED before reaching the append.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RUNTIME = Path(__file__).resolve().parent
sys.path.insert(0, str(RUNTIME))
sys.path.insert(0, str(RUNTIME.parent / "scripts"))

from memory import ContractError, good_bundle  # noqa: E402

from dmr_contract import check_contracts, run_contract_selftest  # noqa: E402
from dmr_pipeline import admit, delete, handoff, lifecycle_sweep  # noqa: E402
from dmr_projection import rebuild  # noqa: E402
from dmr_selftest import run_selftest  # noqa: E402

OK, BAD, USAGE = 0, 2, 64
DEFAULT_ROOT = RUNTIME.parent


class UsageParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"FATAL: {message}", file=sys.stderr)
        raise SystemExit(USAGE)


def build_parser() -> argparse.ArgumentParser:
    root = UsageParser(description=__doc__)
    sub = root.add_subparsers(dest="operation", required=True, parser_class=UsageParser)
    for name in ("check", "selftest", "admit", "delete", "rebuild", "handoff", "sweep"):
        parser = sub.add_parser(name)
        parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
        parser.add_argument("--output", type=Path)
        if name in ("delete", "sweep"):
            parser.add_argument("--at", default="2026-08-16T09:00:00Z")
        if name == "delete":
            parser.add_argument("--authorized-by", default="ed3c")
            parser.add_argument("--reason", default="human-authorised removal")
        if name == "handoff":
            parser.add_argument("--max-bytes", type=int, default=4096)
        if name in ("delete", "rebuild", "handoff", "sweep"):
            parser.add_argument("--log", type=Path)
    return root


def _emit(value: object, output: Path | None) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"WROTE {output}")


def _log(args: argparse.Namespace) -> tuple[list, dict, dict]:
    proposal, decision = good_bundle()
    if getattr(args, "log", None) is not None:
        # Read with json rather than memory.load: the shared loader requires a
        # top-level object because every contract in this module is one, and an
        # event log is a list.
        return json.loads(args.log.read_text(encoding="utf-8")), proposal, decision
    return admit([], proposal, decision)["log"], proposal, decision


def run(args: argparse.Namespace) -> int:
    op = args.operation
    if op == "check":
        schemas, fixtures = check_contracts(args.root.resolve())
        print(
            f"loopx-decision-memory-runtime PASS: {schemas} schemas, "
            f"{fixtures} positive fixtures"
        )
    elif op == "selftest":
        positive, controls = run_selftest(args.root.resolve())
        manifest_controls = run_contract_selftest(args.root.resolve())
        print(
            f"loopx-decision-memory-runtime selftest PASS: {positive} positive, "
            f"{controls} controls, {manifest_controls} manifest mutations"
        )
    elif op == "admit":
        proposal, decision = good_bundle()
        _emit(admit([], proposal, decision), args.output)
    elif op == "delete":
        log, proposal, _ = _log(args)
        _emit(
            delete(
                log, proposal["canonical_key"], args.authorized_by, args.at, args.reason
            ),
            args.output,
        )
    elif op == "rebuild":
        log, _, _ = _log(args)
        _emit(rebuild(log), args.output)
    elif op == "handoff":
        log, proposal, _ = _log(args)
        _emit(
            handoff(log, proposal["scope"]["valid_from_commit"], args.max_bytes),
            args.output,
        )
    elif op == "sweep":
        log, _, _ = _log(args)
        _emit(lifecycle_sweep(log, args.at, "ed3c"), args.output)
    return OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ContractError as exc:
        print(f"loopx-decision-memory-runtime RED: {exc}", file=sys.stderr)
        return BAD
    except (OSError, ValueError) as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
