#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("dual_agent_effect_provider", ROOT / "effect_provider_adapter.py")
assert SPEC is not None and SPEC.loader is not None
provider = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provider)
policy = provider.policy
reducer = policy.reducer
contract = reducer.contract


def expect(code: str, fn: Callable[[], Any]) -> None:
    try:
        fn()
    except (provider.ProviderBoundaryError, policy.EffectPolicyError, reducer.EffectReducerError, contract.EffectContractError) as exc:
        actual = getattr(exc, "code", "")
        if actual != code:
            raise AssertionError(f"expected {code}, got {exc}") from exc
        print(f"{code}: RED/{code}")
    else:
        raise AssertionError(f"{code}: planted control survived")


def auth(request: dict[str, Any]) -> dict[str, Any]:
    return policy.authorize_effect(
        request,
        policy.fixed_policy_observation(request),
        policy.fixed_approval(request),
        policy.fixed_precondition(request),
    )


def result(packet: dict[str, Any], outcome: str = "SUCCESS") -> dict[str, Any]:
    return {
        "schema": "bettor-arena/dual-agent-effect-ledger/provider-observation/v1",
        "effect_identity_digest": packet["effect_identity_digest"],
        "attempt_id": packet["attempt_id"],
        "provider_id": packet["provider_id"],
        "resource_id": packet["resource_id"],
        "action": packet["action"],
        "provider_subject": packet["provider_subject"],
        "outcome": outcome,
        "provider_result_digest": "a" * 64,
        "provider_native_idempotency_observed": True,
        "provider_native_idempotency_is_authority": False,
        "canonical_write_mode": "OBSERVATION_ONLY",
        "canonical_effect_state": "NOT_COMMITTED",
        "cleanup_state": "CLEAN",
        "evidence_class": "DETERMINISTIC_FIXTURE",
    }


def readback(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "bettor-arena/dual-agent-effect-ledger/target-readback/v1",
        "provider_id": packet["provider_id"],
        "resource_id": packet["resource_id"],
        "action": packet["action"],
        "verified": True,
        "digest": "b" * 64,
        "remote_version": packet["expected_remote_version"],
        "cleanup_state": "CLEAN",
        "evidence_class": "API_READBACK_FIXTURE" if packet["route_kind"] == "API" else "BROWSER_READBACK_FIXTURE",
    }


def main() -> int:
    request = contract.fixed_admission_request()
    authorization = auth(request)
    packet = provider.build_attempt_packet(authorization, credential_handle="secret://provider/demo", route_kind="API")
    observation = provider.classify_attempt_result(packet, result(packet, "SUCCESS"))
    assert observation["effect_state_proposal"] == "EFFECT_OBSERVED_PENDING_READBACK"
    rb = provider.validate_target_readback(packet, observation, readback(packet))
    proposal = provider.propose_commit(packet, observation, rb)
    assert proposal["canonical_write_mode"] == "PROPOSAL_ONLY"
    assert proposal["external_effect_state"] == "NOT_EXERCISED"
    print("P1: PASS API observation + exact readback + commit proposal only")

    timeout_obs = provider.classify_attempt_result(packet, result(packet, "TIMEOUT"))
    assert timeout_obs["effect_state_proposal"] == "RESULT_UNKNOWN"
    timeout_rb = provider.validate_target_readback(packet, timeout_obs, readback(packet))
    assert provider.propose_commit(packet, timeout_obs, timeout_rb)["mode"] == "EFFECT_COMMIT_PROPOSAL"
    print("P2: PASS timeout remains unknown until readback")

    browser_packet = provider.build_attempt_packet(authorization, credential_handle="secret://provider/demo", route_kind="BROWSER")
    browser_obs = provider.classify_attempt_result(browser_packet, result(browser_packet, "SUCCESS"))
    browser_rb = readback(browser_packet)
    assert provider.validate_target_readback(browser_packet, browser_obs, browser_rb)["route_kind"] == "BROWSER"
    print("P3: PASS browser evidence remains route-scoped")

    expect("RAW_CREDENTIAL", lambda: provider.build_attempt_packet(authorization, credential_handle="plain-secret", route_kind="API"))

    missing_rb = provider.classify_attempt_result(packet, result(packet, "SUCCESS"))
    expect("READBACK_REQUIRED", lambda: provider.propose_commit(packet, missing_rb, None))

    stale = readback(packet); stale["remote_version"] = "version-other"
    expect("READBACK_DISAGREEMENT", lambda: provider.validate_target_readback(packet, observation, stale))

    wrong_target = readback(packet); wrong_target["resource_id"] = "record-other"
    expect("READBACK_TARGET_MISMATCH", lambda: provider.validate_target_readback(packet, observation, wrong_target))

    self_commit = result(packet, "SUCCESS"); self_commit["canonical_effect_state"] = "EFFECT_COMMITTED"
    expect("PROVIDER_SELF_COMMIT", lambda: provider.classify_attempt_result(packet, self_commit))

    authority = result(packet, "SUCCESS"); authority["provider_native_idempotency_is_authority"] = True
    expect("PROVIDER_IDEMPOTENCY_AS_AUTHORITY", lambda: provider.classify_attempt_result(packet, authority))

    raw = result(packet, "SUCCESS"); raw["token_value"] = "forbidden"
    expect("RAW_CREDENTIAL", lambda: provider.classify_attempt_result(packet, raw))

    drift = result(packet, "SUCCESS"); drift["provider_subject"] = copy.deepcopy(packet["provider_subject"]); drift["provider_subject"]["commit"] = "0" * 40
    expect("MUTABLE_PROVIDER_SUBJECT", lambda: provider.classify_attempt_result(packet, drift))

    dirty = result(packet, "SUCCESS"); dirty["cleanup_state"] = "DIRTY"
    expect("CLEANUP_RESIDUE_HIDDEN", lambda: provider.classify_attempt_result(packet, dirty))

    browser_wrong = readback(browser_packet); browser_wrong["evidence_class"] = "API_READBACK_FIXTURE"
    expect("BROWSER_API_EVIDENCE_SUBSTITUTION", lambda: provider.validate_target_readback(browser_packet, browser_obs, browser_wrong))

    live = result(packet, "SUCCESS"); live["evidence_class"] = "LIVE_PASS"
    expect("FIXTURE_AS_LIVE_PROVIDER_PASS", lambda: provider.classify_attempt_result(packet, live))

    failed_obs = provider.classify_attempt_result(packet, result(packet, "FAILURE"))
    expect("READBACK_NOT_ADMISSIBLE_FOR_FAILED_ATTEMPT", lambda: provider.validate_target_readback(packet, failed_obs, readback(packet)))

    print("PASS: DA-EF-A provider/readback planted controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
