#!/usr/bin/env python3
"""Print what each server behaviour actually produces, state and reason.

The selftest asserts these states. This prints them side by side so a reader can
see the thing the module is arranged around: four behaviours, all producing an
empty findings list, landing in four different places.

Not part of run-all.sh; it is a diagnostic and its output is prose.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from lsp_common import ContractError
from lsp_pipeline import run_query
from lsp_query import to_code_truth_graph
from lsp_selftest import build_workspace_tree, load_inputs, server_argv

BEHAVIOURS = (
    ("clean file", "normal", "src/clean.py", None),
    ("file with a TODO", "normal", "src/app.py", None),
    ("server crash", "crash", "src/clean.py", None),
    ("server hang", "hang", "src/clean.py", None),
    ("exited zero, indexed nothing", "empty-on-fail", "src/clean.py", None),
    ("answers for another tree", "wrong-tree", "src/clean.py", "ws-beta"),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    root = parser.parse_args().root.resolve()

    inputs = load_inputs(root)
    argv = server_argv(root)
    collapsed = 0

    with tempfile.TemporaryDirectory(prefix="loopx-lsp-probe-") as tmp:
        tree = build_workspace_tree(Path(tmp) / "alpha")
        for label, behaviour, path, other in BEHAVIOURS:
            request = json.loads(json.dumps(inputs["request"]))
            request["path"] = path
            try:
                result = run_query(
                    request,
                    inputs["slots"],
                    inputs["limits"],
                    argv,
                    tree,
                    behaviour=behaviour,
                    timeout_s=1.0,
                    other_workspace_id=other,
                )["result"]
            except ContractError as error:
                print(f"[REFUSED]  {label}\n           -> {error}\n")
                continue
            graph = to_code_truth_graph(result)
            print(
                f"[{result['state']:>13}] {label}\n"
                f"                findings={len(result['findings'])} "
                f"admitted_to_graph={graph['admitted']}\n"
                f"                {result['reason'][:100]}\n"
            )
            if result["state"] == "CLEAN" and behaviour != "normal":
                collapsed += 1

    if collapsed:
        print(f"{collapsed} behaviour(s) collapsed into CLEAN", flush=True)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
