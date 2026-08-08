#!/usr/bin/env python3
"""Read the paired auto-permission runs and say what actually differed.

    automode_report.py <results-dir> <expected-answer-substring>
    automode_report.py --selftest

Reports every token field separately rather than one total. A session pays a
large fixed cost before the task starts — a trivial turn already reads ~15k
cached tokens and writes ~28k of cache — so a single number would hide whether
an arm explored more or merely started up. What the reference document predicts
is growth in what the agent PULLED IN, and that lives in cache_creation and in
the turn count, not in the total.

Wrong answers are counted and excluded, never averaged in. An arm that is
refused everything spends less by failing, and a mean that mixes the two says
the guard saved tokens when it actually prevented the work.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

FIELDS = (
    ("input_tokens", "input"),
    ("cache_creation_input_tokens", "cache-write"),
    ("cache_read_input_tokens", "cache-read"),
    ("output_tokens", "output"),
)


def load_arm(d: Path, expect: str) -> tuple[list[dict], list[dict]]:
    """Runs that answered correctly, and runs that did not."""
    good, bad = [], []
    for f in sorted(d.glob("run-*.json")):
        try:
            r = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            bad.append({"file": f.name, "why": "unreadable result json"})
            continue
        answer = r.get("result") or ""
        row = {
            "file": f.name,
            "turns": r.get("num_turns"),
            "cost": r.get("total_cost_usd"),
            "denials": len(r.get("permission_denials") or []),
            "answer": answer.strip()[:80],
        }
        for key, _ in FIELDS:
            row[key] = (r.get("usage") or {}).get(key, 0)
        if r.get("is_error") or expect not in answer:
            row["why"] = (
                "error"
                if r.get("is_error")
                else "answer did not contain the expected path"
            )
            bad.append(row)
        else:
            good.append(row)
    return good, bad


def summarise(rows: list[dict]) -> dict:
    out = {}
    for key, _ in FIELDS:
        out[key] = statistics.median(r[key] for r in rows)
    out["turns"] = statistics.median(r["turns"] for r in rows if r["turns"] is not None)
    out["cost"] = statistics.median(r["cost"] for r in rows if r["cost"] is not None)
    out["denials"] = statistics.median(r["denials"] for r in rows)
    return out


def report(base: Path, expect: str) -> int:
    arms = {}
    for arm in ("off", "on"):
        d = base / arm
        if not d.is_dir():
            continue
        arms[arm] = load_arm(d, expect)

    if not arms:
        print("no arm produced any run — nothing to compare", file=sys.stderr)
        return 2

    # Per-run first, medians second. Reading medians alone at n=1 pointed the
    # wrong way on two fields and the direction reversed at n=3; the runs
    # themselves showed why in one glance — three fields do not overlap between
    # arms and two do, which is the whole result. A summary that hides the spread
    # invites a claim the spread does not support.
    print(
        "\n%-4s %-7s %12s %11s %8s %7s %9s"
        % ("arm", "run", "cache-write", "cache-read", "output", "turns", "cost$")
    )
    print("-" * 62)
    for arm in ("off", "on"):
        if arm not in arms:
            continue
        for r in arms[arm][0] + arms[arm][1]:
            print(
                "%-4s %-7s %12d %11d %8d %7s %9.4f  %s"
                % (
                    arm,
                    r.get("file", "?").replace("run-", "").replace(".json", ""),
                    r.get("cache_creation_input_tokens", 0),
                    r.get("cache_read_input_tokens", 0),
                    r.get("output_tokens", 0),
                    r.get("turns"),
                    r.get("cost") or 0.0,
                    "counted" if "why" not in r else "NOT COUNTED",
                )
            )

    print(
        "\n%-6s %6s %12s %11s %8s %7s %9s %8s"
        % (
            "arm",
            "counted",
            "cache-write",
            "cache-read",
            "input",
            "output",
            "turns",
            "cost$",
        )
    )
    print("-" * 74)
    summaries = {}
    for arm, (good, bad) in arms.items():
        if not good:
            print(
                "%-6s %6d   NO COUNTED RUNS — every run failed or answered wrong"
                % (arm, 0)
            )
            continue
        s = summarise(good)
        summaries[arm] = s
        print(
            "%-6s %6d %12d %11d %8d %7d %9s %8.4f"
            % (
                arm,
                len(good),
                s["cache_creation_input_tokens"],
                s["cache_read_input_tokens"],
                s["input_tokens"],
                s["output_tokens"],
                s["turns"],
                s["cost"],
            )
        )

    for arm, (good, bad) in arms.items():
        for r in bad:
            print("  [not counted] %s/%s — %s" % (arm, r.get("file"), r.get("why")))
        if good:
            d = statistics.median(r["denials"] for r in good)
            print("  %s: median permission denials %s" % (arm, d))

    if len(summaries) == 2:
        off, on = summaries["off"], summaries["on"]
        print("\ndelta (on - off), median of counted runs:")
        for key, label in FIELDS:
            diff = on[key] - off[key]
            base_v = off[key] or 1
            print("  %-12s %+9d  (%+.1f%%)" % (label, diff, 100.0 * diff / base_v))
        print("  %-12s %+9.4f" % ("cost$", on["cost"] - off["cost"]))
        # Stated, not implied: three runs cannot separate a small effect from
        # noise, and a table that looks precise invites reading it as if it could.
        n = min(len(arms["off"][0]), len(arms["on"][0]))
        print("\n  n=%d counted runs per arm. A difference smaller than the spread" % n)
        print("  between runs of the SAME arm is not evidence of anything.")
    elif not summaries:
        # Distinct from the one-arm case on purpose. "Only one arm answered" and
        # "neither arm answered" call for different next moves, and the first
        # version printed the former for both — a message that misnames the
        # failure sends the reader to the wrong place.
        print("\nNEITHER arm produced a counted run — this measured nothing at all")
        return 2
    else:
        print(
            "\nonly one arm has counted runs — there is no comparison here, just one measurement"
        )
        return 2
    return 0


def _selftest() -> int:
    red = 0

    def case(name, got, want):
        nonlocal red
        if got == want:
            print("  [ok]   %s" % name)
        else:
            print("  [RED]  %s — got %r, want %r" % (name, got, want), file=sys.stderr)
            red = 1

    import tempfile

    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "off"
        d.mkdir()
        usage = {
            "input_tokens": 1,
            "cache_creation_input_tokens": 100,
            "cache_read_input_tokens": 10,
            "output_tokens": 5,
        }
        (d / "run-1.json").write_text(
            json.dumps(
                {
                    "result": "loopctl/workflow.lock",
                    "usage": usage,
                    "num_turns": 3,
                    "total_cost_usd": 0.1,
                    "permission_denials": [],
                    "is_error": False,
                }
            )
        )
        # A cheap wrong answer must NOT be counted, or the guard looks free.
        (d / "run-2.json").write_text(
            json.dumps(
                {
                    "result": "I could not read the repository.",
                    "usage": usage,
                    "num_turns": 1,
                    "total_cost_usd": 0.01,
                    "permission_denials": [{"tool": "Bash"}],
                    "is_error": False,
                }
            )
        )
        # An errored run must not be counted either, however cheap.
        (d / "run-3.json").write_text(
            json.dumps(
                {
                    "result": "loopctl/workflow.lock",
                    "usage": usage,
                    "num_turns": 1,
                    "total_cost_usd": 0.0,
                    "permission_denials": [],
                    "is_error": True,
                }
            )
        )
        good, bad = load_arm(d, "loopctl/workflow.lock")
        case("correct-run-is-counted", len(good), 1)
        case("wrong-answer-and-error-are-excluded", len(bad), 2)
        case("denials-are-read-as-a-count", good[0]["denials"], 0)

        # One arm alone is a measurement, not a comparison, and must say so.
        case(
            "single-arm-is-not-a-comparison",
            report(Path(t), "loopctl/workflow.lock"),
            2,
        )

    if red == 0:
        print("SELFTEST GREEN")
        return 0
    print("SELFTEST RED", file=sys.stderr)
    return 2


if __name__ == "__main__":
    if sys.argv[1:2] == ["--selftest"]:
        sys.exit(_selftest())
    if len(sys.argv) < 3:
        sys.exit("usage: automode_report.py <results-dir> <expected-answer-substring>")
    sys.exit(report(Path(sys.argv[1]), sys.argv[2]))
