"""Provider manifests and paired evaluation participants."""

from __future__ import annotations
from pathlib import Path
from knowledge_provider_eval_common import (
    BASE,
    EVALS,
    FAMILIES,
    IDENT,
    SHA256,
    common_safety,
    digest,
    load,
    require,
    safe_path,
    strict_keys,
)

PROVIDERS = {"serena", "grepai", "code-graph-rag", "mem0"}
PARTICIPANTS = PROVIDERS | {"exact-search-control", "repository-authority-control"}


def provider_digests(root: Path) -> dict[str, str]:
    reg = load(root / BASE / "registry.json")
    require(
        reg.get("schema_version") == "knowledge-provider-registry/v1",
        "provider registry",
    )
    out = {}
    for e in reg.get("providers", []):
        strict_keys(
            e, required={"id", "path", "digest"}, label="provider registry entry"
        )
        pid, rel, want = e["id"], e["path"], e["digest"]
        require(isinstance(pid, str) and IDENT.fullmatch(pid), "provider id")
        require(isinstance(rel, str) and safe_path(rel), f"{pid}: manifest path")
        require(isinstance(want, str) and SHA256.fullmatch(want), f"{pid}: digest")
        m = load(root / BASE / rel)
        require(m.get("provider_id") == pid, f"{pid}: id drift")
        require(digest(m) == want, f"{pid}: manifest digest drift")
        require(pid not in out, f"duplicate provider: {pid}")
        out[pid] = want
    require(set(out) == PROVIDERS, "provider set")
    common_safety(reg)
    return out


def load_participants(root: Path, manifests: dict[str, str]) -> dict[str, dict]:
    out = {}
    for p in sorted((root / EVALS / "participants").glob("*.json")):
        e = load(p)
        pid = e.get("id")
        kind = e.get("kind")
        required = {
            "id",
            "kind",
            "families",
            "identity_digest",
            "human_admit_required",
        } | ({"manifest_digest"} if kind == "provider" else {"control_contract"})
        strict_keys(e, required=required, label=f"participant {pid}")
        require(isinstance(pid, str) and IDENT.fullmatch(pid), "participant id")
        require(
            pid not in out and kind in {"control", "provider"}, f"{pid}: participant"
        )
        fam = e["families"]
        require(
            isinstance(fam, list)
            and fam
            and len(fam) == len(set(fam))
            and set(fam) <= FAMILIES,
            f"{pid}: families",
        )
        require(SHA256.fullmatch(str(e["identity_digest"])), f"{pid}: identity")
        if kind == "provider":
            require(
                e["manifest_digest"] == manifests.get(pid), f"{pid}: manifest drift"
            )
        else:
            require(
                isinstance(e["control_contract"], dict)
                and digest(e["control_contract"]) == e["identity_digest"],
                f"{pid}: control drift",
            )
        require(e["human_admit_required"] is True, f"{pid}: Human Admit")
        common_safety(e)
        out[pid] = e
    require(set(out) == PARTICIPANTS, "participant set")
    return out
