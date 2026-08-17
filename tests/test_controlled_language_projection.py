from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/gates/check_controlled_language_projection.py"
sys.path.insert(0, str(CHECKER.parent))
SPEC = importlib.util.spec_from_file_location(
    "controlled_language_projection_cli", CHECKER
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

MODEL = importlib.import_module("controlled_language_binding.model")
PROJECTION = importlib.import_module("controlled_language_binding.projection")


def run_checker(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-S", str(CHECKER), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=600,
        check=False,
    )


def project_fixture(scratch: Path, **kwargs: object) -> dict:
    source, selection = PROJECTION.build_fixture(scratch / "source")
    return PROJECTION.project(
        ROOT,
        source,
        scratch / "target",
        selection,
        dict(PROJECTION.CARRIERS),
        PROJECTION.CONSUMER_BINDING_BLOB,
        "SYNTHETIC_FIXTURE",
        "RETAINED",
        **kwargs,
    )


class PositiveTests(unittest.TestCase):
    def test_projection_passes(self) -> None:
        result = run_checker("--root", str(ROOT), "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        body = json.loads(result.stdout)
        self.assertEqual(body["status"], "PASS")
        self.assertEqual(body["materializer_state"], "PASS")
        self.assertEqual(body["source_class"], "SYNTHETIC_FIXTURE")
        self.assertEqual(body["selftest_controls_refused"], "NOT_EXERCISED")

    def test_all_controls_are_refused(self) -> None:
        result = run_checker("--root", str(ROOT), "--selftest", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        body = json.loads(result.stdout)
        self.assertEqual(body["selftest_controls_refused"], 23)

    def test_contract_binds_the_admitted_07a_blob(self) -> None:
        raw = (ROOT / PROJECTION.CONSUMER_BINDING_PATH).read_bytes()
        self.assertEqual(PROJECTION.blob_id(raw), PROJECTION.CONSUMER_BINDING_BLOB)
        contract = PROJECTION.validate_contract(ROOT)
        self.assertEqual(
            contract["consumer_binding_blob"], PROJECTION.CONSUMER_BINDING_BLOB
        )
        self.assertIsNone(contract["source"]["mutable_ref"])

    def test_receipt_keeps_physical_lanes_unexercised(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            receipt = project_fixture(Path(raw))
        for lane, ceiling in PROJECTION.EVIDENCE_CEILING.items():
            self.assertEqual(receipt["evidence"][lane], ceiling, lane)
        self.assertEqual(receipt["source"]["repository"], None)

    def test_receipt_carries_logical_paths_only(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            scratch = Path(raw)
            receipt = project_fixture(scratch)
        blob = json.dumps(receipt)
        self.assertNotIn(str(scratch), blob)
        self.assertNotIn(str(ROOT), blob)
        for row in receipt["files"]:
            self.assertFalse(row["path"].startswith("/"))

    def test_one_body_owns_both_carriers(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            scratch = Path(raw)
            receipt = project_fixture(scratch)
            target = scratch / "target"
            body = target / PROJECTION.CARRIERS["codex_body"]
            pointer = target / PROJECTION.CARRIERS["claude_pointer"]
            self.assertTrue(pointer.is_symlink())
            link = os.readlink(pointer)
            self.assertFalse(Path(link).is_absolute())
            self.assertEqual(link, PROJECTION.CARRIERS["claude_pointer_target"])
            self.assertEqual(pointer.resolve(), body.resolve())
            for row in receipt["files"]:
                self.assertEqual(
                    (body / row["path"]).read_bytes(),
                    (pointer / row["path"]).read_bytes(),
                )
            executable = [r["path"] for r in receipt["files"] if r["mode"] == "100755"]
            self.assertTrue(executable)
            for rel in executable:
                self.assertTrue(os.access(body / rel, os.X_OK))

    def test_failed_run_leaves_the_target_as_found(self) -> None:
        def tamper(_target: Path, body: Path, _pointer: Path) -> None:
            (body / "SKILL.md").write_text("rewritten\n", encoding="utf-8")

        with tempfile.TemporaryDirectory() as raw:
            scratch = Path(raw)
            target = scratch / "target"
            target.mkdir()
            with self.assertRaises(MODEL.Red):
                source, selection = PROJECTION.build_fixture(scratch / "source")
                PROJECTION.project(
                    ROOT,
                    source,
                    target,
                    selection,
                    dict(PROJECTION.CARRIERS),
                    PROJECTION.CONSUMER_BINDING_BLOB,
                    "SYNTHETIC_FIXTURE",
                    "RETAINED",
                    tamper=tamper,
                )
            self.assertTrue(target.is_dir())
            self.assertEqual(list(target.iterdir()), [])

    def test_materializer_does_not_touch_the_source_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            scratch = Path(raw)
            source, _ = PROJECTION.build_fixture(scratch / "source")
            before = PROJECTION.git(source, "rev-parse", "HEAD^{tree}")
            project_fixture(scratch / "run")
            after = PROJECTION.git(source, "rev-parse", "HEAD^{tree}")
        self.assertEqual(before, after)


class ControlTests(unittest.TestCase):
    def test_each_control_turns_red_with_expected_diagnostic(self) -> None:
        contract = PROJECTION.validate_contract(ROOT)
        self.assertEqual(len(contract["_cases"]), 23)
        for case in contract["_cases"]:
            with self.subTest(case=case["id"]):
                with tempfile.TemporaryDirectory() as raw:
                    with self.assertRaises(MODEL.Red) as raised:
                        PROJECTION.apply_control(case["id"], ROOT, Path(raw))
                self.assertIn(case["expected_error"], str(raised.exception))

    def test_unknown_control_id_is_an_evaluator_defect(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaises(RuntimeError):
                PROJECTION.apply_control("CTL-PROJ-999", ROOT, Path(raw))


class ExitTests(unittest.TestCase):
    def test_policy_failure_is_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw)
            for relative in (
                PROJECTION.CONSUMER_BINDING_PATH,
                PROJECTION.CONTRACT_PATH,
                PROJECTION.CASES_PATH,
            ):
                destination = target / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((ROOT / relative).read_bytes())
            path = target / PROJECTION.CONTRACT_PATH
            body = json.loads(path.read_text(encoding="utf-8"))
            body["evidence_ceiling"]["codex_physical_carrier"] = "PASS"
            path.write_text(
                json.dumps(body, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            result = run_checker("--root", str(target))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("CTL PROJECTION RED", result.stderr)

    def test_missing_or_malformed_input_is_exit_64(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw)
            self.assertEqual(run_checker("--root", str(target)).returncode, 64)
            path = target / PROJECTION.CONSUMER_BINDING_PATH
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / PROJECTION.CONSUMER_BINDING_PATH).read_bytes())
            contract = target / PROJECTION.CONTRACT_PATH
            contract.parent.mkdir(parents=True, exist_ok=True)
            contract.write_text("{broken", encoding="utf-8")
            self.assertEqual(run_checker("--root", str(target)).returncode, 64)

    def test_half_specified_operator_lane_is_exit_64(self) -> None:
        result = run_checker("--root", str(ROOT), "--source", str(ROOT))
        self.assertEqual(result.returncode, 64)
        self.assertIn("CTL PROJECTION USAGE", result.stderr)

    def test_unexpected_evaluator_failure_is_exit_70(self) -> None:
        stderr = io.StringIO()
        with mock.patch.object(
            MODULE,
            "run_projection",
            side_effect=RuntimeError("forced evaluator defect"),
        ):
            with redirect_stderr(stderr):
                code = MODULE.main(["--root", str(ROOT)])
        self.assertEqual(code, 70)
        self.assertIn("CTL PROJECTION EVALUATOR", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
