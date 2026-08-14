#!/usr/bin/env python3
"""LoopX Strategy + HITL public port. Exits 0 ok, 2 refused, 64 unusable input.

The compiler emits a proposal envelope only. It does not append to the ledger,
resume a planner, dispatch a Worker, waive a Gate, merge, promote or Human Admit.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from strategy_common import BAD, OK, USAGE, ContractError, InputError, load_json
from strategy_checkpoint import admit_resume, validate_checkpoint
from strategy_contract import check_contracts
from strategy_decision import validate_decision
from strategy_engine import admit_proposal, compile_resume_envelope, validate_interrupt
from strategy_selftest import run_selftest


class UsageParser(argparse.ArgumentParser):
    """Map argparse's own errors onto the repository's 64, not its default 2."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"FATAL: {message}", file=sys.stderr)
        raise SystemExit(USAGE)


DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    root = UsageParser(description=__doc__)
    sub = root.add_subparsers(dest="operation", required=True, parser_class=UsageParser)

    check = sub.add_parser("check")
    check.add_argument("--root", type=Path, default=DEFAULT_ROOT)

    selftest = sub.add_parser("selftest")
    selftest.add_argument("--root", type=Path, default=DEFAULT_ROOT)

    resume = sub.add_parser("resume")
    resume.add_argument("--interrupt", required=True, type=Path)
    resume.add_argument("--decision", required=True, type=Path)
    resume.add_argument("--state", required=True, type=Path)
    resume.add_argument("--gate-classes", required=True, type=Path)
    resume.add_argument("--observations", required=True, type=Path)
    resume.add_argument("--output", type=Path)

    proposal = sub.add_parser("admit-proposal")
    proposal.add_argument("--proposal", required=True, type=Path)
    proposal.add_argument("--state", required=True, type=Path)
    proposal.add_argument("--subject", required=True, type=Path)
    proposal.add_argument("--output", type=Path)

    ckpt = sub.add_parser("admit-checkpoint")
    ckpt.add_argument("--checkpoint", required=True, type=Path)
    ckpt.add_argument("--state", required=True, type=Path)
    ckpt.add_argument("--subject", required=True, type=Path)
    ckpt.add_argument("--output", type=Path)

    for name, flag in (
        ("validate-interrupt", "--interrupt"),
        ("validate-checkpoint", "--checkpoint"),
    ):
        parser = sub.add_parser(name)
        parser.add_argument(flag, required=True, type=Path)

    decision = sub.add_parser("validate-decision")
    decision.add_argument("--decision", required=True, type=Path)
    decision.add_argument("--gate-classes", required=True, type=Path)
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
            f"loopx-strategy-hitl PASS: {schemas} schemas, {fixtures} positive fixtures"
        )
    elif op == "selftest":
        positive, controls = run_selftest(args.root.resolve())
        print(
            f"loopx-strategy-hitl selftest PASS: {positive} positive, {controls} controls"
        )
    elif op == "resume":
        _emit(
            compile_resume_envelope(
                load_json(args.interrupt),
                load_json(args.decision),
                load_json(args.state),
                load_json(args.gate_classes),
                load_json(args.observations),
            ),
            args.output,
        )
    elif op == "admit-proposal":
        _emit(
            admit_proposal(
                load_json(args.proposal),
                load_json(args.state),
                load_json(args.subject),
            ),
            args.output,
        )
    elif op == "admit-checkpoint":
        _emit(
            admit_resume(
                load_json(args.checkpoint),
                load_json(args.state),
                load_json(args.subject),
            ),
            args.output,
        )
    elif op == "validate-interrupt":
        validate_interrupt(load_json(args.interrupt))
        print("loopx-strategy-hitl PASS: interrupt terms match their digest")
    elif op == "validate-checkpoint":
        validate_checkpoint(load_json(args.checkpoint))
        print("loopx-strategy-hitl PASS: checkpoint is a projection, not an authority")
    elif op == "validate-decision":
        decision = validate_decision(
            load_json(args.decision), load_json(args.gate_classes)
        )
        print(
            f"loopx-strategy-hitl PASS: {decision['decision']} decision is admissible"
        )
    return OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ContractError as exc:
        print(f"loopx-strategy-hitl RED: {exc}", file=sys.stderr)
        return BAD
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
