#!/usr/bin/env python3
"""Offline controls for the external-transmission approval boundary."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().with_name("run-equivalence-live.py")
SPEC = importlib.util.spec_from_file_location("run_equivalence_live", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

STATUS_SCRIPT = Path(__file__).resolve().with_name("check-carrier-status.py")
STATUS_SPEC = importlib.util.spec_from_file_location(
    "check_carrier_status", STATUS_SCRIPT
)
assert STATUS_SPEC and STATUS_SPEC.loader
STATUS_MODULE = importlib.util.module_from_spec(STATUS_SPEC)
STATUS_SPEC.loader.exec_module(STATUS_MODULE)

CDP_SCRIPT = Path(__file__).resolve().with_name("check-research-cdp.py")
CDP_SPEC = importlib.util.spec_from_file_location("check_research_cdp", CDP_SCRIPT)
assert CDP_SPEC and CDP_SPEC.loader
CDP_MODULE = importlib.util.module_from_spec(CDP_SPEC)
CDP_SPEC.loader.exec_module(CDP_MODULE)


class ApprovalBoundaryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="runtime-env-carrier.")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.request = {
            "schema_version": "technical-equivalence-request@1.0.0",
            "request_id": "fixture",
            "original_intent_ssot": "fixture",
            "technical_viewpoint": "fixture",
            "source_anchors": [{"path": "fixture"}],
            "fixed_context": [],
            "iteration_context": [],
            "emergent_context": [],
            "target_binding": ".skill-bindings/dr-research-loop/technical-equivalence",
        }
        self.request["request_digest"] = MODULE.canonical_digest(
            self.request, "request_digest"
        )
        self.request_path = self.write("request.json", self.request)
        raw = self.request_path.read_bytes()
        now = datetime.now(timezone.utc)
        self.approval = {
            "schema": "runtime-env/external-transmission-admit/v1",
            "decision": "APPROVE_EXTERNAL_TRANSMISSION",
            "destination": "https://gemini.google.com/",
            "request_digest": self.request["request_digest"],
            "request_sha256": "sha256:" + MODULE.hashlib.sha256(raw).hexdigest(),
            "risk_acknowledgement": MODULE.RISK_ACKNOWLEDGEMENT,
            "decided_by": "fixture-human",
            "approved_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=5)).isoformat(),
        }
        self.approval["receipt_digest"] = MODULE.canonical_digest(
            self.approval, "receipt_digest"
        )

    def write(self, name: str, value: dict) -> Path:
        path = self.root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        path.chmod(0o600)
        return path

    def test_exact_digest_bound_approval_passes(self) -> None:
        path = self.write("approval.json", self.approval)
        result = MODULE.validate_approval(self.request_path, path)
        self.assertEqual(result["request_digest"], self.request["request_digest"])

    def test_risk_text_tamper_fails_even_with_recomputed_digest(self) -> None:
        approval = dict(self.approval)
        approval["risk_acknowledgement"] = "approve research"
        approval["receipt_digest"] = MODULE.canonical_digest(approval, "receipt_digest")
        with self.assertRaises(MODULE.ApprovalError):
            MODULE.validate_approval(
                self.request_path, self.write("tampered.json", approval)
            )

    def test_world_readable_approval_fails(self) -> None:
        path = self.write("unsafe.json", self.approval)
        path.chmod(0o644)
        with self.assertRaises(MODULE.ApprovalError):
            MODULE.validate_approval(self.request_path, path)

    def test_cross_carrier_environment_is_detected(self) -> None:
        prior = STATUS_MODULE.os.environ.get("CODEX_HOME")
        STATUS_MODULE.os.environ["CODEX_HOME"] = "/fixture/codex"
        try:
            self.assertEqual(
                STATUS_MODULE.forbidden_present(("CODEX_HOME",)), ["CODEX_HOME"]
            )
        finally:
            if prior is None:
                STATUS_MODULE.os.environ.pop("CODEX_HOME", None)
            else:
                STATUS_MODULE.os.environ["CODEX_HOME"] = prior

    def test_cdp_parser_rejects_non_loopback_hosts(self) -> None:
        parsed = CDP_MODULE.urlsplit("https://example.com:9333")
        self.assertNotIn(parsed.hostname, {"127.0.0.1", "localhost", "::1"})


if __name__ == "__main__":
    unittest.main()
