#!/usr/bin/env python3
"""Deterministic hard-drift and live-provider jitter gates."""

from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PROFILE = ROOT / "profile" / "technical-equivalence.md"
TARGET_BINDING = ".skill-bindings/dr-research-loop/technical-equivalence"
METRICS = (
    "candidate_appendix_rate",
    "completion_rate",
    "groundable_candidate_rate",
)


def _metrics(observation: dict[str, Any]) -> dict[str, float]:
    if (
        observation.get("schema_version")
        != "technical-equivalence-canary-observation@1.0.0"
    ):
        raise ValueError("unsupported canary observation schema")
    raw = observation.get("metrics")
    if not isinstance(raw, dict):
        raise ValueError("canary metrics object absent")
    result: dict[str, float] = {}
    for name in METRICS:
        value = raw.get(name)
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not 0 <= value <= 1
        ):
            raise ValueError(f"canary metric {name} must be between 0 and 1")
        result[name] = float(value)
    if not isinstance(observation.get("critical_false_pass"), bool):
        raise ValueError("critical_false_pass must be boolean")
    return result


def assess_soft_jitter(
    admitted_history: list[dict[str, Any]],
    current: dict[str, Any],
) -> dict[str, Any]:
    current_metrics = _metrics(current)
    history_metrics = [_metrics(item) for item in admitted_history]
    critical = current["critical_false_pass"]
    if critical:
        return {
            "state": "live_revalidation_required",
            "baseline_count": len(history_metrics),
            "critical_false_pass": True,
            "over_twenty_percent": [],
            "consecutive_degradations": [],
        }
    if len(history_metrics) < 3:
        return {
            "state": "baseline_building",
            "baseline_count": len(history_metrics),
            "baseline_required": 3,
            "critical_false_pass": False,
            "over_twenty_percent": [],
            "consecutive_degradations": [],
        }

    window = history_metrics[-5:]
    reference = {
        name: statistics.median(item[name] for item in window) for name in METRICS
    }
    degraded = [name for name in METRICS if current_metrics[name] < reference[name]]
    previous = history_metrics[-1]
    consecutive = [name for name in degraded if previous[name] < reference[name]]
    over_twenty = []
    for name in degraded:
        baseline = reference[name]
        relative = (
            1.0 if baseline == 0 else (baseline - current_metrics[name]) / baseline
        )
        if relative > 0.20:
            over_twenty.append(name)
    blocked = bool(consecutive or over_twenty)
    return {
        "state": "live_revalidation_required" if blocked else "no_drift",
        "baseline_count": len(history_metrics),
        "window_count": len(window),
        "reference_median": reference,
        "current": current_metrics,
        "degraded": degraded,
        "over_twenty_percent": over_twenty,
        "consecutive_degradations": consecutive,
        "critical_false_pass": False,
    }


def assess_profile_integrity() -> dict[str, Any]:
    """Everything this repository can decide about its own canonical profile.

    Split out of `assess_hard_drift` because that function graded two unrelated
    subjects through one verdict: whether the canonical profile here is intact,
    and whether a mirror inside a *different* repository has been re-synced
    after it moved. Only the first is this loop's to prove. Fusing them meant a
    stale copy in a peer checkout could hold this repository's proof red with
    nothing here to repair — and the remediation lives behind a human admit in
    that other repository, so the red had no reachable exit at all.
    """
    failures: list[str] = []
    canonical = PROFILE.read_bytes()
    required_clauses = (
        "P9 可觀測性",
        "V5 實證／數據佐證",
        "技術實現等價物（必做）",
        "每一缺口都要給技術實現等價物",
        "technical_equivalence_candidates",
    )
    profile_text = canonical.decode("utf-8")
    for clause in required_clauses:
        if clause not in profile_text:
            failures.append(f"canonical profile required clause absent: {clause}")
    for schema in sorted((ROOT / "schemas").glob("*.json")):
        try:
            payload = json.loads(schema.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            failures.append(f"invalid schema JSON: {schema.name}")
            continue
        if not isinstance(payload, dict) or not payload.get("$id"):
            failures.append(f"schema $id absent: {schema.name}")
    return {
        "state": "intact" if not failures else "profile_drift",
        "failures": failures,
        "profile_sha256": "sha256:" + hashlib.sha256(canonical).hexdigest(),
    }


def assess_mirror_state(target_peer: Path) -> dict[str, Any]:
    """Whether the peer's admitted mirror still carries the canonical profile.

    A statement about `target_peer`, not about this repository. Reported so a
    stale mirror stays visible — suppressing it would be the worse failure —
    but never gating here, because nothing in this checkout can repair it: the
    fix is a re-sync plus admission inside that peer.
    """
    failures: list[str] = []
    canonical = PROFILE.read_bytes()

    if not target_peer.is_dir():
        return {
            "state": "peer_absent",
            "failures": [],
            "target_binding": TARGET_BINDING,
            "peer": str(target_peer),
        }

    pointer_path = target_peer / "loop_wiki/_template_dr/PROMPT.md"
    pointer_present = (
        pointer_path.is_file()
        and f"{TARGET_BINDING}/PROFILE.md" in pointer_path.read_text(encoding="utf-8")
    )
    mirror = target_peer / TARGET_BINDING
    mirror_present = mirror.is_dir()
    if not pointer_present and not mirror_present:
        return {
            "state": "not_admitted",
            "failures": failures,
            "target_binding": TARGET_BINDING,
            "peer": str(target_peer),
        }
    if pointer_present and not mirror_present:
        failures.append("dangling M12 pointer")
    if mirror_present and not pointer_present:
        failures.append("mirror exists but M12 composition pointer is absent")
    if mirror_present:
        mirror_profile = mirror / "PROFILE.md"
        manifest_path = mirror / "source-manifest.json"
        if not mirror_profile.is_file():
            failures.append("mirror PROFILE.md absent")
        elif mirror_profile.read_bytes() != canonical:
            failures.append("mirror PROFILE.md bytes mismatch")
        if not manifest_path.is_file():
            failures.append("mirror source-manifest.json absent")
        else:
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                failures.append("mirror source-manifest.json invalid")
            else:
                expected_sha = "sha256:" + hashlib.sha256(canonical).hexdigest()
                expected = {
                    "schema_version": "technical-equivalence-mirror-manifest@1.0.0",
                    "canonical_owner": "bettor-arena/loop_wiki/evolve-technical-equivalence-research",
                    "source_profile_sha256": expected_sha,
                    "target_binding": TARGET_BINDING,
                }
                for field, value in expected.items():
                    if manifest.get(field) != value:
                        failures.append(f"mirror manifest {field} mismatch")
    return {
        "state": "mirror_drift" if failures else "no_drift",
        "failures": failures,
        "target_binding": TARGET_BINDING,
        "peer": str(target_peer),
    }


def assess_hard_drift(target_peer: Path) -> dict[str, Any]:
    """Both subjects in one verdict, for callers that want the combined view.

    Kept so the pre-split contract still resolves, but no longer what the
    selftest gates on. `hard_drift` here means "either this profile is damaged
    or that mirror is stale", and a verdict that cannot say which of two
    repositories to repair is a verdict nobody can act on.
    """
    integrity = assess_profile_integrity()
    mirror = assess_mirror_state(target_peer)
    failures = list(integrity["failures"]) + list(mirror["failures"])
    if failures:
        state = "hard_drift"
    elif mirror["state"] in {"not_admitted", "peer_absent"}:
        state = "not_admitted"
    else:
        state = "no_drift"
    return {
        "state": state,
        "failures": failures,
        "target_binding": TARGET_BINDING,
        "profile_integrity": integrity["state"],
        "mirror": mirror["state"],
    }
