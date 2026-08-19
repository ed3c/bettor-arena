from __future__ import annotations

import copy

from candidate_contract import CandidateContractError, validate_candidate


def fixture() -> dict:
    return {
        "schema_version": "bettor-arena/inception-discovery-candidate/v1",
        "candidate_id": "INCEPTION-A5-FIXTURE-001",
        "source": {
            "repository": "ed3c/example-public-source",
            "commit": "0123456789abcdef0123456789abcdef01234567",
            "tree": "89abcdef0123456789abcdef0123456789abcdef",
            "content_digest": "sha256:" + "a" * 64,
            "terms_digest": "sha256:" + "b" * 64,
            "terms_captured_before_candidate_bytes": True,
            "rights_state": "REVIEW_REQUIRED",
        },
        "target_spi": "inception/context-compactor/v1",
        "restricted_context": {
            "raw_source_bytes_allowed": False,
            "artifact_mode": "DERIVED_INTERFACE_ONLY",
            "self_claim_clean_room": False,
        },
        "benchmark": {
            "state": "NOT_EXERCISED",
            "workload_digest": None,
            "environment_digest": None,
            "repetitions": 0,
            "outcomes": [],
        },
        "state": "CANDIDATE",
        "human_admission_subject": None,
        "commercially_safe": False,
        "clean_room_equivalent": False,
        "superior": False,
        "activated": False,
        "promoted": False,
        "claims_not_proven": [
            "No commercial or legal clearance is established.",
            "No benchmark or independent Shadow has executed.",
            "No Human admission or activation exists.",
        ],
    }


def refuse(label: str, mutate, expected: str) -> None:
    value = copy.deepcopy(fixture())
    mutate(value)
    try:
        validate_candidate(value)
    except CandidateContractError as exc:
        assert expected in str(exc), f"{label}: {exc}"
        return
    raise AssertionError(f"{label}: mutation was not refused")


def main() -> None:
    decision = validate_candidate(fixture())
    assert decision.state == "CANDIDATE"
    assert decision.benchmark_state == "NOT_EXERCISED"

    refuse("mutable commit", lambda v: v["source"].__setitem__("commit", "main"), "40-hex")
    refuse("missing terms", lambda v: v["source"].__setitem__("terms_digest", "latest"), "terms_digest")
    refuse("rights after bytes", lambda v: v["source"].__setitem__("terms_captured_before_candidate_bytes", False), "terms must precede")
    refuse("restricted bytes", lambda v: v["restricted_context"].__setitem__("raw_source_bytes_allowed", True), "restricted source bytes")
    refuse("self clean room", lambda v: v["restricted_context"].__setitem__("self_claim_clean_room", True), "clean-room self claim")
    refuse("multiple SPIs", lambda v: v.__setitem__("target_spi", "spi/a|spi/b"), "one canonical SPI")
    refuse("fabricated benchmark", lambda v: v["benchmark"].__setitem__("outcomes", ["PASS"]), "must not fabricate")
    refuse("auto admit", lambda v: v.__setitem__("state", "ADMITTED"), "candidate state")
    refuse("auto commercial", lambda v: v.__setitem__("commercially_safe", True), "forbidden automated claim")
    refuse("auto promotion", lambda v: v.__setitem__("promoted", True), "forbidden automated claim")

    executed = fixture()
    executed["benchmark"] = {
        "state": "EXECUTED",
        "workload_digest": "sha256:" + "c" * 64,
        "environment_digest": "sha256:" + "d" * 64,
        "repetitions": 4,
        "outcomes": ["PASS", "FAILED", "TIMEOUT", "INCONCLUSIVE"],
    }
    validate_candidate(executed)

    print("PASS inception-a5 candidate contract and disagreement controls")


if __name__ == "__main__":
    main()
