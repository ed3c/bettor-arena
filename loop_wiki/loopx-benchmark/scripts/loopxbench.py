#!/usr/bin/env python3
"""LoopX Benchmark port. Exits 0 ok, 2 refused, 64 unusable input.

    check      manifest, schemas and vocabulary
    selftest   positive properties, planted controls, manifest mutations
    synthetic  deterministic trials with no timing meaning, for CI
    measure    run a real workload here and report every trial
    verdict    place a claim on the ladder against one or more reports

`measure` is deliberately not what CI runs. A duration from a shared runner whose
neighbours nobody can see is a number about that runner at that moment, and
publishing it as a repository fact is the thing this module exists to stop. CI
runs `synthetic`, which proves the pipeline and carries no timing meaning at all.

There is no subcommand that promotes a claim. Promotion is Human Admit.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bm_claim import evaluate  # noqa: E402
from bm_common import BAD, OK, USAGE, ContractError, InputError, load_json  # noqa: E402
from bm_contract import check_contracts, run_contract_selftest  # noqa: E402
from bm_report import summarize  # noqa: E402
from bm_run import SYNTHETIC_ENVIRONMENT, execute, synthetic  # noqa: E402
from bm_selftest import CLAIM, IDENTITIES, SUBJECT, WORKLOAD, run_selftest  # noqa: E402

DEFAULT_ROOT = Path(__file__).resolve().parents[3]


class UsageParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"FATAL: {message}", file=sys.stderr)
        raise SystemExit(USAGE)


def build_parser() -> argparse.ArgumentParser:
    root = UsageParser(description=__doc__)
    sub = root.add_subparsers(dest="operation", required=True, parser_class=UsageParser)
    for name in ("check", "selftest", "synthetic", "measure", "verdict"):
        parser = sub.add_parser(name)
        parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
        parser.add_argument("--output", type=Path)
        if name == "measure":
            parser.add_argument("--repetitions", type=int, default=8)
            parser.add_argument("--cache-state", default="COLD")
        if name == "verdict":
            parser.add_argument("--reports", type=Path, nargs="+", required=True)
    return root


def _emit(value: object, output: Path | None) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"WROTE {output}")


def local_subject(root: Path) -> dict[str, object]:
    """The commit and dirty state, read from git rather than declared.

    Declared subjects are the ones that drift: a report that names a commit it
    was not run at is a comparison waiting to be made against the wrong thing.
    """

    def git(*args: str) -> str:
        done = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
        )
        if done.returncode != 0:
            raise InputError(f"git {' '.join(args)} failed: {done.stderr.strip()}")
        return done.stdout.strip()

    return {
        "commit": git("rev-parse", "HEAD"),
        "tree_dirty": bool(git("status", "--porcelain")),
        "dependency_digest": "sha256:" + "0" * 64,
        "enforcement_policy": "gates-strict-v1",
    }


def local_environment() -> dict[str, object]:
    return {
        "os": f"{platform.system().lower()}-{platform.release()}",
        "arch": platform.machine(),
        "cpu": platform.processor() or platform.machine(),
        "ram_gb": 1,
        "runtime": f"python-{platform.python_version()}",
        "image": "none",
        "locale": "LOCAL",
    }


def run(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    op = args.operation

    if op == "check":
        schemas, files = check_contracts(root)
        print(f"loopx-benchmark PASS: {schemas} schemas, {files} contract files")
    elif op == "selftest":
        positive, controls = run_selftest(root)
        mutations = run_contract_selftest(root)
        print(
            f"loopx-benchmark selftest PASS: {positive} positive, {controls} controls, "
            f"{mutations} manifest mutations"
        )
    elif op == "synthetic":
        result = synthetic(WORKLOAD)
        report = summarize(
            SUBJECT, SYNTHETIC_ENVIRONMENT, IDENTITIES, WORKLOAD, result["trials"]
        )
        _emit(
            {**report, "warmup_runs_discarded": result["warmup_runs_discarded"]},
            args.output,
        )
    elif op == "measure":
        workload = {**WORKLOAD, "repetitions": args.repetitions}
        result = execute(workload, cache_state=args.cache_state)
        report = summarize(
            local_subject(root),
            local_environment(),
            IDENTITIES,
            workload,
            result["trials"],
        )
        _emit(
            {**report, "warmup_runs_discarded": result["warmup_runs_discarded"]},
            args.output,
        )
    elif op == "verdict":
        reports = [load_json(path) for path in args.reports]
        result = evaluate(CLAIM, reports)
        _emit(result, args.output)
        print(f"loopx-benchmark VERDICT {result['verdict']}", file=sys.stderr)
    return OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ContractError as exc:
        print(f"loopx-benchmark RED: {exc}", file=sys.stderr)
        return BAD
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
