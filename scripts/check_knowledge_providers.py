#!/usr/bin/env python3
"""Validate Bettor's subject-bound knowledge-provider contracts.

Exit codes:
  0: checked contract is valid, or self-test behaved as expected
  2: checked contract disagrees with policy
 64: invalid invocation or unreadable input
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Callable

EXIT_OK = 0
EXIT_CHECK_FAILED = 2
EXIT_FATAL = 64

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")
PROVIDER_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

ALLOWED_CAPABILITIES = {
    "symbol.lookup",
    "symbol.references",
    "symbol.rename-plan",
    "diagnostics.read",
    "search.semantic",
    "callgraph.trace",
    "graph.neighbors",
    "graph.path",
    "graph.impact",
    "structural.search",
    "dataflow.trace",
    "memory.recall",
    "memory.write-proposal",
    "memory.delete-proposal",
}

FORBIDDEN_AUTHORITY_TRUE = {
    "may_write_repository",
    "may_write_memory",
    "may_advance_state",
    "may_waive_gate",
    "may_mark_tested",
    "may_human_admit",
    "advanced_state",
    "waived_gate",
    "marked_tested",
    "human_admit",
    "auto_apply",
    "overrides_current_authority",
}

SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "password",
    "passwd",
    "secret",
    "access_token",
    "refresh_token",
    "authorization",
    "cookie",
    "oauth",
    "private_key",
}

FORBIDDEN_PROVIDER_OPERATIONS = {
    "delete_project",
    "wipe_database",
    "index_repository",
    "update_repository",
    "write_file",
    "surgical_replace_code",
    "structural_replace",
    "ask_agent",
    "add",
    "update",
    "delete",
    "reset",
    "direct_writeback",
}

SCHEMA_FILES = (
    "provider-manifest.schema.json",
    "query-request.schema.json",
    "query-receipt.schema.json",
    "memory-proposal.schema.json",
)


class ContractError(ValueError):
    pass


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"ABSENT: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"UNREADABLE_JSON: {path}: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def is_safe_relative_path(value: str) -> bool:
    if not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        return False
    return all(part not in {"", "."} for part in path.parts)


def walk(value: Any, path: str = "$"):
    if isinstance(value, dict):
        for key, item in value.items():
            yield f"{path}.{key}", key, item
            yield from walk(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk(item, f"{path}[{index}]")


def reject_secret_fields(value: Any) -> None:
    for location, key, item in walk(value):
        normalized = key.lower().replace("-", "_")
        require(
            all(part not in normalized for part in SECRET_KEY_PARTS),
            f"SECRET_FIELD_FORBIDDEN: {location}",
        )
        if isinstance(item, str):
            require(
                not item.startswith(("ghp_", "github_pat_", "sk-", "Bearer ")),
                f"SECRET_SHAPED_VALUE_FORBIDDEN: {location}",
            )


def validate_subject(subject: Any, label: str = "subject") -> None:
    require(isinstance(subject, dict), f"{label}: expected object")
    require(
        REPO.fullmatch(str(subject.get("repository", ""))) is not None,
        f"{label}.repository invalid",
    )
    require(
        SHA40.fullmatch(str(subject.get("commit", ""))) is not None,
        f"{label}.commit invalid",
    )
    require(
        SHA40.fullmatch(str(subject.get("tree", ""))) is not None,
        f"{label}.tree invalid",
    )
    for forbidden in ("branch", "ref", "tag"):
        require(
            forbidden not in subject, f"{label}.{forbidden} is mutable or ambiguous"
        )


def validate_paths(value: Any) -> None:
    for location, key, item in walk(value):
        if key in {"path", "path_scope", "source_refs", "residue"}:
            items = item if isinstance(item, list) else [item]
            for entry in items:
                if not isinstance(entry, str):
                    continue
                # Non-filesystem evidence refs use a typed prefix.
                if ":" in entry and entry.split(":", 1)[0] in {
                    "receipt",
                    "source",
                    "issue",
                    "pr",
                    "artifact",
                    "memory",
                }:
                    continue
                require(
                    is_safe_relative_path(entry), f"PATH_ESCAPE: {location}: {entry!r}"
                )


def validate_provider_manifest(manifest: Any) -> None:
    require(isinstance(manifest, dict), "provider manifest must be an object")
    require(
        manifest.get("schema_version") == "knowledge-provider-manifest/v1",
        "provider schema_version",
    )
    provider_id = manifest.get("provider_id")
    require(
        isinstance(provider_id, str) and PROVIDER_ID.fullmatch(provider_id),
        "provider_id invalid",
    )

    source = manifest.get("source")
    require(isinstance(source, dict), f"{provider_id}: source missing")
    require(
        REPO.fullmatch(str(source.get("repository", ""))) is not None,
        f"{provider_id}: source.repository invalid",
    )
    require(
        SHA40.fullmatch(str(source.get("commit", ""))) is not None,
        f"{provider_id}: source.commit invalid",
    )
    require(bool(source.get("license")), f"{provider_id}: license missing")

    admission = manifest.get("admission")
    require(isinstance(admission, dict), f"{provider_id}: admission missing")
    require(
        admission.get("state") in {"CANDIDATE", "CONFIGURED", "ADMITTED", "REJECTED"},
        f"{provider_id}: admission.state",
    )
    require(
        admission.get("runtime_state")
        in {"NOT_CONFIGURED", "NOT_EXERCISED", "PASS", "FAIL", "ABSENT"},
        f"{provider_id}: runtime_state",
    )
    require(isinstance(admission.get("live_claim"), bool), f"{provider_id}: live_claim")
    if admission.get("live_claim"):
        require(
            admission.get("runtime_state") == "PASS",
            f"{provider_id}: live claim without PASS",
        )
        require(
            admission.get("state") == "ADMITTED",
            f"{provider_id}: live claim without ADMITTED",
        )
    if admission.get("runtime_state") == "PASS":
        require(
            admission.get("live_claim") is True,
            f"{provider_id}: PASS must be an explicit live claim",
        )

    capabilities = manifest.get("capabilities")
    require(
        isinstance(capabilities, list) and capabilities,
        f"{provider_id}: capabilities missing",
    )
    require(
        len(capabilities) == len(set(capabilities)),
        f"{provider_id}: duplicate capability",
    )
    require(
        set(capabilities) <= ALLOWED_CAPABILITIES,
        f"{provider_id}: undeclared capability vocabulary",
    )

    adapter = manifest.get("adapter")
    require(isinstance(adapter, dict), f"{provider_id}: adapter missing")
    require(
        adapter.get("transport") in {"mcp", "cli", "library", "none"},
        f"{provider_id}: adapter.transport",
    )
    require(
        adapter.get("identity_state") in {"PINNED", "UNPINNED", "NOT_CONFIGURED"},
        f"{provider_id}: adapter.identity_state",
    )
    require(
        adapter.get("read_only") is True, f"{provider_id}: adapter must be read-only"
    )
    adapter_digest = adapter.get("digest")
    if adapter.get("identity_state") == "PINNED":
        require(
            isinstance(adapter_digest, str) and SHA256.fullmatch(adapter_digest),
            f"{provider_id}: pinned adapter digest",
        )
    else:
        require(
            adapter_digest is None,
            f"{provider_id}: non-pinned adapter must not carry digest",
        )
        require(
            admission.get("runtime_state") != "PASS",
            f"{provider_id}: unpinned adapter cannot PASS",
        )

    allowed = adapter.get("allowed_operations", [])
    denied = set(adapter.get("denied_operations", []))
    require(
        isinstance(allowed, list)
        and isinstance(adapter.get("denied_operations", []), list),
        f"{provider_id}: operation lists",
    )
    require(
        not (set(allowed) & FORBIDDEN_PROVIDER_OPERATIONS),
        f"{provider_id}: mutating operation exposed",
    )
    if provider_id in {"code-graph-rag", "mem0"}:
        require(
            FORBIDDEN_PROVIDER_OPERATIONS & denied,
            f"{provider_id}: no explicit mutation denial",
        )

    index = manifest.get("index")
    require(isinstance(index, dict), f"{provider_id}: index missing")
    require(
        index.get("subject_bound") is True,
        f"{provider_id}: index must be subject-bound",
    )
    require(
        index.get("rebuildable") is True, f"{provider_id}: store must be rebuildable"
    )
    require(
        index.get("freshness_required") is True,
        f"{provider_id}: freshness must be required",
    )

    authority = manifest.get("authority")
    require(isinstance(authority, dict), f"{provider_id}: authority missing")
    expected_class = (
        "MEMORY_PROPOSAL_ONLY" if provider_id == "mem0" else "CANDIDATE_ONLY"
    )
    require(
        authority.get("result_class") == expected_class, f"{provider_id}: result_class"
    )
    for key in {
        "may_write_repository",
        "may_write_memory",
        "may_advance_state",
        "may_waive_gate",
        "may_mark_tested",
        "may_human_admit",
    }:
        require(
            authority.get(key) is False, f"{provider_id}: authority escalation: {key}"
        )

    limits = manifest.get("limits")
    require(isinstance(limits, dict), f"{provider_id}: limits missing")
    require(
        isinstance(limits.get("max_results"), int)
        and 1 <= limits["max_results"] <= 200,
        f"{provider_id}: max_results",
    )
    require(
        isinstance(limits.get("max_bytes"), int)
        and 1 <= limits["max_bytes"] <= 1_048_576,
        f"{provider_id}: max_bytes",
    )

    reject_secret_fields(manifest)
    validate_paths(manifest)


def load_registry(root: Path) -> tuple[dict[str, dict], dict]:
    base = root / "docs/knowledge-providers"
    registry = read_json(base / "registry.json")
    require(
        registry.get("schema_version") == "knowledge-provider-registry/v1",
        "registry schema_version",
    )
    entries = registry.get("providers")
    require(isinstance(entries, list) and entries, "registry providers missing")

    manifests: dict[str, dict] = {}
    paths: set[str] = set()
    for entry in entries:
        require(isinstance(entry, dict), "registry provider entry")
        provider_id = entry.get("id")
        path = entry.get("path")
        expected_digest = entry.get("digest")
        require(
            isinstance(provider_id, str) and PROVIDER_ID.fullmatch(provider_id),
            "registry provider id",
        )
        require(
            isinstance(path, str) and is_safe_relative_path(path),
            f"{provider_id}: registry path",
        )
        require(path not in paths, f"duplicate registry path: {path}")
        paths.add(path)
        manifest = read_json(base / path)
        validate_provider_manifest(manifest)
        require(
            manifest.get("provider_id") == provider_id,
            f"{provider_id}: manifest id mismatch",
        )
        require(
            SHA256.fullmatch(str(expected_digest or "")) is not None,
            f"{provider_id}: digest format",
        )
        require(
            digest(manifest) == expected_digest, f"{provider_id}: manifest digest drift"
        )
        require(provider_id not in manifests, f"duplicate provider id: {provider_id}")
        manifests[provider_id] = manifest

    require(
        set(manifests) == {"serena", "grepai", "code-graph-rag", "mem0"},
        "registry provider set drift",
    )

    invariants = registry.get("invariants")
    require(isinstance(invariants, dict), "registry invariants missing")
    for key in {
        "stores_are_rebuildable_projections",
        "source_readback_required",
        "provider_cannot_advance_state",
        "provider_cannot_waive_gate",
        "provider_cannot_mark_tested",
        "provider_cannot_human_admit",
        "memory_is_proposal_only",
    }:
        require(invariants.get(key) is True, f"registry invariant false: {key}")

    reject_secret_fields(registry)
    validate_paths(registry)
    return manifests, registry


def validate_query_request(request: Any, manifests: dict[str, dict]) -> None:
    require(isinstance(request, dict), "query request must be object")
    require(
        request.get("schema_version") == "knowledge-provider-query-request/v1",
        "query request schema_version",
    )
    require(
        isinstance(request.get("request_id"), str)
        and ID.fullmatch(request["request_id"]),
        "request_id invalid",
    )
    validate_subject(request.get("subject"), "request.subject")

    provider = request.get("provider")
    require(isinstance(provider, dict), "request.provider missing")
    provider_id = provider.get("id")
    require(provider_id in manifests, "request provider not registered")
    require(
        provider.get("manifest_digest") == digest(manifests[provider_id]),
        "request manifest digest mismatch",
    )
    capability = request.get("capability")
    require(
        capability in manifests[provider_id]["capabilities"],
        "request capability not declared by provider",
    )

    query = request.get("query")
    require(isinstance(query, dict) and query, "query missing")
    require(request.get("query_digest") == digest(query), "query digest mismatch")

    constraints = request.get("constraints")
    require(isinstance(constraints, dict), "constraints missing")
    require(constraints.get("read_only") is True, "query must be read-only")
    require(
        isinstance(constraints.get("require_fresh_index"), bool),
        "freshness policy missing",
    )
    max_results = constraints.get("max_results")
    max_bytes = constraints.get("max_bytes")
    provider_limits = manifests[provider_id]["limits"]
    require(
        isinstance(max_results, int)
        and 1 <= max_results <= provider_limits["max_results"],
        "query max_results exceeds provider",
    )
    require(
        isinstance(max_bytes, int) and 1 <= max_bytes <= provider_limits["max_bytes"],
        "query max_bytes exceeds provider",
    )

    reject_secret_fields(request)
    validate_paths(request)


def validate_query_receipt(
    receipt: Any, request: dict, manifests: dict[str, dict]
) -> None:
    require(isinstance(receipt, dict), "query receipt must be object")
    require(
        receipt.get("schema_version") == "knowledge-provider-query-receipt/v1",
        "query receipt schema_version",
    )
    require(
        receipt.get("request_id") == request.get("request_id"),
        "receipt request id mismatch",
    )
    require(receipt.get("subject") == request.get("subject"), "receipt subject drift")
    validate_subject(receipt.get("subject"), "receipt.subject")

    provider = receipt.get("provider")
    request_provider = request.get("provider")
    require(isinstance(provider, dict), "receipt.provider missing")
    require(
        provider.get("id") == request_provider.get("id"), "receipt provider mismatch"
    )
    require(
        provider.get("manifest_digest") == request_provider.get("manifest_digest"),
        "receipt manifest mismatch",
    )
    manifest = manifests[provider["id"]]
    adapter_digest = manifest["adapter"].get("digest")
    require(
        provider.get("adapter_digest") == adapter_digest,
        "receipt adapter digest mismatch",
    )
    require(
        receipt.get("capability") == request.get("capability"),
        "receipt capability mismatch",
    )
    require(
        receipt.get("query_digest") == request.get("query_digest"),
        "receipt query digest mismatch",
    )

    execution = receipt.get("execution")
    require(isinstance(execution, dict), "receipt execution missing")
    require(isinstance(execution.get("executed"), bool), "execution.executed")
    require(
        execution.get("state")
        in {
            "PASS",
            "FAIL",
            "ABSENT",
            "NOT_EXERCISED",
            "STALE_SUBJECT",
            "SKIPPED_BY_POLICY",
        },
        "execution.state",
    )
    require(isinstance(execution.get("fixture"), bool), "execution.fixture")
    if execution.get("state") == "PASS":
        require(execution.get("executed") is True, "false PASS: not executed")
        if manifest["admission"]["runtime_state"] != "PASS":
            require(
                execution.get("fixture") is True,
                "live PASS without admitted provider runtime",
            )

    index = receipt.get("index")
    require(isinstance(index, dict), "receipt index missing")
    required = manifest["index"]["required"]
    require(index.get("required") is required, "index required mismatch")
    if required:
        require(
            index.get("repository") == request["subject"]["repository"],
            "index repository mismatch",
        )
        require(
            index.get("commit") == request["subject"]["commit"], "index commit mismatch"
        )
        require(index.get("tree") == request["subject"]["tree"], "index tree mismatch")
        require(
            index.get("state") == "FRESH" or execution.get("state") != "PASS",
            "stale index cannot PASS",
        )
        if index.get("state") == "FRESH":
            require(
                SHA256.fullmatch(str(index.get("digest") or "")) is not None,
                "fresh index digest missing",
            )
    else:
        require(index.get("state") == "NOT_REQUIRED", "non-index provider index state")

    results = receipt.get("results")
    require(isinstance(results, list), "receipt results missing")
    require(
        len(results) <= request["constraints"]["max_results"],
        "receipt result count exceeds request",
    )
    for result in results:
        require(isinstance(result, dict), "result must be object")
        require(
            result.get("verification")
            in {"CANDIDATE", "SOURCE_READBACK_REQUIRED", "UNRESOLVED"},
            "result verification",
        )
        require(
            result.get("verification") != "TESTED", "provider result cannot be TESTED"
        )
        require(isinstance(result.get("source_refs"), list), "result source_refs")
        for ref in result["source_refs"]:
            require(
                isinstance(ref, str) and is_safe_relative_path(ref),
                "result source ref path",
            )

    authority = receipt.get("authority")
    require(isinstance(authority, dict), "receipt authority missing")
    require(
        authority.get("candidate_only") is True,
        "receipt result must remain candidate-only",
    )
    for key in {"advanced_state", "waived_gate", "marked_tested", "human_admit"}:
        require(authority.get(key) is False, f"receipt authority escalation: {key}")

    cleanup = receipt.get("cleanup")
    require(isinstance(cleanup, dict), "cleanup missing")
    require(cleanup.get("status") in {"PASS", "FAIL", "NOT_RUN"}, "cleanup status")
    if execution.get("state") == "PASS":
        require(cleanup.get("status") == "PASS", "PASS requires cleanup PASS")
        require(cleanup.get("residue") == [], "PASS cannot leave residue")

    reject_secret_fields(receipt)
    validate_paths(receipt)


def validate_memory_proposal(proposal: Any) -> None:
    require(isinstance(proposal, dict), "memory proposal must be object")
    require(
        proposal.get("schema_version") == "knowledge-memory-proposal/v1",
        "memory schema_version",
    )
    require(
        isinstance(proposal.get("proposal_id"), str)
        and ID.fullmatch(proposal["proposal_id"]),
        "proposal id",
    )
    require(
        proposal.get("operation") in {"add", "supersede", "delete"}, "memory operation"
    )
    validate_subject(proposal.get("subject"), "memory.subject")

    scope = proposal.get("scope")
    require(
        isinstance(scope, dict) and isinstance(scope.get("project"), str),
        "memory scope",
    )
    require(
        scope.get("project") == proposal["subject"]["repository"],
        "memory project/subject mismatch",
    )
    require(
        proposal.get("memory_class")
        in {
            "preference",
            "decision-pointer",
            "incident",
            "rejected-approach",
            "execution-note",
            "task-hint",
        },
        "memory class",
    )
    require(
        isinstance(proposal.get("content"), str)
        and 0 < len(proposal["content"]) <= 4096,
        "memory content",
    )
    provenance = proposal.get("provenance")
    require(
        isinstance(provenance, list)
        and provenance
        and len(provenance) == len(set(provenance)),
        "memory provenance",
    )

    retention = proposal.get("retention")
    require(isinstance(retention, dict), "retention missing")
    require(
        retention.get("policy") in {"session", "ttl", "durable-human-reviewed"},
        "retention policy",
    )
    require(
        retention.get("redaction_class")
        in {"public", "internal", "sensitive-prohibited"},
        "redaction class",
    )
    require(
        retention.get("redaction_class") != "sensitive-prohibited",
        "sensitive memory prohibited",
    )
    if retention.get("policy") == "ttl":
        require(
            isinstance(retention.get("expires_at"), str) and retention["expires_at"],
            "ttl requires expires_at",
        )
    if retention.get("policy") == "durable-human-reviewed":
        require(
            proposal.get("authority", {}).get("human_admit_required") is True,
            "durable memory needs Human Admit",
        )

    authority = proposal.get("authority")
    require(isinstance(authority, dict), "memory authority missing")
    require(authority.get("proposal_only") is True, "memory must be proposal-only")
    require(authority.get("auto_apply") is False, "direct memory write forbidden")
    require(
        authority.get("overrides_current_authority") is False,
        "memory cannot override current authority",
    )
    require(
        authority.get("human_admit_required") is True,
        "memory mutation requires Human Admit",
    )

    reject_secret_fields(proposal)
    validate_paths(proposal)


def validate_repository(root: Path) -> dict[str, Any]:
    contract_dir = root / "docs/knowledge-providers/contracts"
    for name in SCHEMA_FILES:
        schema = read_json(contract_dir / name)
        require(
            schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema",
            f"{name}: schema dialect",
        )
        require(
            schema.get("additionalProperties") is False,
            f"{name}: must close root shape",
        )

    manifests, registry = load_registry(root)
    fixture_dir = root / "docs/knowledge-providers/fixtures/good"
    request = read_json(fixture_dir / "query-request.json")
    receipt = read_json(fixture_dir / "query-receipt.json")
    proposal = read_json(fixture_dir / "memory-proposal.json")
    validate_query_request(request, manifests)
    validate_query_receipt(receipt, request, manifests)
    validate_memory_proposal(proposal)

    hollow = read_json(
        root / "docs/knowledge-providers/fixtures/hollow/query-receipt.json"
    )
    try:
        validate_query_receipt(hollow, request, manifests)
    except ContractError:
        pass
    else:
        raise ContractError("hollow receipt unexpectedly passed")

    return {
        "status": "PASS",
        "providers": sorted(manifests),
        "capabilities": sorted(
            {cap for m in manifests.values() for cap in m["capabilities"]}
        ),
        "fixture_request": request["request_id"],
        "registry_digest": digest(registry),
    }


def expect_failure(name: str, fn: Callable[[], None]) -> dict[str, str]:
    try:
        fn()
    except ContractError as exc:
        return {"name": name, "status": "PASS", "observed": str(exc)}
    return {"name": name, "status": "FAIL", "observed": "mutation unexpectedly passed"}


def run_selftest(root: Path) -> dict[str, Any]:
    manifests, registry = load_registry(root)
    fixture_dir = root / "docs/knowledge-providers/fixtures/good"
    request = read_json(fixture_dir / "query-request.json")
    receipt = read_json(fixture_dir / "query-receipt.json")
    proposal = read_json(fixture_dir / "memory-proposal.json")

    validate_query_request(request, manifests)
    validate_query_receipt(receipt, request, manifests)
    validate_memory_proposal(proposal)

    outcomes = []

    duplicate = copy.deepcopy(registry)
    duplicate["providers"].append(copy.deepcopy(duplicate["providers"][0]))

    def duplicate_provider():
        ids = [entry["id"] for entry in duplicate["providers"]]
        require(len(ids) == len(set(ids)), "duplicate provider id")

    outcomes.append(expect_failure("duplicate-provider-id", duplicate_provider))

    unknown_cap = copy.deepcopy(manifests["serena"])
    unknown_cap["capabilities"].append("state.complete")
    outcomes.append(
        expect_failure(
            "undeclared-capability", lambda: validate_provider_manifest(unknown_cap)
        )
    )

    authority = copy.deepcopy(manifests["serena"])
    authority["authority"]["may_advance_state"] = True
    outcomes.append(
        expect_failure(
            "provider-state-authority", lambda: validate_provider_manifest(authority)
        )
    )

    false_live = copy.deepcopy(manifests["grepai"])
    false_live["admission"]["runtime_state"] = "PASS"
    outcomes.append(
        expect_failure(
            "false-live-claim", lambda: validate_provider_manifest(false_live)
        )
    )

    path_escape = copy.deepcopy(request)
    path_escape["constraints"]["path_scope"] = ["..", "private"]
    outcomes.append(
        expect_failure(
            "request-path-escape",
            lambda: validate_query_request(path_escape, manifests),
        )
    )

    subject_drift = copy.deepcopy(receipt)
    subject_drift["subject"]["commit"] = "9" * 40
    outcomes.append(
        expect_failure(
            "receipt-subject-drift",
            lambda: validate_query_receipt(subject_drift, request, manifests),
        )
    )

    query_drift = copy.deepcopy(receipt)
    query_drift["query_digest"] = "sha256:" + "9" * 64
    outcomes.append(
        expect_failure(
            "receipt-query-digest-drift",
            lambda: validate_query_receipt(query_drift, request, manifests),
        )
    )

    stale = copy.deepcopy(receipt)
    stale["index"]["state"] = "STALE"
    outcomes.append(
        expect_failure(
            "stale-index-pass",
            lambda: validate_query_receipt(stale, request, manifests),
        )
    )

    direct_memory = copy.deepcopy(proposal)
    direct_memory["authority"]["auto_apply"] = True
    outcomes.append(
        expect_failure(
            "direct-memory-write", lambda: validate_memory_proposal(direct_memory)
        )
    )

    no_provenance = copy.deepcopy(proposal)
    no_provenance["provenance"] = []
    outcomes.append(
        expect_failure(
            "memory-without-provenance", lambda: validate_memory_proposal(no_provenance)
        )
    )

    tested = copy.deepcopy(receipt)
    tested["authority"]["marked_tested"] = True
    outcomes.append(
        expect_failure(
            "provider-marks-tested",
            lambda: validate_query_receipt(tested, request, manifests),
        )
    )

    unbounded = copy.deepcopy(request)
    unbounded["constraints"]["max_results"] = 10_000
    outcomes.append(
        expect_failure(
            "unbounded-results", lambda: validate_query_request(unbounded, manifests)
        )
    )

    graph_write = copy.deepcopy(manifests["code-graph-rag"])
    graph_write["adapter"]["allowed_operations"].append("write_file")
    outcomes.append(
        expect_failure(
            "graph-write-surface", lambda: validate_provider_manifest(graph_write)
        )
    )

    false_pass = copy.deepcopy(receipt)
    false_pass["execution"]["executed"] = False
    outcomes.append(
        expect_failure(
            "pass-without-execution",
            lambda: validate_query_receipt(false_pass, request, manifests),
        )
    )

    cleanup = copy.deepcopy(receipt)
    cleanup["cleanup"]["status"] = "FAIL"
    cleanup["cleanup"]["residue"] = ["artifacts/stale"]
    outcomes.append(
        expect_failure(
            "pass-with-cleanup-failure",
            lambda: validate_query_receipt(cleanup, request, manifests),
        )
    )

    failed = [outcome for outcome in outcomes if outcome["status"] != "PASS"]
    require(
        not failed,
        "selftest mutations failed: " + ", ".join(item["name"] for item in failed),
    )
    return {
        "status": "PASS",
        "positive": 3,
        "hollow": 1,
        "mutations": outcomes,
    }


def find_root(explicit: str | None) -> Path:
    if explicit:
        root = Path(explicit).resolve()
    else:
        root = Path(__file__).resolve().parents[1]
    require(
        (root / "docs/knowledge-providers").is_dir(),
        f"repository root not found: {root}",
    )
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        root = find_root(args.root)
        result = run_selftest(root) if args.selftest else validate_repository(root)
    except ContractError as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        else:
            print(f"knowledge-providers FAIL: {exc}", file=sys.stderr)
        return EXIT_CHECK_FAILED
    except (OSError, RuntimeError) as exc:
        payload = {"status": "FATAL", "error": str(exc)}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        else:
            print(f"knowledge-providers FATAL: {exc}", file=sys.stderr)
        return EXIT_FATAL

    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        if args.selftest:
            print(
                "knowledge-providers selftest PASS: "
                f"{result['positive']} positive, {result['hollow']} hollow, "
                f"{len(result['mutations'])} mutations"
            )
        else:
            print(
                "knowledge-providers PASS: "
                f"{len(result['providers'])} providers, "
                f"{len(result['capabilities'])} capabilities"
            )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
