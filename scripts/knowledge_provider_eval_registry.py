"""Load provider manifests and independent control participants."""
from __future__ import annotations

from pathlib import Path

from knowledge_provider_eval_common import (
    BASE, EVALS, FAMILIES, IDENT, SHA256, common_safety, digest, load, require,
    safe_path,
)


def provider_digests(root: Path) -> dict[str, str]:
    registry = load(root / BASE / "registry.json")
    require(registry.get("schema_version") == "knowledge-provider-registry/v1", "provider registry")
    result: dict[str, str] = {}
    for entry in registry.get("providers", []):
        provider_id = entry.get("id")
        rel = entry.get("path")
        expected = entry.get("digest")
        require(isinstance(provider_id, str) and IDENT.fullmatch(provider_id), "provider id")
        require(isinstance(rel, str) and safe_path(rel), f"{provider_id}: manifest path")
        require(isinstance(expected, str) and SHA256.fullmatch(expected), f"{provider_id}: digest")
        manifest = load(root / BASE / rel)
        require(manifest.get("provider_id") == provider_id, f"{provider_id}: id drift")
        require(digest(manifest) == expected, f"{provider_id}: manifest digest drift")
        result[provider_id] = expected
    require(set(result) == {"serena", "grepai", "code-graph-rag", "mem0"}, "provider set")
    common_safety(registry)
    return result


def load_participants(root: Path, manifests: dict[str, str]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    paths = sorted((root / EVALS / "participants").glob("*.json"))
    require(paths, "participant registry empty")
    for path in paths:
        entry = load(path)
        pid = entry.get("id")
        kind = entry.get("kind")
        require(isinstance(pid, str) and IDENT.fullmatch(pid), "participant id")
        require(pid not in result, f"duplicate participant: {pid}")
        require(kind in {"control", "provider"}, f"{pid}: kind")
        families = entry.get("families", [])
        require(families and len(families) == len(set(families)), f"{pid}: families")
        require(set(families) <= FAMILIES, f"{pid}: family")
        require(SHA256.fullmatch(str(entry.get("identity_digest", ""))), f"{pid}: identity")
        if kind == "provider":
            require(entry.get("manifest_digest") == manifests.get(pid), f"{pid}: manifest drift")
        else:
            contract = entry.get("control_contract")
            require(
                isinstance(contract, dict) and digest(contract) == entry["identity_digest"],
                f"{pid}: control drift",
            )
        require(entry.get("human_admit_required") is True, f"{pid}: Human Admit")
        common_safety(entry)
        result[pid] = entry
    require(
        set(result)
        == {"exact-search-control", "repository-authority-control", "serena", "grepai", "code-graph-rag", "mem0"},
        "participant set",
    )
    return result
