#!/usr/bin/env python3
"""Public-seam tests for the technical-equivalence loop."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
ARENA = ROOT.parents[1]
CLI = ARENA / "loopctl" / "loopctl.sh"
sys.path.insert(0, str(ROOT))
from equivalence import (  # noqa: E402
    VerificationFailure,
    assert_head_bound,
    collect_live_research,
    completed_adapter_run,
    extract_structured_candidates,
    load_resume_cache,
    plan_gap_prompts,
)
from profile_validator import validate_schema_inventory  # noqa: E402


def canonical_digest(payload: dict) -> str:
    body = dict(payload)
    body.pop("request_digest", None)
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(raw.encode()).hexdigest()


class EquivalenceCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="equivalence-cli.")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.target = self.base / "skill-bettor"
        (self.target / ".skill-bindings/dr-research-loop").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(self.target)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.target),
                "config",
                "user.email",
                "test@example.invalid",
            ],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.target), "config", "user.name", "test"], check=True
        )
        (self.target / "README.md").write_text("fixture\n", encoding="utf-8")
        prompt = self.target / "loop_wiki/_template_dr/PROMPT.md"
        prompt.parent.mkdir(parents=True)
        prompt.write_text(
            "| M12 | 技術實作等價物 | 核心 claim 的開源可商用實作 |\n",
            encoding="utf-8",
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.target),
                "add",
                "README.md",
                "loop_wiki/_template_dr/PROMPT.md",
            ],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.target), "commit", "-qm", "fixture"], check=True
        )
        self.candidate_repo = self.base / "durable-engine"
        self.candidate_repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.candidate_repo)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.candidate_repo),
                "config",
                "user.email",
                "test@example.invalid",
            ],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.candidate_repo), "config", "user.name", "test"],
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.candidate_repo),
                "remote",
                "add",
                "origin",
                "https://github.com/example/durable-engine",
            ],
            check=True,
        )
        (self.candidate_repo / "probe.py").write_text(
            "print('BOUND')\n", encoding="utf-8"
        )
        subprocess.run(
            ["git", "-C", str(self.candidate_repo), "add", "probe.py"], check=True
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.candidate_repo),
                "commit",
                "-qm",
                "fixture behavior",
            ],
            check=True,
        )
        self.candidate_commit = subprocess.run(
            ["git", "-C", str(self.candidate_repo), "rev-parse", "HEAD"],
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        probe = subprocess.run(
            ["python3", "probe.py"],
            cwd=self.candidate_repo,
            text=True,
            capture_output=True,
            check=False,
        )
        self.audit_receipt = self.write_evidence(
            "audit",
            {
                "schema_version": "technical-equivalence-code-audit-receipt@1.0.0",
                "repo_url": "https://github.com/example/durable-engine",
                "repo_commit": self.candidate_commit,
                "checkout_path": str(self.candidate_repo),
                "audited_files": ["probe.py"],
                "code_anchors": ["probe.py:1"],
            },
        )
        self.probe_receipt = self.write_evidence(
            "probe",
            {
                "schema_version": "technical-equivalence-probe-receipt@1.0.0",
                "repo_commit": self.candidate_commit,
                "command": ["python3", "probe.py"],
                "exit": probe.returncode,
                "stdout_sha256": "sha256:"
                + hashlib.sha256(probe.stdout.encode()).hexdigest(),
                "observed_behavior": "BOUND",
            },
        )
        self.rebuild_receipt = self.write_evidence(
            "rebuild",
            {
                "schema_version": "technical-equivalence-rebuild-comparison@1.0.0",
                "repo_commit": self.candidate_commit,
                "baseline": {"state_binding": "hash-bound", "probe_exit": 0},
                "alternative": {"state_binding": "hash-bound", "probe_exit": 0},
                "decision": "equivalent-on-measured-fixture",
            },
        )

    def test_empty_schema_inventory_is_rejected(self) -> None:
        empty = self.base / "empty-schemas"
        empty.mkdir()
        errors = validate_schema_inventory(empty)
        self.assertIn("schema inventory is empty", errors)

    def write_evidence(self, name: str, payload: dict) -> dict:
        path = self.base / f"{name}-receipt.json"
        raw = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        path.write_text(raw, encoding="utf-8")
        return {
            "status": "passed",
            "path": str(path),
            "sha256": "sha256:" + hashlib.sha256(raw.encode()).hexdigest(),
        }

    def fake_antigravity(self) -> Path:
        peer = self.base / "antigravity"
        peer.mkdir()
        subprocess.run(["git", "init", "-q", str(peer)], check=True)
        subprocess.run(
            ["git", "-C", str(peer), "config", "user.email", "test@example.invalid"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(peer), "config", "user.name", "test"], check=True
        )
        (peer / "automate.js").write_text(
            "import fs from 'fs'; const i=process.argv.indexOf('--dr-once'); "
            "if(i<0) process.exit(9); const p=fs.readFileSync(process.argv[i+1],'utf8'); "
            "fs.writeFileSync(process.argv[i+2], '1. Live adapter topic with implementation details\\n'+p.slice(0,80));\n",
            encoding="utf-8",
        )
        for name in ("ui.js", "data.js", "state.js"):
            (peer / name).write_text(f"// fixture {name}\n", encoding="utf-8")
        (peer / "package.json").write_text('{"name":"lookalike"}\n', encoding="utf-8")
        (peer / "package-lock.json").write_text(
            '{"name":"lookalike","lockfileVersion":3}\n', encoding="utf-8"
        )
        subprocess.run(["git", "-C", str(peer), "add", "."], check=True)
        subprocess.run(
            ["git", "-C", str(peer), "commit", "-qm", "fixture adapter"], check=True
        )
        return peer

    def request(self) -> Path:
        payload = {
            "schema_version": "technical-equivalence-request@1.0.0",
            "request_id": "fixture-viewpoint",
            "original_intent_ssot": "fixture://human-accepted-design",
            "technical_viewpoint": "Durable workflow state must be hash-bound across resumable phases.",
            "source_anchors": [
                {
                    "repo": "fixture",
                    "commit": "a" * 40,
                    "path": "data.js",
                    "anchor": "PATH_B_REFINE_TEMPLATE",
                }
            ],
            "fixed_context": ["profile/technical-equivalence.md"],
            "iteration_context": [],
            "emergent_context": [],
            "target_binding": ".skill-bindings/dr-research-loop/technical-equivalence",
        }
        payload["request_digest"] = canonical_digest(payload)
        path = self.base / "request.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return path

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["EQUIVALENCE_RUN_ROOT"] = str(self.base / "runs")
        return subprocess.run(
            ["sh", str(CLI), *args],
            cwd=ARENA,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def first_route(self) -> dict:
        result = self.run_cli(
            "equivalence",
            "run",
            "--request",
            str(self.request()),
            "--target-peer",
            str(self.target),
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        envelope = json.loads(result.stdout)
        return json.loads(Path(envelope["artifacts"][-1]).read_text(encoding="utf-8"))

    def research_result(self, research_digest: str) -> Path:
        payload = {
            "schema_version": "technical-equivalence-research-result@1.0.0",
            "upstream_research_request_digest": research_digest,
            "provider": "fixture-gemini",
            "raw_markdown": "\n".join(
                f"{i}. Topic number {i} implementation details" for i in range(1, 8)
            ),
            "candidates": [
                {
                    "candidate_id": "durable-engine",
                    "claim": "The engine binds resumable state to immutable packet hashes.",
                    "repo_url": "https://github.com/example/durable-engine",
                    "commit": self.candidate_commit,
                    "checkout_path": str(self.candidate_repo),
                    "spdx": "Apache-2.0",
                    "source_urls": [
                        "https://github.com/example/durable-engine/blob/main/README.md"
                    ],
                    "code_anchors": ["probe.py:1"],
                    "code_audit": self.audit_receipt,
                    "probe": self.probe_receipt,
                    "load_bearing": True,
                    "equivalence_uncertain": False,
                    "wrong_decision_costly": True,
                    "rebuild_comparison": self.rebuild_receipt,
                    "inference": False,
                },
                {
                    "candidate_id": "forged-receipts",
                    "claim": "Producer says PASS without physical evidence.",
                    "repo_url": "https://github.com/example/forged",
                    "commit": "d" * 40,
                    "spdx": "Apache-2.0",
                    "source_urls": ["https://github.com/example/forged"],
                    "code_anchors": ["src/fake.py:1"],
                    "code_audit": {"status": "passed", "receipt": "sha256:" + "4" * 64},
                    "probe": {
                        "status": "passed",
                        "exit": 0,
                        "receipt": "sha256:" + "5" * 64,
                    },
                    "load_bearing": False,
                    "equivalence_uncertain": False,
                    "wrong_decision_costly": False,
                    "inference": False,
                },
                {
                    "candidate_id": "copyleft",
                    "claim": "Physical evidence exists but license is outside the commercial allowlist.",
                    "repo_url": "https://github.com/example/durable-engine",
                    "commit": self.candidate_commit,
                    "checkout_path": str(self.candidate_repo),
                    "spdx": "GPL-3.0-only",
                    "source_urls": ["https://github.com/example/durable-engine"],
                    "code_anchors": ["probe.py:1"],
                    "code_audit": self.audit_receipt,
                    "probe": self.probe_receipt,
                    "load_bearing": False,
                    "equivalence_uncertain": False,
                    "wrong_decision_costly": False,
                    "inference": False,
                },
                {
                    "candidate_id": "name-only",
                    "claim": "Repository name sounds similar.",
                    "repo_url": "https://github.com/example/name-only",
                    "commit": "c" * 40,
                    "spdx": "MIT",
                    "source_urls": ["https://github.com/example/name-only"],
                    "code_anchors": [],
                    "code_audit": {"status": "not_exercised"},
                    "probe": {"status": "not_exercised"},
                    "load_bearing": False,
                    "inference": False,
                },
                {
                    "candidate_id": "risk-omitted",
                    "claim": "Evidence exists but the producer omitted two rebuild triggers.",
                    "repo_url": "https://github.com/example/durable-engine",
                    "commit": self.candidate_commit,
                    "checkout_path": str(self.candidate_repo),
                    "spdx": "Apache-2.0",
                    "source_urls": ["https://github.com/example/durable-engine"],
                    "code_anchors": ["probe.py:1"],
                    "code_audit": self.audit_receipt,
                    "probe": self.probe_receipt,
                    "load_bearing": False,
                    "inference": False,
                },
                {
                    "candidate_id": "private-layout",
                    "claim": "No public implementation is available.",
                    "repo_url": None,
                    "commit": None,
                    "spdx": None,
                    "source_urls": ["https://example.com/primary-source"],
                    "code_anchors": [],
                    "code_audit": {"status": "not_exercised"},
                    "probe": {"status": "not_exercised"},
                    "load_bearing": False,
                    "inference": True,
                    "falsification_conditions": [
                        "A public audited implementation is found"
                    ],
                },
            ],
        }
        payload["research_result_digest"] = canonical_digest_field(
            payload, "research_result_digest"
        )
        path = self.base / "research-result.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return path

    def test_run_without_research_emits_hash_bound_research_request(self) -> None:
        result = self.run_cli(
            "equivalence",
            "run",
            "--request",
            str(self.request()),
            "--target-peer",
            str(self.target),
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        envelope = json.loads(result.stdout)
        self.assertEqual(envelope["exit"], 0)
        route_path = Path(envelope["artifacts"][-1])
        route = json.loads(route_path.read_text(encoding="utf-8"))
        self.assertEqual(route["state"], "research_required")
        research = json.loads(
            Path(route["artifacts"]["research_request"]).read_text(encoding="utf-8")
        )
        self.assertEqual(research["upstream_request_digest"], route["request_digest"])
        self.assertIn("技術實現等價物（必做）", research["prompt"])
        self.assertIn("P9 可觀測性", research["prompt"])

    def test_tampered_request_fails_closed(self) -> None:
        request = self.request()
        data = json.loads(request.read_text(encoding="utf-8"))
        data["technical_viewpoint"] = "tampered after approval"
        request.write_text(json.dumps(data), encoding="utf-8")
        result = self.run_cli(
            "equivalence",
            "run",
            "--request",
            str(request),
            "--target-peer",
            str(self.target),
        )
        self.assertEqual(result.returncode, 64)
        self.assertIn("digest mismatch", result.stderr)

    def test_research_result_is_truncated_and_grounded_before_judging(self) -> None:
        first = self.first_route()
        research = json.loads(
            Path(first["artifacts"]["research_request"]).read_text(encoding="utf-8")
        )
        result_path = self.research_result(research["research_request_digest"])
        result = self.run_cli(
            "equivalence",
            "run",
            "--request",
            str(self.request()),
            "--target-peer",
            str(self.target),
            "--research-result",
            str(result_path),
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        route = json.loads(
            Path(json.loads(result.stdout)["artifacts"][-1]).read_text(encoding="utf-8")
        )
        self.assertEqual(route["state"], "judge_required")
        verification = json.loads(
            Path(route["artifacts"]["verification_bundle"]).read_text(encoding="utf-8")
        )
        self.assertEqual(verification["gap_topics"]["selected_count"], 6)
        self.assertEqual(verification["gap_topics"]["truncated_count"], 1)
        states = {
            c["candidate_id"]: c["grounding_state"] for c in verification["candidates"]
        }
        self.assertEqual(
            states,
            {
                "durable-engine": "technical_equivalent",
                "name-only": "candidate",
                "private-layout": "[推論]",
                "forged-receipts": "candidate",
                "copyleft": "candidate",
                "risk-omitted": "candidate",
            },
        )
        self.assertEqual(verification["semantic_judge"]["status"], "NOT_EXERCISED")

    def test_passed_fresh_judge_emits_candidate_sync_bundle_without_applying(
        self,
    ) -> None:
        first = self.first_route()
        research = json.loads(
            Path(first["artifacts"]["research_request"]).read_text(encoding="utf-8")
        )
        result_path = self.research_result(research["research_request_digest"])
        pending = self.run_cli(
            "equivalence",
            "run",
            "--request",
            str(self.request()),
            "--target-peer",
            str(self.target),
            "--research-result",
            str(result_path),
            "--json",
        )
        route = json.loads(
            Path(json.loads(pending.stdout)["artifacts"][-1]).read_text(
                encoding="utf-8"
            )
        )
        verification = json.loads(
            Path(route["artifacts"]["verification_bundle"]).read_text(encoding="utf-8")
        )
        judge_packet = json.loads(
            Path(route["artifacts"]["judge_packet"]).read_text(encoding="utf-8")
        )
        execution = self.write_evidence(
            "judge-execution",
            {
                "schema_version": "technical-equivalence-judge-execution-receipt@1.0.0",
                "judge_packet_digest": judge_packet["judge_packet_digest"],
                "judge_id": "codex",
                "carrier": "codex-cli-fresh-session",
                "session_id": "fixture-fresh-session",
                "independence_contract": "fresh-zero-context",
                "verdict": "PASS",
            },
        )
        judge = {
            "schema_version": "technical-equivalence-judge-result@1.0.0",
            "upstream_verification_bundle_digest": verification[
                "verification_bundle_digest"
            ],
            "upstream_judge_packet_digest": judge_packet["judge_packet_digest"],
            "judge_id": "codex",
            "independence_contract": "fresh-zero-context",
            "verdict": "PASS",
            "findings": [],
            "quality_status": "operational_substitute",
            "execution_receipt": execution,
        }
        judge["judge_result_digest"] = canonical_digest_field(
            judge, "judge_result_digest"
        )
        Path(route["artifacts"]["expected_judge_result"]).write_text(
            json.dumps(judge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        admitted_candidate = self.run_cli(
            "equivalence",
            "run",
            "--request",
            str(self.request()),
            "--target-peer",
            str(self.target),
            "--research-result",
            str(result_path),
            "--json",
        )
        self.assertEqual(admitted_candidate.returncode, 0, admitted_candidate.stdout)
        final_route = json.loads(
            Path(json.loads(admitted_candidate.stdout)["artifacts"][-1]).read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(final_route["state"], "human_required")
        bundle = json.loads(
            Path(final_route["artifacts"]["sync_bundle"]).read_text(encoding="utf-8")
        )
        self.assertEqual(
            bundle["expected_target_head"],
            subprocess.run(
                ["git", "-C", str(self.target), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip(),
        )
        self.assertEqual(bundle["status"], "candidate_until_human_admit")
        self.assertTrue(
            all(
                item["path"].startswith(
                    ".skill-bindings/dr-research-loop/technical-equivalence/"
                )
                for item in bundle["artifacts"]
            )
        )
        self.assertFalse(
            (
                self.target / ".skill-bindings/dr-research-loop/technical-equivalence"
            ).exists()
        )

    def test_self_declared_judge_pass_without_execution_receipt_is_rejected(
        self,
    ) -> None:
        first = self.first_route()
        research = json.loads(
            Path(first["artifacts"]["research_request"]).read_text(encoding="utf-8")
        )
        result_path = self.research_result(research["research_request_digest"])
        pending = self.run_cli(
            "equivalence",
            "run",
            "--request",
            str(self.request()),
            "--target-peer",
            str(self.target),
            "--research-result",
            str(result_path),
            "--json",
        )
        route = json.loads(
            Path(json.loads(pending.stdout)["artifacts"][-1]).read_text(
                encoding="utf-8"
            )
        )
        verification = json.loads(
            Path(route["artifacts"]["verification_bundle"]).read_text(encoding="utf-8")
        )
        judge_packet = json.loads(
            Path(route["artifacts"]["judge_packet"]).read_text(encoding="utf-8")
        )
        forged = {
            "schema_version": "technical-equivalence-judge-result@1.0.0",
            "upstream_verification_bundle_digest": verification[
                "verification_bundle_digest"
            ],
            "upstream_judge_packet_digest": judge_packet["judge_packet_digest"],
            "judge_id": "codex",
            "independence_contract": "fresh-zero-context",
            "verdict": "PASS",
            "findings": [],
            "quality_status": "operational_substitute",
        }
        forged["judge_result_digest"] = canonical_digest_field(
            forged, "judge_result_digest"
        )
        Path(route["artifacts"]["expected_judge_result"]).write_text(
            json.dumps(forged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        result = self.run_cli(
            "equivalence",
            "run",
            "--request",
            str(self.request()),
            "--target-peer",
            str(self.target),
            "--research-result",
            str(result_path),
            "--json",
        )
        self.assertEqual(result.returncode, 64)
        self.assertIn("execution_receipt", json.loads(result.stdout)["stderr"])

    def test_judge_fail_lands_route_result_and_returns_declared_failure(self) -> None:
        first = self.first_route()
        research = json.loads(
            Path(first["artifacts"]["research_request"]).read_text(encoding="utf-8")
        )
        result_path = self.research_result(research["research_request_digest"])
        pending = self.run_cli(
            "equivalence",
            "run",
            "--request",
            str(self.request()),
            "--target-peer",
            str(self.target),
            "--research-result",
            str(result_path),
            "--json",
        )
        route = json.loads(
            Path(json.loads(pending.stdout)["artifacts"][-1]).read_text(
                encoding="utf-8"
            )
        )
        verification = json.loads(
            Path(route["artifacts"]["verification_bundle"]).read_text(encoding="utf-8")
        )
        judge_packet = json.loads(
            Path(route["artifacts"]["judge_packet"]).read_text(encoding="utf-8")
        )
        execution = self.write_evidence(
            "judge-fail-execution",
            {
                "schema_version": "technical-equivalence-judge-execution-receipt@1.0.0",
                "judge_packet_digest": judge_packet["judge_packet_digest"],
                "judge_id": "codex",
                "carrier": "codex-cli-fresh-session",
                "session_id": "fixture-fresh-fail-session",
                "independence_contract": "fresh-zero-context",
                "verdict": "FAIL",
            },
        )
        judge = {
            "schema_version": "technical-equivalence-judge-result@1.0.0",
            "upstream_verification_bundle_digest": verification[
                "verification_bundle_digest"
            ],
            "upstream_judge_packet_digest": judge_packet["judge_packet_digest"],
            "judge_id": "codex",
            "independence_contract": "fresh-zero-context",
            "verdict": "FAIL",
            "findings": ["candidate grounding exceeds its physical evidence"],
            "quality_status": "operational_substitute",
            "execution_receipt": execution,
        }
        judge["judge_result_digest"] = canonical_digest_field(
            judge, "judge_result_digest"
        )
        Path(route["artifacts"]["expected_judge_result"]).write_text(
            json.dumps(judge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        failed = self.run_cli(
            "equivalence",
            "run",
            "--request",
            str(self.request()),
            "--target-peer",
            str(self.target),
            "--research-result",
            str(result_path),
            "--json",
        )
        self.assertEqual(failed.returncode, 2)
        envelope = json.loads(failed.stdout)
        failed_route = json.loads(
            Path(envelope["artifacts"][-1]).read_text(encoding="utf-8")
        )
        self.assertEqual(failed_route["state"], "verification_failed")
        self.assertNotIn("sync_bundle", failed_route["artifacts"])

    def test_execute_gemini_rejects_an_unpinned_lookalike_source_peer(self) -> None:
        source = self.fake_antigravity()
        result = self.run_cli(
            "equivalence",
            "run",
            "--request",
            str(self.request()),
            "--target-peer",
            str(self.target),
            "--source-peer",
            str(source),
            "--execute-gemini",
            "--json",
        )
        self.assertEqual(result.returncode, 64)
        envelope = json.loads(result.stdout)
        self.assertIn("adapter source commit drift", envelope["stderr"])

    def test_live_gap_plan_fans_out_six_and_records_truncation(self) -> None:
        raw = "\n".join(
            f"{i}. Gap topic {i} needs production implementation evidence"
            for i in range(1, 8)
        )
        prompts, ledger = plan_gap_prompts("PRIMARY", raw)
        self.assertEqual(len(prompts), 6)
        self.assertEqual(ledger["truncated_count"], 1)
        self.assertTrue(all("技術實現等價物（必做）" in prompt for prompt in prompts))

    def test_live_gap_plan_uses_batch_fallback_when_topics_are_not_parseable(
        self,
    ) -> None:
        raw = "Unnumbered but detailed gap analysis " * 8
        prompts, ledger = plan_gap_prompts("PRIMARY", raw)
        self.assertEqual(len(prompts), 1)
        self.assertEqual(ledger["mode"], "batch-fallback")
        self.assertIn("每一缺口都要給技術實現等價物", prompts[0])

    def test_live_result_requires_machine_readable_candidate_appendix(self) -> None:
        raw = 'report\n```json\n{"technical_equivalence_candidates":[{"candidate_id":"x"}]}\n```'
        self.assertEqual(extract_structured_candidates(raw), [{"candidate_id": "x"}])

    def test_live_collection_runs_primary_then_six_gaps_and_deduplicates(self) -> None:
        calls: list[tuple[str, str]] = []

        def invoke(label: str, prompt: str) -> str:
            calls.append((label, prompt))
            topics = (
                "\n".join(
                    f"{i}. Gap topic {i} needs production implementation evidence"
                    for i in range(1, 8)
                )
                if label == "primary"
                else "gap detail"
            )
            candidate = {
                "candidate_id": label,
                "claim": "fixture",
                "inference": True,
            }
            if label == "gap-02":
                candidate["candidate_id"] = "gap-01"
            return (
                topics
                + "\n```json\n"
                + json.dumps({"technical_equivalence_candidates": [candidate]})
                + "\n```"
            )

        reports, candidates, ledger = collect_live_research("PRIMARY", invoke)
        self.assertEqual(len(calls), 7)
        self.assertEqual(
            [label for label, _ in calls],
            ["primary", "gap-01", "gap-02", "gap-03", "gap-04", "gap-05", "gap-06"],
        )
        self.assertEqual(len(reports), 7)
        self.assertEqual(len(candidates), 6)
        self.assertEqual(ledger["truncated_count"], 1)

    def test_live_collection_fails_closed_without_any_candidate_appendix(self) -> None:
        with self.assertRaisesRegex(VerificationFailure, "candidate appendix"):
            collect_live_research(
                "PRIMARY", lambda _label, _prompt: "no fenced candidate JSON"
            )

    def test_resume_cache_reuses_only_digest_bound_successes(self) -> None:
        run_dir = self.base / "resume"
        run_dir.mkdir()
        raw = run_dir / "gemini-primary-result.md"
        raw.write_text("completed report", encoding="utf-8")
        prompt = "BOUND PROMPT"
        (run_dir / "gemini-primary-prompt.md").write_text(prompt, encoding="utf-8")
        receipt = {
            "schema_version": "technical-equivalence-adapter-receipt@1.0.0",
            "research_request_digest": "sha256:request",
            "status": "failed",
            "invocations": [
                {
                    "label": "primary",
                    "prompt_sha256": "sha256:"
                    + hashlib.sha256(prompt.encode()).hexdigest(),
                    "output_sha256": "sha256:"
                    + hashlib.sha256(raw.read_bytes()).hexdigest(),
                    "raw_exit": 0,
                },
                {
                    "label": "gap-01",
                    "prompt_sha256": "sha256:failed",
                    "output_sha256": None,
                    "raw_exit": 1,
                },
            ],
        }
        receipt_path = run_dir / "adapter-receipt.json"
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        cache = load_resume_cache(run_dir, "sha256:request")
        self.assertEqual(cache["primary"]["raw"], "completed report")
        self.assertEqual(cache["primary"]["prompt"], prompt)
        self.assertNotIn("gap-01", cache)

    def test_resume_cache_rejects_tampered_output(self) -> None:
        run_dir = self.base / "tampered-resume"
        run_dir.mkdir()
        (run_dir / "gemini-primary-prompt.md").write_text("p", encoding="utf-8")
        (run_dir / "gemini-primary-result.md").write_text("tampered", encoding="utf-8")
        receipt = {
            "schema_version": "technical-equivalence-adapter-receipt@1.0.0",
            "research_request_digest": "sha256:request",
            "status": "failed",
            "invocations": [
                {
                    "label": "primary",
                    "prompt_sha256": "sha256:bad",
                    "output_sha256": "sha256:bad",
                    "raw_exit": 0,
                }
            ],
        }
        (run_dir / "adapter-receipt.json").write_text(
            json.dumps(receipt), encoding="utf-8"
        )
        with self.assertRaisesRegex(Exception, "resume evidence digest mismatch"):
            load_resume_cache(run_dir, "sha256:request")

    def test_completed_adapter_run_is_reused_without_a_new_attempt(self) -> None:
        run_dir = self.base / "completed-run"
        run_dir.mkdir()
        receipt_path = run_dir / "adapter-receipt.attempt-02.json"
        receipt_path.write_text(
            json.dumps(
                {"status": "passed", "adapter_receipt_digest": "sha256:receipt"}
            ),
            encoding="utf-8",
        )
        result_path = run_dir / "research-result.json"
        result_path.write_text(
            json.dumps(
                {
                    "upstream_research_request_digest": "sha256:request",
                    "adapter_receipt_digest": "sha256:receipt",
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(
            completed_adapter_run(run_dir, [receipt_path], "sha256:request"),
            (result_path, receipt_path),
        )

    def test_sync_source_bytes_must_exist_unchanged_at_head(self) -> None:
        repo = self.base / "source-lineage"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(
            ["git", "-C", str(repo), "config", "user.email", "test@example.invalid"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(repo), "config", "user.name", "test"], check=True
        )
        tracked = repo / "PROFILE.md"
        tracked.write_text("at head\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "PROFILE.md"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "profile"], check=True)
        self.assertIsNone(
            assert_head_bound(repo, Path("PROFILE.md"), tracked.read_bytes())
        )
        tracked.write_text("dirty replacement\n", encoding="utf-8")
        with self.assertRaisesRegex(Exception, "not the bytes at HEAD"):
            assert_head_bound(repo, Path("PROFILE.md"), tracked.read_bytes())


def canonical_digest_field(payload: dict, field: str) -> str:
    body = dict(payload)
    body.pop(field, None)
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(raw.encode()).hexdigest()


if __name__ == "__main__":
    unittest.main()
