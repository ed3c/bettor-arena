from __future__ import annotations

from pathlib import Path
from typing import Any

from .constants import (
    CANDIDATE,
    EVIDENCE_STATES,
    HUMAN_OWNED,
    PROFILE,
    ROLLBACK,
    SOURCE_PROPOSAL,
)
from .model import Document, Red, scan_durable, validate_artifact


def validate_privacy_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != "controlled-language-privacy-policy/v1":
        raise Red("privacy policy schema is unsupported")
    if policy.get("policy_id") != "bettor-arena-controlled-language-privacy":
        raise Red("privacy policy identity drifted")
    if policy.get("policy_version") != "1.0.0":
        raise Red("privacy policy version drifted")
    if policy.get("default_network_allowed") is not False:
        raise Red("privacy network default must remain disabled")
    if policy.get("provider_health_is_privacy_approval") is not False:
        raise Red("provider health cannot become privacy approval")

    rows = policy.get("classifications")
    if not isinstance(rows, list):
        raise Red("privacy classifications must be a list")
    rules: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("classification"), str):
            raise Red("privacy classification row is malformed")
        name = row["classification"]
        if name in rules:
            raise Red(f"duplicate privacy classification: {name}")
        rules[name] = row

    if set(rules) != {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}:
        raise Red("privacy classification coverage drifted")
    if rules["RESTRICTED"].get("allowed_lanes") != ["LOCAL_ONLY"]:
        raise Red("RESTRICTED permits LOCAL_ONLY only")
    if rules["RESTRICTED"].get("network_default") is not False:
        raise Red("RESTRICTED network must remain disabled")
    if rules["CONFIDENTIAL"].get("external_human_approval_required") is not True:
        raise Red("CONFIDENTIAL external processing requires Human approval")


def validate_termbase(termbase: dict[str, Any]) -> None:
    if termbase.get("schema_version") != "controlled-language-termbase-fixture/v1":
        raise Red("fixture termbase schema is unsupported")
    if termbase.get("source_classification") != "FIXTURE":
        raise Red("fixture termbase source classification drifted")
    if termbase.get("state") != "FIXTURE_ONLY":
        raise Red("fixture termbase cannot become production admitted")
    if termbase.get("production_admission") is not False:
        raise Red("fixture termbase cannot become production admitted")
    if termbase.get("human_review_receipt") is not None:
        raise Red("fixture termbase cannot cite a production approval receipt")

    terms = termbase.get("terms")
    if not isinstance(terms, list):
        raise Red("fixture termbase terms must be a list")
    ids: set[str] = set()
    types: set[str] = set()
    for term in terms:
        if not isinstance(term, dict):
            raise Red("fixture termbase term is malformed")
        term_id = term.get("term_id")
        if not isinstance(term_id, str) or not term_id:
            raise Red("fixture termbase term_id is absent")
        if term_id in ids:
            raise Red(f"duplicate fixture term id: {term_id}")
        ids.add(term_id)
        term_type = term.get("term_type")
        types.add(str(term_type))
        if term.get("production_admission") is not False:
            raise Red("fixture termbase cannot become production admitted")
        if term.get("human_review_receipt") is not None:
            raise Red("fixture term cannot cite a production approval receipt")
        if term_type == "TN" and term.get("allowed_parts_of_speech") != ["NOUN"]:
            raise Red("Technical Name fixture must be admitted only as a noun")
        if term_type == "TV":
            if term.get("allowed_parts_of_speech") != ["VERB"]:
                raise Red("Technical Verb fixture must be admitted only as a verb")
            if term.get("general_verb_assessment") != "NO_APPROVED_GENERAL_VERB":
                raise Red("Technical Verb fixture requires no-general-verb assessment")
        if term_type == "REJECT" and not term.get("replacement"):
            raise Red("rejected fixture term requires a replacement")
    if types != {"TN", "TV", "REJECT"}:
        raise Red("fixture termbase must cover TN, TV, and REJECT")


def validate_cases(cases: dict[str, Any]) -> None:
    if cases.get("schema_version") != "controlled-language-consumer-cases/v1":
        raise Red("control-case schema is unsupported")
    rows = cases.get("cases")
    if not isinstance(rows, list) or len(rows) != 23:
        raise Red("control cases must contain 23 mutations")
    ids: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise Red("control case is malformed")
        case_id = row.get("id")
        if not isinstance(case_id, str) or not case_id:
            raise Red("control case id is absent")
        if case_id in ids:
            raise Red("duplicate control id")
        ids.add(case_id)
        if not isinstance(row.get("expected_error"), str) or not row["expected_error"]:
            raise Red(f"{case_id}: expected diagnostic is absent")


def validate_upstream(binding: dict[str, Any]) -> None:
    upstream = binding.get("upstream")
    if not isinstance(upstream, dict):
        raise Red("upstream binding is absent")
    if upstream.get("repository") != "ed3c/skills-shared":
        raise Red("upstream repository drifted")
    if upstream.get("mutable_ref") is not None:
        raise Red("mutable upstream ref cannot identify a release bundle")

    candidate = upstream.get("candidate")
    rollback = upstream.get("rollback")
    if not isinstance(candidate, dict) or not isinstance(rollback, dict):
        raise Red("candidate or rollback bundle is absent")
    if candidate.get("commit") != CANDIDATE["commit"]:
        raise Red("candidate commit differs from the selected immutable subject")
    if candidate.get("tree") != CANDIDATE["tree"]:
        raise Red("candidate tree differs from the selected immutable subject")
    if candidate.get("skill_tree") != CANDIDATE["skill_tree"]:
        raise Red("candidate Skill tree differs from the selected immutable subject")
    if candidate.get("evals_blob") != CANDIDATE["evals_blob"]:
        raise Red("candidate evals blob differs from the selected immutable subject")
    if candidate.get("authority_composition", {}).get("scorer_blob") != (
        CANDIDATE["authority_composition"]["scorer_blob"]
    ):
        raise Red("candidate authority scorer differs from the selected bundle")
    if candidate != CANDIDATE:
        raise Red("candidate immutable identity has undeclared drift")
    if all(
        candidate.get(field) == rollback.get(field)
        for field in ("commit", "tree", "skill_tree", "evals_blob")
    ):
        raise Red("rollback bundle must differ from candidate")
    if rollback != ROLLBACK:
        raise Red("rollback immutable identity has undeclared drift")
    if rollback.get("authority_composition", {}).get("state") != "ABSENT":
        raise Red("rollback must remain the pre-authority-composition bundle")


def validate_privacy_selection(binding: dict[str, Any]) -> None:
    selection = binding.get("privacy")
    expected = {
        "default_lane": "LOCAL_ONLY",
        "default_network_allowed": False,
        "external_human_approval_receipt": None,
        "external_human_approval_state": "ABSENT",
        "policy_id": "bettor-arena-controlled-language-privacy",
        "provider_health_is_privacy_approval": False,
        "selected_execution_lane": "LOCAL_ONLY",
        "selected_fixture_classification": "RESTRICTED",
        "selected_network_allowed": False,
    }
    if not isinstance(selection, dict):
        raise Red("privacy selection is absent")
    if selection.get("provider_health_is_privacy_approval") is not False:
        raise Red("provider health cannot become privacy approval")
    classification = selection.get("selected_fixture_classification")
    lane = selection.get("selected_execution_lane")
    network = selection.get("selected_network_allowed")
    if classification == "RESTRICTED" and lane != "LOCAL_ONLY":
        raise Red("RESTRICTED permits LOCAL_ONLY only")
    if classification == "RESTRICTED" and network is not False:
        raise Red("RESTRICTED network must remain disabled")
    if (
        classification == "CONFIDENTIAL"
        and lane == "EXTERNAL_APPROVED"
        and selection.get("external_human_approval_state") != "ADMITTED"
    ):
        raise Red("CONFIDENTIAL external processing requires Human approval")
    if selection != expected:
        raise Red("privacy selection drifted")


def validate_evaluation(binding: dict[str, Any]) -> None:
    evaluation = binding.get("evaluation")
    if not isinstance(evaluation, dict):
        raise Red("evaluation boundary is absent")
    expected_authority = {
        "authority_commit": CANDIDATE["commit"],
        "authority_repository": "ed3c/skills-shared",
        "authority_scorer_blob": CANDIDATE["authority_composition"]["scorer_blob"],
        "compliance_claim": "NOT_CLAIMED",
        "generalization": "NOT_EXERCISED",
        "physical_runs": "NOT_EXERCISED",
        "state": "VERIFIED_OFFLINE_MECHANISM_ONLY",
    }
    if evaluation.get("upstream_authority_bound_ab") != expected_authority:
        raise Red("authority-bound offline A/B evidence ceiling drifted")
    if evaluation.get("conditions") != [
        "no_skill",
        "current_skill",
        "candidate_skill",
        "wrong_profile",
    ]:
        raise Red("physical matrix conditions drifted")
    if evaluation.get("harnesses") != ["codex", "claude"]:
        raise Red("physical matrix harnesses drifted")
    if evaluation.get("minimum_repetitions_per_condition") != 3:
        raise Red("physical matrix repetition floor drifted")
    if evaluation.get("expected_cells") != 24:
        raise Red("physical matrix expected-cell count drifted")
    state = evaluation.get("consumer_physical_matrix_state")
    if state == "NOT_EXERCISED":
        if evaluation.get("consumer_receipt") is not None or evaluation.get(
            "observed_cells"
        ) != 0:
            raise Red("unexecuted physical matrix cannot cite results")
    elif not (
        state in {"PASS", "FAIL"}
        and evaluation.get("consumer_receipt")
        and evaluation.get("observed_cells") == 24
    ):
        raise Red("physical PASS requires an exact receipt and complete cells")


def validate_bundle(
    documents: dict[str, Document], root: Path | None = None
) -> None:
    binding = documents["binding"].value
    privacy = documents["privacy"].value
    termbase = documents["termbase"].value
    cases = documents["cases"].value

    for document in documents.values():
        scan_durable(document.value)
    if binding.get("schema_version") != "controlled-language-consumer-binding/v1":
        raise Red("binding schema is unsupported")
    if binding.get("binding_id") != "bettor-arena-controlled-language-harness":
        raise Red("binding identity drifted")
    if binding.get("binding_version") != "1.0.0":
        raise Red("binding version drifted")
    if binding.get("consumer") != {
        "repository": "ed3c/bettor-arena",
        "role": "INTEGRATION_ACCEPTANCE_PLANE",
    }:
        raise Red("consumer identity drifted")

    validate_upstream(binding)
    source = binding.get("source_proposal")
    if not isinstance(source, dict):
        raise Red("source proposal identity is absent")
    if source.get("classification") != "SOURCE_PROPOSAL" or source.get(
        "authority"
    ) != "NON_NORMATIVE":
        raise Red("SOURCE_PROPOSAL cannot become official authority")
    if source != SOURCE_PROPOSAL:
        raise Red("source proposal identity drifted")

    profile = binding.get("profile")
    if not isinstance(profile, dict):
        raise Red("profile boundary is absent")
    if (
        profile.get("official_standard_pack_state") == "ABSENT"
        and profile.get("official_compliance_claim") != "FORBIDDEN"
    ):
        raise Red("official compliance remains forbidden while the pack is absent")
    if profile != PROFILE:
        raise Red("profile boundary drifted")

    validate_artifact(
        root,
        binding,
        documents,
        "privacy_policy",
        "privacy",
        ".skill-bindings/controlled-technical-language-harness/privacy-policy.json",
    )
    validate_artifact(
        root,
        binding,
        documents,
        "fixture_termbase",
        "termbase",
        ".skill-bindings/controlled-technical-language-harness/fixtures/termbase.json",
    )
    validate_artifact(
        root,
        binding,
        documents,
        "control_cases",
        "cases",
        ".skill-bindings/controlled-technical-language-harness/fixtures/cases.json",
    )
    validate_privacy_policy(privacy)
    validate_termbase(termbase)
    validate_cases(cases)
    validate_privacy_selection(binding)
    validate_evaluation(binding)

    expected_projection = {
        "claude_projection_state": "NOT_IMPLEMENTED",
        "codex_projection_state": "NOT_IMPLEMENTED",
        "content_digest_parity_state": "NOT_EXERCISED",
        "generated_binding_state": "NOT_IMPLEMENTED",
        "projection_receipt": None,
        "shared_requirements_update_state": "NOT_IMPLEMENTED",
    }
    if binding.get("projection") != expected_projection:
        raise Red("projection PASS requires generated closure and digest parity")
    expected_writeback = {
        "context_state": "NOT_IMPLEMENTED",
        "durable_writeback_allowed": False,
        "human_admit_required": True,
        "mem0_state": "NOT_IMPLEMENTED",
    }
    if binding.get("writeback") != expected_writeback:
        raise Red("durable memory and context writeback remain disabled")
    if binding.get("evidence_states") != EVIDENCE_STATES:
        raise Red("evidence vocabulary drifted")
    if binding.get("human_owned") != HUMAN_OWNED:
        raise Red("Human-owned operation boundary drifted")
    if binding.get("private_reasoning_persistence") != "FORBIDDEN":
        raise Red("private reasoning fields are forbidden")
