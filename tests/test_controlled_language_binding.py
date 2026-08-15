from __future__ import annotations

import copy
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/gates/check_controlled_language_binding.py"
sys.path.insert(0, str(CHECKER.parent))
SPEC = importlib.util.spec_from_file_location(
    "controlled_language_binding_cli", CHECKER
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

CONSTANTS = importlib.import_module("controlled_language_binding.constants")
MODEL = importlib.import_module("controlled_language_binding.model")
MUTATIONS = importlib.import_module("controlled_language_binding.mutations")
VALIDATE = importlib.import_module("controlled_language_binding.validate")

MODULE.CANDIDATE = CONSTANTS.CANDIDATE
MODULE.ROLLBACK = CONSTANTS.ROLLBACK
MODULE.FILES = CONSTANTS.FILES
MODULE.Red = MODEL.Red
MODULE.load_bundle = MODEL.load_bundle
MODULE.mutate = MUTATIONS.mutate
MODULE.validate_bundle = VALIDATE.validate_bundle


def run_checker(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-S", str(CHECKER), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


class PositiveTests(unittest.TestCase):
    def test_binding_passes(self) -> None:
        result = run_checker("--root", str(ROOT), "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        body = json.loads(result.stdout)
        self.assertEqual(body["status"], "PASS")
        self.assertEqual(body["selftest_mutations_refused"], "NOT_EXERCISED")

    def test_all_mutations_are_refused(self) -> None:
        result = run_checker("--root", str(ROOT), "--selftest", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        body = json.loads(result.stdout)
        self.assertEqual(body["selftest_mutations_refused"], 23)

    def test_candidate_and_rollback_bind_different_closures(self) -> None:
        bundle = MODULE.load_bundle(ROOT)["binding"].value
        self.assertEqual(bundle["upstream"]["candidate"], MODULE.CANDIDATE)
        self.assertEqual(bundle["upstream"]["rollback"], MODULE.ROLLBACK)
        self.assertNotEqual(MODULE.CANDIDATE["commit"], MODULE.ROLLBACK["commit"])
        self.assertNotEqual(
            MODULE.CANDIDATE["skill_tree"], MODULE.ROLLBACK["skill_tree"]
        )
        self.assertNotEqual(
            MODULE.CANDIDATE["evals_blob"], MODULE.ROLLBACK["evals_blob"]
        )

    def test_entrypoint_may_stay_equal_while_evidence_changes(self) -> None:
        self.assertEqual(
            MODULE.CANDIDATE["entrypoint_blob"], MODULE.ROLLBACK["entrypoint_blob"]
        )
        self.assertNotEqual(
            MODULE.CANDIDATE["authority_composition"]["state"],
            MODULE.ROLLBACK["authority_composition"]["state"],
        )

    def test_source_proposal_is_non_normative(self) -> None:
        source = MODULE.load_bundle(ROOT)["binding"].value["source_proposal"]
        self.assertEqual(source["classification"], "SOURCE_PROPOSAL")
        self.assertEqual(source["authority"], "NON_NORMATIVE")

    def test_fixture_termbase_is_not_production(self) -> None:
        terms = MODULE.load_bundle(ROOT)["termbase"].value
        self.assertEqual(terms["state"], "FIXTURE_ONLY")
        self.assertFalse(terms["production_admission"])
        self.assertTrue(
            all(not term["production_admission"] for term in terms["terms"])
        )

    def test_missing_physical_and_projection_lanes_are_explicit(self) -> None:
        binding = MODULE.load_bundle(ROOT)["binding"].value
        self.assertEqual(
            binding["evaluation"]["consumer_physical_matrix_state"],
            "NOT_EXERCISED",
        )
        self.assertEqual(
            binding["projection"]["generated_binding_state"], "NOT_IMPLEMENTED"
        )
        self.assertFalse(binding["writeback"]["durable_writeback_allowed"])


class MutationTests(unittest.TestCase):
    def test_each_case_turns_red_with_expected_diagnostic(self) -> None:
        base = MODULE.load_bundle(ROOT)
        for case in base["cases"].value["cases"]:
            with self.subTest(case=case["id"]):
                trial = copy.deepcopy(base)
                before = b"\0".join(trial[name].raw for name in MODULE.FILES)
                MODULE.mutate(trial, case["id"])
                after = b"\0".join(trial[name].raw for name in MODULE.FILES)
                self.assertNotEqual(before, after)
                with self.assertRaises(MODULE.Red) as raised:
                    MODULE.validate_bundle(trial)
                self.assertIn(case["expected_error"], str(raised.exception))


class ExitTests(unittest.TestCase):
    def copy_bundle(self, target: Path) -> None:
        for relative in MODULE.FILES.values():
            source = ROOT / relative
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())

    def test_policy_failure_is_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw)
            self.copy_bundle(target)
            path = target / MODULE.FILES["binding"]
            body = json.loads(path.read_text(encoding="utf-8"))
            body["upstream"]["mutable_ref"] = "main"
            path.write_text(
                json.dumps(body, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            result = run_checker("--root", str(target))
        self.assertEqual(result.returncode, 2)
        self.assertIn("CTL BINDING RED", result.stderr)

    def test_missing_or_malformed_input_is_exit_64(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw)
            self.assertEqual(run_checker("--root", str(target)).returncode, 64)
            path = target / MODULE.FILES["binding"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{broken", encoding="utf-8")
            self.assertEqual(run_checker("--root", str(target)).returncode, 64)

    def test_unexpected_evaluator_failure_is_exit_70(self) -> None:
        stderr = io.StringIO()
        with mock.patch.object(
            MODULE, "load_bundle", side_effect=RuntimeError("forced evaluator defect")
        ):
            with redirect_stderr(stderr):
                code = MODULE.main(["--root", str(ROOT)])
        self.assertEqual(code, 70)
        self.assertIn("CTL BINDING EVALUATOR", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
