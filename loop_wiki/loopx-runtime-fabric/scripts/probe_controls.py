#!/usr/bin/env python3
"""Print the actual error each contract control produces.

A green selftest only says every control turned red. It does not say each turned
red for the reason it was written for -- and a control failing for an unrelated
reason is a false negative wearing a green badge.

The physical controls are not here; they live in control_fabric.py, which
asserts on real filesystem state rather than on an exception message.
"""

from __future__ import annotations

import argparse
import copy
from pathlib import Path

from fabric_common import ContractError
from fabric_selftest import CONTROLS, _run_trial, load_bundle


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
        try:
            _run_trial(trial)
        except ContractError as error:
            print(f"[red] {name}\n       -> {error}\n")
        else:
            print(f"[SURVIVED] {name}\n")
            survived += 1
    return 2 if survived else 0


if __name__ == "__main__":
    raise SystemExit(main())
