#!/usr/bin/env python3
"""Print the actual refusal or outcome each planted control produces.

The selftest requires each raising control's message to contain the phrase its
own rule raises, and each outcome control to reach its expected verdict *for a
reason naming why*. This prints both so a reader can check those needles are not
themselves vacuous.

Not part of run-all.sh; it is a diagnostic and its output is prose.
"""

from __future__ import annotations

import argparse
import copy
from pathlib import Path

from se_common import ContractError
from se_selftest import (
    OUTCOME_CONTROLS,
    RAISING_CONTROLS,
    _evaluate,
    load_inputs,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    root = parser.parse_args().root.resolve()

    base = load_inputs(root)
    survived = 0

    print("=== controls that must refuse ===\n")
    for name, mutate, needle in RAISING_CONTROLS:
        inputs = copy.deepcopy(base)
        mutate(inputs)
        try:
            _evaluate(inputs)
        except ContractError as error:
            mark = "red" if needle in str(error) else "WRONG REASON"
            print(f"[{mark}] {name}\n        needle={needle!r}\n        -> {error}\n")
            if mark != "red":
                survived += 1
        except Exception as error:  # noqa: BLE001
            print(
                f"[BROKEN PROBE] {name}\n        -> {type(error).__name__}: {error}\n"
            )
            survived += 1
        else:
            print(f"[SURVIVED] {name}\n")
            survived += 1

    print("=== controls that must reach a verdict ===\n")
    for name, mutate, expected, needle in OUTCOME_CONTROLS:
        inputs = copy.deepcopy(base)
        mutate(inputs)
        try:
            decision = _evaluate(inputs)["decision"]
        except Exception as error:  # noqa: BLE001
            print(
                f"[BROKEN PROBE] {name}\n        -> {type(error).__name__}: {error}\n"
            )
            survived += 1
            continue
        ok = decision["outcome"] == expected and any(
            needle in reason for reason in decision["reasons"]
        )
        print(
            f"[{'ok' if ok else 'WRONG'}] {name}\n"
            f"        expected={expected} got={decision['outcome']}\n"
            f"        needle={needle!r}\n"
            f"        -> {decision['reasons']}\n"
        )
        if not ok:
            survived += 1

    return 2 if survived else 0


if __name__ == "__main__":
    raise SystemExit(main())
