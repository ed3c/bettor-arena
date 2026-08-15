#!/usr/bin/env python3
"""Print the actual refusal each planted control produces.

The selftest requires each control's message to contain the phrase its own rule
raises. This prints the messages so a reader can check those needles are not
themselves vacuous.

Lease collisions surface as refusals inside the cycle rather than as exceptions
-- one task colliding must not stop the fleet -- so this looks in both places
and says which one answered.

Not part of run-all.sh; it is a diagnostic and its output is prose.
"""

from __future__ import annotations

import argparse
import copy
from pathlib import Path

from wf_common import ContractError
from wf_selftest import CONTROLS, _cycle, load_inputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    root = parser.parse_args().root.resolve()

    base = load_inputs(root)
    survived = 0
    for name, mutate, needle in CONTROLS:
        inputs = copy.deepcopy(base)
        mutate(inputs)
        try:
            cycle = _cycle(inputs)
        except ContractError as error:
            mark = "red" if needle in str(error) else "WRONG REASON"
            print(
                f"[{mark} raised] {name}\n        needle={needle!r}\n        -> {error}\n"
            )
            if mark != "red":
                survived += 1
            continue
        except Exception as error:  # noqa: BLE001
            print(
                f"[BROKEN PROBE] {name}\n        -> {type(error).__name__}: {error}\n"
            )
            survived += 1
            continue

        refusals = "; ".join(row["reason"] for row in cycle["lease_refusals"])
        if needle in refusals:
            print(
                f"[red refused] {name}\n        needle={needle!r}\n        -> {refusals}\n"
            )
        else:
            print(f"[SURVIVED] {name}\n        refusals={refusals or '(none)'}\n")
            survived += 1
    return 2 if survived else 0


if __name__ == "__main__":
    raise SystemExit(main())
