#!/usr/bin/env python3
"""LoopX Strategy + HITL public port. Exits 0 ok, 2 refused, 64 unusable input.

This is the only entry point callers are meant to touch. It validates and
emits receipts; it never writes canonical task state, which stays with the
ledger reducer.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from strategy_common import BAD, OK, USAGE, ContractError, InputError, load_json
from strategy_checkpoint import admit_resume, validate_checkpoint
from strategy_decision import validate_decision
from strategy_engine import admit_proposal, apply_human_decision, validate_proposal
from strategy_selftest import run_selftest


class UsageParser(argparse.ArgumentParser):
    """Map argparse's own errors onto the repository's 64, not its default 2."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"FATAL: {message}", file=sys.stderr)
        raise SystemExit(USAGE)


def build_parser() -> argparse.ArgumentParser:
    root = UsageParser(description=__doc__)
    sub = root.add_subparsers(dest="operation", required=True, parser_class=UsageParser)

    proposal = sub.add_parser("validate-proposal")
    proposal.add_argument("--proposal", required=True, type=Path)

    checkpoint = sub.add_parser("validate-checkpoint")
    checkpoint.add_argument("--checkpoint", required=True, type=Path)

    decision = sub.add_parser("validate-decision")
    decision.add_argument("--decision", required=True, type=Path)
    decision.add_argument("--gate-classes", required=True, type=Path)

    resume = sub.add_parser("admit-resume")
    resume.add_argument("--checkpoint", required=True, type=Path)
    resume.add_argument("--ledger-head", required=True, type=Path)
    resume.add_argument("--subject", required=True, type=Path)
    resume.add_argument("--receipt", type=Path)

    propose = sub.add_parser("admit-proposal")
    propose.add_argument("--proposal", required=True, type=Path)
    propose.add_argument("--subject", required=True, type=Path)
    propose.add_argument("--state", required=True)
    propose.add_argument("--revision", required=True, type=int)
    propose.add_argument("--receipt", type=Path)

    apply_ = sub.add_parser("apply-decision")
    apply_.add_argument("--decision", required=True, type=Path)
    apply_.add_argument("--subject", required=True, type=Path)
    apply_.add_argument("--ledger-head", required=True, type=Path)
    apply_.add_argument("--gate-classes", required=True, type=Path)
    apply_.add_argument("--observations", required=True, type=Path)
    apply_.add_argument("--state", default="HITL_PENDING")
    apply_.add_argument("--receipt", type=Path)

    selftest = sub.add_parser("selftest")
    selftest.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    return root


def _emit(value: object, receipt: Path | None) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if receipt is None:
        sys.stdout.write(text)
    else:
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(text, encoding="utf-8")
        print(f"WROTE {receipt}")


def run(args: argparse.Namespace) -> int:
    op = args.operation
    if op == "validate-proposal":
        validate_proposal(load_json(args.proposal))
        print("loopx-strategy PASS: proposal is a Contract v1 command")
    elif op == "validate-checkpoint":
        validate_checkpoint(load_json(args.checkpoint))
        print("loopx-strategy PASS: checkpoint is a cursor, not a second authority")
    elif op == "validate-decision":
        decision = validate_decision(
            load_json(args.decision), load_json(args.gate_classes)
        )
        print(f"loopx-strategy PASS: {decision['action']} decision is admissible")
    elif op == "admit-resume":
        _emit(
            admit_resume(
                load_json(args.checkpoint),
                load_json(args.ledger_head),
                load_json(args.subject),
            ),
            args.receipt,
        )
    elif op == "admit-proposal":
        _emit(
            admit_proposal(
                load_json(args.proposal),
                args.state,
                args.revision,
                load_json(args.subject),
            ),
            args.receipt,
        )
    elif op == "apply-decision":
        head = load_json(args.ledger_head)
        _emit(
            apply_human_decision(
                load_json(args.decision),
                args.state,
                head["state_revision"],
                load_json(args.subject),
                head["event_digest"],
                load_json(args.gate_classes),
                load_json(args.observations),
            ),
            args.receipt,
        )
    elif op == "selftest":
        positive, controls = run_selftest(args.root.resolve())
        print(f"loopx-strategy selftest PASS: {positive} positive, {controls} controls")
    return OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ContractError as exc:
        print(f"loopx-strategy RED: {exc}", file=sys.stderr)
        return BAD
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
