#!/usr/bin/env python3
"""Compare the rebuilt extractor against frozen legacy evidence held in-repo.

The peer used to be a gate input: this check read `antigravity/data.js` and
`automate.js` directly and returned 64 when they were absent. That made the
control resolve a sibling repository by its own path depth
(`ROOT.parents[2] / "antigravity"`), so it was green in the checkout that
happened to sit beside that peer and red in every worktree — an upward
resolution that can only ever pass in one place on one machine.

The evidence itself does not need the peer. The four load-bearing prompt bodies
were already frozen byte-for-byte in `profile/legacy-baseline.md`, and the one
thing that still required executing the legacy JavaScript — its topic-extractor
behaviour — is now frozen there too, as an input/output pair captured by running
that JavaScript rather than by recording what the rebuild returns. A baseline
written from the rebuild would compare the rebuild against itself.

The peer remains an *upgrade*, never a requirement: with `ANTIGRAVITY_PEER` set
and present, the frozen bytes are re-verified against it and a drift is a hard
failure. Absent, the frozen copy answers alone and the receipt line says so, so
a reader never has to guess which of the two evidence levels produced the green.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from equivalence import parse_gap_topics  # noqa: E402

BASELINE = ROOT / "profile" / "legacy-baseline.md"
PROFILE = ROOT / "profile" / "technical-equivalence.md"

FROZEN_BODIES = (
    "COMPLETENESS_RUBRIC",
    "PATH_B_REFINE_TEMPLATE",
    "SINGLE_GAP_QUERY",
    "BATCH_GAP_QUERY",
)
PROFILE_FRAGMENTS = (
    "P1 部署拓撲",
    "P9 可觀測性",
    "V1 核心主張與底層機制",
    "V5 實證／數據佐證",
    "技術實現等價物（必做）",
    "每一缺口都要給技術實現等價物",
)


class BaselineError(RuntimeError):
    pass


def frozen(baseline: str, name: str) -> str:
    start, end = f"<!-- {name}:START -->\n", f"\n<!-- {name}:END -->"
    if start not in baseline or end not in baseline:
        raise BaselineError(f"baseline markers absent: {name}")
    body = baseline.split(start, 1)[1].split(end, 1)[0]
    if not body.strip():
        raise BaselineError(f"baseline block empty: {name}")
    return body


def check(baseline: str, profile: str) -> list[str]:
    """Everything decidable from this repository alone."""
    failures = []
    missing = [x for x in PROFILE_FRAGMENTS if x not in profile]
    if missing:
        failures.append(f"profile fragment drift: {missing}")
    for name in FROZEN_BODIES:
        frozen(baseline, name)

    # The captured input carried a trailing newline that the marker convention
    # strips, and the extractor's last-line handling is exactly what this pair
    # pins — so it is restored explicitly rather than left to the reader.
    gap = frozen(baseline, "GAP_TOPICS_INPUT") + "\n"
    expected = json.loads(frozen(baseline, "GAP_TOPICS_OUTPUT"))
    observed, truncated = parse_gap_topics(gap)
    if observed != expected:
        failures.append(f"extractor drift: frozen={expected!r} rebuilt={observed!r}")
    if truncated:
        failures.append(f"frozen input unexpectedly truncated: {truncated!r}")
    return failures


def reverify_against_peer(peer: Path, baseline: str) -> tuple[str, list[str]]:
    """Optional stronger lane: the frozen bytes still match the live legacy.

    Returns (state, failures). A peer that is absent is `not_bound`, never a
    failure — absence of the upgrade is not evidence of drift, and conflating
    the two is what made this an unrunnable check outside one directory.
    """
    data, automate = peer / "data.js", peer / "automate.js"
    if not data.is_file() or not automate.is_file():
        return "not_bound", []

    failures = []
    data_source = data.read_text(encoding="utf-8")
    automate_source = automate.read_text(encoding="utf-8")
    source = data_source + automate_source
    missing = [x for x in PROFILE_FRAGMENTS if x not in source]
    if missing:
        failures.append(f"peer fragment drift: {missing}")

    def legacy_const(name: str) -> str | None:
        match = re.search(rf"export const {name} = `(.*?)`;", data_source, re.S)
        return match.group(1) if match else None

    queries = re.findall(
        r"const q = `(基於以下「已知相關資訊」.*?\$\{reportMd\})`;",
        automate_source,
        re.S,
    )
    live = {
        "COMPLETENESS_RUBRIC": legacy_const("COMPLETENESS_RUBRIC"),
        "PATH_B_REFINE_TEMPLATE": legacy_const("PATH_B_REFINE_TEMPLATE"),
        "SINGLE_GAP_QUERY": queries[0] if len(queries) == 2 else None,
        "BATCH_GAP_QUERY": queries[1] if len(queries) == 2 else None,
    }
    for name, body in live.items():
        if body is None:
            failures.append(f"peer no longer exposes {name}")
        elif body != frozen(baseline, name):
            failures.append(f"frozen body no longer matches peer: {name}")

    gap = frozen(baseline, "GAP_TOPICS_INPUT") + "\n"
    env = dict(os.environ, GAP_TEXT=gap)
    script = (
        f'import {{parseGapTopics}} from "{data.resolve().as_uri()}"; '
        "console.log(JSON.stringify(parseGapTopics(process.env.GAP_TEXT)));"
    )
    legacy = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if legacy.returncode != 0:
        # node absent or the module stopped loading: the peer is bound but this
        # lane could not run, which is neither a pass nor a drift.
        return "bound_extractor_not_run", failures
    if json.loads(legacy.stdout) != json.loads(frozen(baseline, "GAP_TOPICS_OUTPUT")):
        failures.append("frozen extractor output no longer matches peer")
    return "bound_reverified", failures


def controls() -> list[str]:
    """A green that cannot be shown to go red is not evidence of anything."""
    baseline = BASELINE.read_text(encoding="utf-8")
    profile = PROFILE.read_text(encoding="utf-8")
    red = []

    planted = (
        ("profile-fragment", baseline, profile.replace("P9 可觀測性", "P9 X", 1)),
        (
            "extractor-output",
            baseline.replace(
                'Observability evidence and eval pipeline"]',
                'something else"]',
                1,
            ),
            profile,
        ),
        (
            "extractor-input",
            baseline.replace("1. Durable packet state", "1. Renamed packet state", 1),
            profile,
        ),
    )
    for name, mutated_baseline, mutated_profile in planted:
        if mutated_baseline == baseline and mutated_profile == profile:
            red.append(f"{name} control could not be planted")
        elif not check(mutated_baseline, mutated_profile):
            red.append(f"{name} control stayed green")

    for name in FROZEN_BODIES + ("GAP_TOPICS_INPUT", "GAP_TOPICS_OUTPUT"):
        removed = baseline.replace(f"<!-- {name}:START -->", "<!-- X:START -->", 1)
        if removed == baseline:
            red.append(f"missing-block control could not be planted: {name}")
            continue
        try:
            check(removed, profile)
        except BaselineError:
            continue
        red.append(f"missing-block control stayed green: {name}")
    return red


def main(argv: list[str]) -> int:
    baseline = BASELINE.read_text(encoding="utf-8")
    profile = PROFILE.read_text(encoding="utf-8")
    try:
        failures = check(baseline, profile)
    except BaselineError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    peer_state, peer_failures = "not_requested", []
    configured = os.environ.get("ANTIGRAVITY_PEER")
    if configured:
        peer_state, peer_failures = reverify_against_peer(
            Path(configured).resolve(), baseline
        )
        failures.extend(peer_failures)

    if "--selftest" in argv:
        broken = controls()
        if broken:
            print(f"FAIL: red controls did not fire: {broken}", file=sys.stderr)
            return 2

    if failures:
        for line in failures:
            print(f"FAIL: {line}", file=sys.stderr)
        return 2
    print(
        f"PASS: four legacy prompt bodies frozen in-repo and the rebuilt topic "
        f"extractor matches the captured legacy output (peer={peer_state})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
