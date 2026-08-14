#!/usr/bin/env python3
"""Evaluate normalized provider/control observations without launching tools."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from knowledge_provider_eval_common import ContractError, EVALS, save
from knowledge_provider_eval_engine import evaluate
from knowledge_provider_eval_selftest import run as run_selftest

OK, FAIL, FATAL = 0, 2, 64


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--observations",
        default=str(EVALS / "fixtures/good/observations.json.gz"),
    )
    parser.add_argument("--output")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        if args.selftest:
            result = run_selftest(root)
            print(
                "knowledge-provider-evals selftest PASS: "
                f"{result['positive']} positive, "
                f"{result['hollow']} hollow, "
                f"{result['mutations']} mutations"
            )
            return OK
        path = Path(args.observations)
        if not path.is_absolute():
            path = root / path
        report = evaluate(root, path)
        if args.output:
            output = Path(args.output)
            save(output if output.is_absolute() else root / output, report)
        print(
            f"knowledge-provider-evals {report['status']}: "
            f"{report['suite']['case_count']} cases, "
            f"{report['suite']['observation_count']} observations, "
            f"pairs={report['pair_coverage']['observed']}/"
            f"{report['pair_coverage']['expected']}, "
            f"scope={report['evidence_scope']}"
        )
        return OK if report["status"] == "PASS" else FAIL
    except ContractError as exc:
        print(f"knowledge-provider-evals FAIL: {exc}", file=sys.stderr)
        return FAIL
    except (OSError, ValueError) as exc:
        print(f"knowledge-provider-evals ERROR: {exc}", file=sys.stderr)
        return FATAL


if __name__ == "__main__":
    raise SystemExit(main())
