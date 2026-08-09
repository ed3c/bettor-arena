#!/usr/bin/env python3
"""Run the legacy topic extractor and compare load-bearing prompt fragments."""

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


def main() -> int:
    peer = Path(os.environ.get("ANTIGRAVITY_PEER", ROOT.parents[2] / "antigravity"))
    data = peer / "data.js"
    automate = peer / "automate.js"
    if not data.is_file() or not automate.is_file():
        print(f"NOT_EXERCISED: legacy peer absent: {peer}", file=sys.stderr)
        return 64
    profile = (ROOT / "profile" / "technical-equivalence.md").read_text(
        encoding="utf-8"
    )
    baseline = (ROOT / "profile" / "legacy-baseline.md").read_text(encoding="utf-8")
    data_source = data.read_text(encoding="utf-8")
    automate_source = automate.read_text(encoding="utf-8")
    source = data_source + automate_source
    fragments = [
        "P1 部署拓撲",
        "P9 可觀測性",
        "V1 核心主張與底層機制",
        "V5 實證／數據佐證",
        "技術實現等價物（必做）",
        "每一缺口都要給技術實現等價物",
    ]
    missing_source = [x for x in fragments if x not in source]
    missing_profile = [x for x in fragments if x not in profile]
    if missing_source or missing_profile:
        print(
            f"FAIL: fragment drift source={missing_source} profile={missing_profile}",
            file=sys.stderr,
        )
        return 2

    def legacy_const(name: str) -> str:
        match = re.search(rf"export const {name} = `(.*?)`;", data_source, re.S)
        if not match:
            raise ValueError(f"legacy const absent: {name}")
        return match.group(1)

    def frozen(name: str) -> str:
        start, end = f"<!-- {name}:START -->\n", f"\n<!-- {name}:END -->"
        if start not in baseline or end not in baseline:
            raise ValueError(f"baseline markers absent: {name}")
        return baseline.split(start, 1)[1].split(end, 1)[0]

    queries = re.findall(
        r"const q = `(基於以下「已知相關資訊」.*?\$\{reportMd\})`;",
        automate_source,
        re.S,
    )
    if len(queries) != 2:
        print(
            f"FAIL: expected two legacy gap queries, found {len(queries)}",
            file=sys.stderr,
        )
        return 2
    exact = {
        "COMPLETENESS_RUBRIC": legacy_const("COMPLETENESS_RUBRIC"),
        "PATH_B_REFINE_TEMPLATE": legacy_const("PATH_B_REFINE_TEMPLATE"),
        "SINGLE_GAP_QUERY": queries[0],
        "BATCH_GAP_QUERY": queries[1],
    }
    drift = [name for name, body in exact.items() if body != frozen(name)]
    if drift:
        print(f"FAIL: byte-exact legacy baseline drift: {drift}", file=sys.stderr)
        return 2
    gap = "前言\n研究題目清單\n1. Durable packet state implementation\n2）Retry and rollback production mechanism\n題目三：Observability evidence and eval pipeline\n"
    env = dict(os.environ)
    env["GAP_TEXT"] = gap
    module_url = data.resolve().as_uri()
    script = f'import {{parseGapTopics}} from "{module_url}"; console.log(JSON.stringify(parseGapTopics(process.env.GAP_TEXT)));'
    legacy = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if legacy.returncode != 0:
        print(
            f"FAIL: legacy parseGapTopics did not run: {legacy.stderr}", file=sys.stderr
        )
        return 2
    old = json.loads(legacy.stdout)
    new, truncated = parse_gap_topics(gap)
    if old != new or truncated:
        print(
            f"FAIL: topic extractor drift old={old!r} new={new!r} truncated={truncated!r}",
            file=sys.stderr,
        )
        return 2
    print(
        "PASS: four legacy prompt bodies are byte-exact and legacy/new topic extractors agree"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
