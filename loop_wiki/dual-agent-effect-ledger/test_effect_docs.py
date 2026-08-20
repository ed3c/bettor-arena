#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
README = ROOT / "README.md"
AGENTS = ROOT / "AGENTS.md"
INDEX = ROOT / "stack-index.json"

EXPECTED = {
    "DA-EF-C": (216, "f9b64994979042fc3726c524944a61da4f9cb8b5", "e0f0ff4bf0b55627b420ace027043c3b7fee5d1d", 32269722930),
    "DA-EF-K": (224, "6b99815d2b3fb76436c05641b32d1e7be1a36ec4", "ac7dba91541dfb8c1bcbc1d4f9bc7d2726735eac", 32274232055),
    "DA-EF-P": (225, "ba9ebfe5f4efa01d040ec3b51f93b32045899b23", "a128ea330647d9a3c83f7852eb7174bcdbbd6511", 32274465651),
    "DA-EF-A": (226, "ee7b99080e71c834c979ba56fb2d9a3f6c7c27db", "67ed1df8a447e1e4ac958a819203ecf5d4ce8020", 32274717005),
    "DA-EF-COMP": (227, "50f0e5ca7a9a2860d7429f00f3a7b3189910ba08", "40ae3458df32137fdb1b05e42e7985f5607b5715", 32274943051),
    "DA-EF-E": (228, "5ba49cc935c059a8fd96e78773c3df9a2ab9be4c", "6eb20d4289d7296be7348c70aa8618e2d8a9aecc", 32275372163),
}


class DocsError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (f": {detail}" if detail else ""))


def refuse(code: str, detail: str = "") -> None:
    raise DocsError(code, detail)


def expect(code: str, fn: Callable[[], Any]) -> None:
    try:
        fn()
    except DocsError as exc:
        if exc.code != code:
            raise AssertionError(f"expected {code}, got {exc}") from exc
        print(f"{code}: RED/{code}")
    else:
        raise AssertionError(f"{code}: planted control survived")


def load_index() -> dict[str, Any]:
    return json.loads(INDEX.read_text(encoding="utf-8"))


def validate_index(value: dict[str, Any]) -> None:
    if value.get("schema") != "bettor-arena/dual-agent-effect-ledger/stack-index/v1":
        refuse("STACK_INDEX_SCHEMA_MISMATCH")
    if value.get("canonical_task_writer") != "loopx-ledger":
        refuse("TASK_WRITER_DRIFT")
    if value.get("canonical_effect_writer") != "dual-agent-effect-ledger":
        refuse("EFFECT_WRITER_DRIFT")
    if value.get("evidence_ceiling") != "COMPLETE_DETERMINISTIC_EFFECT_MATRIX_ONLY":
        refuse("EVIDENCE_CEILING_DRIFT")

    rows = value.get("effect_stack")
    if not isinstance(rows, list) or {row.get("atom") for row in rows} != set(EXPECTED):
        refuse("STACK_DENOMINATOR_DRIFT")
    by_atom = {row["atom"]: row for row in rows}
    for atom, (pr, head, tree, run) in EXPECTED.items():
        row = by_atom[atom]
        if (row.get("pr"), row.get("head"), row.get("tree"), row.get("ci_run")) != (pr, head, tree, run):
            refuse("STACK_SUBJECT_DRIFT", atom)
        if row.get("ci_state") != "SUCCESS" or row.get("state") != "CLOSED_DETERMINISTIC":
            refuse("STACK_STATE_DRIFT", atom)
        if atom == "DA-EF-E" and row.get("denominator_cases") != 16:
            refuse("STACK_DENOMINATOR_DRIFT")

    substrate = value.get("substrate_reference")
    if not isinstance(substrate, dict):
        refuse("SUBSTRATE_ROUTE_DRIFT")
    if substrate.get("pr") != 196 or substrate.get("reuse_mode") != "REFERENCE_SUBSTRATE_ONLY" or substrate.get("writer_authority") != "NONE":
        refuse("SUBSTRATE_AUTHORITY_PROMOTION")

    live = value.get("live_frontier")
    if not isinstance(live, dict) or live.get("issue") != 223:
        refuse("LIVE_FRONTIER_DRIFT")
    if live.get("state") != "NOT_EXERCISED" or live.get("admission") != "HUMAN_TRUSTED_AUTHORITY_REQUIRED":
        refuse("FIXTURE_AS_LIVE_PASS")

    external = value.get("external_states")
    if not isinstance(external, dict):
        refuse("EXTERNAL_STATE_DRIFT")
    for key, state in external.items():
        expected = "NOT_PERFORMED" if key in {"merge", "release"} else "NOT_EXERCISED"
        if state != expected:
            refuse("EXTERNAL_STATE_PROMOTION", key)


def validate_docs(readme: str, agents: str) -> None:
    required_readme = (
        "canonical effect writer = dual-agent-effect-ledger",
        "canonical **task** writer",
        "REFERENCE_SUBSTRATE_ONLY",
        "PR #228 DA-EF-E",
        "#223 DA-EF-LIVE",
        "COMPLETE_DETERMINISTIC_EFFECT_MATRIX_ONLY",
        "skipped",
        "RESULT_UNKNOWN != EFFECT_COMMITTED",
    )
    for text in required_readme:
        if text not in readme:
            refuse("README_ROUTE_MISSING", text)

    required_agents = (
        "canonical task writer   loopx-ledger",
        "canonical effect writer dual-agent-effect-ledger",
        "REFERENCE_SUBSTRATE_ONLY",
        "HUMAN_TRUSTED_AUTHORITY_REQUIRED",
        "skipped workflow    for PASS",
        "RESULT_UNKNOWN != EFFECT_COMMITTED",
        "COMPLETE_DETERMINISTIC_EFFECT_MATRIX_ONLY",
    )
    for text in required_agents:
        if text not in agents:
            refuse("AGENT_ROUTE_MISSING", text)

    forbidden_promotions = (
        "#223 DA-EF-LIVE\nreal reversible provider effect + readback\n        PASS",
        "provider I/O\n        PASS",
        "target readback\n        PASS",
        "release\n        PASS",
    )
    for text in forbidden_promotions:
        if text in readme or text in agents:
            refuse("DOCS_FALSE_PROMOTION", text)


def main() -> int:
    readme = README.read_text(encoding="utf-8")
    agents = AGENTS.read_text(encoding="utf-8")
    index = load_index()
    validate_index(index)
    validate_docs(readme, agents)
    print("P1: PASS exact Stack subjects + deterministic evidence ceiling")
    print("P2: PASS single task/effect writer routes")
    print("P3: PASS PR #196 reference-only substrate route")
    print("P4: PASS #223 live frontier remains Human-gated / NOT_EXERCISED")

    bad = json.loads(json.dumps(index)); bad["canonical_effect_writer"] = "provider-demo"
    expect("EFFECT_WRITER_DRIFT", lambda: validate_index(bad))

    bad = json.loads(json.dumps(index)); bad["substrate_reference"]["writer_authority"] = "dual-agent-effect-ledger"
    expect("SUBSTRATE_AUTHORITY_PROMOTION", lambda: validate_index(bad))

    bad = json.loads(json.dumps(index)); bad["live_frontier"]["state"] = "LIVE_PASS"
    expect("FIXTURE_AS_LIVE_PASS", lambda: validate_index(bad))

    bad = json.loads(json.dumps(index)); bad["external_states"]["provider_io"] = "PASS"
    expect("EXTERNAL_STATE_PROMOTION", lambda: validate_index(bad))

    bad = json.loads(json.dumps(index)); bad["effect_stack"][-1]["denominator_cases"] = 15
    expect("STACK_DENOMINATOR_DRIFT", lambda: validate_index(bad))

    bad = json.loads(json.dumps(index)); bad["effect_stack"][1]["head"] = "0" * 40
    expect("STACK_SUBJECT_DRIFT", lambda: validate_index(bad))

    expect("README_ROUTE_MISSING", lambda: validate_docs(readme.replace("REFERENCE_SUBSTRATE_ONLY", "REFERENCE_ONLY", 1), agents))
    expect("AGENT_ROUTE_MISSING", lambda: validate_docs(readme, agents.replace("HUMAN_TRUSTED_AUTHORITY_REQUIRED", "AUTO", 1)))

    print("PASS: DA-EF-D docs/Agent/Stack traceability controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
