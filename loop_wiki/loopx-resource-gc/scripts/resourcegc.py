#!/usr/bin/env python3
"""LoopX Resource GC public port. Exits 0 ok, 2 refused, 64 unusable, 70 exhausted.

`plan` produces a dry run. `run` executes one, and needs `--apply` plus a
per-resource `--admit`. Neither can select immutable evidence, blocked evidence,
a leased or dirty worktree, or a projection whose rebuild has not been proven
against the original.

Exit 70 is disk exhaustion: not a task that failed and not a gate that
disagreed. Someone reading "GC failed" goes to debug the GC; someone reading
"the disk filled" goes to find space.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rgc_common import (  # noqa: E402
    BAD,
    OK,
    USAGE,
    ContractError,
    InputError,
    ResourceExhausted,
    load_json,
)
from rgc_contract import check_contracts, run_contract_selftest  # noqa: E402
from rgc_execute import validate_receipt  # noqa: E402
from rgc_fixtures import build_tree  # noqa: E402
from rgc_pipeline import run_gc  # noqa: E402
from rgc_selftest import load_inputs, run_selftest  # noqa: E402

EXHAUSTED = 70
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

    for name in ("plan", "run"):
        parser = sub.add_parser(name)
        parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
        parser.add_argument("--tree", type=Path)
        parser.add_argument("--admit", action="append", default=None)
        parser.add_argument("--output", type=Path)
        if name == "run":
            parser.add_argument(
                "--apply",
                action="store_true",
                help="actually delete; omitting it is a dry run",
            )

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


def _gc(args: argparse.Namespace, apply: bool) -> dict:
    inputs = load_inputs(args.root.resolve())
    config = inputs["config"]
    admitted = config["admitted"] if args.admit is None else args.admit

    if args.tree is not None:
        return run_gc(
            config["root_id"],
            inputs["resources"],
            set(config["held_leases"]),
            set(config["live_subjects"]),
            inputs["rebuild-specs"],
            admitted,
            config["authorized_by"],
            config["now"],
            config["max_age_s"],
            args.tree.resolve(),
            apply=apply,
        )
    # No tree given: build the fixture tree in a disposable directory. A GC whose
    # default target was the caller's cwd would eventually be run from a checkout.
    with tempfile.TemporaryDirectory(prefix="loopx-rgc-") as tmp:
        tree = build_tree(Path(tmp) / "tree")
        return run_gc(
            config["root_id"],
            inputs["resources"],
            set(config["held_leases"]),
            set(config["live_subjects"]),
            inputs["rebuild-specs"],
            admitted,
            config["authorized_by"],
            config["now"],
            config["max_age_s"],
            tree,
            apply=apply,
        )


def run(args: argparse.Namespace) -> int:
    op = args.operation
    if op == "check":
        schemas, fixtures = check_contracts(args.root.resolve())
        print(
            f"loopx-resource-gc PASS: {schemas} schemas, {fixtures} positive fixtures"
        )
    elif op == "selftest":
        root = args.root.resolve()
        positive, controls = run_selftest(root)
        manifest_controls = run_contract_selftest(root)
        print(
            f"loopx-resource-gc selftest PASS: {positive} positive, {controls} "
            f"controls, {manifest_controls} manifest mutations"
        )
    elif op == "plan":
        _emit(_gc(args, apply=False), args.output)
    elif op == "run":
        _emit(_gc(args, apply=args.apply), args.output)
    elif op == "verify-receipt":
        validate_receipt(load_json(args.receipt))
        print("loopx-resource-gc PASS: receipt records what is still on the machine")
    return OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ContractError as exc:
        print(f"loopx-resource-gc RED: {exc}", file=sys.stderr)
        return BAD
    except ResourceExhausted as exc:
        print(f"loopx-resource-gc RESOURCE_EXHAUSTED: {exc}", file=sys.stderr)
        return EXHAUSTED
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
