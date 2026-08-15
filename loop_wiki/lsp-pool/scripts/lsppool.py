#!/usr/bin/env python3
"""LoopX LSP Pool public port. Exits 0 ok, 2 refused, 64 unusable input.

`query` runs one request through the pool against the deterministic fixture
server. There is no subcommand that starts a real language server: admitting a
real one is a canary with its own exact binary and config, and it is Human
Admit — the contract manifest pins `canary_state` to `NOT_EXERCISED` until then.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lsp_common import (  # noqa: E402
    BAD,
    OK,
    USAGE,
    ContractError,
    InputError,
    ServerUnavailable,
    load_json,
)
from lsp_contract import check_contracts, run_contract_selftest  # noqa: E402
from lsp_pipeline import run_query  # noqa: E402
from lsp_query import to_code_truth_graph  # noqa: E402
from lsp_selftest import (  # noqa: E402
    build_workspace_tree,
    load_inputs,
    run_selftest,
    server_argv,
)

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

    query = sub.add_parser("query")
    query.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    query.add_argument(
        "--behaviour",
        default="normal",
        choices=["normal", "crash", "hang", "wrong-tree", "empty-on-fail"],
    )
    query.add_argument("--fallback", action="store_true")
    query.add_argument("--output", type=Path)

    graph = sub.add_parser("to-graph")
    graph.add_argument("--result", required=True, type=Path)
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
        print(f"lsp-pool PASS: {schemas} schemas, {fixtures} positive fixtures")
    elif op == "selftest":
        root = args.root.resolve()
        positive, controls = run_selftest(root)
        manifest_controls = run_contract_selftest(root)
        print(
            f"lsp-pool selftest PASS: {positive} positive, {controls} controls, "
            f"{manifest_controls} manifest mutations"
        )
    elif op == "query":
        root = args.root.resolve()
        inputs = load_inputs(root)
        with tempfile.TemporaryDirectory(prefix="loopx-lsp-") as tmp:
            tree = build_workspace_tree(Path(tmp) / "alpha")
            _emit(
                run_query(
                    inputs["request"],
                    inputs["slots"],
                    inputs["limits"],
                    server_argv(root),
                    tree,
                    behaviour=args.behaviour,
                    timeout_s=5.0,
                    fallback_admission=(
                        inputs["fallback-admission"] if args.fallback else None
                    ),
                    other_workspace_id=(
                        "ws-beta" if args.behaviour == "wrong-tree" else None
                    ),
                ),
                args.output,
            )
    elif op == "to-graph":
        _emit(to_code_truth_graph(load_json(args.result)), None)
    return OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except (ContractError, ServerUnavailable) as exc:
        print(f"lsp-pool RED: {exc}", file=sys.stderr)
        return BAD
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
