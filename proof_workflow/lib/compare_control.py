#!/usr/bin/env python3
"""Compare a captured real run against what the macro proof claims to cover.

Called by control_macro_entry.sh with the run already captured; everything it
needs arrives in the environment so the shell never has to build JSON by hand.

The comparison is deliberately one-directional. A path the ENTRY POINT touches
and the proof does not cover is a gap in the proof — the proof would stay green
while that path rotted. A path the proof covers and the entry point never names
is not a gap: the macro loop is bigger than its activation step (hooks, gates,
the commit path), and the proof is supposed to cover more.

Exit: 0 no gap · 2 gap, or bootstrap itself exited non-zero · 64 unreadable input.

--selftest drives both verdicts on synthetic inputs, because a comparator that
has only ever been seen agreeing is not known to be able to disagree.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def read_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return [
        ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()
    ]


def covered(path: str, proof_paths: set[str]) -> bool:
    """A directory the entry point names counts as covered when the proof walks
    something inside it — bootstrap names `.githooks`, the proof covers
    `.githooks/pre-commit`, and that is real coverage, not a near miss."""
    return any(p == path or p.startswith(path.rstrip("/") + "/") for p in proof_paths)


def proof_coverage(receipt_dir: Path, short: str) -> dict[str, str]:
    """Every path covered by ANY proof at this commit, mapped to which proof.

    Not the macro receipt alone: the question is whether proof_workflow covers
    the path, and openwiki/.last-update.json is a terminus of the openwiki
    traversal. Charging that to the macro proof would invent a gap and push the
    fix in the wrong direction.
    """
    covered_by: dict[str, str] = {}
    for name in ("macro", "micro", "openwiki"):
        for candidate in (f"{name}-{short}.json", f"{name}-{short}-dirty.json"):
            path = receipt_dir / candidate
            if not path.is_file():
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            for step in data["steps"]:
                if step.get("path"):
                    covered_by.setdefault(step["path"], name)
            break
    return covered_by


def compare(rundir: Path, macro_receipt: Path, receipt_dir: Path, short: str) -> dict:
    macro = json.loads(macro_receipt.read_text(encoding="utf-8"))
    covered_by = proof_coverage(receipt_dir, short)
    proof_paths = set(covered_by)

    classes: dict[str, tuple[str, int]] = {}
    for line in read_lines(rundir / "path-class.txt"):
        rel, cls, rc = line.split("\t")
        classes[rel] = (cls, int(rc))
    named = read_lines(rundir / "named-paths.txt")
    unclassified = [p for p in named if p not in classes]
    if unclassified:
        raise ValueError(
            f"the probe produced no classification for {unclassified}; "
            "an unclassified path must never default to optional"
        )

    required_uncovered = [
        p for p in named if classes[p][0] == "required" and not covered(p, proof_paths)
    ]
    optional_uncovered = [
        p for p in named if classes[p][0] == "optional" and not covered(p, proof_paths)
    ]
    # Doctor-gated tools are not files, so no proof hashes them. They are covered
    # transitively: the macro proof RUNS bootstrap, and bootstrap exits 64 when
    # one is missing. That only holds while a green bootstrap step is actually in
    # the receipt, so it is checked rather than assumed.
    bootstrap_step = next(
        (s for s in macro["steps"] if s["id"] == "bootstrap" and s["state"] == "ran"),
        None,
    )
    tools_covered = bool(bootstrap_step) and bootstrap_step["exit"] == 0
    return {
        "entry_point_named_paths": {
            p: {"class": classes[p][0], "probe_exit": classes[p][1]} for p in named
        },
        "doctor_gated_tools": read_lines(rundir / "tools-named.txt"),
        "tools_covered_transitively_by_bootstrap_step": tools_covered,
        "message_lanes_fired": read_lines(rundir / "fired-lanes.txt"),
        "proof_covered_paths": {p: covered_by[p] for p in sorted(proof_paths)},
        "required_uncovered": required_uncovered,
        "optional_uncovered": optional_uncovered,
    }


def stream_manifest(rundir: Path) -> list[dict]:
    records = []
    for line in read_lines(rundir / "run.jsonl"):
        rec = json.loads(line)
        for lane in ("stdout", "stderr"):
            records.append(
                {
                    "step": rec["id"],
                    "path": f"{rundir.name}/{rec[lane]['path']}",
                    "sha256": rec[lane]["sha256"],
                    "bytes": rec[lane]["bytes"],
                }
            )
    return records


def main() -> int:
    try:
        rundir = Path(os.environ["CONTROL_RUNDIR"])
        macro_receipt = Path(os.environ["CONTROL_MACRO_RECEIPT"])
        receipt_path = Path(os.environ["CONTROL_RECEIPT"])
        run_id = os.environ["CONTROL_RUN_ID"]
        commit = os.environ["CONTROL_COMMIT"]
        bootstrap_rc = int(os.environ["CONTROL_BOOTSTRAP_RC"])
    except (KeyError, ValueError) as exc:
        print(f"control FATAL: bad invocation environment: {exc}", file=sys.stderr)
        return 64

    short = commit[:12]
    try:
        result = compare(rundir, macro_receipt, macro_receipt.parent, short)
    except ValueError as exc:
        print(f"control FATAL: {exc}", file=sys.stderr)
        return 64
    streams = stream_manifest(rundir)
    failed = (
        result["required_uncovered"]
        or not result["tools_covered_transitively_by_bootstrap_step"]
        or bootstrap_rc != 0
    )
    status = "failed" if failed else "passed"

    receipt = {
        "schema_version": "bettor-arena-control-macro-receipt@1.0.0",
        "control_of": "prove_macro_loop.sh",
        "method": "run the entry point for real, keep the trace, derive what it "
        "touches from its own source and its own output, compare against the "
        "macro receipt's covered paths",
        "run_id": run_id,
        "commit": commit,
        "status": status,
        "bootstrap_exit": bootstrap_rc,
        "compared_against": macro_receipt.name,
        "compared_against_dirty_stamp": macro_receipt.name.endswith("-dirty.json"),
        "capture_dir": f"proof_workflow/data/{run_id}",
        "capture_dir_tracked": False,
        "capture_note": "gitignored: gate stdout embeds this machine's absolute "
        "repo root. These sha256 are what binds the on-disk trace to this commit.",
        "captured_streams": streams,
        "comparison": result,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(
        f"control[macro-entry] captured {len(streams)} stream(s) under proof_workflow/data/{run_id}"
    )
    for lane in result["message_lanes_fired"]:
        print(f"  [fired] {lane}")
    if bootstrap_rc != 0:
        print(f"FAIL: bootstrap.sh exited {bootstrap_rc}", file=sys.stderr)
    for p, meta in result["entry_point_named_paths"].items():
        where = result["proof_covered_paths"].get(p)
        if where is None:
            where = next(
                (
                    v
                    for k, v in result["proof_covered_paths"].items()
                    if k.startswith(p.rstrip("/") + "/")
                ),
                None,
            )
        mark = f"covered by {where} proof" if where else "NOT covered"
        print(f"  [{meta['class']:8}] {p} — {mark}")
    if not result["tools_covered_transitively_by_bootstrap_step"]:
        print(
            "  GAP: the macro receipt has no green bootstrap step, so the doctor-gated "
            f"tools {result['doctor_gated_tools']} are covered by nothing",
            file=sys.stderr,
        )
    for p in result["required_uncovered"]:
        print(
            f"  GAP: {p} is REQUIRED (removing it changes bootstrap's exit) and no proof covers it",
            file=sys.stderr,
        )
    for p in result["optional_uncovered"]:
        print(
            f"  note: {p} is optional by the program's own behaviour and no proof covers it — reported, not a failure"
        )
    print(f"control[macro-entry] receipt={receipt_path.name} status={status}")
    return 0 if status == "passed" else 2


# ---------------------------------------------------------------- selftest


def _selftest() -> int:
    import tempfile

    red = 0

    def case(name: str, got, want) -> None:
        nonlocal red
        if got != want:
            print(
                f"SELFTEST case failed — {name}: got {got}, want {want}",
                file=sys.stderr,
            )
            red = 1

    proof = {"a/b.py", "c/d.txt"}
    case("exact-path-covered", covered("a/b.py", proof), True)
    case("directory-covered-by-child", covered("a", proof), True)
    case("directory-with-slash-covered", covered("a/", proof), True)
    case("uncovered-path-is-a-gap", covered("z/z.py", proof), False)
    # The failure that matters: a prefix that is not a path boundary must NOT
    # count as coverage, or `.grep` would be "covered" by `.grepai/index.gob`.
    case("prefix-is-not-coverage", covered("a/b", proof), False)

    with tempfile.TemporaryDirectory() as td:
        rundir = Path(td) / "run"
        (rundir / "streams").mkdir(parents=True)
        rdir = Path(td) / "receipts"
        rdir.mkdir()
        short = "0123456789ab"
        (rundir / "named-paths.txt").write_text(
            "a\nz/z.py\nopt/thing\n", encoding="utf-8"
        )
        (rundir / "path-class.txt").write_text(
            "a\trequired\t64\nz/z.py\trequired\t64\nopt/thing\toptional\t0\n",
            encoding="utf-8",
        )
        (rundir / "tools-named.txt").write_text("git\n", encoding="utf-8")
        (rundir / "fired-lanes.txt").write_text("bootstrap OK: x\n", encoding="utf-8")
        (rundir / "run.jsonl").write_text("", encoding="utf-8")
        macro = rdir / f"macro-{short}.json"
        macro.write_text(
            json.dumps(
                {
                    "steps": [
                        {
                            "id": "bootstrap",
                            "state": "ran",
                            "exit": 0,
                            "path": "bootstrap.sh",
                        },
                        {"id": "x", "state": "ran", "exit": 0, "path": "a/b.py"},
                        {"id": "y", "state": "read", "exit": None, "path": None},
                    ]
                }
            ),
            encoding="utf-8",
        )
        out = compare(rundir, macro, rdir, short)
        case("required-gap-detected", out["required_uncovered"], ["z/z.py"])
        case("covered-required-not-a-gap", "a" in out["required_uncovered"], False)
        case(
            "optional-uncovered-is-not-a-gap", out["optional_uncovered"], ["opt/thing"]
        )
        case(
            "tools-covered-by-green-bootstrap-step",
            out["tools_covered_transitively_by_bootstrap_step"],
            True,
        )
        case("null-path-step-ignored", None in out["proof_covered_paths"], False)

        # A sibling proof's coverage must count, or the control invents a gap
        # and points the fix at the wrong traversal.
        (rdir / f"openwiki-{short}.json").write_text(
            json.dumps(
                {
                    "steps": [
                        {
                            "id": "t",
                            "state": "present-at-head",
                            "exit": None,
                            "path": "z/z.py",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        out = compare(rundir, macro, rdir, short)
        case("sibling-proof-coverage-counts", out["required_uncovered"], [])

        # Remove the green bootstrap step: the transitive tool claim must die.
        macro.write_text(
            json.dumps(
                {"steps": [{"id": "x", "state": "ran", "exit": 0, "path": "a/b.py"}]}
            ),
            encoding="utf-8",
        )
        out = compare(rundir, macro, rdir, short)
        case(
            "tools-uncovered-without-bootstrap-step",
            out["tools_covered_transitively_by_bootstrap_step"],
            False,
        )

        # An unclassified path must FATAL, never default to optional.
        (rundir / "path-class.txt").write_text("a\trequired\t64\n", encoding="utf-8")
        try:
            compare(rundir, macro, rdir, short)
            case("unclassified-path-raises", False, True)
        except ValueError:
            case("unclassified-path-raises", True, True)

    print("SELFTEST " + ("GREEN" if not red else "RED"))
    return red


if __name__ == "__main__":
    if sys.argv[1:2] == ["--selftest"]:
        raise SystemExit(_selftest())
    raise SystemExit(main())
