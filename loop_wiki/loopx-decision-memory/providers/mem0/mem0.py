#!/usr/bin/env python3
"""Mem0 provider projection public port. Exits 0 ok, 2 refused, 64 unusable, 70 provider.

`project` builds an index from admitted ledger events. `query` reads it.
`writeback` produces a *proposal* addressed to the memory admission path.

There is no subcommand that writes LoopX state, edits a repository document,
marks a gate, or turns a retrieval into durable memory. Exit 70 is the provider
being unavailable: a store that is down said nothing about the memory, and
folding that into 2 would record a refusal about memory that was never checked.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
for _sub in ("scripts", "runtime"):
    sys.path.insert(0, str(BASE / _sub))

from memory import ContractError, good_bundle  # noqa: E402

from dmr_pipeline import admit  # noqa: E402
from mem0_authority import writeback_proposal  # noqa: E402
from mem0_contract import check_contracts, run_contract_selftest  # noqa: E402
from mem0_projection import build, query, rebuild_equivalent  # noqa: E402
from mem0_selftest import OSS, POLICY, run_selftest  # noqa: E402

OK, BAD, USAGE, PROVIDER = 0, 2, 64, 70
DEFAULT_ROOT = Path(__file__).resolve().parent


class UsageParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"FATAL: {message}", file=sys.stderr)
        raise SystemExit(USAGE)


def build_parser() -> argparse.ArgumentParser:
    root = UsageParser(description=__doc__)
    sub = root.add_subparsers(dest="operation", required=True, parser_class=UsageParser)
    for name in ("check", "selftest", "project", "query", "rebuild", "writeback"):
        parser = sub.add_parser(name)
        parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
        parser.add_argument("--output", type=Path)
        if name == "query":
            parser.add_argument("--term", default="boundary")
            parser.add_argument(
                "--availability",
                default="AVAILABLE",
                choices=["AVAILABLE", "UNAVAILABLE", "NOT_EXERCISED"],
            )
    return root


def _emit(value: object, output: Path | None) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"WROTE {output}")


def _projection():
    proposal, decision = good_bundle()
    log = admit([], proposal, decision)["log"]
    return log, proposal, build(log, OSS, POLICY, "2026-08-16T10:00:00Z")


def run(args: argparse.Namespace) -> int:
    op = args.operation
    if op == "check":
        schemas, fixtures = check_contracts(args.root.resolve())
        print(f"mem0-projection PASS: {schemas} schemas, {fixtures} contract files")
    elif op == "selftest":
        positive, controls = run_selftest(args.root.resolve())
        manifest_controls = run_contract_selftest(args.root.resolve())
        print(
            f"mem0-projection selftest PASS: {positive} positive, {controls} controls, "
            f"{manifest_controls} manifest mutations"
        )
    elif op == "project":
        _, _, projection = _projection()
        _emit(projection, args.output)
    elif op == "query":
        _, _, projection = _projection()
        result = query(projection, args.term, args.availability)
        _emit(result, args.output)
        if result["state"] == "PROVIDER_UNAVAILABLE":
            print(
                f"mem0-projection PROVIDER_UNAVAILABLE: {result['reason']}",
                file=sys.stderr,
            )
            return PROVIDER
    elif op == "rebuild":
        log, _, projection = _projection()
        _emit(
            rebuild_equivalent(log, projection, POLICY, "2026-08-16T11:00:00Z"),
            args.output,
        )
    elif op == "writeback":
        _, proposal, projection = _projection()
        hits = query(projection, "boundary", "AVAILABLE")["hits"]
        _emit(
            writeback_proposal(hits, proposal["canonical_key"], "a retrieved claim"),
            args.output,
        )
    return OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ContractError as exc:
        print(f"mem0-projection RED: {exc}", file=sys.stderr)
        return BAD
    except (OSError, ValueError) as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
