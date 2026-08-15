#!/usr/bin/env python3
"""CI parity gate. Exits 0 ok, 2 a checked invariant disagreed, 64 unusable input.

    index      inventory the declared workflows and their local equivalents
    check      run the index and refuse unpinned actions or overreaching coverage
    selftest   positive properties, planted controls and manifest mutations
    compare    build a parity receipt from a local result and an optional remote one

`compare` with no `--remote` is the ordinary case and it answers
`NOT_EXERCISED`. There is no flag that makes a local run stand in for a billed
one, and no subcommand that merges, publishes, reruns a workflow or recovers
billing -- those stay with a human.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cp_common import BAD, OK, USAGE, ContractError, InputError, load_json  # noqa: E402
from cp_contract import check_contracts, run_contract_selftest  # noqa: E402
from cp_index import build_index  # noqa: E402
from cp_parity import compare, local_result, publication_decision, remote_result  # noqa: E402
from cp_selftest import run_selftest  # noqa: E402

DEFAULT_ROOT = Path(__file__).resolve().parents[3]
INDEX_REL = ".github-delivery/ci-parity/index.json"


class UsageParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"FATAL: {message}", file=sys.stderr)
        raise SystemExit(USAGE)


def build_parser() -> argparse.ArgumentParser:
    root = UsageParser(description=__doc__)
    sub = root.add_subparsers(dest="operation", required=True, parser_class=UsageParser)
    for name in ("index", "check", "selftest", "compare"):
        parser = sub.add_parser(name)
        parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
        parser.add_argument("--output", type=Path)
        if name == "compare":
            parser.add_argument("--local", type=Path, required=True)
            parser.add_argument("--remote", type=Path)
            parser.add_argument("--head", required=True)
            parser.add_argument("--covers", default="")
    return root


def _emit(value: object, output: Path | None) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"WROTE {output}")


def load_index(root: Path) -> dict:
    declared = load_json(root / INDEX_REL)
    if not isinstance(declared, dict) or "workflows" not in declared:
        raise InputError(f"{INDEX_REL} does not declare a workflow list")
    return build_index(root, declared["workflows"])


def run(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    op = args.operation

    if op == "index":
        _emit(load_index(root), args.output)
    elif op == "check":
        index = load_index(root)
        contracts = check_contracts(root)
        print(
            f"ci-parity PASS: {len(index['entries'])} declared workflow(s), "
            f"{index['workflows_in_tree']} in tree, {len(index['undeclared'])} "
            f"undeclared, {contracts} contract file(s)"
        )
    elif op == "selftest":
        positive, controls = run_selftest(root)
        mutations = run_contract_selftest(root)
        print(
            f"ci-parity selftest PASS: {positive} positive, {controls} controls, "
            f"{mutations} manifest mutations"
        )
    elif op == "compare":
        local = local_result(load_json(args.local))
        remote = remote_result(load_json(args.remote)) if args.remote else None
        covers = [name for name in args.covers.split(",") if name]
        receipt = compare(local, remote, args.head, covers)
        receipt["publication"] = publication_decision(receipt)
        _emit(receipt, args.output)
        print(f"ci-parity VERDICT {receipt['verdict']}", file=sys.stderr)
    return OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ContractError as exc:
        print(f"ci-parity RED: {exc}", file=sys.stderr)
        return BAD
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
