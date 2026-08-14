#!/usr/bin/env python3
"""Contract entry point: validate the schemas, then prove this checker can fail."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from strategy_common import BAD, OK, USAGE, ContractError, InputError
from strategy_contract import check_contracts, run_contract_selftest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        schemas, fixtures = check_contracts(root)
        if args.selftest:
            mutations = run_contract_selftest(root)
            print(
                f"loopx-strategy-hitl-contracts selftest PASS: {mutations} manifest "
                "mutations refused"
            )
        else:
            print(
                f"loopx-strategy-hitl-contracts PASS: {schemas} schemas, "
                f"{fixtures} positive fixtures"
            )
        return OK
    except ContractError as exc:
        print(f"loopx-strategy-hitl-contracts RED: {exc}", file=sys.stderr)
        return BAD
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
