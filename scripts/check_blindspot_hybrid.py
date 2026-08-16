#!/usr/bin/env python3
"""Validate bettor-arena's consumer-owned Blindspot Hybrid binding."""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
from typing import Any

OK, FAIL, INVALID, MECHANISM = 0, 2, 64, 70
SCHEMA = "bettor-arena/blindspot-hybrid-binding/v1"
REQUIRED = {"grepai", "scip", "tree-sitter", "serena", "source-readback", "test", "sqlite", "lancedb"}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
EXPECTED = {
    "scip": ("scip-code/scip", "5890b2ac1c0970c5606b71c833b733cffd091c90", "Apache-2.0"),
    "tree-sitter": ("tree-sitter/tree-sitter", "dff1fd868c750dbbae179fcd5c43ce987e4e0528", "MIT"),
    "lancedb": ("lancedb/lancedb", "928c3dde2dd94173931632bde06062e786e495be", "Apache-2.0"),
}
ROLES = {
    "grepai": "intent-anchor-and-runtime-mcp-exploration",
    "scip": "compiler-indexed-symbol-relation-candidate",
    "tree-sitter": "ast-structure-and-coverage",
    "serena": "symbol-aware-agent-executor",
    "source-readback": "current-source-admission",
    "test": "targeted-behavior-observation",
    "sqlite": "authoritative-event-link-admission-ledger",
    "lancedb": "rebuildable-similarity-projection",
}

class Bad(ValueError): pass
class Broken(RuntimeError): pass

def canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canon(value).encode()).hexdigest()

def load(path: Path) -> Any:
    try: return json.loads(path.read_text())
    except FileNotFoundError as exc: raise Bad(f"ABSENT: {path}") from exc
    except json.JSONDecodeError as exc: raise Bad(f"UNREADABLE_JSON: {path}: {exc}") from exc
    except OSError as exc: raise Broken(str(exc)) from exc

def validate(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, dict): raise Bad("binding must be an object")
    failures: list[dict[str, str]] = []
    def fail(code: str, detail: str) -> None: failures.append({"code": code, "detail": detail})
    if value.get("schema") != SCHEMA: raise Bad(f"schema must be {SCHEMA}")
    subject = value.get("subject")
    if not isinstance(subject, dict): raise Bad("subject must be an object")
    for key in ("base_commit", "base_tree"):
        if not isinstance(subject.get(key), str) or not SHA40.fullmatch(subject[key]): fail("MUTABLE_SUBJECT", key)
    replacement = value.get("replacement", {})
    if replacement.get("code_graph_rag") != "RETIRED_FROM_ACTIVE_COMPOSITION": fail("CODE_GRAPH_RAG_NOT_RETIRED", "replacement state")
    lanes = value.get("active_lanes")
    if not isinstance(lanes, dict): raise Bad("active_lanes must be an object")
    if set(lanes) != REQUIRED: fail("ACTIVE_LANE_SET_INVALID", ",".join(sorted(set(lanes) ^ REQUIRED)))
    if "code-graph-rag" in lanes or "code_graph_rag" in lanes: fail("CODE_GRAPH_RAG_ACTIVE", "legacy graph lane present")
    for lane, role in ROLES.items():
        if not isinstance(lanes.get(lane), dict) or lanes[lane].get("role") != role: fail("LANE_ROLE_INVALID", lane)
    authority = value.get("authority", {})
    if authority.get("observation_ledger") != "sqlite": fail("SQLITE_NOT_AUTHORITY", "observation_ledger")
    if authority.get("vector_projection") != "lancedb": fail("VECTOR_PROJECTION_INVALID", "vector_projection")
    if authority.get("provider_self_admission") is not False: fail("PROVIDER_SELF_ADMISSION_ENABLED", "authority")
    if authority.get("source_claim_admission") != ["source-readback"]: fail("SOURCE_READBACK_GATE_INVALID", "source claims")
    if authority.get("behavior_claim_admission") != ["source-readback", "test"]: fail("BEHAVIOR_GATE_INVALID", "behavior claims")
    lancedb = lanes.get("lancedb", {})
    if lancedb.get("authority") is not False or lancedb.get("rebuildable") is not True or lancedb.get("source_lane") != "sqlite": fail("LANCEDB_AUTHORITY_VIOLATION", "projection contract")
    if lanes.get("grepai", {}).get("evidence_ceiling") != "B+_CANDIDATE": fail("GREPAI_EXACTNESS_OVERCLAIM", "evidence ceiling")
    for lane, (repository, commit, license_id) in EXPECTED.items():
        item = lanes.get(lane, {})
        if (item.get("source_repository"), item.get("source_commit"), item.get("license")) != (repository, commit, license_id): fail("SOURCE_PIN_INVALID", lane)
    for lane, item in lanes.items():
        if isinstance(item, dict) and item.get("runtime_state") not in {"NOT_CONFIGURED", "NOT_EXERCISED"}: fail("RUNTIME_STATE_OVERCLAIM", lane)
    effects = value.get("effects", {})
    if not isinstance(effects, dict) or any(item is not False for item in effects.values()): fail("EFFECT_OVERCLAIM", "all static-binding effects must be false")
    return sorted(failures, key=canon)

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--binding", type=Path, required=True); parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    try:
        value = load(args.binding); failures = validate(value)
        receipt = {"schema": "bettor-arena/blindspot-hybrid-binding-receipt/v1", "binding_sha256": digest(value), "state": "FAIL" if failures else "PASS", "runtime_state": "NOT_EXERCISED", "effects": {"providers_invoked": False, "mcp_started": False, "database_created": False, "forgejo_contacted": False}, "failures": failures}
        if args.receipt:
            args.receipt.parent.mkdir(parents=True, exist_ok=True); args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
        print(canon(receipt), file=sys.stderr if failures else sys.stdout)
        return FAIL if failures else OK
    except Bad as exc: print(f"INVALID: {exc}", file=sys.stderr); return INVALID
    except (Broken, OSError) as exc: print(f"MECHANISM_ERROR: {exc}", file=sys.stderr); return MECHANISM
if __name__ == "__main__": raise SystemExit(main())
