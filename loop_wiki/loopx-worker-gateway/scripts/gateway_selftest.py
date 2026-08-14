#!/usr/bin/env python3
"""Executable positive, hollow and mutation controls for Worker Gateway v1."""

from __future__ import annotations

import copy
import tempfile
from pathlib import Path
from typing import Callable

from gateway_common import (
    GatewayError,
    host_by_id,
    load_json,
    validate_event,
    validate_receipt,
    validate_registry,
    validate_request,
    validate_request_against_host,
)
from gateway_engine import execute


def expect_red(call: Callable[[], object], name: str) -> None:
    try:
        call()
    except GatewayError:
        return
    raise GatewayError(f"negative control accepted: {name}")


def selftest(root: Path) -> None:
    module = root / "loop_wiki" / "loopx-worker-gateway"
    fixtures = module / "tests" / "fixtures"
    registry = validate_registry(load_json(fixtures / "good" / "fixture-registry.json"))
    request = validate_request(load_json(fixtures / "good" / "request.json"))
    descriptor = host_by_id(registry, request["host_id"])
    validate_request_against_host(request, descriptor)

    with tempfile.TemporaryDirectory(prefix="loopx-worker-gateway-selftest-") as temp:
        temp_root = Path(temp)

        rc, positive = execute(root=root, registry=registry, request=request, output=temp_root / "positive")
        if rc != 0 or positive["state"] != "PASS":
            raise GatewayError("positive fixture did not PASS")
        validate_receipt(positive, request, descriptor)

        hollow_request = validate_request(load_json(fixtures / "hollow" / "request.json"))
        rc, hollow = execute(root=root, registry=registry, request=hollow_request, output=temp_root / "hollow")
        if rc != 2 or hollow["state"] != "FAIL" or hollow["execution"]["exit_code"] != 7:
            raise GatewayError("hollow fixture did not preserve checked failure")

        timeout_request = copy.deepcopy(request)
        timeout_request["request_id"] = "fixture-worker-timeout"
        timeout_request["workspace"]["lease_id"] = "lease-fixture-timeout"
        timeout_request["invocation"]["args"] = ["--mode", "sleep"]
        timeout_request["invocation"]["timeout_ms"] = 50
        rc, timeout_receipt = execute(
            root=root, registry=registry, request=timeout_request, output=temp_root / "timeout"
        )
        if (
            rc != 2
            or timeout_receipt["state"] != "FAIL"
            or not timeout_receipt["execution"]["timed_out"]
            or timeout_receipt["cleanup"]["state"] != "PASS"
        ):
            raise GatewayError("timeout/process-group control failed")

        spawn_request = copy.deepcopy(request)
        spawn_request["request_id"] = "fixture-worker-spawn-timeout"
        spawn_request["workspace"]["lease_id"] = "lease-fixture-spawn-timeout"
        spawn_request["invocation"]["args"] = ["--mode", "spawn"]
        spawn_request["invocation"]["timeout_ms"] = 100
        rc, spawn_receipt = execute(
            root=root, registry=registry, request=spawn_request, output=temp_root / "spawn"
        )
        if (
            rc != 2
            or not spawn_receipt["execution"]["timed_out"]
            or not spawn_receipt["cleanup"]["descendants_terminated"]
        ):
            raise GatewayError("descendant process-group cleanup control failed")

        production = validate_registry(load_json(module / "contracts" / "host-registry.json"))
        rc, non_live = execute(
            root=root, registry=production, request=request, output=temp_root / "not-exercised"
        )
        if rc != 2 or non_live["state"] != "NOT_EXERCISED" or non_live["execution"]["executed"]:
            raise GatewayError("production registry presence was confused with execution")

        fake = copy.deepcopy(positive)
        fake["execution"]["executed"] = False
        expect_red(lambda: validate_receipt(fake, request, descriptor), "fake-pass-without-execution")

        replayed = copy.deepcopy(positive)
        replayed["host"]["host_id"] = "claude-code"
        expect_red(lambda: validate_receipt(replayed, request, descriptor), "host-replay")

        drift = copy.deepcopy(positive)
        drift["subject"]["tree"] = "3" * 40
        expect_red(lambda: validate_receipt(drift, request, descriptor), "subject-drift")

        drift = copy.deepcopy(positive)
        drift["skill_digest"] = "sha256:" + "4" * 64
        drift["context_digest"] = "sha256:" + "5" * 64
        expect_red(lambda: validate_receipt(drift, request, descriptor), "skill-context-drift")

        escalated = copy.deepcopy(positive)
        escalated["authority"]["wrote_gate_verdict"] = True
        expect_red(lambda: validate_receipt(escalated, request, descriptor), "worker-authority-escalation")

        dirty = copy.deepcopy(positive)
        dirty["cleanup"]["state"] = "FAIL"
        dirty["cleanup"]["workspace_removed"] = False
        dirty["cleanup"]["residue_paths"] = ["worker-residue"]
        expect_red(lambda: validate_receipt(dirty, request, descriptor), "cleanup-failure")

        claude_descriptor = host_by_id(registry, "claude-code")
        claude_request = copy.deepcopy(request)
        claude_request["host_id"] = "claude-code"
        event = {
            "schema_version": "loopx/worker-event/v1",
            "request_id": claude_request["request_id"],
            "host_id": "claude-code",
            "sequence": 0,
            "observed_at": "2026-08-14T00:00:00Z",
            "kind": "TOOL_EVENT_OBSERVED",
            "trace_completeness": "TOOL_EVENTS",
            "payload": {"tool": "invented-hidden-tool"},
        }
        expect_red(
            lambda: validate_event(event, claude_descriptor, claude_request),
            "gray-box-fabricated-event",
        )

        request_mutation = copy.deepcopy(request)
        request_mutation["shell"] = True
        expect_red(lambda: validate_request(request_mutation), "raw-shell-field")

        request_mutation = copy.deepcopy(request)
        request_mutation["invocation"]["args"].append("../escape")
        expect_red(lambda: validate_request(request_mutation), "path-traversal-arg")

        request_mutation = copy.deepcopy(request)
        request_mutation["invocation"]["args"].append("token=forbidden-secret-value")
        expect_red(lambda: validate_request(request_mutation), "secret-shaped-arg")

        request_mutation = copy.deepcopy(request)
        request_mutation["workspace"]["allow_reuse"] = True
        expect_red(lambda: validate_request(request_mutation), "reusable-workspace")

        request_mutation = copy.deepcopy(request)
        request_mutation["host_id"] = "ante"
        request_mutation["expected"]["minimum_trace"] = "TOOL_EVENTS"
        ante = host_by_id(registry, "ante")
        expect_red(
            lambda: validate_request_against_host(request_mutation, ante),
            "trace-above-host-ceiling",
        )
