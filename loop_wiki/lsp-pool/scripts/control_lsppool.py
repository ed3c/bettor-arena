#!/usr/bin/env python3
"""Physical control group. Real server processes, real trees, real crashes.

The selftest already drives the fixture server as a subprocess. This group
exists for the claim underneath everything else in this module: that the four
ways a server can produce an empty findings list are actually distinguishable at
runtime, and that the pool tells them apart on real processes rather than on
fixtures describing processes.

Four controls, each running the server for real:

1. a clean file and a crashed server both produce zero findings -- and land in
   different states. Without this pair, every other check here is about one of
   them in isolation and the collapse it guards against is never demonstrated;
2. a hung server is SERVER_FAILED after a timeout, not CLEAN. The process really
   sleeps and is really killed;
3. a server answering for another workspace is refused, and the refusal happens
   before a well-formed result exists;
4. two workspaces with different content produce different findings through the
   same pool -- so the provenance on each is attributable to its own tree rather
   than to whichever slot was warm.

Exit: 0 all controls behaved, 2 one did not, 64 unusable environment.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lsp_common import BAD, OK, USAGE, ContractError, InputError  # noqa: E402
from lsp_pipeline import run_query  # noqa: E402
from lsp_selftest import load_inputs, server_argv  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    module_root = parser.parse_args().root.resolve()

    try:
        inputs = load_inputs(module_root)
    except InputError as exc:
        print(f"lsp-pool control FATAL: {exc}", file=sys.stderr)
        return USAGE

    argv = server_argv(module_root)
    failures: list[str] = []
    observed: dict[str, str] = {}

    with tempfile.TemporaryDirectory(prefix="loopx-lsp-control-") as tmp:
        base = Path(tmp)

        alpha = base / "alpha"
        (alpha / "src").mkdir(parents=True)
        (alpha / "src/app.py").write_text("a = 1\n", encoding="utf-8")

        beta = base / "beta"
        (beta / "src").mkdir(parents=True)
        (beta / "src/app.py").write_text("b = 2\n# TODO: beta only\n", encoding="utf-8")

        request = inputs["request"]
        slots, limits = inputs["slots"], inputs["limits"]

        # --- control 1: the pair that shows the collapse is real -------------
        clean = run_query(json.loads(json.dumps(request)), slots, limits, argv, alpha)
        crashed = run_query(
            json.loads(json.dumps(request)),
            slots,
            limits,
            argv,
            alpha,
            behaviour="crash",
        )
        observed["clean-file"] = clean["result"]["state"]
        observed["crashed-server"] = crashed["result"]["state"]

        if clean["result"]["findings"] or crashed["result"]["findings"]:
            failures.append("one of the pair returned findings; the pair must be empty")
        if clean["result"]["state"] == crashed["result"]["state"]:
            failures.append(
                f"a clean file and a crashed server both produced "
                f"{clean['result']['state']}; both return zero findings, and after "
                "they are rendered the same nobody can separate them again"
            )
        if clean["result"]["state"] != "CLEAN":
            failures.append(f"a clean file produced {clean['result']['state']}")
        if crashed["result"]["state"] != "SERVER_FAILED":
            failures.append(f"a crashed server produced {crashed['result']['state']}")

        # --- control 2: a hung process, really killed ------------------------
        started = time.monotonic()
        hung = run_query(
            json.loads(json.dumps(request)),
            slots,
            limits,
            argv,
            alpha,
            behaviour="hang",
            timeout_s=1.0,
        )
        elapsed = time.monotonic() - started
        observed["hung-server"] = hung["result"]["state"]
        if hung["result"]["state"] != "SERVER_FAILED":
            failures.append(f"a hung server produced {hung['result']['state']}")
        if elapsed < 0.5:
            failures.append(
                f"the hang control returned in {elapsed:.2f}s; the server cannot have "
                "actually hung, so the timeout path was not exercised"
            )
        if elapsed > 20:
            failures.append(f"the hang control took {elapsed:.1f}s; the timeout leaked")

        # --- control 3: an answer for the wrong tree -------------------------
        try:
            run_query(
                json.loads(json.dumps(request)),
                slots,
                limits,
                argv,
                alpha,
                behaviour="wrong-tree",
                other_workspace_id="ws-beta",
            )
        except ContractError as exc:
            observed["wrong-tree"] = "REFUSED"
            if "as authoritative as a correct one" not in str(exc):
                failures.append(f"the cross-worktree refusal read: {exc}")
        else:
            failures.append(
                "a server answering for another workspace produced a result; the "
                "response is well-formed in every other respect, which is the point"
            )

        # --- control 4: two trees, one pool, attributable answers ------------
        beta_request = json.loads(json.dumps(request))
        beta_request["request_id"] = "req-beta"
        beta_request["workspace"] = inputs["workspaces"][1]
        beta_result = run_query(beta_request, slots, limits, argv, beta)["result"]
        observed["beta-workspace"] = beta_result["state"]

        if beta_result["state"] != "FINDINGS":
            failures.append(
                f"the beta workspace produced {beta_result['state']}; its file has a "
                "TODO and alpha's does not, so this control cannot show attribution"
            )
        if beta_result["provenance"]["workspace_id"] != "ws-beta":
            failures.append("the beta result carried alpha's provenance")
        if (
            clean["result"]["provenance"]["workspace_id"]
            == (beta_result["provenance"]["workspace_id"])
        ):
            failures.append("two workspaces produced the same provenance")

    if failures:
        for line in failures:
            print(f"lsp-pool control RED: {line}", file=sys.stderr)
        return BAD

    print(
        json.dumps(
            {
                "module": "lsp-pool",
                "controls": [
                    "clean-file-and-crashed-server-land-in-different-states",
                    "hung-server-times-out-as-server-failed",
                    "answer-for-another-workspace-is-refused",
                    "two-trees-produce-attributable-provenance",
                ],
                "observed": observed,
                "state": "PASS",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return OK


if __name__ == "__main__":
    raise SystemExit(main())
