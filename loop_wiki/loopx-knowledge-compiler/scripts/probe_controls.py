#!/usr/bin/env python3
"""Print the actual refusal each planted control produces.

The selftest already requires each control's message to contain the phrase its
own rule raises, so a control passing for an unrelated reason fails there. This
prints the messages so a reader can check that requirement is not itself
matching something vacuous -- a needle so generic it appears in every error is a
substring test that never disagrees.

Not part of run-all.sh; it is a diagnostic and its output is prose.
"""

from __future__ import annotations

import argparse
import copy
import tempfile
from pathlib import Path

from kc_common import ContractError
from kc_selftest import CONTROLS, _compile, _load


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    root = parser.parse_args().root.resolve()

    base = _load(root)
    survived = 0
    with tempfile.TemporaryDirectory(prefix="loopx-kc-probe-") as tmp:
        for index, (name, mutate, needle) in enumerate(CONTROLS):
            bundle = copy.deepcopy(base)
            mutate(bundle)
            try:
                _compile(bundle, Path(tmp) / f"probe-{index}")
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
    return 2 if survived else 0


if __name__ == "__main__":
    raise SystemExit(main())
