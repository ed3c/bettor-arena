#!/usr/bin/env python3
"""What a measurement is allowed to say about a claim.

The PDF carries `<30MB`, `<50MB`, TTFT figures, speedups, token counts and VPS
recommendations. Every one of them is a thing someone measured somewhere, and a
number in a document is the most persuasive object in the document -- it looks
like it was checked, because at some point it was, by someone else, on something
else.

So a claim starts at CLAIM_UNVERIFIED and only moves when something specific
happened:

    PROFILE_OBSERVED    one profile measured it and the measurement addresses it
    CORROBORATED        at least two *independent* profiles agree

Independent is the load-bearing word. Two runs on the same machine at the same
commit under the same cache state are one observation performed twice, and
running it again is the cheapest way to feel more certain without becoming so.

A source proposal is never evidence. `SOURCE_PROPOSAL` is an origin, and every
function here refuses it by name rather than scoring it low.
"""

from __future__ import annotations

from typing import Any

from bm_common import (
    SYNTHETIC_LOCALE,
    ContractError,
    digest,
    exact_object,
    non_empty_str,
)

CLAIM_KEYS = {"id", "statement", "metric", "origin", "threshold", "comparator"}

# Where a claim came from. Only MEASURED_HERE can support anything; the other two
# are named so a report can say what it is standing on.
ORIGINS = ("SOURCE_PROPOSAL", "VENDOR_BENCHMARK", "MEASURED_HERE")

COMPARATORS = {
    "lt": lambda observed, threshold: observed < threshold,
    "lte": lambda observed, threshold: observed <= threshold,
    "gt": lambda observed, threshold: observed > threshold,
    "gte": lambda observed, threshold: observed >= threshold,
}


def validate_claim(value: Any) -> dict[str, Any]:
    claim = exact_object(value, CLAIM_KEYS, "claim")
    non_empty_str(claim["id"], "claim.id")
    non_empty_str(claim["statement"], "claim.statement")
    if claim["metric"] not in ("wall_ms", "peak_rss_mb"):
        raise ContractError(
            f"claim.metric is {claim['metric']!r}; this contract measures wall_ms and "
            "peak_rss_mb. A claim about something nothing here measures is "
            "CLAIM_UNVERIFIED, and calling it a metric would hide that"
        )
    if claim["origin"] not in ORIGINS:
        raise ContractError(
            f"claim.origin is {claim['origin']!r}; known: {sorted(ORIGINS)}"
        )
    if claim["comparator"] not in COMPARATORS:
        raise ContractError(f"claim.comparator is {claim['comparator']!r}")
    if not isinstance(claim["threshold"], (int, float)) or isinstance(
        claim["threshold"], bool
    ):
        raise ContractError("claim.threshold must be a number")
    return claim


def profile_of(report: dict[str, Any]) -> dict[str, Any]:
    """The profile a report's numbers belong to, and nothing wider."""
    return {
        "locale": report["environment"]["locale"],
        "os": report["environment"]["os"],
        "arch": report["environment"]["arch"],
        "cpu": report["environment"]["cpu"],
        "image": report["environment"]["image"],
        "host": report["identities"]["host"],
        "model": report["identities"]["model"],
        "provider": report["identities"]["provider"],
        "cache_states": report["cache_states_observed"],
    }


def independent(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Two profiles are independent when the machine or the runtime differs.

    Same box, same image, same cache state means one observation performed twice.
    Repetition raises confidence in the mean; it does not widen what the mean is
    about.
    """
    return (
        left["locale"] != right["locale"]
        or left["cpu"] != right["cpu"]
        or left["arch"] != right["arch"]
        or left["image"] != right["image"]
    )


def evaluate(claim: Any, reports: list[dict[str, Any]]) -> dict[str, Any]:
    """Place a claim on the ladder. Nothing climbs it on its own."""
    claim = validate_claim(claim)

    if claim["origin"] != "MEASURED_HERE":
        return _verdict(
            claim,
            "CLAIM_UNVERIFIED",
            [],
            f"the claim's origin is {claim['origin']}. A number in a source proposal or a "
            "vendor benchmark was measured somewhere, on hardware nobody here has, with "
            "software nobody here pinned. It is a hypothesis with a decimal point",
        )

    usable: list[dict[str, Any]] = []
    notes: list[str] = []
    for report in reports:
        stats = report.get(claim["metric"])
        if stats is None:
            notes.append(
                f"a report withheld {claim['metric']}: {report.get('summary_withheld')}"
            )
            continue
        if report["environment"]["locale"] == SYNTHETIC_LOCALE:
            notes.append(
                "a synthetic report was excluded; it proves the pipeline runs and carries "
                "no timing meaning at all"
            )
            continue
        if report["moving_targets"]:
            notes.append(
                f"a report pinned to moving targets {report['moving_targets']} was "
                "excluded from corroboration; the thing measured can be replaced without "
                "the version string moving"
            )
            continue
        usable.append(report)

    if not usable:
        return _verdict(
            claim,
            "CLAIM_UNVERIFIED",
            [],
            "no report addresses this claim: "
            + ("; ".join(notes) or "none were supplied"),
            notes,
        )

    # Every usable report is checked. Choosing the ones that agree is the
    # cherry-pick this whole file exists to prevent, so the ones that disagree are
    # named in the result.
    check = COMPARATORS[claim["comparator"]]
    holds = []
    fails = []
    for report in usable:
        observed = report[claim["metric"]]["p90"]
        entry = {
            "report_digest": report["report_digest"],
            "observed_p90": observed,
            "profile": profile_of(report),
        }
        (holds if check(observed, claim["threshold"]) else fails).append(entry)

    if fails:
        return _verdict(
            claim,
            "CLAIM_UNVERIFIED",
            holds + fails,
            f"{len(fails)} of {len(usable)} profiles did not satisfy the claim. Reporting "
            "only the ones that did would be the same measurement with a different "
            "conclusion",
            notes,
        )

    profiles = [entry["profile"] for entry in holds]
    pairs = [
        (i, j)
        for i in range(len(profiles))
        for j in range(i + 1, len(profiles))
        if independent(profiles[i], profiles[j])
    ]
    if pairs:
        return _verdict(
            claim,
            "CORROBORATED",
            holds,
            f"{len(holds)} profiles agree and at least two are independent",
            notes,
        )

    return _verdict(
        claim,
        "PROFILE_OBSERVED",
        holds,
        f"observed on {len(holds)} profile(s), none of them independent of each other. "
        "Running the same box again raises confidence in the mean; it does not widen "
        "what the mean is about",
        notes,
    )


def _verdict(
    claim: dict[str, Any],
    state: str,
    evidence: list[dict[str, Any]],
    reason: str,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "loopx/benchmark-claim-verdict/v1",
        "claim": claim,
        "verdict": state,
        "evidence": evidence,
        # The profiles the verdict is about, inside the verdict. Beside it, they
        # get dropped in the sentence that quotes the number.
        "profiles": [entry["profile"] for entry in evidence],
        "reason": reason,
        "notes": notes or [],
        "promotable_by_gate": False,
        "promotion_owner": "HUMAN_ADMIT",
        "verdict_digest": digest(
            {"claim": claim["id"], "state": state, "evidence": evidence}
        ),
    }


def require_no_universal_claim(verdict: dict[str, Any]) -> None:
    """Refuse a shared-runner observation being read as a guarantee."""
    for profile in verdict["profiles"]:
        if (
            profile["locale"] in ("SHARED_RUNNER", "LOCAL")
            and verdict["verdict"] == "CORROBORATED"
        ):
            continue
        if profile["locale"] == "LOCAL" and verdict["verdict"] == "PROFILE_OBSERVED":
            raise ContractError(
                "a LOCAL observation is being read as a general guarantee. It is a fact "
                "about one machine with its own page cache, its own thermal headroom and "
                "its own idle neighbours, and a VPS has none of those"
            )
