#!/usr/bin/env python3
"""LoopX Notes Retrieval public port. Exits 0 ok, 2 refused, 64 unusable, 70 provider.

`build` produces both projections. `query` runs a macro read and one micro
query with readback on every hit. Exit 70 is the vector provider being absent:
nothing was asked, so nothing about the notes follows.

There is no subcommand that turns a hit into a fact or a gate verdict.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nr_common import BAD, OK, PROVIDER, USAGE, ContractError, InputError  # noqa: E402
from nr_contract import check_contracts, run_contract_selftest  # noqa: E402
from nr_pipeline import build, query  # noqa: E402
from nr_selftest import (
    CARDS,
    EVIDENCE,
    MANIFEST_DIGEST,
    POLICY,
    TEXTS,
    _tree,
    run_selftest,
)  # noqa: E402

DEFAULT_ROOT = Path(__file__).resolve().parents[1]


class UsageParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"FATAL: {message}", file=sys.stderr)
        raise SystemExit(USAGE)


def build_parser() -> argparse.ArgumentParser:
    root = UsageParser(description=__doc__)
    sub = root.add_subparsers(dest="operation", required=True, parser_class=UsageParser)
    for name in ("check", "selftest", "build", "query"):
        parser = sub.add_parser(name)
        parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
        parser.add_argument("--output", type=Path)
        if name in ("build", "query"):
            parser.add_argument("--no-provider", action="store_true")
        if name == "query":
            parser.add_argument("--term", default="compare-and-set")
    return root


def _emit(value: object, output: Path | None) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"WROTE {output}")


def _built(provider: bool):
    return build(
        "ed3c/bettor-notes",
        "1a" * 20,
        "2b" * 20,
        MANIFEST_DIGEST,
        POLICY,
        CARDS,
        EVIDENCE,
        TEXTS,
        provider,
    )


def run(args: argparse.Namespace) -> int:
    op = args.operation
    if op == "check":
        schemas, files = check_contracts(args.root.resolve())
        print(f"loopx-notes-retrieval PASS: {schemas} schemas, {files} contract files")
    elif op == "selftest":
        positive, controls = run_selftest(args.root.resolve())
        manifest_controls = run_contract_selftest(args.root.resolve())
        print(
            f"loopx-notes-retrieval selftest PASS: {positive} positive, {controls} "
            f"controls, {manifest_controls} manifest mutations"
        )
    elif op == "build":
        _emit(_built(not args.no_provider), args.output)
    elif op == "query":
        with tempfile.TemporaryDirectory(prefix="loopx-nr-") as tmp:
            tree = _tree(Path(tmp) / "notes")
            built = _built(not args.no_provider)
            result = query(built, built["index_subject"], args.term, tree)
            _emit(result, args.output)
            if result["micro"]["state"] == "PROVIDER_ABSENT":
                print(
                    f"loopx-notes-retrieval PROVIDER_ABSENT: {result['micro']['reason']}",
                    file=sys.stderr,
                )
                return PROVIDER
    return OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ContractError as exc:
        print(f"loopx-notes-retrieval RED: {exc}", file=sys.stderr)
        return BAD
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
