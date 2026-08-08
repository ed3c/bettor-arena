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

# Per platform, and deliberately NOT merged into one set of column names. The
# two CLIs do not mean the same thing by their fields: Claude reports cache reads
# and cache writes DISJOINT from input_tokens, while Codex's input_tokens already
# INCLUDES cached_input_tokens. Printing both under one header would invite
# subtracting numbers that are not comparable. The comparison that matters is
# guard-on vs guard-off WITHIN a platform, and that works fine per-platform.
CLAUDE_FIELDS = (
    ("input_tokens", "input"),
    ("cache_creation_input_tokens", "cache-write"),
    ("cache_read_input_tokens", "cache-read"),
    ("output_tokens", "output"),
)
CODEX_FIELDS = (
    ("input_tokens", "input(incl cached)"),
    ("cached_input_tokens", "cached-in"),
    ("cache_write_input_tokens", "cache-write"),
    ("output_tokens", "output"),
    ("reasoning_output_tokens", "reasoning"),
)
FIELDS = CLAUDE_FIELDS


def _read_claude(path: Path) -> dict | None:
    try:
        r = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return {
        "answer": r.get("result") or "",
        "turns": r.get("num_turns"),
        "cost": r.get("total_cost_usd"),
        "denials": len(r.get("permission_denials") or []),
        "usage": r.get("usage") or {},
        "failed": bool(r.get("is_error")),
    }


def _read_codex(path: Path) -> dict | None:
    """Codex writes JSONL events; usage lives on every `turn.completed`.

    `is_error` has no equivalent and must NOT be faked from the event types: a
    healthy run emits item.completed entries of type "error" for things like a
    hook-timeout note and a skills-budget note. Treating those as failures would
    discard every run and leave the arm looking uniformly broken. A run failed
    when it produced no agent message at all.
    """
    usage: dict[str, int] = {}
    answer = ""
    turns = 0
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "turn.completed":
            turns += 1
            for k, v in (ev.get("usage") or {}).items():
                if isinstance(v, int):
                    usage[k] = usage.get(k, 0) + v
        item = ev.get("item") or {}
        if item.get("type") == "agent_message":
            answer = item.get("text") or answer
    if not lines:
        # Empty is not unreadable. A run that never started (a rejected flag) and
        # a file that cannot be parsed send the reader to different places, and
        # calling both "unreadable" sent me to the parser when the answer was in
        # the .err file beside it.
        return {
            "answer": "",
            "turns": None,
            "cost": None,
            "denials": 0,
            "usage": {},
            "failed": True,
            "why": "the run produced no output at all",
        }
    return {
        "answer": answer,
        "turns": turns,
        "cost": None,
        "denials": 0,
        "usage": usage,
        "failed": not answer,
    }


def load_arm(
    d: Path, expect: str, platform: str = "claude"
) -> tuple[list[dict], list[dict]]:
    """Runs that answered correctly, and runs that did not."""
    reader, fields, pattern = (
        (_read_claude, CLAUDE_FIELDS, "run-*.json")
        if platform == "claude"
        else (_read_codex, CODEX_FIELDS, "run-*.jsonl")
    )
    good, bad = [], []
    for f in sorted(d.glob(pattern)):
        r = reader(f)
        if r is None:
            bad.append({"file": f.name, "why": "unreadable result file"})
            continue
        answer = r["answer"]
        row = {
            "file": f.name,
            "turns": r["turns"],
            "cost": r["cost"],
            "denials": r["denials"],
            "answer": answer.strip()[:80],
        }
        for key, _ in fields:
            row[key] = r["usage"].get(key, 0)
        if r["failed"] or expect not in answer:
            row["why"] = r.get("why") or (
                "produced no answer"
                if r["failed"]
                else "answer did not contain the expected path"
            )
            bad.append(row)
        else:
            good.append(row)
    return good, bad


def summarise(rows: list[dict], fields=FIELDS) -> dict:
    out = {}
    for key, _ in fields:
        out[key] = statistics.median(r[key] for r in rows)
    out["turns"] = statistics.median(r["turns"] for r in rows if r["turns"] is not None)
    # Codex reports no cost at all, so this list is empty for every codex run and
    # statistics.median raises on empty data. It crashed the whole report AFTER
    # printing a correct per-run table — the numbers were there and unreadable.
    # Absent stays absent rather than becoming a zero that reads as "free".
    costs = [r["cost"] for r in rows if r["cost"] is not None]
    out["cost"] = statistics.median(costs) if costs else None
    out["denials"] = statistics.median(r["denials"] for r in rows)
    return out


def report(base: Path, expect: str, platform: str = "claude") -> int:
    fields = CLAUDE_FIELDS if platform == "claude" else CODEX_FIELDS
    arms = {}
    for arm in ("off", "on"):
        d = base / arm
        if not d.is_dir():
            continue
        arms[arm] = load_arm(d, expect, platform)

    if not arms:
        print("no arm produced any run — nothing to compare", file=sys.stderr)
        return 2

    # Per-run first, medians second. Reading medians alone at n=1 pointed the
    # wrong way on two fields and the direction reversed at n=3; the runs
    # themselves showed why in one glance — three fields do not overlap between
    # arms and two do, which is the whole result. A summary that hides the spread
    # invites a claim the spread does not support.
    # Columns are driven by the platform's own field list. Hardcoding Claude's
    # names and pointing them at Codex's numbers would print `cache-read` over a
    # column Codex does not have, which is how two CLIs that disagree about what
    # `input_tokens` includes end up silently compared.
    head = "\n%-4s %-7s" % ("arm", "run") + "".join(
        " %>16s".replace(">", "") % lab for _, lab in fields
    )
    print(head + " %7s %9s" % ("turns", "cost$"))
    print("-" * len(head))
    for arm in ("off", "on"):
        if arm not in arms:
            continue
        for r in arms[arm][0] + arms[arm][1]:
            line = "%-4s %-7s" % (
                arm,
                r.get("file", "?").replace("run-", "").split(".")[0],
            )
            line += "".join(" %16d" % r.get(k, 0) for k, _ in fields)
            line += " %7s %9.4f  %s" % (
                r.get("turns"),
                r.get("cost") or 0.0,
                "counted" if "why" not in r else "NOT COUNTED",
            )
            print(line)

    head = "\n%-6s %6s" % ("arm", "counted") + "".join(
        " %16s" % lab for _, lab in fields
    )
    print(head + " %7s %9s" % ("turns", "cost$"))
    print("-" * len(head))
    summaries = {}
    for arm, (good, bad) in arms.items():
        if not good:
            print(
                "%-6s %6d   NO COUNTED RUNS — every run failed or answered wrong"
                % (arm, 0)
            )
            continue
        s = summarise(good, fields)
        summaries[arm] = s
        line = "%-6s %6d" % (arm, len(good))
        line += "".join(" %16d" % s[k] for k, _ in fields)
        line += " %7s %9.4f" % (s["turns"], s["cost"] or 0.0)
        print(line)

    for arm, (good, bad) in arms.items():
        for r in bad:
            print("  [not counted] %s/%s — %s" % (arm, r.get("file"), r.get("why")))
        if good:
            d = statistics.median(r["denials"] for r in good)
            print("  %s: median permission denials %s" % (arm, d))

    if len(summaries) == 2:
        off, on = summaries["off"], summaries["on"]
        print("\ndelta (on - off), median of counted runs:")
        for key, label in fields:
            diff = on[key] - off[key]
            base_v = off[key] or 1
            print("  %-18s %+9d  (%+.1f%%)" % (label, diff, 100.0 * diff / base_v))
        if off["cost"] is not None and on["cost"] is not None:
            print("  %-18s %+9.4f" % ("cost$", on["cost"] - off["cost"]))
        else:
            # Codex reports no cost field. Printing a zero delta would read as
            # "the money was the same", which is a claim, not an absence.
            print("  %-18s  not reported by this CLI" % "cost$")
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

    # Codex speaks JSONL and emits informational items typed "error". Reading
    # those as failures would discard every healthy run and make an arm look
    # uniformly broken, so the loader is tested against exactly that shape.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "on"
        d.mkdir()
        events = [
            {"type": "thread.started", "thread_id": "x"},
            {
                "type": "item.completed",
                "item": {"type": "error", "message": "hook timeout note"},
            },
            {"type": "turn.started"},
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": "loopctl/workflow.lock"},
            },
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 100,
                    "cached_input_tokens": 40,
                    "cache_write_input_tokens": 7,
                    "output_tokens": 5,
                    "reasoning_output_tokens": 3,
                },
            },
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 50,
                    "cached_input_tokens": 20,
                    "cache_write_input_tokens": 0,
                    "output_tokens": 2,
                    "reasoning_output_tokens": 1,
                },
            },
        ]
        (d / "run-1.jsonl").write_text("\n".join(json.dumps(e) for e in events))
        # No agent message at all IS a failure, unlike an "error" item.
        (d / "run-2.jsonl").write_text(
            json.dumps(
                {"type": "item.completed", "item": {"type": "error", "message": "boom"}}
            )
        )
        good, bad = load_arm(d, "loopctl/workflow.lock", "codex")
        case("codex-informational-error-item-is-not-a-failure", len(good), 1)
        case("codex-usage-sums-across-turns", good[0]["input_tokens"], 150)
        case("codex-turns-are-counted", good[0]["turns"], 2)
        case("codex-run-with-no-answer-is-excluded", len(bad), 1)
        case("codex-cost-is-absent-not-zero", good[0]["cost"], None)
        # summarise() over cost-less rows crashed the report after it had already
        # printed a correct table. The read side had a case for a missing cost;
        # the summary side did not, and one instance repaired is not the class.
        case(
            "codex-summary-survives-absent-cost",
            summarise(good, CODEX_FIELDS)["cost"],
            None,
        )

    if red == 0:
        print("SELFTEST GREEN")
        return 0
    print("SELFTEST RED", file=sys.stderr)
    return 2


if __name__ == "__main__":
    argv = sys.argv[1:]
    if argv[:1] == ["--selftest"]:
        sys.exit(_selftest())
    platform = "claude"
    if argv[:1] == ["--platform"]:
        platform = argv[1]
        argv = argv[2:]
    if len(argv) < 2:
        sys.exit(
            "usage: automode_report.py [--platform claude|codex] <results-dir> <expected-answer-substring>"
        )
    sys.exit(report(Path(argv[0]), argv[1], platform))
