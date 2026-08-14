#!/usr/bin/env python3
"""Print the actual refusal or keep-reason each planted control produces.

The selftest requires each raising control's message to contain the phrase its
own rule raises, and each keeping control to hold its resource *for the named
reason*. This prints both so a reader can check those needles are not vacuous.

Not part of run-all.sh; it is a diagnostic and its output is prose.
"""

from __future__ import annotations

import argparse
import copy
import tempfile
from pathlib import Path

from rgc_common import ContractError
from rgc_fixtures import build_tree
from rgc_selftest import KEEPING, RAISING, _actions, _run, load_inputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    root = parser.parse_args().root.resolve()

    base = load_inputs(root)
    survived = 0

    with tempfile.TemporaryDirectory(prefix="loopx-rgc-probe-") as tmp:
        print("=== controls that must refuse ===\n")
        for name, mutate, needle in RAISING:
            inputs = copy.deepcopy(base)
            mutate(inputs)
            tree = build_tree(Path(tmp) / f"r-{name}")
            try:
                _run(inputs, tree)
            except ContractError as error:
                mark = "red" if needle in str(error) else "WRONG REASON"
                print(
                    f"[{mark}] {name}\n        needle={needle!r}\n        -> {error}\n"
                )
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

        print("=== controls that must keep a resource ===\n")
        for name, mutate, resource_id, needle in KEEPING:
            inputs = copy.deepcopy(base)
            mutate(inputs)
            tree = build_tree(Path(tmp) / f"k-{name}")
            try:
                action = _actions(_run(inputs, tree)).get(resource_id)
            except Exception as error:  # noqa: BLE001
                print(
                    f"[BROKEN PROBE] {name}\n        -> {type(error).__name__}: {error}\n"
                )
                survived += 1
                continue
            ok = (
                action is not None
                and action["action"] == "KEEP"
                and needle in action["reason"]
            )
            print(
                f"[{'ok' if ok else 'WRONG'}] {name} ({resource_id})\n"
                f"        needle={needle!r}\n"
                f"        -> {action['action'] if action else 'ABSENT'}: "
                f"{action['reason'] if action else '-'}\n"
            )
            if not ok:
                survived += 1

    return 2 if survived else 0


if __name__ == "__main__":
    raise SystemExit(main())
