#!/usr/bin/env python3
"""Validate provider manifests and subject-bound provider receipts.

Exit 0 means valid, 2 means a contract violation, and 64 means the input could
not be read or parsed.  This validator deliberately uses only the Python
standard library so the negative controls remain portable and deterministic.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any


EXPECTED_PROVIDERS = {"code-graph-rag", "grepai", "mem0", "serena"}
FALSE_AUTHORITY = {
    "source_truth": False,
    "state_transition": False,
    "gate_verdict": False,
    "promotion": False,
    "human_admit": False,
}
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
GIT_OBJECT = re.compile(r"^[0-9a-f]{40}$")


class ContractViolation(Exception):
    pass


def fail(message: str) -> None:
    raise ContractViolation(message)


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"UNREADABLE {path}: {error}", file=sys.stderr)
        raise SystemExit(64) from error


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{label} must be an object")
    return value


def require_keys(value: dict[str, Any], required: set[str], label: str) -> None:
    missing = required - value.keys()
    if missing:
        fail(f"{label} missing keys: {sorted(missing)}")


def require_exact_keys(value: dict[str, Any], required: set[str], label: str) -> None:
    require_keys(value, required, label)
    unexpected = value.keys() - required
    if unexpected:
        fail(f"{label} has unexpected keys: {sorted(unexpected)}")


def require_allowed_keys(
    value: dict[str, Any], required: set[str], allowed: set[str], label: str
) -> None:
    require_keys(value, required, label)
    unexpected = value.keys() - allowed
    if unexpected:
        fail(f"{label} has unexpected keys: {sorted(unexpected)}")


def require_sha(value: Any, label: str) -> None:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        fail(f"{label} must be sha256:<64 lowercase hex>")


def require_git_object(value: Any, label: str) -> None:
    if not isinstance(value, str) or not GIT_OBJECT.fullmatch(value):
        fail(f"{label} must be a 40-character lowercase Git object id")


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def safe_relative_path(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value:
        fail(f"{label} must be a non-empty relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value:
        fail(f"{label} escapes the repository subject: {value!r}")


def check_subject(value: Any, label: str) -> dict[str, Any]:
    subject = require_object(value, label)
    require_exact_keys(subject, {"repository", "commit", "tree"}, label)
    if not isinstance(subject["repository"], str) or "/" not in subject["repository"]:
        fail(f"{label}.repository must be owner/repository")
    require_git_object(subject["commit"], f"{label}.commit")
    require_git_object(subject["tree"], f"{label}.tree")
    return subject


def check_authority(value: Any, label: str, *, include_effects: bool = False) -> None:
    authority = require_object(value, label)
    expected = (
        {"direct_write", "canonical_mutation", "state_transition", "gate_verdict"}
        if include_effects
        else set(FALSE_AUTHORITY)
    )
    require_exact_keys(authority, expected, label)
    for key in expected:
        if authority[key] is not False:
            fail(f"{label}.{key} must remain false")


def resolve_inside(root: Path, relative: Any, label: str) -> Path:
    safe_relative_path(relative, label)
    candidate = (root / str(relative)).resolve()
    if root != candidate and root not in candidate.parents:
        fail(f"{label} resolves outside module root")
    return candidate


def check_manifest(value: Any, source: Path) -> dict[str, Any]:
    manifest = require_object(value, str(source))
    required = {
        "schema_version",
        "id",
        "family",
        "upstream_repository",
        "observed_commit",
        "version",
        "admission_state",
        "runtime_state",
        "capabilities",
        "effect_mode",
        "adapter",
        "index",
        "authority",
        "fallback",
        "canary_artifacts",
    }
    require_exact_keys(manifest, required, str(source))
    if manifest["schema_version"] != "knowledge-provider-manifest/v1":
        fail(f"{source}: unsupported schema_version")
    if manifest["admission_state"] not in {"CANDIDATE", "ADMITTED", "REJECTED"}:
        fail(f"{source}: invalid admission_state")
    if manifest["runtime_state"] not in {"NOT_EXERCISED", "PASS", "FAIL", "ABSENT"}:
        fail(f"{source}: invalid runtime_state")
    require_git_object(manifest["observed_commit"], f"{source}.observed_commit")
    capabilities = manifest["capabilities"]
    if (
        not isinstance(capabilities, list)
        or not capabilities
        or len(capabilities) != len(set(capabilities))
    ):
        fail(f"{source}: capabilities must be a non-empty unique list")
    if manifest["effect_mode"] not in {"READ_ONLY", "PROPOSAL_ONLY"}:
        fail(f"{source}: invalid effect_mode")
    full_authority = require_object(manifest["authority"], f"{source}.authority")
    require_exact_keys(
        full_authority,
        set(FALSE_AUTHORITY) | {"code_mutation", "memory_mutation"},
        f"{source}.authority",
    )
    for key, enabled in full_authority.items():
        if enabled is not False:
            fail(f"{source}.authority.{key} must remain false")
    adapter = require_object(manifest["adapter"], f"{source}.adapter")
    index = require_object(manifest["index"], f"{source}.index")
    require_exact_keys(adapter, {"state", "digest"}, f"{source}.adapter")
    require_exact_keys(index, {"state", "digest"}, f"{source}.index")
    canaries = manifest["canary_artifacts"]
    if not isinstance(canaries, list):
        fail(f"{source}.canary_artifacts must be a list")
    for position, item in enumerate(canaries):
        safe_relative_path(item, f"{source}.canary_artifacts[{position}]")
    if manifest["admission_state"] == "ADMITTED":
        if manifest["runtime_state"] != "PASS":
            fail(f"{source}: ADMITTED requires runtime_state PASS")
        require_sha(adapter["digest"], f"{source}.adapter.digest")
        require_sha(index["digest"], f"{source}.index.digest")
        if not canaries:
            fail(f"{source}: ADMITTED requires canary artifacts")
    elif manifest["runtime_state"] == "PASS":
        fail(f"{source}: PASS runtime cannot be claimed before admission")
    return manifest


def check_registry(root: Path, registry_path: Path) -> dict[str, dict[str, Any]]:
    registry = require_object(read_json(registry_path), str(registry_path))
    require_allowed_keys(
        registry,
        {"schema_version", "providers"},
        {
            "schema_version",
            "providers",
            "authority_order",
            "live_claim_requirements",
        },
        str(registry_path),
    )
    if registry["schema_version"] != "knowledge-provider-registry/v1":
        fail("unsupported registry schema_version")
    refs = registry["providers"]
    if not isinstance(refs, list) or len(refs) != 4:
        fail("registry must select exactly four initial providers")
    manifests: dict[str, dict[str, Any]] = {}
    for position, ref in enumerate(refs):
        path = resolve_inside(root, ref, f"providers[{position}]")
        manifest = check_manifest(read_json(path), path)
        provider_id = manifest.get("id")
        if not isinstance(provider_id, str):
            fail(f"{path}: id must be a string")
        if provider_id in manifests:
            fail(f"duplicate provider id: {provider_id}")
        manifests[provider_id] = manifest
    if set(manifests) != EXPECTED_PROVIDERS:
        fail(f"registry providers must be exactly {sorted(EXPECTED_PROVIDERS)}")
    return manifests


def check_pair(root: Path, request_path: Path, receipt_path: Path) -> None:
    manifests = check_registry(root, root / "registry.json")
    request = require_object(read_json(request_path), str(request_path))
    receipt = require_object(read_json(receipt_path), str(receipt_path))
    request_keys = {
        "schema_version",
        "request_id",
        "subject",
        "provider",
        "index",
        "capability",
        "effect_mode",
        "query",
        "query_digest",
    }
    receipt_keys = {
        "schema_version",
        "request_id",
        "subject",
        "provider",
        "index",
        "capability",
        "query_digest",
        "status",
        "evidence_mode",
        "results",
        "result_count",
        "authority",
        "source_readback_required",
        "canary_artifacts",
        "generated_at",
    }
    require_exact_keys(request, request_keys, str(request_path))
    require_exact_keys(receipt, receipt_keys, str(receipt_path))
    if request["schema_version"] != "knowledge-provider-query-request/v1":
        fail("unsupported request schema_version")
    if receipt["schema_version"] != "knowledge-provider-query-receipt/v1":
        fail("unsupported receipt schema_version")
    request_subject = check_subject(request["subject"], "request.subject")
    receipt_subject = check_subject(receipt["subject"], "receipt.subject")
    if request_subject != receipt_subject:
        fail("receipt subject does not match request subject")
    request_provider = require_object(request["provider"], "request.provider")
    receipt_provider = require_object(receipt["provider"], "receipt.provider")
    provider_keys = {"id", "version", "adapter_digest"}
    require_exact_keys(request_provider, provider_keys, "request.provider")
    require_exact_keys(receipt_provider, provider_keys, "receipt.provider")
    if request_provider != receipt_provider:
        fail("receipt provider identity does not match request")
    provider_id = request_provider["id"]
    if provider_id not in manifests:
        fail(f"request names unknown provider: {provider_id}")
    manifest = manifests[provider_id]
    if request_provider["version"] != manifest["version"]:
        fail("request provider version does not match manifest")
    require_sha(request_provider["adapter_digest"], "request.provider.adapter_digest")
    if request["capability"] not in manifest["capabilities"]:
        fail("request capability is not declared by provider")
    if request["effect_mode"] != manifest["effect_mode"]:
        fail("request effect_mode does not match provider")
    if request["request_id"] != receipt["request_id"]:
        fail("receipt request_id does not match request")
    if request["capability"] != receipt["capability"]:
        fail("receipt capability does not match request")
    query = require_object(request["query"], "request.query")
    require_exact_keys(query, {"parameters", "max_results"}, "request.query")
    max_results = query["max_results"]
    if (
        not isinstance(max_results, int)
        or isinstance(max_results, bool)
        or not 1 <= max_results <= 100
    ):
        fail("request.query.max_results must be an integer from 1 through 100")
    expected_digest = canonical_digest(query)
    if request["query_digest"] != expected_digest:
        fail("request query_digest does not match canonical query bytes")
    if receipt["query_digest"] != expected_digest:
        fail("receipt query_digest does not match request query")
    request_index = require_object(request["index"], "request.index")
    receipt_index = require_object(receipt["index"], "receipt.index")
    require_exact_keys(
        request_index, {"subject_commit", "subject_tree", "digest"}, "request.index"
    )
    require_exact_keys(
        receipt_index,
        {"subject_commit", "subject_tree", "digest", "staleness"},
        "receipt.index",
    )
    for label, index in (
        ("request.index", request_index),
        ("receipt.index", receipt_index),
    ):
        require_git_object(index["subject_commit"], f"{label}.subject_commit")
        require_git_object(index["subject_tree"], f"{label}.subject_tree")
        require_sha(index["digest"], f"{label}.digest")
    if {key: receipt_index[key] for key in request_index} != request_index:
        fail("receipt index identity does not match request index")
    subject_current = (
        request_index["subject_commit"] == request_subject["commit"]
        and request_index["subject_tree"] == request_subject["tree"]
    )
    if receipt_index["staleness"] not in {"CURRENT", "STALE", "UNKNOWN"}:
        fail("receipt index staleness is invalid")
    results = receipt["results"]
    count = receipt["result_count"]
    if (
        not isinstance(results, list)
        or not isinstance(count, int)
        or isinstance(count, bool)
    ):
        fail("receipt results/result_count have invalid types")
    if count != len(results) or count > max_results:
        fail("receipt result_count must equal results length and respect max_results")
    status = receipt["status"]
    if status == "CANDIDATE":
        if not subject_current or receipt_index["staleness"] != "CURRENT":
            fail("CANDIDATE requires an exact current index subject")
    elif status == "STALE_INDEX":
        if receipt_index["staleness"] != "STALE" or results:
            fail("STALE_INDEX requires STALE and no results")
    elif status == "SUBJECT_MISMATCH":
        if subject_current or results:
            fail("SUBJECT_MISMATCH requires drift and no results")
    elif status not in {"PROVIDER_UNAVAILABLE", "ERROR", "NOT_EXERCISED"}:
        fail("receipt status is invalid")
    elif results:
        fail(f"{status} cannot carry candidate results")
    for position, result in enumerate(results):
        item = require_object(result, f"results[{position}]")
        require_exact_keys(
            item,
            {"path", "line_start", "line_end", "claim", "provenance"},
            f"results[{position}]",
        )
        safe_relative_path(item["path"], f"results[{position}].path")
        if not isinstance(item["provenance"], str) or not item["provenance"].strip():
            fail(f"results[{position}].provenance must be non-empty")
        if (
            not isinstance(item["line_start"], int)
            or not isinstance(item["line_end"], int)
            or item["line_start"] < 1
            or item["line_end"] < item["line_start"]
        ):
            fail(f"results[{position}] has an invalid line range")
    check_authority(receipt["authority"], "receipt.authority")
    if receipt["source_readback_required"] is not True:
        fail("receipt.source_readback_required must be true")
    evidence_mode = receipt["evidence_mode"]
    canaries = receipt["canary_artifacts"]
    if not isinstance(canaries, list):
        fail("receipt.canary_artifacts must be a list")
    for position, item in enumerate(canaries):
        safe_relative_path(item, f"receipt.canary_artifacts[{position}]")
    if evidence_mode == "live-canary":
        if (
            manifest["admission_state"] != "ADMITTED"
            or manifest["runtime_state"] != "PASS"
        ):
            fail("live-canary claim requires an admitted passing manifest")
        if canaries != manifest["canary_artifacts"]:
            fail("live-canary artifacts must match admitted manifest")
    elif evidence_mode != "synthetic-fixture":
        fail("receipt.evidence_mode is invalid")
    try:
        datetime.fromisoformat(str(receipt["generated_at"]).replace("Z", "+00:00"))
    except ValueError as error:
        fail(f"receipt.generated_at is invalid: {error}")


def check_memory(root: Path, proposal_path: Path) -> None:
    manifests = check_registry(root, root / "registry.json")
    proposal = require_object(read_json(proposal_path), str(proposal_path))
    required = {
        "schema_version",
        "proposal_id",
        "provider_id",
        "operation",
        "subject",
        "scope",
        "memory_class",
        "content_digest",
        "evidence_refs",
        "retention",
        "effects",
        "status",
        "requires_human_admit",
    }
    require_exact_keys(proposal, required, str(proposal_path))
    if proposal["schema_version"] != "knowledge-provider-memory-proposal/v1":
        fail("unsupported memory proposal schema_version")
    if proposal["provider_id"] != "mem0" or proposal["provider_id"] not in manifests:
        fail("memory proposal provider must be mem0")
    if proposal["operation"] not in {"memory.write-proposal", "memory.delete-proposal"}:
        fail("memory operation must remain proposal-only")
    check_subject(proposal["subject"], "proposal.subject")
    require_sha(proposal["content_digest"], "proposal.content_digest")
    refs = proposal["evidence_refs"]
    if not isinstance(refs, list) or not refs:
        fail("memory proposal requires at least one evidence_ref")
    for position, ref in enumerate(refs):
        path = str(ref).split(":", 1)[0]
        safe_relative_path(path, f"evidence_refs[{position}]")
        evidence = resolve_inside(root.parent, path, f"evidence_refs[{position}]")
        if not evidence.is_file():
            fail(f"evidence_refs[{position}] does not identify a repository file")
    check_authority(proposal["effects"], "proposal.effects", include_effects=True)
    if proposal["status"] != "PROPOSED" or proposal["requires_human_admit"] is not True:
        fail("memory mutation requires PROPOSED plus Human Admit")
    retention = require_object(proposal["retention"], "proposal.retention")
    require_exact_keys(retention, {"expires_at", "delete_scope"}, "proposal.retention")
    if retention["delete_scope"] != "proposal-id":
        fail("memory delete scope must be proposal-id")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    check = subparsers.add_parser("check")
    check.add_argument("--root", type=Path, required=True)
    check.add_argument("--registry", type=Path)
    pair = subparsers.add_parser("pair")
    pair.add_argument("--root", type=Path, required=True)
    pair.add_argument("--request", type=Path, required=True)
    pair.add_argument("--receipt", type=Path, required=True)
    memory = subparsers.add_parser("memory")
    memory.add_argument("--root", type=Path, required=True)
    memory.add_argument("--proposal", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    try:
        if args.mode == "check":
            check_registry(root, (args.registry or root / "registry.json").resolve())
        elif args.mode == "pair":
            check_pair(root, args.request.resolve(), args.receipt.resolve())
        else:
            check_memory(root, args.proposal.resolve())
    except ContractViolation as error:
        print(f"CONTRACT_VIOLATION: {error}", file=sys.stderr)
        return 2
    print(f"PASS knowledge-provider {args.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
