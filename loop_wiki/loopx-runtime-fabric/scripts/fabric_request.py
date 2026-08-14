#!/usr/bin/env python3
"""Provider-neutral runtime request, and the enforcement ceiling it must declare.

The rule this file exists to hold: a request may only *claim* an enforcement
level the adapter can actually deliver. `network: deny` on a local process
adapter with no namespace is a claim nothing enforces -- and a receipt that
records it as enforced is a fabricated safety property, which is worse than
having no isolation at all, because someone will rely on it.

So every enforcement dimension carries both what was requested and what the
adapter attests. A mismatch is refused at admission rather than discovered in
an incident.
"""

from __future__ import annotations

from typing import Any

from fabric_common import (
    ContractError,
    contained_relative_path,
    exact_object,
    non_empty_str,
    positive_int,
    require,
    sha256_ref,
    validate_subject,
)

REQUEST_KEYS = {
    "schema_version",
    "request_id",
    "subject",
    "closure_digest",
    "provider",
    "workspace",
    "process",
    "network",
    "environment",
    "dependencies",
    "artifacts",
}
PROVIDER_KEYS = {"provider_id", "adapter_id", "image_ref", "runtime_identity"}
WORKSPACE_KEYS = {"lease_id", "read_only_paths", "writable_paths", "cleanup"}
PROCESS_KEYS = {
    "argv",
    "timeout_ms",
    "process_group",
    "max_output_bytes",
    "max_memory_bytes",
    "max_disk_bytes",
}
NETWORK_KEYS = {"requested", "attested", "allowlist"}
ENVIRONMENT_KEYS = {"allowlist", "secret_refs"}
DEPENDENCY_KEYS = {"cache_policy", "cache_key", "contamination_check"}
ARTIFACT_KEYS = {"expected_paths", "capture_root"}

NETWORK_MODES = {"deny", "allowlisted", "inherit"}
# What an adapter is allowed to say about a network mode. UNENFORCED is not a
# failure -- a local process adapter honestly saying it cannot enforce deny is
# the correct answer, and the request simply may not claim deny.
ATTESTATIONS = {"ENFORCED", "UNENFORCED", "NOT_OBSERVED"}
CACHE_POLICIES = {"none", "subject_scoped", "shared_readonly"}
CLEANUP_MODES = {"REQUIRED"}


def validate_request(value: Any) -> dict[str, Any]:
    request = exact_object(value, REQUEST_KEYS, "request")
    require(
        request["schema_version"] == "loopx/runtime-request/v1",
        "runtime request schema version drifted",
    )
    non_empty_str(request["request_id"], "request.request_id")
    validate_subject(request["subject"], "request.subject")
    sha256_ref(request["closure_digest"], "request.closure_digest")

    provider = exact_object(request["provider"], PROVIDER_KEYS, "request.provider")
    for field in ("provider_id", "adapter_id", "runtime_identity"):
        non_empty_str(provider[field], f"request.provider.{field}")
    if provider["image_ref"] is not None:
        non_empty_str(provider["image_ref"], "request.provider.image_ref")

    workspace = exact_object(request["workspace"], WORKSPACE_KEYS, "request.workspace")
    non_empty_str(workspace["lease_id"], "request.workspace.lease_id")
    if workspace["cleanup"] not in CLEANUP_MODES:
        raise ContractError(
            "request.workspace.cleanup must be REQUIRED; a workspace that may "
            "survive its task is not disposable"
        )
    for field in ("read_only_paths", "writable_paths"):
        paths = workspace[field]
        if not isinstance(paths, list):
            raise ContractError(f"request.workspace.{field} must be an array")
        for index, path in enumerate(paths):
            contained_relative_path(path, f"request.workspace.{field}[{index}]")
    overlap = sorted(
        set(workspace["read_only_paths"]) & set(workspace["writable_paths"])
    )
    if overlap:
        raise ContractError(
            f"paths declared both read-only and writable: {overlap}; a source mount "
            "that is also writable is not a read-only mount"
        )

    process = exact_object(request["process"], PROCESS_KEYS, "request.process")
    argv = process["argv"]
    if not isinstance(argv, list) or not argv:
        raise ContractError("request.process.argv must be a non-empty array")
    for index, item in enumerate(argv):
        non_empty_str(item, f"request.process.argv[{index}]")
    if process["process_group"] is not True:
        raise ContractError(
            "request.process.process_group must be true; without it a timeout kills "
            "the parent and leaves the children running"
        )
    for field in (
        "timeout_ms",
        "max_output_bytes",
        "max_memory_bytes",
        "max_disk_bytes",
    ):
        positive_int(process[field], f"request.process.{field}")

    network = exact_object(request["network"], NETWORK_KEYS, "request.network")
    if network["requested"] not in NETWORK_MODES:
        raise ContractError(
            f"request.network.requested must be one of {sorted(NETWORK_MODES)}"
        )
    if network["attested"] not in ATTESTATIONS:
        raise ContractError(
            f"request.network.attested must be one of {sorted(ATTESTATIONS)}"
        )
    if not isinstance(network["allowlist"], list):
        raise ContractError("request.network.allowlist must be an array")

    # The claim that has to be earned.
    if (
        network["requested"] in {"deny", "allowlisted"}
        and network["attested"] != "ENFORCED"
    ):
        raise ContractError(
            f"request.network.requested={network['requested']!r} but the adapter "
            f"attests {network['attested']!r}; a restriction nothing enforces is a "
            "fabricated safety property, and someone will rely on it"
        )
    if network["requested"] != "allowlisted" and network["allowlist"]:
        raise ContractError(
            "request.network.allowlist is only meaningful when requested=allowlisted"
        )

    environment = exact_object(
        request["environment"], ENVIRONMENT_KEYS, "request.environment"
    )
    for field in ("allowlist", "secret_refs"):
        if not isinstance(environment[field], list):
            raise ContractError(f"request.environment.{field} must be an array")
    for index, name in enumerate(environment["allowlist"]):
        non_empty_str(name, f"request.environment.allowlist[{index}]")
    for index, ref in enumerate(environment["secret_refs"]):
        # References only. A value here would be a secret in a tracked request.
        sha256_ref(ref, f"request.environment.secret_refs[{index}]")

    dependencies = exact_object(
        request["dependencies"], DEPENDENCY_KEYS, "request.dependencies"
    )
    if dependencies["cache_policy"] not in CACHE_POLICIES:
        raise ContractError(
            f"request.dependencies.cache_policy must be one of {sorted(CACHE_POLICIES)}"
        )
    if dependencies["contamination_check"] is not True:
        raise ContractError(
            "request.dependencies.contamination_check must be true; a cache shared "
            "across subjects without a check is how one task's build output becomes "
            "another task's evidence"
        )
    if dependencies["cache_policy"] == "subject_scoped":
        key = non_empty_str(dependencies["cache_key"], "request.dependencies.cache_key")
        if request["subject"]["commit"] not in key:
            raise ContractError(
                "a subject-scoped cache key must contain the subject commit, or it is "
                "not scoped to the subject it claims"
            )
    elif dependencies["cache_key"] is not None:
        raise ContractError(
            "request.dependencies.cache_key belongs to a subject_scoped policy only"
        )

    artifacts = exact_object(request["artifacts"], ARTIFACT_KEYS, "request.artifacts")
    capture_root = contained_relative_path(
        artifacts["capture_root"], "request.artifacts.capture_root"
    )
    if not isinstance(artifacts["expected_paths"], list):
        raise ContractError("request.artifacts.expected_paths must be an array")
    for index, path in enumerate(artifacts["expected_paths"]):
        text = contained_relative_path(
            path, f"request.artifacts.expected_paths[{index}]"
        )
        if not text.startswith(capture_root.rstrip("/") + "/"):
            raise ContractError(
                f"expected artifact {text!r} is outside the capture root "
                f"{capture_root!r}; an artifact collected from anywhere is not a "
                "bounded capture"
            )
    if capture_root not in workspace["writable_paths"]:
        raise ContractError(
            "the artifact capture root must be declared writable, or collection would "
            "depend on a permission the request never asked for"
        )
    return request
