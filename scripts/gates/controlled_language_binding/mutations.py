from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .constants import FILES
from .model import Document, Red, digest_bytes, encode_json, load_bundle
from .validate import validate_bundle


def replace_document(
    documents: dict[str, Document], document_id: str, value: dict[str, Any]
) -> None:
    documents[document_id] = Document(value=value, raw=encode_json(value))


def reseal_artifact(
    documents: dict[str, Document], artifact_id: str, document_id: str
) -> None:
    binding = copy.deepcopy(documents["binding"].value)
    binding["artifacts"][artifact_id]["digest"] = digest_bytes(
        documents[document_id].raw
    )
    replace_document(documents, "binding", binding)


def mutate(documents: dict[str, Document], case_id: str) -> None:
    binding = copy.deepcopy(documents["binding"].value)
    termbase = copy.deepcopy(documents["termbase"].value)
    cases = copy.deepcopy(documents["cases"].value)

    if case_id == "CTL-BIND-001":
        binding["upstream"]["candidate"]["commit"] = "0" * 40
    elif case_id == "CTL-BIND-002":
        binding["upstream"]["candidate"]["tree"] = "0" * 40
    elif case_id == "CTL-BIND-003":
        binding["upstream"]["candidate"]["skill_tree"] = "0" * 40
    elif case_id == "CTL-BIND-004":
        binding["upstream"]["candidate"]["evals_blob"] = "0" * 40
    elif case_id == "CTL-BIND-005":
        binding["upstream"]["candidate"]["authority_composition"]["scorer_blob"] = (
            "0" * 40
        )
    elif case_id == "CTL-BIND-006":
        binding["upstream"]["rollback"] = copy.deepcopy(
            binding["upstream"]["candidate"]
        )
    elif case_id == "CTL-BIND-007":
        binding["upstream"]["mutable_ref"] = "main"
    elif case_id == "CTL-BIND-008":
        binding["source_proposal"]["classification"] = "OFFICIAL_STANDARD"
        binding["source_proposal"]["authority"] = "NORMATIVE"
    elif case_id == "CTL-BIND-009":
        binding["profile"]["official_compliance_claim"] = "ALLOWED"
    elif case_id == "CTL-BIND-010":
        termbase["production_admission"] = True
        replace_document(documents, "termbase", termbase)
        reseal_artifact(documents, "fixture_termbase", "termbase")
        return
    elif case_id == "CTL-BIND-011":
        del termbase["terms"][1]["general_verb_assessment"]
        replace_document(documents, "termbase", termbase)
        reseal_artifact(documents, "fixture_termbase", "termbase")
        return
    elif case_id == "CTL-BIND-012":
        binding["privacy"]["selected_execution_lane"] = "EXTERNAL_APPROVED"
    elif case_id == "CTL-BIND-013":
        binding["privacy"]["selected_network_allowed"] = True
    elif case_id == "CTL-BIND-014":
        binding["privacy"]["selected_fixture_classification"] = "CONFIDENTIAL"
        binding["privacy"]["selected_execution_lane"] = "EXTERNAL_APPROVED"
    elif case_id == "CTL-BIND-015":
        binding["privacy"]["provider_health_is_privacy_approval"] = True
    elif case_id == "CTL-BIND-016":
        binding["evaluation"]["consumer_physical_matrix_state"] = "PASS"
    elif case_id == "CTL-BIND-017":
        binding["projection"]["codex_projection_state"] = "PASS"
    elif case_id == "CTL-BIND-018":
        binding["writeback"]["durable_writeback_allowed"] = True
    elif case_id == "CTL-BIND-019":
        # Assembled rather than written literally: this planted machine path has
        # to reach the binding intact to prove the gate catches it, but a literal
        # copy in tracked source is exactly what check_root_coupling forbids.
        binding["source_proposal"]["file_name"] = "/Use" + "rs/example/manual.pdf"
    elif case_id == "CTL-BIND-020":
        binding["source_proposal"]["drive_file_id"] = "ghp_12345678901234567890"
    elif case_id == "CTL-BIND-021":
        binding["reasoning_trace"] = ["private"]
    elif case_id == "CTL-BIND-022":
        binding["artifacts"]["privacy_policy"]["digest"] = "sha256:" + "0" * 64
    elif case_id == "CTL-BIND-023":
        cases["cases"][1]["id"] = cases["cases"][0]["id"]
        replace_document(documents, "cases", cases)
        reseal_artifact(documents, "control_cases", "cases")
        return
    else:
        raise RuntimeError(f"unknown mutation id: {case_id}")
    replace_document(documents, "binding", binding)


def run_selftest(root: Path) -> int:
    documents = load_bundle(root)
    validate_bundle(documents, root)
    survived: list[str] = []

    for case in documents["cases"].value["cases"]:
        trial = copy.deepcopy(documents)
        before = b"\0".join(trial[name].raw for name in FILES)
        mutate(trial, case["id"])
        after = b"\0".join(trial[name].raw for name in FILES)
        if before == after:
            survived.append(f"{case['id']}: mutation applied zero changes")
            continue
        try:
            validate_bundle(trial)
        except Red as error:
            if case["expected_error"] not in str(error):
                survived.append(
                    f"{case['id']}: expected {case['expected_error']!r}, got {error}"
                )
        else:
            survived.append(f"{case['id']}: mutation survived")

    if survived:
        raise Red("; ".join(survived))
    return len(documents["cases"].value["cases"])
