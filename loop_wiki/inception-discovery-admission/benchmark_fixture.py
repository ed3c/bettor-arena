"""Matched, public-only benchmark fixture for Inception A5 admission candidates."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Callable

from candidate_contract import CandidateContractError, validate_candidate

_SHA_PREFIX = "sha256:"
_ALLOWED_OUTCOMES = {
    "PASS",
    "FAILED",
    "TIMEOUT",
    "OOM",
    "BLOCKED",
    "REJECTED",
    "DEFERRED",
    "INCONCLUSIVE",
}
_CASES = (
    "valid",
    "blocked",
    "rejected",
    "failed",
    "timeout",
    "oom",
    "deferred",
    "inconclusive",
)
_EXPECTED = {
    "valid": "PASS",
    "blocked": "BLOCKED",
    "rejected": "REJECTED",
    "failed": "FAILED",
    "timeout": "TIMEOUT",
    "oom": "OOM",
    "deferred": "DEFERRED",
    "inconclusive": "INCONCLUSIVE",
}


class BenchmarkFixtureError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BenchmarkFixtureError(message)


def _digest_json(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _SHA_PREFIX + sha256(payload).hexdigest()


@dataclass(frozen=True)
class BenchmarkSubject:
    workload_digest: str
    environment_digest: str
    repetitions: int


@dataclass(frozen=True)
class Trial:
    case_id: str
    repetition: int
    outcome: str


@dataclass(frozen=True)
class ArmReceipt:
    arm_id: str
    subject: BenchmarkSubject
    implementation_digest: str
    trials: tuple[Trial, ...]


def _candidate() -> dict:
    return {
        "schema_version": "bettor-arena/inception-discovery-candidate/v1",
        "candidate_id": "INCEPTION-A5-BENCHMARK-FIXTURE",
        "source": {
            "repository": "ed3c/public-fixture",
            "commit": "0123456789abcdef0123456789abcdef01234567",
            "tree": "89abcdef0123456789abcdef0123456789abcdef",
            "content_digest": _SHA_PREFIX + "a" * 64,
            "terms_digest": _SHA_PREFIX + "b" * 64,
            "terms_captured_before_candidate_bytes": True,
            "rights_state": "REVIEW_REQUIRED",
        },
        "target_spi": "inception/public-fixture/v1",
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
            "This public fixture does not establish legal or commercial clearance.",
            "This benchmark does not establish external-candidate superiority.",
            "No Human admission or activation exists.",
        ],
    }


def _candidate_case(case_id: str) -> str:
    value = copy.deepcopy(_candidate())
    try:
        if case_id == "valid":
            decision = validate_candidate(value)
            _require(decision.state == "CANDIDATE", "valid fixture state drift")
            return "PASS"
        if case_id == "blocked":
            value["state"] = "BLOCKED"
            value["source"]["rights_state"] = "BLOCKED"
            decision = validate_candidate(value)
            _require(decision.state == "BLOCKED", "blocked fixture state drift")
            return "BLOCKED"
        if case_id == "rejected":
            value["source"]["commit"] = "main"
            validate_candidate(value)
            return "FAILED"
        if case_id == "failed":
            raise RuntimeError("planted candidate execution failure")
        if case_id == "timeout":
            raise TimeoutError("planted bounded timeout")
        if case_id == "oom":
            raise MemoryError("planted bounded OOM")
        if case_id == "deferred":
            value["state"] = "DEFERRED"
            decision = validate_candidate(value)
            _require(decision.state == "DEFERRED", "deferred fixture state drift")
            return "DEFERRED"
        if case_id == "inconclusive":
            value["state"] = "UNKNOWN"
            decision = validate_candidate(value)
            _require(decision.state == "UNKNOWN", "unknown fixture state drift")
            return "INCONCLUSIVE"
    except CandidateContractError:
        if case_id == "rejected":
            return "REJECTED"
        return "FAILED"
    except TimeoutError:
        return "TIMEOUT"
    except MemoryError:
        return "OOM"
    except Exception:
        return "FAILED"
    raise BenchmarkFixtureError(f"unknown benchmark case:{case_id}")


def _oracle_case(case_id: str) -> str:
    _require(case_id in _EXPECTED, f"unknown oracle case:{case_id}")
    return _EXPECTED[case_id]


def _run_arm(
    arm_id: str,
    subject: BenchmarkSubject,
    implementation_digest: str,
    runner: Callable[[str], str],
) -> ArmReceipt:
    trials: list[Trial] = []
    for repetition in range(1, subject.repetitions + 1):
        for case_id in _CASES:
            outcome = runner(case_id)
            _require(outcome in _ALLOWED_OUTCOMES, f"unknown outcome:{outcome}")
            trials.append(Trial(case_id=case_id, repetition=repetition, outcome=outcome))
    return ArmReceipt(
        arm_id=arm_id,
        subject=subject,
        implementation_digest=implementation_digest,
        trials=tuple(trials),
    )


def validate_matched_arms(baseline: ArmReceipt, candidate: ArmReceipt) -> None:
    _require(baseline.arm_id != candidate.arm_id, "benchmark arms must be distinct")
    _require(baseline.subject == candidate.subject, "benchmark subject mismatch")
    _require(baseline.subject.repetitions > 0, "benchmark repetitions")
    for arm in (baseline, candidate):
        _require(arm.implementation_digest.startswith(_SHA_PREFIX), "implementation digest")
        keys = [(trial.case_id, trial.repetition) for trial in arm.trials]
        _require(len(keys) == len(set(keys)), f"duplicate trial key:{arm.arm_id}")
        expected_keys = {
            (case_id, repetition)
            for repetition in range(1, arm.subject.repetitions + 1)
            for case_id in _CASES
        }
        _require(set(keys) == expected_keys, f"trial denominator mismatch:{arm.arm_id}")
        _require(
            all(trial.outcome in _ALLOWED_OUTCOMES for trial in arm.trials),
            f"unknown trial outcome:{arm.arm_id}",
        )
    _require(
        [(t.case_id, t.repetition) for t in baseline.trials]
        == [(t.case_id, t.repetition) for t in candidate.trials],
        "trial ordering mismatch",
    )


def run_matched_public_fixture_benchmark(repetitions: int = 3) -> dict:
    _require(repetitions > 0, "benchmark repetitions")
    workload = {
        "schema": "bettor-arena/inception-a5-public-workload/v1",
        "cases": list(_CASES),
        "target_spi": "inception/public-fixture/v1",
    }
    environment = {
        "schema": "bettor-arena/inception-a5-public-environment/v1",
        "network": "NONE",
        "external_credentials": False,
        "restricted_source_bytes": False,
    }
    subject = BenchmarkSubject(
        workload_digest=_digest_json(workload),
        environment_digest=_digest_json(environment),
        repetitions=repetitions,
    )
    baseline = _run_arm(
        "protocol-oracle/v1",
        subject,
        _digest_json({"runner": "sealed-protocol-oracle/v1", "expected": _EXPECTED}),
        _oracle_case,
    )
    candidate = _run_arm(
        "candidate-contract/v1",
        subject,
        _digest_json({"runner": "candidate-contract/v1"}),
        _candidate_case,
    )
    validate_matched_arms(baseline, candidate)
    baseline_outcomes = [trial.outcome for trial in baseline.trials]
    candidate_outcomes = [trial.outcome for trial in candidate.trials]
    _require(candidate_outcomes == baseline_outcomes, "candidate differs from sealed fixture oracle")
    return {
        "schema_version": "bettor-arena/inception-a5-matched-public-benchmark/v1",
        "subject": {
            "workload_digest": subject.workload_digest,
            "environment_digest": subject.environment_digest,
            "repetitions": subject.repetitions,
        },
        "arms": {
            baseline.arm_id: [trial.__dict__ for trial in baseline.trials],
            candidate.arm_id: [trial.__dict__ for trial in candidate.trials],
        },
        "outcome_denominator": sorted(_ALLOWED_OUTCOMES),
        "comparison_state": "MATCHED_FIXTURE_NO_SUPERIORITY_CLAIM",
        "claims_not_proven": [
            "This benchmark uses a sealed public fixture, not an external project or model.",
            "No latency, cost, quality superiority, legal clearance or clean-room equivalence is established.",
            "No external independent Shadow or Human admission has occurred.",
        ],
    }
