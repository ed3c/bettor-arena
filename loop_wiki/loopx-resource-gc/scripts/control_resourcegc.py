#!/usr/bin/env python3
"""Physical control group. Real trees, real rebuilds, a real process.

The selftest already runs against a real tree. This group exists for the one
claim the selftest asserts but does not *demonstrate*: that a `DIVERGENT`
projection is worth keeping.

The demonstration matters because the alternative reading is very reasonable.
The rebuild command exists, it runs, it exits zero, and it produces an index --
so the projection is rebuildable and deleting it costs nothing. Control 3 below
deletes it anyway and then rebuilds, and shows the original content does not come
back. That is the cost, measured rather than argued.

Four controls:

1. the three proof states are reached against a real filesystem, and the digests
   are printed so a reader can see PROVEN really is byte equality;
2. a PROVEN projection deleted and rebuilt comes back identical -- without this,
   control 3's loss could be blamed on the rebuild machinery rather than on the
   divergence;
3. a DIVERGENT projection deleted and rebuilt comes back *different*, and the
   original bytes are unrecoverable;
4. a real process still holding a resource turns the run red instead of PASS.

Exit: 0 all controls behaved, 2 one did not, 64 unusable environment.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rgc_common import BAD, OK, USAGE, ContractError, load_json, text_digest  # noqa: E402
from rgc_fixtures import build_tree  # noqa: E402
from rgc_pipeline import run_gc  # noqa: E402
from rgc_rebuild import prove  # noqa: E402

SLEEPER = "import time; time.sleep(120)"


def _content(root: Path, relative: str) -> str:
    path = root / relative
    if not path.exists():
        return ""
    return text_digest(
        b"".join(sorted(p.read_bytes() for p in path.rglob("*") if p.is_file()))
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    module_root = parser.parse_args().root.resolve()

    good = module_root / "tests/fixtures/good"
    try:
        specs = load_json(good / "rebuild-specs.json")
        resources = load_json(good / "resources.json")
        config = load_json(good / "config.json")
    except Exception as exc:  # noqa: BLE001
        print(f"resource-gc control FATAL: {exc}", file=sys.stderr)
        return USAGE

    by_id = {spec["resource_id"]: spec for spec in specs}
    failures: list[str] = []
    printed: dict[str, dict[str, str]] = {}

    with tempfile.TemporaryDirectory(prefix="loopx-rgc-control-") as tmp:
        base = Path(tmp)

        # --- control 1: the three states, on a real filesystem ---------------
        root = build_tree(base / "proofs")
        expected = {
            "vector-stale": "PROVEN",
            "graph-divergent": "DIVERGENT",
            "lsp-unprovable": "UNPROVABLE",
        }
        for resource_id, want in expected.items():
            proof = prove(by_id[resource_id], root)
            printed[resource_id] = {
                "state": proof["state"],
                "original": (proof["original_digest"] or "")[:23],
                "rebuilt": (proof["rebuilt_digest"] or "-")[:23],
            }
            if proof["state"] != want:
                failures.append(
                    f"{resource_id} proved {proof['state']}, expected {want}"
                )
        if printed.get("vector-stale", {}).get("original") != printed.get(
            "vector-stale", {}
        ).get("rebuilt"):
            failures.append(
                "PROVEN was reported without the digests matching; PROVEN is byte "
                "equality and nothing else"
            )
        if printed.get("graph-divergent", {}).get("original") == printed.get(
            "graph-divergent", {}
        ).get("rebuilt"):
            failures.append("DIVERGENT was reported with identical digests")

        # --- control 2: a PROVEN projection really does come back ------------
        proven_root = build_tree(base / "proven")
        before = _content(proven_root, "data/resource-gc/vector-stale")
        shutil.rmtree(proven_root / "data/resource-gc/vector-stale")
        rebuilt = proven_root / "data/resource-gc/vector-stale"
        completed = subprocess.run(
            ["python3", "tools/rebuild_vector.py", str(rebuilt)],
            cwd=str(proven_root),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if completed.returncode != 0:
            failures.append(
                f"rebuilding a PROVEN projection failed: {completed.stderr}"
            )
        elif _content(proven_root, "data/resource-gc/vector-stale") != before:
            failures.append(
                "a PROVEN projection did not come back identical; control 3's loss "
                "could then be blamed on the rebuild machinery rather than on "
                "divergence"
            )

        # --- control 3: what deleting a DIVERGENT projection actually costs --
        divergent_root = build_tree(base / "divergent")
        original = _content(divergent_root, "data/resource-gc/graph-divergent")
        shutil.rmtree(divergent_root / "data/resource-gc/graph-divergent")
        target = divergent_root / "data/resource-gc/graph-divergent"
        subprocess.run(
            ["python3", "tools/rebuild_divergent.py", str(target)],
            cwd=str(divergent_root),
            capture_output=True,
            text=True,
            timeout=30,
        )
        recovered = _content(divergent_root, "data/resource-gc/graph-divergent")
        if recovered == original:
            failures.append(
                "deleting the DIVERGENT projection and rebuilding recovered the "
                "original, so this control cannot demonstrate the loss it exists for"
            )

        # And the GC, given the same tree, keeps it.
        keep_root = build_tree(base / "kept")
        result = run_gc(
            config["root_id"],
            resources,
            set(config["held_leases"]),
            set(config["live_subjects"]),
            specs,
            config["admitted"],
            config["authorized_by"],
            config["now"],
            config["max_age_s"],
            keep_root,
            apply=True,
        )
        if not (keep_root / "data/resource-gc/graph-divergent").exists():
            failures.append("the GC deleted the DIVERGENT projection")
        if not result["receipt"]["tombstones"]:
            failures.append("the GC removed resources without leaving tombstones")

        # --- control 4: a real process holding a resource --------------------
        holder = subprocess.Popen(
            [sys.executable, "-c", SLEEPER], start_new_session=True
        )
        try:
            deadline = time.monotonic() + 5
            while holder.poll() is not None and time.monotonic() < deadline:
                time.sleep(0.05)
            residue_root = build_tree(base / "residue")
            try:
                run_gc(
                    config["root_id"],
                    resources,
                    set(config["held_leases"]),
                    set(config["live_subjects"]),
                    specs,
                    config["admitted"],
                    config["authorized_by"],
                    config["now"],
                    config["max_age_s"],
                    residue_root,
                    apply=True,
                    live_processes={holder.pid},
                    claimed={"processes": [holder.pid]},
                )
            except ContractError as exc:
                if "still held" not in str(exc):
                    failures.append(f"residue refused for the wrong reason: {exc}")
            else:
                failures.append(
                    f"a run left process {holder.pid} running and still reported "
                    "success"
                )
        finally:
            holder.kill()
            holder.wait(timeout=10)

    if failures:
        for line in failures:
            print(f"resource-gc control RED: {line}", file=sys.stderr)
        return BAD

    print(
        json.dumps(
            {
                "module": "loopx-resource-gc",
                "controls": [
                    "three-proof-states-reached-on-a-real-filesystem",
                    "proven-projection-comes-back-identical",
                    "divergent-projection-does-not-come-back",
                    "live-process-turns-the-run-red",
                ],
                "proofs": printed,
                "state": "PASS",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return OK


if __name__ == "__main__":
    raise SystemExit(main())
