#!/usr/bin/env python3
"""Print the actual error each control produces.

A green selftest only says every control turned red. It does not say each one
turned red for the reason it was written for -- and a control failing for an
unrelated reason is a false negative wearing a green badge: the failure it names
would still get through. This prints the pairing so it can be read.

Not part of run-all.sh; it is a diagnostic, and its output is prose.
"""

from __future__ import annotations

import argparse
import copy
from pathlib import Path

from strategy_common import ContractError
from strategy_selftest import CONTROLS, load_bundle, run_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    root = parser.parse_args().root.resolve()

    bundle = load_bundle(root)
    survived = 0
    for name, mutate in CONTROLS:
        trial = copy.deepcopy(bundle)
        mutate(trial)
        tokens = trial.pop("_tokens", None)
        decisions = trial.pop("_decisions", None)
        try:
            run_pipeline(trial, tokens, decisions)
        except ContractError as error:
            print(f"[red] {name}\n       -> {error}\n")
        else:
            print(f"[SURVIVED] {name}\n")
            survived += 1
    return 2 if survived else 0


if __name__ == "__main__":
    raise SystemExit(main())
