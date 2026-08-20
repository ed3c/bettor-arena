from __future__ import annotations

from dataclasses import replace
import unittest

from benchmark_fixture import (
    ArmReceipt,
    BenchmarkFixtureError,
    BenchmarkSubject,
    Trial,
    run_matched_public_fixture_benchmark,
    validate_matched_arms,
)


class MatchedPublicBenchmarkTests(unittest.TestCase):
    def test_benchmark_is_matched_and_preserves_complete_denominator(self) -> None:
        receipt = run_matched_public_fixture_benchmark(repetitions=3)
        self.assertEqual(receipt["comparison_state"], "MATCHED_FIXTURE_NO_SUPERIORITY_CLAIM")
        self.assertEqual(receipt["subject"]["repetitions"], 3)
        self.assertEqual(
            set(receipt["outcome_denominator"]),
            {"PASS", "FAILED", "TIMEOUT", "OOM", "BLOCKED", "REJECTED", "DEFERRED", "INCONCLUSIVE"},
        )
        baseline = receipt["arms"]["protocol-oracle/v1"]
        candidate = receipt["arms"]["candidate-contract/v1"]
        self.assertEqual(
            [(x["case_id"], x["repetition"], x["outcome"]) for x in baseline],
            [(x["case_id"], x["repetition"], x["outcome"]) for x in candidate],
        )
        self.assertTrue(receipt["claims_not_proven"])

    def _arms(self) -> tuple[ArmReceipt, ArmReceipt]:
        subject = BenchmarkSubject(
            workload_digest="sha256:" + "a" * 64,
            environment_digest="sha256:" + "b" * 64,
            repetitions=1,
        )
        trials = tuple(
            Trial(case_id=case_id, repetition=1, outcome=outcome)
            for case_id, outcome in (
                ("valid", "PASS"),
                ("blocked", "BLOCKED"),
                ("rejected", "REJECTED"),
                ("failed", "FAILED"),
                ("timeout", "TIMEOUT"),
                ("oom", "OOM"),
                ("deferred", "DEFERRED"),
                ("inconclusive", "INCONCLUSIVE"),
            )
        )
        baseline = ArmReceipt("baseline", subject, "sha256:" + "c" * 64, trials)
        candidate = ArmReceipt("candidate", subject, "sha256:" + "d" * 64, trials)
        return baseline, candidate

    def test_environment_drift_is_refused(self) -> None:
        baseline, candidate = self._arms()
        drifted = replace(
            candidate,
            subject=replace(candidate.subject, environment_digest="sha256:" + "e" * 64),
        )
        with self.assertRaisesRegex(BenchmarkFixtureError, "subject mismatch"):
            validate_matched_arms(baseline, drifted)

    def test_omitted_failure_trial_is_refused(self) -> None:
        baseline, candidate = self._arms()
        truncated = replace(candidate, trials=candidate.trials[:-1])
        with self.assertRaisesRegex(BenchmarkFixtureError, "trial denominator mismatch"):
            validate_matched_arms(baseline, truncated)

    def test_duplicate_arm_identity_is_refused(self) -> None:
        baseline, candidate = self._arms()
        duplicate = replace(candidate, arm_id=baseline.arm_id)
        with self.assertRaisesRegex(BenchmarkFixtureError, "arms must be distinct"):
            validate_matched_arms(baseline, duplicate)

    def test_repetition_drift_is_refused(self) -> None:
        baseline, candidate = self._arms()
        drifted = replace(candidate, subject=replace(candidate.subject, repetitions=2))
        with self.assertRaisesRegex(BenchmarkFixtureError, "subject mismatch"):
            validate_matched_arms(baseline, drifted)


if __name__ == "__main__":
    unittest.main()
