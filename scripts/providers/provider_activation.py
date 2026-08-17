#!/usr/bin/env python3
"""Exact-subject activation controller for Serena and GrepAI.

The controller has a closed provider set and fixed repository-relative paths. It
accepts no provider command, shell string, host path, credential, or arbitrary
manifest. ``activate`` changes only the two provider manifests, their registry
digests, and one activation receipt after both live canaries agree on the same
clean committed subject.

Exit codes: 0 admitted/check passed, 2 checked policy failure, 64 bad invocation.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any


OK, BLOCKED, USAGE = 0, 2, 64
REPOSITORY = "ed3c/bettor-arena"
SCHEMA = "bettor-arena/provider-activation-receipt/v1"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
PROVIDERS = ("grepai", "serena")
MANIFESTS = {
    provider: Path(f"docs/knowledge-providers/providers/{provider}.json")
    for provider in PROVIDERS
}
REGISTRY = Path("docs/knowledge-providers/registry.json")
SCHEMA_PATH = Path(
    "docs/knowledge-providers/contracts/provider-activation-receipt.schema.json"
)
CONFIGURATION_SCHEMA_PATH = Path(
    "docs/knowledge-providers/contracts/provider-configuration-receipt.schema.json"
)
POLICY_PATH = Path("docs/knowledge-providers/activation/policy.json")
PROJECTION_JSON_PATHS = (
    Path("docs/knowledge-providers/fixtures/good/query-request.json"),
    Path("docs/knowledge-providers/fixtures/good/query-receipt.json"),
    Path("docs/knowledge-providers/fixtures/hollow/query-receipt.json"),
    Path("docs/knowledge-providers/evals/participants/grepai.json"),
    Path("docs/knowledge-providers/evals/participants/serena.json"),
    Path("docs/knowledge-providers/evals/fixtures/good/packets/obs-symbol-serena.json"),
)
PROJECTION_GZIP_PATHS = (
    Path("docs/knowledge-providers/evals/fixtures/good/observations.json.gz"),
    Path("docs/knowledge-providers/evals/fixtures/hollow/observations.json.gz"),
)
ACTIVATION_KEYS = {
    "mode",
    "version",
    "artifact_digest",
    "sbom_disposition",
    "secret_references",
    "data_scope",
    "network_scope",
    "spend_usd_ceiling",
    "request_ceiling",
    "rollback",
}
POLICY_PROVIDER_KEYS = ACTIVATION_KEYS | {
    "provider_id",
    "source_repository",
    "source_commit",
    "license",
}


class PolicyError(ValueError):
    """A checked activation input is absent, stale, or disagrees with policy."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PolicyError(message)


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PolicyError(f"ABSENT {label}: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise PolicyError(f"INVALID {label}: {exc}") from exc
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def exact_keys(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{label} must be an object")
    require(
        set(value) == keys,
        f"{label} keys drift: missing={sorted(keys - set(value))} "
        f"extra={sorted(set(value) - keys)}",
    )
    return value


def load_policy(root: Path) -> dict[str, dict[str, Any]]:
    document = exact_keys(
        load_json(root / POLICY_PATH, "activation policy"),
        {"schema", "providers"},
        "activation policy",
    )
    require(
        document["schema"] == "bettor-arena/provider-activation-policy/v1",
        "activation policy schema",
    )
    entries = document["providers"]
    require(isinstance(entries, list) and len(entries) == 2, "activation policy set")
    policies: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(entries):
        entry = exact_keys(raw, POLICY_PROVIDER_KEYS, f"policy.providers[{index}]")
        provider = entry["provider_id"]
        require(provider in PROVIDERS and provider not in policies, "policy provider")
        require(
            SHA40.fullmatch(str(entry["source_commit"])) is not None,
            f"{provider}: policy source commit",
        )
        require(
            SHA256.fullmatch(str(entry["artifact_digest"])) is not None,
            f"{provider}: policy artifact digest",
        )
        require(entry["source_repository"].count("/") == 1, f"{provider}: source")
        require(bool(entry["license"]), f"{provider}: license")
        activation = {key: entry[key] for key in ACTIVATION_KEYS}
        configured = {
            "provider_id": provider,
            "source": {
                "repository": entry["source_repository"],
                "commit": entry["source_commit"],
                "license": entry["license"],
            },
            "adapter": {
                "identity_state": "PINNED",
                "digest": entry["artifact_digest"],
            },
            "admission": {
                "state": "CONFIGURED",
                "runtime_state": "NOT_EXERCISED",
                "live_claim": False,
            },
            "activation": activation,
        }
        activation_policy(configured, provider)
        policies[provider] = entry
    require(set(policies) == set(PROVIDERS), "activation policy coverage")
    return policies


def subject(repository: str, commit: str, tree: str, label: str) -> dict[str, str]:
    require(repository == REPOSITORY, f"{label}.repository mismatch")
    require(SHA40.fullmatch(commit) is not None, f"{label}.commit invalid")
    require(SHA40.fullmatch(tree) is not None, f"{label}.tree invalid")
    return {"repository": repository, "commit": commit, "tree": tree}


def run_git(
    root: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise PolicyError(f"git {' '.join(args)} failed: {detail}")
    return result


def bind_repository(
    root: Path,
    expected_commit: str,
    expected_tree: str,
    rollback_commit: str,
    rollback_tree: str,
) -> tuple[dict[str, str], dict[str, str]]:
    current = subject(
        REPOSITORY,
        run_git(root, "rev-parse", "HEAD").stdout.strip(),
        run_git(root, "rev-parse", "HEAD^{tree}").stdout.strip(),
        "subject",
    )
    expected = subject(REPOSITORY, expected_commit, expected_tree, "expected_subject")
    require(current == expected, "STALE_SUBJECT: HEAD/tree changed")
    observed_rollback_tree = run_git(
        root, "rev-parse", f"{rollback_commit}^{{tree}}"
    ).stdout.strip()
    rollback = subject(REPOSITORY, rollback_commit, rollback_tree, "rollback_subject")
    require(observed_rollback_tree == rollback_tree, "rollback tree mismatch")
    ancestor = run_git(
        root,
        "merge-base",
        "--is-ancestor",
        rollback_commit,
        expected_commit,
        check=False,
    )
    require(ancestor.returncode == 0, "rollback subject is not an ancestor")
    return expected, rollback


def activation_policy(manifest: dict[str, Any], provider: str) -> dict[str, Any]:
    activation = exact_keys(
        manifest.get("activation"), ACTIVATION_KEYS, f"{provider}.activation"
    )
    adapter = manifest.get("adapter", {})
    source = manifest.get("source", {})
    admission = manifest.get("admission", {})
    require(manifest.get("provider_id") == provider, f"{provider}: manifest id")
    require(
        admission
        == {
            "state": "CONFIGURED",
            "runtime_state": "NOT_EXERCISED",
            "live_claim": False,
        },
        f"{provider}: activation requires CONFIGURED/NOT_EXERCISED",
    )
    require(adapter.get("identity_state") == "PINNED", f"{provider}: unpinned")
    require(
        SHA256.fullmatch(str(adapter.get("digest", ""))) is not None,
        f"{provider}: adapter digest",
    )
    require(
        activation["artifact_digest"] == adapter["digest"],
        f"{provider}: artifact digest mismatch",
    )
    require(activation["mode"] == "ON_DEMAND_READ_ONLY", f"{provider}: activation mode")
    require(
        isinstance(activation["version"], str) and activation["version"],
        f"{provider}: version",
    )
    require(
        isinstance(activation["sbom_disposition"], str)
        and activation["sbom_disposition"],
        f"{provider}: SBOM",
    )
    require(
        activation["secret_references"] == [], f"{provider}: secrets are not allowed"
    )
    require(
        activation["data_scope"] == "EXACT_SUBJECT_COVERAGE_ONLY",
        f"{provider}: data scope",
    )
    expected_network = "LOOPBACK_ONLY" if provider == "grepai" else "DENIED"
    require(
        activation["network_scope"] == expected_network, f"{provider}: network scope"
    )
    require(activation["spend_usd_ceiling"] == 0, f"{provider}: spend ceiling")
    require(
        isinstance(activation["request_ceiling"], int)
        and 1 <= activation["request_ceiling"] <= 20,
        f"{provider}: request ceiling",
    )
    require(
        activation["rollback"] == "RESTORE_ROLLBACK_SUBJECT", f"{provider}: rollback"
    )
    require(
        SHA40.fullmatch(str(source.get("commit", ""))) is not None,
        f"{provider}: source commit",
    )
    require(bool(source.get("license")), f"{provider}: license")
    return activation


def canary_path(provider: str, expected_commit: str) -> Path:
    return Path(f"data/provider-canaries/{provider}/{expected_commit}.json")


def configuration_evidence_path(provider: str, evidence_commit: str) -> Path:
    return Path(f"data/provider-canaries/{provider}/{evidence_commit}.json")


def validate_configuration_evidence(
    receipt: dict[str, Any],
    manifest: dict[str, Any],
    provider: str,
    evidence_subject: dict[str, str],
    policy: dict[str, Any],
) -> None:
    require(
        receipt.get("schema") == "bettor-arena/provider-live-canary/v1",
        f"{provider}: evidence schema",
    )
    require(receipt.get("provider_id") == provider, f"{provider}: evidence id")
    require(receipt.get("status") == "PASS", f"{provider}: evidence status")
    require(receipt.get("subject") == evidence_subject, f"{provider}: evidence subject")
    observed_manifest = receipt.get("manifest", {})
    require(
        observed_manifest.get("digest") == digest(manifest),
        f"{provider}: historical manifest drift",
    )
    require(
        observed_manifest.get("identity_match") is False,
        f"{provider}: configuration evidence must precede pinning",
    )
    require(
        observed_manifest.get("identity_state") == "UNPINNED",
        f"{provider}: historical identity state",
    )
    require(
        receipt.get("admission")
        == {"state": "BLOCKED_POLICY", "reason": "manifest-identity-drift"},
        f"{provider}: historical policy outcome",
    )
    require(
        receipt.get("execution", {}).get("state") == "PASS",
        f"{provider}: evidence execution",
    )
    require(
        receipt.get("execution", {}).get("executed") is True,
        f"{provider}: evidence not executed",
    )
    require(
        receipt.get("source_readback", {}).get("token_observed") is True,
        f"{provider}: evidence source readback",
    )
    require(
        receipt.get("cleanup") == {"status": "PASS", "residue": []},
        f"{provider}: evidence cleanup",
    )
    for field in (
        "candidate_only",
        "result_secret_scan",
        "stale_subject",
        "wrong_workspace",
    ):
        require(
            receipt.get("controls", {}).get(field) == "PASS",
            f"{provider}: evidence control {field}",
        )
    for field in (
        "advanced_state",
        "waived_gate",
        "marked_tested",
        "activated_provider",
        "promoted_release",
    ):
        require(
            receipt.get("authority", {}).get(field) is False,
            f"{provider}: evidence authority {field}",
        )
    identity = receipt.get("provider_identity", {})
    require(
        identity.get("source_repository") == policy["source_repository"],
        f"{provider}: evidence repository",
    )
    require(
        identity.get("source_commit") == policy["source_commit"],
        f"{provider}: evidence source commit",
    )
    require(
        identity.get("version") == policy["version"], f"{provider}: evidence version"
    )
    require(
        identity.get("license") == policy["license"], f"{provider}: evidence license"
    )
    require(
        identity.get("sbom") == policy["sbom_disposition"], f"{provider}: evidence SBOM"
    )
    require(
        identity.get("executable", {}).get("sha256")
        == policy["artifact_digest"].removeprefix("sha256:"),
        f"{provider}: evidence executable",
    )


def validate_canary(
    receipt: dict[str, Any],
    manifest: dict[str, Any],
    provider: str,
    expected_subject: dict[str, str],
) -> dict[str, Any]:
    require(
        receipt.get("schema") == "bettor-arena/provider-live-canary/v1",
        f"{provider}: canary schema",
    )
    require(receipt.get("provider_id") == provider, f"{provider}: canary id")
    require(receipt.get("status") == "PASS", f"{provider}: canary status")
    require(
        receipt.get("subject") == expected_subject, f"{provider}: STALE_SUBJECT receipt"
    )
    require(
        receipt.get("manifest", {}).get("digest") == digest(manifest),
        f"{provider}: manifest digest drift",
    )
    require(
        receipt.get("manifest", {}).get("identity_match") is True,
        f"{provider}: identity mismatch",
    )
    require(
        receipt.get("manifest", {}).get("identity_state") == "PINNED",
        f"{provider}: receipt unpinned",
    )
    require(
        receipt.get("execution", {}).get("state") == "PASS", f"{provider}: execution"
    )
    require(
        receipt.get("execution", {}).get("executed") is True,
        f"{provider}: not executed",
    )
    require(
        receipt.get("source_readback", {}).get("token_observed") is True,
        f"{provider}: source readback",
    )
    require(
        receipt.get("cleanup") == {"status": "PASS", "residue": []},
        f"{provider}: cleanup",
    )
    admission = receipt.get("admission", {})
    require(
        admission == {"state": "CANDIDATE", "reason": "identity-bound"},
        f"{provider}: canary admission",
    )
    authority = receipt.get("authority", {})
    for field in (
        "advanced_state",
        "waived_gate",
        "marked_tested",
        "activated_provider",
        "promoted_release",
    ):
        require(
            authority.get(field) is False, f"{provider}: authority escalation {field}"
        )
    controls = receipt.get("controls", {})
    for field in (
        "candidate_only",
        "result_secret_scan",
        "stale_subject",
        "wrong_workspace",
    ):
        require(controls.get(field) == "PASS", f"{provider}: control {field}")
    configuration = receipt.get("configuration", {})
    require(configuration.get("external_spend_usd") == 0, f"{provider}: external spend")
    require(configuration.get("secrets") == "DENIED", f"{provider}: secrets")
    expected_network = "LOOPBACK_ONLY" if provider == "grepai" else "DENIED"
    observed_network = configuration.get(
        "network_scope", configuration.get("external_network")
    )
    require(observed_network == expected_network, f"{provider}: network evidence")
    identity = receipt.get("provider_identity", {})
    activation = activation_policy(manifest, provider)
    require(
        identity.get("version") == activation["version"], f"{provider}: version drift"
    )
    require(
        identity.get("source_commit") == manifest["source"]["commit"],
        f"{provider}: source drift",
    )
    require(
        identity.get("license") == manifest["source"]["license"],
        f"{provider}: license drift",
    )
    require(
        identity.get("sbom") == activation["sbom_disposition"],
        f"{provider}: SBOM drift",
    )
    require(
        identity.get("executable", {}).get("sha256")
        == activation["artifact_digest"].removeprefix("sha256:"),
        f"{provider}: executable drift",
    )
    return activation


def update_registry(
    registry: dict[str, Any], manifests: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    updated = copy.deepcopy(registry)
    entries = updated.get("providers")
    require(isinstance(entries, list), "registry providers absent")
    seen: set[str] = set()
    for entry in entries:
        provider = entry.get("id") if isinstance(entry, dict) else None
        if provider in manifests:
            require(
                entry.get("path") == f"providers/{provider}.json",
                f"{provider}: registry path",
            )
            entry["digest"] = digest(manifests[provider])
            seen.add(provider)
    require(seen == set(PROVIDERS), "registry provider coverage")
    return updated


def replace_exact_strings(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {
            key: replace_exact_strings(item, replacements)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [replace_exact_strings(item, replacements) for item in value]
    if isinstance(value, str):
        return replacements.get(value, value)
    return value


def projection_bytes(
    root: Path,
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
) -> dict[Path, bytes]:
    replacements = {
        digest(before[provider]): digest(after[provider]) for provider in PROVIDERS
    }
    documents: dict[Path, bytes] = {}
    for relative in PROJECTION_JSON_PATHS:
        value = load_json(root / relative, f"projection {relative}")
        updated = replace_exact_strings(value, replacements)
        if relative.name in {"query-receipt.json"}:
            provider = updated.get("provider", {})
            if provider.get("id") == "serena":
                provider["adapter_digest"] = after["serena"]["adapter"]["digest"]
        documents[root / relative] = (
            json.dumps(updated, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
    for relative in PROJECTION_GZIP_PATHS:
        try:
            with gzip.open(root / relative, "rt", encoding="utf-8") as handle:
                value = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise PolicyError(f"INVALID projection {relative}: {exc}") from exc
        updated = replace_exact_strings(value, replacements)
        documents[root / relative] = gzip.compress(canonical(updated), mtime=0)
    return documents


def configured_manifest(
    manifest: dict[str, Any], provider: str, policy: dict[str, Any]
) -> dict[str, Any]:
    updated = copy.deepcopy(manifest)
    require(updated.get("provider_id") == provider, f"{provider}: manifest id")
    require(
        updated.get("admission")
        == {
            "state": "CANDIDATE",
            "runtime_state": "NOT_EXERCISED",
            "live_claim": False,
        },
        f"{provider}: configuration requires CANDIDATE/NOT_EXERCISED",
    )
    require(
        updated.get("adapter", {}).get("identity_state") == "UNPINNED"
        and updated["adapter"].get("digest") is None,
        f"{provider}: configuration requires UNPINNED",
    )
    updated["source"] = {
        "repository": policy["source_repository"],
        "commit": policy["source_commit"],
        "license": policy["license"],
    }
    updated["adapter"]["identity_state"] = "PINNED"
    updated["adapter"]["digest"] = policy["artifact_digest"]
    updated["admission"] = {
        "state": "CONFIGURED",
        "runtime_state": "NOT_EXERCISED",
        "live_claim": False,
    }
    updated["activation"] = {key: policy[key] for key in ACTIVATION_KEYS}
    activation_policy(updated, provider)
    return updated


def require_manifest_matches_policy(
    manifest: dict[str, Any], provider: str, policy: dict[str, Any]
) -> dict[str, Any]:
    activation = activation_policy(manifest, provider)
    require(
        manifest.get("source")
        == {
            "repository": policy["source_repository"],
            "commit": policy["source_commit"],
            "license": policy["license"],
        },
        f"{provider}: configured source differs from policy",
    )
    require(
        manifest.get("adapter", {}).get("digest") == policy["artifact_digest"],
        f"{provider}: configured artifact differs from policy",
    )
    require(
        activation == {key: policy[key] for key in ACTIVATION_KEYS},
        f"{provider}: configured activation differs from policy",
    )
    return activation


def configuration_receipt_document(
    expected: dict[str, str],
    evidence: dict[str, str],
    rollback: dict[str, str],
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema": "bettor-arena/provider-configuration-receipt/v1",
        "operation": "CONFIGURE_ON_DEMAND_READ_ONLY",
        "outcome": "CONFIGURED",
        "subject": expected,
        "evidence_subject": evidence,
        "rollback_subject": rollback,
        "providers": [
            {
                "provider_id": provider,
                "manifest_digest_before": digest(before[provider]),
                "manifest_digest_after": digest(after[provider]),
                "evidence_receipt_path": configuration_evidence_path(
                    provider, evidence["commit"]
                ).as_posix(),
                "state_before": "CANDIDATE",
                "state_after": "CONFIGURED",
            }
            for provider in PROVIDERS
        ],
        "authority": {
            "configured_provider": True,
            "activated_provider": False,
            "advanced_state": False,
            "marked_tested": False,
            "promoted_release": False,
            "waived_gate": False,
        },
        "cleanup": {"status": "PASS", "residue": []},
    }


def receipt_document(
    expected: dict[str, str],
    rollback: dict[str, str],
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
    activations: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    providers = []
    for provider in PROVIDERS:
        activation = activations[provider]
        providers.append(
            {
                "provider_id": provider,
                "manifest_path": MANIFESTS[provider].as_posix(),
                "canary_receipt_path": canary_path(
                    provider, expected["commit"]
                ).as_posix(),
                "manifest_digest_before": digest(before[provider]),
                "manifest_digest_after": digest(after[provider]),
                "executable_digest": activation["artifact_digest"],
                "version": activation["version"],
                "source_commit": before[provider]["source"]["commit"],
                "sbom_disposition": activation["sbom_disposition"],
                "state_before": "CONFIGURED",
                "state_after": "ADMITTED",
            }
        )
    return {
        "schema": SCHEMA,
        "operation": "ACTIVATE_ON_DEMAND_READ_ONLY",
        "outcome": "ADMITTED",
        "subject": expected,
        "rollback_subject": rollback,
        "providers": providers,
        "policy": {
            "data_scope": "EXACT_SUBJECT_COVERAGE_ONLY",
            "external_network": "DENIED_OR_LOOPBACK_ONLY",
            "external_spend_usd": 0,
            "secrets": "DENIED",
            "source_readback": "PASS",
            "cleanup": "PASS",
            "exact_subject": "PASS",
        },
        "authority": {
            "activated_provider": True,
            "advanced_state": False,
            "marked_tested": False,
            "promoted_release": False,
            "waived_gate": False,
        },
        "cleanup": {"status": "PASS", "residue": []},
    }


def write_atomic(path: Path, value: dict[str, Any]) -> None:
    write_atomic_bytes(
        path,
        (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        ),
    )


def write_atomic_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb", dir=path.parent, delete=False
    ) as handle:
        handle.write(raw)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def apply_lifecycle_documents(
    root: Path,
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
    output: Path,
    receipt: dict[str, Any],
) -> None:
    require(
        not output.exists(),
        f"lifecycle receipt already exists: {output.relative_to(root)}",
    )
    registry_before = load_json(root / REGISTRY, "provider registry")
    documents = projection_bytes(root, before, after)
    documents.update(
        {
            root / MANIFESTS[provider]: (
                json.dumps(
                    after[provider], ensure_ascii=False, indent=2, sort_keys=True
                )
                + "\n"
            ).encode("utf-8")
            for provider in PROVIDERS
        }
    )
    documents[root / REGISTRY] = (
        json.dumps(
            update_registry(registry_before, after),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    originals = {path: path.read_bytes() for path in documents}
    try:
        for path, raw in documents.items():
            write_atomic_bytes(path, raw)
        write_atomic(output, receipt)
        checked = subprocess.run(
            [sys.executable, "scripts/check_knowledge_provider_module.py"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        require(
            checked.returncode == 0,
            "post-lifecycle provider contract failed: "
            + (checked.stderr or checked.stdout).strip(),
        )
    except Exception:
        for path, raw in originals.items():
            path.write_bytes(raw)
        if output.exists():
            output.unlink()
        raise


def validate_schema(root: Path) -> None:
    expected = {
        SCHEMA_PATH: SCHEMA,
        CONFIGURATION_SCHEMA_PATH: "bettor-arena/provider-configuration-receipt/v1",
    }
    for path, identity in expected.items():
        schema = load_json(root / path, f"schema {path.name}")
        require(
            schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema",
            f"{path.name}: schema dialect",
        )
        require(schema.get("type") == "object", f"{path.name}: root type")
        require(
            schema.get("additionalProperties") is False,
            f"{path.name}: schema must be closed",
        )
        require(
            schema.get("properties", {}).get("schema", {}).get("const") == identity,
            f"{path.name}: schema identity",
        )
    load_policy(root)


def configure(args: argparse.Namespace, root: Path) -> dict[str, Any]:
    expected, rollback = bind_repository(
        root,
        args.expected_commit,
        args.expected_tree,
        args.rollback_commit,
        args.rollback_tree,
    )
    evidence_tree = run_git(
        root, "rev-parse", f"{args.evidence_commit}^{{tree}}"
    ).stdout.strip()
    evidence = subject(
        REPOSITORY,
        args.evidence_commit,
        args.evidence_tree,
        "evidence_subject",
    )
    require(evidence_tree == evidence["tree"], "evidence tree mismatch")
    require(
        not run_git(root, "status", "--porcelain").stdout.strip(),
        "configuration requires a clean worktree",
    )
    policies = load_policy(root)
    before = {
        provider: load_json(root / MANIFESTS[provider], f"{provider} manifest")
        for provider in PROVIDERS
    }
    after = {}
    for provider in PROVIDERS:
        receipt = load_json(
            root / configuration_evidence_path(provider, evidence["commit"]),
            f"{provider} configuration evidence",
        )
        validate_configuration_evidence(
            receipt, before[provider], provider, evidence, policies[provider]
        )
        after[provider] = configured_manifest(
            before[provider], provider, policies[provider]
        )
    configuration_receipt = configuration_receipt_document(
        expected, evidence, rollback, before, after
    )
    output = root / "data/provider-configurations" / f"{expected['commit']}.json"
    apply_lifecycle_documents(root, before, after, output, configuration_receipt)
    return configuration_receipt


def activate(args: argparse.Namespace, root: Path) -> dict[str, Any]:
    expected, rollback = bind_repository(
        root,
        args.expected_commit,
        args.expected_tree,
        args.rollback_commit,
        args.rollback_tree,
    )
    allowed_untracked = {
        canary_path(provider, expected["commit"]).as_posix() for provider in PROVIDERS
    }
    status = run_git(root, "status", "--porcelain").stdout.splitlines()
    for line in status:
        require(
            line.startswith("?? ") and line[3:] in allowed_untracked,
            f"dirty or out-of-scope path: {line}",
        )
    before = {
        provider: load_json(root / MANIFESTS[provider], f"{provider} manifest")
        for provider in PROVIDERS
    }
    policies = load_policy(root)
    activations = {}
    for provider in PROVIDERS:
        receipt = load_json(
            root / canary_path(provider, expected["commit"]), f"{provider} canary"
        )
        require_manifest_matches_policy(before[provider], provider, policies[provider])
        activations[provider] = validate_canary(
            receipt, before[provider], provider, expected
        )
    after = copy.deepcopy(before)
    for manifest in after.values():
        manifest["admission"] = {
            "state": "ADMITTED",
            "runtime_state": "PASS",
            "live_claim": True,
        }
    activation_receipt = receipt_document(
        expected, rollback, before, after, activations
    )
    output = root / "data/provider-activations" / f"{expected['commit']}.json"
    apply_lifecycle_documents(root, before, after, output, activation_receipt)
    return activation_receipt


def selftest(root: Path) -> int:
    validate_schema(root)
    base_subject = {"repository": REPOSITORY, "commit": "1" * 40, "tree": "2" * 40}
    checks = 0
    for provider in PROVIDERS:
        manifest = load_json(root / MANIFESTS[provider], f"{provider} manifest")
        configured = copy.deepcopy(manifest)
        configured["source"]["commit"] = "3" * 40
        configured["source"]["license"] = "MIT"
        configured["adapter"]["identity_state"] = "PINNED"
        configured["adapter"]["digest"] = "sha256:" + "4" * 64
        configured["admission"] = {
            "state": "CONFIGURED",
            "runtime_state": "NOT_EXERCISED",
            "live_claim": False,
        }
        configured["activation"] = {
            "mode": "ON_DEMAND_READ_ONLY",
            "version": "1.0.0",
            "artifact_digest": "sha256:" + "4" * 64,
            "sbom_disposition": "TEST_SBOM",
            "secret_references": [],
            "data_scope": "EXACT_SUBJECT_COVERAGE_ONLY",
            "network_scope": "LOOPBACK_ONLY" if provider == "grepai" else "DENIED",
            "spend_usd_ceiling": 0,
            "request_ceiling": 5,
            "rollback": "RESTORE_ROLLBACK_SUBJECT",
        }
        activation_policy(configured, provider)
        receipt = {
            "schema": "bettor-arena/provider-live-canary/v1",
            "provider_id": provider,
            "status": "PASS",
            "subject": base_subject,
            "manifest": {
                "digest": digest(configured),
                "identity_match": True,
                "identity_state": "PINNED",
            },
            "execution": {"state": "PASS", "executed": True},
            "source_readback": {"token_observed": True},
            "cleanup": {"status": "PASS", "residue": []},
            "admission": {"state": "CANDIDATE", "reason": "identity-bound"},
            "authority": {
                "advanced_state": False,
                "waived_gate": False,
                "marked_tested": False,
                "activated_provider": False,
                "promoted_release": False,
            },
            "controls": {
                "candidate_only": "PASS",
                "result_secret_scan": "PASS",
                "stale_subject": "PASS",
                "wrong_workspace": "PASS",
            },
            "configuration": {
                "external_spend_usd": 0,
                "secrets": "DENIED",
                "network_scope": "LOOPBACK_ONLY",
            }
            if provider == "grepai"
            else {
                "external_spend_usd": 0,
                "secrets": "DENIED",
                "external_network": "DENIED",
            },
            "provider_identity": {
                "version": "1.0.0",
                "source_commit": "3" * 40,
                "license": "MIT",
                "sbom": "TEST_SBOM",
                "executable": {"sha256": "4" * 64},
            },
        }
        validate_canary(receipt, configured, provider, base_subject)
        checks += 1
        mutations = (
            lambda value: value["subject"].__setitem__("commit", "9" * 40),
            lambda value: value["cleanup"].__setitem__("status", "FAIL"),
            lambda value: value["configuration"].__setitem__("external_spend_usd", 1),
            lambda value: value["authority"].__setitem__("marked_tested", True),
            lambda value: value["manifest"].__setitem__("digest", "sha256:" + "8" * 64),
        )
        for mutate in mutations:
            planted = copy.deepcopy(receipt)
            mutate(planted)
            try:
                validate_canary(planted, configured, provider, base_subject)
            except PolicyError:
                checks += 1
            else:
                raise PolicyError(f"{provider}: planted mutation stayed green")
        unpinned = copy.deepcopy(configured)
        unpinned["adapter"]["identity_state"] = "UNPINNED"
        try:
            activation_policy(unpinned, provider)
        except PolicyError:
            checks += 1
        else:
            raise PolicyError(f"{provider}: unpinned manifest stayed green")
    return checks


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="provider_activation.py")
    sub = result.add_subparsers(dest="operation", required=True)
    sub.add_parser("check")
    sub.add_parser("selftest")
    configure_parser = sub.add_parser("configure")
    for name in (
        "expected-commit",
        "expected-tree",
        "evidence-commit",
        "evidence-tree",
        "rollback-commit",
        "rollback-tree",
    ):
        configure_parser.add_argument(f"--{name}", required=True)
    activate_parser = sub.add_parser("activate")
    for name in (
        "expected-commit",
        "expected-tree",
        "rollback-commit",
        "rollback-tree",
    ):
        activate_parser.add_argument(f"--{name}", required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    try:
        validate_schema(root)
        if args.operation == "check":
            print("provider-activation contract PASS")
        elif args.operation == "selftest":
            checks = selftest(root)
            print(f"provider-activation selftest PASS: {checks} controls")
        elif args.operation == "configure":
            value = configure(args, root)
            print(
                "provider-activation CONFIGURED "
                f"subject={value['subject']['commit'][:12]}"
            )
        else:
            value = activate(args, root)
            print(
                f"provider-activation ADMITTED subject={value['subject']['commit'][:12]}"
            )
        return OK
    except PolicyError as exc:
        print(f"provider-activation BLOCKED_POLICY: {exc}", file=sys.stderr)
        return BLOCKED


if __name__ == "__main__":
    raise SystemExit(main())
