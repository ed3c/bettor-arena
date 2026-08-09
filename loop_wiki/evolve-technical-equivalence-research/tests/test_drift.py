#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from drift import assess_hard_drift, assess_soft_jitter  # noqa: E402
from selftest import assurance_states, live_observation  # noqa: E402


class DriftTest(unittest.TestCase):
    def observation(self, value: float, critical: bool = False) -> dict:
        return {
            "schema_version": "technical-equivalence-canary-observation@1.0.0",
            "metrics": {
                "candidate_appendix_rate": value,
                "completion_rate": value,
                "groundable_candidate_rate": value,
            },
            "critical_false_pass": critical,
        }

    def test_offline_pass_does_not_promote_unexercised_authority_edges(self) -> None:
        states = assurance_states(red=False, live="NOT_EXERCISED")
        self.assertEqual(states["offline_surface"], "EXERCISED_PASS")
        self.assertEqual(states["live_carrier"], "NOT_EXERCISED")
        self.assertEqual(
            states["fresh_semantic_judge"],
            "NOT_EXERCISED_REQUIRES_TWO_BLINDED_BATCHES",
        )
        self.assertEqual(states["human_admit"], "NOT_EXERCISED_REQUIRES_EXTERNAL_HUMAN")
        self.assertEqual(states["maximum_claim"], "offline_surface_implemented")

    def test_first_three_observations_only_build_baseline(self) -> None:
        result = assess_soft_jitter(
            [self.observation(1.0), self.observation(0.98)], self.observation(0.99)
        )
        self.assertEqual(result["state"], "baseline_building")
        self.assertEqual(result["baseline_count"], 2)

    def test_one_more_than_twenty_percent_degradation_blocks(self) -> None:
        result = assess_soft_jitter([self.observation(1.0)] * 3, self.observation(0.79))
        self.assertEqual(result["state"], "live_revalidation_required")
        self.assertTrue(result["over_twenty_percent"])

    def test_two_consecutive_degradations_block(self) -> None:
        history = [self.observation(1.0)] * 3 + [self.observation(0.99)]
        result = assess_soft_jitter(history, self.observation(0.98))
        self.assertEqual(result["state"], "live_revalidation_required")
        self.assertIn("candidate_appendix_rate", result["consecutive_degradations"])

    def test_critical_false_pass_blocks_without_a_baseline(self) -> None:
        result = assess_soft_jitter([], self.observation(1.0, critical=True))
        self.assertEqual(result["state"], "live_revalidation_required")
        self.assertTrue(result["critical_false_pass"])

    def test_hard_drift_detects_a_dangling_m12_pointer_and_profile_mismatch(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="equivalence-drift.") as raw:
            target = Path(raw)
            prompt = target / "loop_wiki/_template_dr/PROMPT.md"
            prompt.parent.mkdir(parents=True)
            prompt.write_text(
                "M12 .skill-bindings/dr-research-loop/technical-equivalence/PROFILE.md\n",
                encoding="utf-8",
            )
            dangling = assess_hard_drift(target)
            self.assertEqual(dangling["state"], "hard_drift")
            self.assertIn("dangling M12 pointer", dangling["failures"])

            mirror = target / ".skill-bindings/dr-research-loop/technical-equivalence"
            mirror.mkdir(parents=True)
            (mirror / "PROFILE.md").write_text("wrong\n", encoding="utf-8")
            canonical = (ROOT / "profile/technical-equivalence.md").read_text(
                encoding="utf-8"
            )
            manifest = {
                "schema_version": "technical-equivalence-mirror-manifest@1.0.0",
                "canonical_owner": "bettor-arena/loop_wiki/evolve-technical-equivalence-research",
                "source_profile_sha256": "sha256:"
                + hashlib.sha256(canonical.encode()).hexdigest(),
                "target_binding": ".skill-bindings/dr-research-loop/technical-equivalence",
            }
            (mirror / "source-manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            mismatch = assess_hard_drift(target)
            self.assertEqual(mismatch["state"], "hard_drift")
            self.assertIn("mirror PROFILE.md bytes mismatch", mismatch["failures"])

    def test_live_observation_reduces_physical_receipts_to_numeric_metrics(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="equivalence-live-observation.") as raw:
            root = Path(raw)
            adapter = {
                "adapter_receipt_digest": "sha256:" + "a" * 64,
                "invocations": [
                    {
                        "raw_exit": 0,
                        "output_sha256": "sha256:" + "b" * 64,
                        "structured_candidate_count": 1,
                    }
                ],
            }
            result = {
                "research_result_digest": "sha256:" + "c" * 64,
                "candidates": [{"inference": True}],
            }
            for name, payload in (
                ("adapter.json", adapter),
                ("result.json", result),
            ):
                (root / name).write_text(json.dumps(payload), encoding="utf-8")
            route = {
                "artifacts": {
                    "adapter_receipt": str(root / "adapter.json"),
                    "research_result": str(root / "result.json"),
                }
            }
            route_path = root / "route.json"
            route_path.write_text(json.dumps(route), encoding="utf-8")
            observation, _route = live_observation(route_path)
            self.assertEqual(
                observation["metrics"],
                {
                    "candidate_appendix_rate": 1.0,
                    "completion_rate": 1.0,
                    "groundable_candidate_rate": 1.0,
                },
            )
            self.assertEqual(
                observation["critical_false_pass_status"],
                "NOT_EXERCISED_REQUIRES_FRESH_JUDGE",
            )


if __name__ == "__main__":
    unittest.main()
