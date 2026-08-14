#!/usr/bin/env python3
"""Evidence-bound LoopX decision-memory admission compiler.

This program validates proposals and Human decisions and emits a candidate
capsule. It never persists a durable memory event, writes a provider index,
updates repository documentation, advances LoopX state or performs Human Admit.

Exit codes: 0 checked-clean, 2 checked refusal, 64 usage/infrastructure failure.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any

PROPOSAL = "loopx/memory-proposal/v1"
DECISION = "loopx/memory-admission-decision/v1"
CAPSULE = "loopx/memory-capsule/v1"
DELETION = "loopx/memory-deletion-receipt/v1"
SHA = re.compile(r"^sha256:[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
FORBIDDEN_TEXT = re.compile(
    r"(?:chain[- ]of[- ]thought|thought stream|private reasoning|hidden reasoning|"
    r"BEGIN [A-Z ]*PRIVATE KEY|api[_ -]?key\s*[:=]|password\s*[:=]|bearer\s+[A-Za-z0-9._-]+)",
    re.I,
)


class ContractError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise OSError(f"missing JSON: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise OSError(f"unreadable JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"object required: {path}")
    return value


def exact(value: dict[str, Any], keys: set[str], label: str) -> None:
    if set(value) != keys:
        raise ContractError(
            f"{label}: key drift missing={sorted(keys - set(value))} "
            f"extra={sorted(set(value) - keys)}"
        )


def timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise ContractError(f"{label}: timestamp required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError(f"{label}: invalid timestamp") from exc
    if parsed.tzinfo is None:
        raise ContractError(f"{label}: timezone required")
    return parsed.astimezone(timezone.utc)


def relative(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ContractError(f"{label}: non-empty path required")
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts:
        raise ContractError(f"{label}: absolute/traversal path refused")
    return normalized


def validate_subject(value: dict[str, Any]) -> None:
    exact(value, {"repository", "commit", "tree", "task_id"}, "subject")
    if not isinstance(value["repository"], str) or "/" not in value["repository"]:
        raise ContractError("subject.repository")
    if not isinstance(value["commit"], str) or not HEX40.fullmatch(value["commit"]):
        raise ContractError("subject.commit")
    if not isinstance(value["tree"], str) or not HEX40.fullmatch(value["tree"]):
        raise ContractError("subject.tree")
    if not isinstance(value["task_id"], str) or len(value["task_id"]) < 3:
        raise ContractError("subject.task_id")


def validate_retention(value: dict[str, Any], kind: str, created: datetime | None = None) -> None:
    exact(value, {"max_age_seconds", "expires_at", "review_required_at"}, "retention")
    age = value["max_age_seconds"]
    if not isinstance(age, int) or not 60 <= age <= 31_536_000:
        raise ContractError("retention.max_age_seconds")
    expires = timestamp(value["expires_at"], "retention.expires_at")
    review = timestamp(value["review_required_at"], "retention.review_required_at")
    if review > expires:
        raise ContractError("review must not follow expiry")
    if created is not None:
        if expires <= created or review <= created:
            raise ContractError("retention must be after decision")
        if expires - created > timedelta(seconds=age, minutes=1):
            raise ContractError("expiry exceeds declared max age")
    if kind == "HYPOTHESIS" and age > 2_592_000:
        raise ContractError("hypothesis retention exceeds 30 days")


def validate_proposal(value: dict[str, Any]) -> None:
    exact(
        value,
        {"schema_version", "proposal_id", "subject", "kind", "statement", "canonical_key", "epistemic", "evidence_refs", "scope", "retention", "privacy", "conflict", "producer"},
        "proposal",
    )
    if value["schema_version"] != PROPOSAL:
        raise ContractError("proposal schema")
    validate_subject(value["subject"])
    if value["kind"] not in {"DEAD_END", "CODEBASE_QUIRK", "HYPOTHESIS", "DECISION", "INCIDENT_POINTER", "PROJECT_PREFERENCE"}:
        raise ContractError("proposal kind")
    statement = value["statement"]
    if not isinstance(statement, str) or not 8 <= len(statement) <= 4096:
        raise ContractError("statement length")
    if FORBIDDEN_TEXT.search(statement):
        raise ContractError("private reasoning or secret-shaped statement refused")
    if not isinstance(value["canonical_key"], str) or len(value["canonical_key"]) < 8:
        raise ContractError("canonical_key")
    epistemic = value["epistemic"]
    exact(epistemic, {"claim_kind", "verification", "confidence", "falsifier"}, "epistemic")
    if epistemic["claim_kind"] not in {"OBSERVATION", "INFERENCE", "HYPOTHESIS", "NORMATIVE"}:
        raise ContractError("claim_kind")
    if epistemic["verification"] not in {"SUPPORTED", "TESTED", "CONTESTED", "UNCHECKED"}:
        raise ContractError("verification")
    if epistemic["confidence"] not in {"LOW", "MEDIUM", "HIGH"}:
        raise ContractError("confidence")
    if not isinstance(epistemic["falsifier"], str) or not epistemic["falsifier"].strip():
        raise ContractError("falsifier")
    if (value["kind"] == "HYPOTHESIS" or epistemic["claim_kind"] == "HYPOTHESIS") and epistemic["confidence"] == "HIGH":
        raise ContractError("hypothesis cannot be HIGH")
    evidence = value["evidence_refs"]
    if not isinstance(evidence, list) or not evidence:
        raise ContractError("evidence required")
    ids: set[str] = set()
    test_backed = False
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            raise ContractError(f"evidence[{index}]")
        exact(item, {"evidence_id", "kind", "digest", "locator", "subject_commit"}, f"evidence[{index}]")
        if item["evidence_id"] in ids:
            raise ContractError("duplicate evidence_id")
        ids.add(item["evidence_id"])
        if item["kind"] not in {"SOURCE_SPAN", "TEST_RESULT", "RUNTIME_RECEIPT", "ADR", "INCIDENT", "COUNTEREXAMPLE"}:
            raise ContractError("evidence kind")
        if not isinstance(item["digest"], str) or not SHA.fullmatch(item["digest"]):
            raise ContractError("evidence digest")
        if not isinstance(item["locator"], str) or not item["locator"]:
            raise ContractError("evidence locator")
        if item["subject_commit"] != value["subject"]["commit"]:
            raise ContractError("evidence subject drift")
        test_backed |= item["kind"] in {"TEST_RESULT", "RUNTIME_RECEIPT"}
    if epistemic["verification"] == "TESTED" and not test_backed:
        raise ContractError("TESTED requires test/runtime artifact")
    scope = value["scope"]
    exact(scope, {"valid_from_commit", "paths", "symbols", "invalidated_by"}, "scope")
    if scope["valid_from_commit"] != value["subject"]["commit"]:
        raise ContractError("scope commit drift")
    if not isinstance(scope["paths"], list) or not isinstance(scope["symbols"], list):
        raise ContractError("scope paths/symbols")
    for index, path in enumerate(scope["paths"]):
        relative(path, f"scope.paths[{index}]")
    if not isinstance(scope["invalidated_by"], list) or not scope["invalidated_by"]:
        raise ContractError("scope invalidation criteria required")
    validate_retention(value["retention"], value["kind"])
    privacy = value["privacy"]
    exact(privacy, {"classification", "contains_private_reasoning", "contains_secret_value", "redaction_state"}, "privacy")
    if privacy["contains_private_reasoning"] is not False or privacy["contains_secret_value"] is not False:
        raise ContractError("privacy boundary")
    if privacy["classification"] not in {"PUBLIC", "INTERNAL", "SENSITIVE_POINTER_ONLY"}:
        raise ContractError("privacy classification")
    if privacy["redaction_state"] not in {"PASS", "NOT_REQUIRED"}:
        raise ContractError("redaction state")
    conflict = value["conflict"]
    exact(conflict, {"state", "known_conflicts", "current_repository_wins"}, "conflict")
    if conflict["current_repository_wins"] is not True:
        raise ContractError("current repository must outrank memory")
    if conflict["state"] not in {"NONE", "OPEN", "UNKNOWN"}:
        raise ContractError("conflict state")
    if conflict["state"] == "OPEN" and not conflict["known_conflicts"]:
        raise ContractError("open conflict requires refs")
    producer = value["producer"]
    exact(producer, {"actor_class", "receipt_ref"}, "producer")
    if producer["actor_class"] not in {"WORKER", "GATE", "HUMAN", "SYSTEM"}:
        raise ContractError("producer actor")
    if not isinstance(producer["receipt_ref"], str) or not SHA.fullmatch(producer["receipt_ref"]):
        raise ContractError("producer receipt")


def validate_decision(value: dict[str, Any], proposal: dict[str, Any]) -> None:
    exact(value, {"schema_version", "decision_id", "proposal_digest", "subject", "decision", "authority", "rationale_artifact_ref", "retention_override", "created_at"}, "decision")
    if value["schema_version"] != DECISION:
        raise ContractError("decision schema")
    validate_subject(value["subject"])
    if value["subject"] != proposal["subject"] or value["proposal_digest"] != digest(proposal):
        raise ContractError("decision subject/proposal mismatch")
    if value["decision"] not in {"ADMIT", "REJECT", "DEFER", "CONFLICT"}:
        raise ContractError("decision")
    authority = value["authority"]
    exact(authority, {"kind", "signer_id", "authority_receipt_ref"}, "decision.authority")
    if authority["kind"] != "HUMAN" or not isinstance(authority["signer_id"], str) or len(authority["signer_id"]) < 3:
        raise ContractError("Human authority required")
    if not isinstance(authority["authority_receipt_ref"], str) or not SHA.fullmatch(authority["authority_receipt_ref"]):
        raise ContractError("authority receipt")
    if not isinstance(value["rationale_artifact_ref"], str) or not SHA.fullmatch(value["rationale_artifact_ref"]):
        raise ContractError("rationale artifact")
    created = timestamp(value["created_at"], "decision.created_at")
    if value["retention_override"] is not None:
        if not isinstance(value["retention_override"], dict):
            raise ContractError("retention override")
        validate_retention(value["retention_override"], proposal["kind"], created)


def stable_id(canonical_key: str) -> str:
    return "memory-" + hashlib.sha256(canonical_key.encode("utf-8")).hexdigest()[:16]


def compile_capsule(proposal: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    validate_proposal(proposal)
    validate_decision(decision, proposal)
    if decision["decision"] not in {"ADMIT", "CONFLICT"}:
        raise ContractError("REJECT/DEFER cannot compile a capsule")
    retention = decision["retention_override"] or proposal["retention"]
    created = timestamp(decision["created_at"], "decision.created_at")
    validate_retention(retention, proposal["kind"], created)
    contested = decision["decision"] == "CONFLICT" or proposal["conflict"]["state"] == "OPEN" or proposal["epistemic"]["verification"] == "CONTESTED"
    capsule = {
        "schema_version": CAPSULE,
        "stable_id": stable_id(proposal["canonical_key"]),
        "canonical_key": proposal["canonical_key"],
        "revision": 1,
        "status": "CANDIDATE_CONTESTED" if contested else "CANDIDATE_ACTIVE",
        "proposal_digest": digest(proposal),
        "subject": proposal["subject"],
        "kind": proposal["kind"],
        "statement": proposal["statement"],
        "epistemic": proposal["epistemic"],
        "evidence_refs": proposal["evidence_refs"],
        "scope": proposal["scope"],
        "retention": retention,
        "privacy": proposal["privacy"],
        "conflict": {"state": "OPEN" if contested else "NONE", "known_conflicts": proposal["conflict"]["known_conflicts"], "current_repository_wins": True},
        "decision_ref": {"decision_id": decision["decision_id"], "decision_digest": digest(decision), "authority_receipt_ref": decision["authority"]["authority_receipt_ref"]},
        "projections": [
            {"provider": "mem0", "state": "NOT_CONFIGURED", "authority": "REBUILDABLE_CACHE"},
            {"provider": "vector", "state": "NOT_CONFIGURED", "authority": "REBUILDABLE_CACHE"},
            {"provider": "graph", "state": "NOT_CONFIGURED", "authority": "REBUILDABLE_CACHE"}
        ],
        "authority": {"canonical_store": "LOOPX_MEMORY_LEDGER", "state_writer": "TRUSTED_REDUCER", "model_write": False, "persisted": False},
        "created_at": decision["created_at"]
    }
    validate_capsule(capsule, proposal, decision)
    return capsule


def validate_capsule(value: dict[str, Any], proposal: dict[str, Any] | None = None, decision: dict[str, Any] | None = None) -> None:
    exact(value, {"schema_version", "stable_id", "canonical_key", "revision", "status", "proposal_digest", "subject", "kind", "statement", "epistemic", "evidence_refs", "scope", "retention", "privacy", "conflict", "decision_ref", "projections", "authority", "created_at"}, "capsule")
    if value["schema_version"] != CAPSULE or value["stable_id"] != stable_id(value["canonical_key"]):
        raise ContractError("capsule identity")
    validate_subject(value["subject"])
    if value["status"] not in {"CANDIDATE_ACTIVE", "CANDIDATE_CONTESTED"}:
        raise ContractError("capsule status")
    authority = value["authority"]
    exact(authority, {"canonical_store", "state_writer", "model_write", "persisted"}, "capsule.authority")
    if authority != {"canonical_store": "LOOPX_MEMORY_LEDGER", "state_writer": "TRUSTED_REDUCER", "model_write": False, "persisted": False}:
        raise ContractError("capsule authority escalation")
    conflict = value["conflict"]
    exact(conflict, {"state", "known_conflicts", "current_repository_wins"}, "capsule.conflict")
    if conflict["current_repository_wins"] is not True:
        raise ContractError("memory cannot outrank repository")
    if value["status"] == "CANDIDATE_CONTESTED" and conflict["state"] != "OPEN":
        raise ContractError("contested capsule must preserve conflict")
    if value["status"] == "CANDIDATE_ACTIVE" and conflict["state"] != "NONE":
        raise ContractError("active capsule conflict mismatch")
    if FORBIDDEN_TEXT.search(value["statement"]):
        raise ContractError("capsule private reasoning/secret")
    for projection in value["projections"]:
        exact(projection, {"provider", "state", "authority"}, "projection")
        if projection["authority"] != "REBUILDABLE_CACHE":
            raise ContractError("projection became canonical")
    if proposal is not None and (value["proposal_digest"] != digest(proposal) or value["subject"] != proposal["subject"]):
        raise ContractError("capsule proposal mismatch")
    if decision is not None and value["decision_ref"]["decision_digest"] != digest(decision):
        raise ContractError("capsule decision mismatch")


def validate_deletion(value: dict[str, Any]) -> None:
    exact(value, {"schema_version", "capsule_id", "subject", "deletion_event_ref", "authority", "projections", "deleted_at"}, "deletion")
    if value["schema_version"] != DELETION or not re.fullmatch(r"memory-[0-9a-f]{16}", value["capsule_id"]):
        raise ContractError("deletion identity")
    validate_subject(value["subject"])
    if not isinstance(value["deletion_event_ref"], str) or not SHA.fullmatch(value["deletion_event_ref"]):
        raise ContractError("deletion event")
    authority = value["authority"]
    exact(authority, {"kind", "signer_id", "authority_receipt_ref"}, "deletion.authority")
    if authority["kind"] != "HUMAN" or not isinstance(authority["authority_receipt_ref"], str) or not SHA.fullmatch(authority["authority_receipt_ref"]):
        raise ContractError("deletion Human authority")
    timestamp(value["deleted_at"], "deleted_at")
    for projection in value["projections"]:
        exact(projection, {"provider", "state", "residue_count"}, "deletion projection")
        if projection["state"] in {"PASS", "NOT_CONFIGURED"} and projection["residue_count"] != 0:
            raise ContractError("projection deletion residue")


def root() -> Path:
    return Path(__file__).resolve().parents[1]


def check_contracts() -> list[str]:
    failures: list[str] = []
    ids: set[str] = set()
    schemas = sorted((root() / "contracts").glob("*.schema.json"))
    if len(schemas) != 4:
        failures.append(f"schema count={len(schemas)} expected=4")
    for path in schemas:
        try:
            value = load(path)
            if value.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                failures.append(f"schema draft: {path.name}")
            schema_id = value.get("$id")
            if not isinstance(schema_id, str) or schema_id in ids:
                failures.append(f"schema id: {path.name}")
            ids.add(str(schema_id))
        except (ContractError, OSError) as exc:
            failures.append(str(exc))
    try:
        manifest = load(root() / "contracts/manifest.json")
        exact(manifest, {"schema_version", "memory_proposal_schema", "memory_capsule_schema", "admission_decision_schema", "deletion_receipt_schema"}, "manifest")
        if manifest["schema_version"] != "loopx/decision-memory-contract-manifest/v1":
            failures.append("manifest schema")
        for key, relative_path in manifest.items():
            if key.endswith("_schema") and not (root() / "contracts" / relative_path).is_file():
                failures.append(f"manifest missing: {relative_path}")
    except (ContractError, OSError) as exc:
        failures.append(str(exc))
    return failures


def good_bundle() -> tuple[dict[str, Any], dict[str, Any]]:
    created = datetime(2026, 8, 14, 0, 0, tzinfo=timezone.utc)
    commit = "1" * 40
    subject = {"repository": "ed3c/bettor-arena", "commit": commit, "tree": "2" * 40, "task_id": "decision-memory-fixture"}
    retention = {"max_age_seconds": 604800, "expires_at": (created + timedelta(days=7)).isoformat().replace("+00:00", "Z"), "review_required_at": (created + timedelta(days=3)).isoformat().replace("+00:00", "Z")}
    proposal = {
        "schema_version": PROPOSAL,
        "proposal_id": "proposal-dead-end-001",
        "subject": subject,
        "kind": "DEAD_END",
        "statement": "The attempted direct import violates the public module boundary for this exact subject.",
        "canonical_key": "DEAD_END|public-module-boundary|src/example.py|" + commit,
        "epistemic": {"claim_kind": "OBSERVATION", "verification": "TESTED", "confidence": "HIGH", "falsifier": "A current exact-subject control demonstrates the import through an admitted public port."},
        "evidence_refs": [
            {"evidence_id": "EV-test-public-boundary", "kind": "TEST_RESULT", "digest": "sha256:" + "3" * 64, "locator": "tests/test_boundary.py::test_private_import_rejected", "subject_commit": commit},
            {"evidence_id": "EV-source-public-port", "kind": "SOURCE_SPAN", "digest": "sha256:" + "4" * 64, "locator": "loopctl/contract.json#public-port", "subject_commit": commit}
        ],
        "scope": {"valid_from_commit": commit, "paths": ["src/example.py"], "symbols": ["example.private_import"], "invalidated_by": ["module interface change", "public port change", "test contract change"]},
        "retention": retention,
        "privacy": {"classification": "INTERNAL", "contains_private_reasoning": False, "contains_secret_value": False, "redaction_state": "PASS"},
        "conflict": {"state": "NONE", "known_conflicts": [], "current_repository_wins": True},
        "producer": {"actor_class": "GATE", "receipt_ref": "sha256:" + "5" * 64}
    }
    decision = {
        "schema_version": DECISION,
        "decision_id": "decision-admit-001",
        "proposal_digest": digest(proposal),
        "subject": subject,
        "decision": "ADMIT",
        "authority": {"kind": "HUMAN", "signer_id": "reviewer-fixture", "authority_receipt_ref": "sha256:" + "6" * 64},
        "rationale_artifact_ref": "sha256:" + "7" * 64,
        "retention_override": None,
        "created_at": created.isoformat().replace("+00:00", "Z")
    }
    return proposal, decision


def selftest() -> None:
    failures = check_contracts()
    if failures:
        raise ContractError(f"contract baseline failed: {failures}")
    proposal, decision = good_bundle()
    capsule = compile_capsule(proposal, decision)
    if capsule["status"] != "CANDIDATE_ACTIVE" or capsule["authority"]["persisted"] is not False:
        raise ContractError("positive capsule failed")
    mutations = 0

    def reject_proposal(value: dict[str, Any]) -> None:
        nonlocal mutations
        try:
            validate_proposal(value)
        except ContractError:
            mutations += 1
            return
        raise ContractError("proposal mutation accepted")

    value = copy.deepcopy(proposal); value["private_reasoning"] = "hidden"; reject_proposal(value)
    value = copy.deepcopy(proposal); value["statement"] = "chain-of-thought: hidden"; reject_proposal(value)
    value = copy.deepcopy(proposal); value["evidence_refs"] = []; reject_proposal(value)
    value = copy.deepcopy(proposal); value["conflict"]["current_repository_wins"] = False; reject_proposal(value)
    value = copy.deepcopy(proposal); value["scope"]["paths"] = ["../escape"]; reject_proposal(value)
    value = copy.deepcopy(proposal); value["epistemic"]["verification"] = "TESTED"; value["evidence_refs"] = [value["evidence_refs"][1]]; reject_proposal(value)
    value = copy.deepcopy(proposal); value["kind"] = "HYPOTHESIS"; value["epistemic"]["claim_kind"] = "HYPOTHESIS"; value["epistemic"]["confidence"] = "HIGH"; reject_proposal(value)
    value = copy.deepcopy(proposal); value["kind"] = "HYPOTHESIS"; value["epistemic"]["claim_kind"] = "HYPOTHESIS"; value["epistemic"]["confidence"] = "LOW"; value["retention"]["max_age_seconds"] = 31536000; reject_proposal(value)
    value = copy.deepcopy(proposal); value["evidence_refs"][0]["subject_commit"] = "9" * 40; reject_proposal(value)
    value = copy.deepcopy(proposal); value["privacy"]["contains_secret_value"] = True; reject_proposal(value)

    bad_decision = copy.deepcopy(decision); bad_decision["authority"]["kind"] = "MODEL"
    try:
        validate_decision(bad_decision, proposal)
    except ContractError:
        mutations += 1
    else:
        raise ContractError("model authority accepted")

    bad_decision = copy.deepcopy(decision); bad_decision["proposal_digest"] = "sha256:" + "0" * 64
    try:
        validate_decision(bad_decision, proposal)
    except ContractError:
        mutations += 1
    else:
        raise ContractError("proposal digest drift accepted")

    rejected = copy.deepcopy(decision); rejected["decision"] = "REJECT"
    try:
        compile_capsule(proposal, rejected)
    except ContractError:
        mutations += 1
    else:
        raise ContractError("rejected proposal compiled")

    conflict_proposal = copy.deepcopy(proposal)
    conflict_proposal["conflict"] = {"state": "OPEN", "known_conflicts": ["ADR-42"], "current_repository_wins": True}
    conflict_proposal["epistemic"]["verification"] = "CONTESTED"
    conflict_decision = copy.deepcopy(decision)
    conflict_decision["proposal_digest"] = digest(conflict_proposal)
    conflict_decision["decision"] = "CONFLICT"
    contested = compile_capsule(conflict_proposal, conflict_decision)
    contested["status"] = "CANDIDATE_ACTIVE"
    try:
        validate_capsule(contested, conflict_proposal, conflict_decision)
    except ContractError:
        mutations += 1
    else:
        raise ContractError("conflict was silently erased")

    provider_authority = copy.deepcopy(capsule)
    provider_authority["projections"][0]["authority"] = "CANONICAL"
    try:
        validate_capsule(provider_authority, proposal, decision)
    except ContractError:
        mutations += 1
    else:
        raise ContractError("provider became canonical")

    persisted = copy.deepcopy(capsule)
    persisted["authority"]["persisted"] = True
    try:
        validate_capsule(persisted, proposal, decision)
    except ContractError:
        mutations += 1
    else:
        raise ContractError("compiler claimed persistence")

    deletion = {
        "schema_version": DELETION,
        "capsule_id": capsule["stable_id"],
        "subject": proposal["subject"],
        "deletion_event_ref": "sha256:" + "8" * 64,
        "authority": {"kind": "HUMAN", "signer_id": "reviewer-fixture", "authority_receipt_ref": "sha256:" + "9" * 64},
        "projections": [{"provider": "mem0", "state": "NOT_CONFIGURED", "residue_count": 0}, {"provider": "vector", "state": "PASS", "residue_count": 0}],
        "deleted_at": "2026-08-21T00:00:00Z"
    }
    validate_deletion(deletion)
    deletion["projections"][1]["residue_count"] = 1
    try:
        validate_deletion(deletion)
    except ContractError:
        mutations += 1
    else:
        raise ContractError("deletion residue accepted")

    if mutations < 17:
        raise ContractError(f"mutation count too low: {mutations}")
    with tempfile.TemporaryDirectory(prefix="loopx-decision-memory.") as temp:
        output = Path(temp) / "capsule.json"
        output.write_text(json.dumps(capsule, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        validate_capsule(load(output), proposal, decision)
    print(f"loopx-decision-memory selftest PASS: 1 positive, {mutations} mutations/controls")


def main() -> int:
    parser = argparse.ArgumentParser(prog="loopx-decision-memory")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    sub.add_parser("selftest")
    compile_parser = sub.add_parser("compile")
    compile_parser.add_argument("--proposal", type=Path, required=True)
    compile_parser.add_argument("--decision", type=Path, required=True)
    compile_parser.add_argument("--output", type=Path, required=True)
    delete_parser = sub.add_parser("check-deletion")
    delete_parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "check":
            failures = check_contracts()
            if failures:
                for failure in failures:
                    print(f"DECISION-MEMORY-RED {failure}")
                return 2
            print("loopx-decision-memory contracts PASS: 4 schemas")
            return 0
        if args.command == "selftest":
            selftest()
            return 0
        if args.command == "check-deletion":
            validate_deletion(load(args.receipt))
            print("loopx-decision-memory deletion receipt PASS")
            return 0
        if args.output.exists():
            raise ContractError("output already exists")
        proposal = load(args.proposal)
        decision = load(args.decision)
        capsule = compile_capsule(proposal, decision)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(capsule, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"loopx-decision-memory candidate capsule WROTE {args.output}")
        return 0
    except ContractError as exc:
        print(f"decision-memory checked refusal: {exc}")
        return 2
    except OSError as exc:
        print(f"decision-memory FATAL: {exc}")
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
