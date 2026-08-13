"""Positive, hollow, and mutation controls for the provider evaluator."""
from __future__ import annotations

import copy
import tempfile
from pathlib import Path

from knowledge_provider_eval_common import ContractError, EVALS, load, require, save
from knowledge_provider_eval_engine import evaluate


def expect_failure(root: Path, values: list[dict], text: str, name: str) -> None:
    with tempfile.TemporaryDirectory(prefix="provider-eval-") as tmp:
        path = Path(tmp) / "observations.json"
        save(path, values)
        try:
            evaluate(root, path)
        except ContractError as exc:
            require(text in str(exc), f"{name}: wrong failure: {exc}")
            return
        raise ContractError(f"{name}: mutation unexpectedly passed")


def run(root: Path) -> dict:
    good_path = root / EVALS / "fixtures/good/observations.json"
    good = load(good_path)
    report = evaluate(root, good_path)
    require(report["status"] == "PASS", "positive fixture")
    require(report["evidence_scope"] == "FIXTURE_ONLY", "fixture scope")
    require(report["admission"]["winner"] is None, "fixture winner")
    hollow = load(root / EVALS / "fixtures/hollow/observations.json")
    expect_failure(root, hollow, "memory overrode authority", "hollow")
    mutations = [
        ("subject", "subject drift", lambda x: x[0]["subject"].update(commit="f" * 40)),
        ("query", "query digest mismatch", lambda x: x[0].update(query_digest="sha256:" + "f" * 64)),
        ("identity", "participant identity drift", lambda x: x[0].update(participant_identity_digest="sha256:" + "f" * 64)),
        ("false-pass", "false PASS", lambda x: x[0]["execution"].update(executed=False)),
        ("stale", "stale index", lambda x: x[0]["index"].update(state="STALE")),
        ("readback", "FOUND without source readback", lambda x: x[0]["results"][0].update(verification="CANDIDATE_ONLY")),
        ("authority", "authority escalation", lambda x: x[0]["authority"].update(advanced_state=True)),
        ("budget", "context budget", lambda x: x[0]["resources"].update(context_bytes=10**9)),
        ("cleanup", "cleanup failed", lambda x: x[0]["cleanup"].update(status="FAIL")),
        ("path", "PATH_ESCAPE", lambda x: x[0]["results"][0].update(source_refs=["../outside"])),
        ("unexpected-key", "unexpected observation keys", lambda x: x[0].update(unexpected_field="fixture")),
        ("memory-write", "direct durable memory write", lambda x: next(
            item for item in x if item["case_id"] == "memory-authority-conflict"
        )["memory_policy"].update(durable_write_performed=True)),
    ]
    for name, text, mutate in mutations:
        candidate = copy.deepcopy(good)
        mutate(candidate)
        expect_failure(root, candidate, text, name)
    return {"status": "PASS", "positive": 1, "hollow": 1, "mutations": len(mutations)}
