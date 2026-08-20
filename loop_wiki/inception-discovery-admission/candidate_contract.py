"""Strict public candidate contract for bounded discovery and admission."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_DENOMINATOR = {"PASS", "FAILED", "TIMEOUT", "OOM", "BLOCKED", "REJECTED", "DEFERRED", "INCONCLUSIVE"}
_CANDIDATE_STATES = {"CANDIDATE", "BLOCKED", "UNKNOWN", "DEFERRED", "REJECTED"}
_MUTABLE_IDENTITIES = {"main", "master", "latest", "nightly", "head"}


class CandidateContractError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CandidateContractError(message)


def _digest(value: object, field: str) -> str:
    _require(isinstance(value, str) and _SHA256.fullmatch(value) is not None, field)
    return value


def _text(value: object, field: str) -> str:
    _require(isinstance(value, str) and value.strip() == value and bool(value), field)
    return value


@dataclass(frozen=True)
class CandidateDecision:
    candidate_id: str
    source_commit: str
    source_tree: str
    target_spi: str
    state: str
    benchmark_state: str


def validate_candidate(value: dict[str, Any]) -> CandidateDecision:
    _require(value.get("schema_version") == "bettor-arena/inception-discovery-candidate/v1", "schema_version")
    candidate_id = _text(value.get("candidate_id"), "candidate_id")

    source = value.get("source")
    _require(isinstance(source, dict), "source")
    _text(source.get("repository"), "source.repository")
    commit = _text(source.get("commit"), "source.commit")
    tree = _text(source.get("tree"), "source.tree")
    _require(_HEX40.fullmatch(commit) is not None, "source.commit must be exact 40-hex")
    _require(_HEX40.fullmatch(tree) is not None, "source.tree must be exact 40-hex")
    _require(commit.lower() not in _MUTABLE_IDENTITIES and tree.lower() not in _MUTABLE_IDENTITIES, "mutable source identity")
    _digest(source.get("content_digest"), "source.content_digest")
    _digest(source.get("terms_digest"), "source.terms_digest")
    _require(source.get("terms_captured_before_candidate_bytes") is True, "terms must precede candidate bytes")
    _require(source.get("rights_state") in {"REVIEW_REQUIRED", "BLOCKED", "UNKNOWN"}, "rights_state")

    target_spi = _text(value.get("target_spi"), "target_spi")
    _require("," not in target_spi and "|" not in target_spi, "one canonical SPI")

    restricted = value.get("restricted_context")
    _require(isinstance(restricted, dict), "restricted_context")
    _require(restricted.get("raw_source_bytes_allowed") is False, "restricted source bytes")
    _require(restricted.get("artifact_mode") == "DERIVED_INTERFACE_ONLY", "artifact_mode")
    _require(restricted.get("self_claim_clean_room") is False, "clean-room self claim")

    benchmark = value.get("benchmark")
    _require(isinstance(benchmark, dict), "benchmark")
    benchmark_state = benchmark.get("state")
    _require(benchmark_state in {"NOT_EXERCISED", "EXECUTED"}, "benchmark.state")
    outcomes = benchmark.get("outcomes")
    _require(isinstance(outcomes, list), "benchmark.outcomes")
    if benchmark_state == "NOT_EXERCISED":
        _require(outcomes == [], "unexercised benchmark must not fabricate outcomes")
    else:
        _digest(benchmark.get("workload_digest"), "benchmark.workload_digest")
        _digest(benchmark.get("environment_digest"), "benchmark.environment_digest")
        _require(isinstance(benchmark.get("repetitions"), int) and benchmark["repetitions"] > 0, "benchmark.repetitions")
        _require(outcomes and all(item in _DENOMINATOR for item in outcomes), "benchmark denominator")

    state = value.get("state")
    _require(state in _CANDIDATE_STATES, "candidate state")
    _require(value.get("human_admission_subject") is None, "Human admission cannot be automated")
    for forbidden in ("commercially_safe", "clean_room_equivalent", "superior", "activated", "promoted"):
        _require(value.get(forbidden) in (None, False), f"forbidden automated claim:{forbidden}")
    claims = value.get("claims_not_proven")
    _require(isinstance(claims, list) and claims and len(claims) == len(set(claims)), "claims_not_proven")

    return CandidateDecision(
        candidate_id=candidate_id,
        source_commit=commit,
        source_tree=tree,
        target_spi=target_spi,
        state=state,
        benchmark_state=benchmark_state,
    )
