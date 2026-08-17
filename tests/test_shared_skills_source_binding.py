from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "gates" / "check_shared_skills_source_binding.py"
SPEC = importlib.util.spec_from_file_location("_binding_gate", SCRIPT)
assert SPEC and SPEC.loader
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class SharedSkillsSourceBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pin, self.requirements, self.binding = gate._valid_documents()

    def problems(self, pin=None, requirements=None, binding=None):
        pin = copy.deepcopy(pin or self.pin)
        requirements = copy.deepcopy(requirements or self.requirements)
        binding = copy.deepcopy(binding or self.binding)
        req_bytes = json.dumps(requirements, indent=2, sort_keys=True) + "\n"
        return (
            gate.validate_pin(pin)
            + gate.validate_requirements(requirements)
            + gate.validate_binding_shape(binding)
            + gate.validate_relation(
                pin,
                requirements,
                binding,
                requirements_digest=hashlib.sha256(req_bytes.encode()).hexdigest(),
            )
        )

    def assertCode(self, problems, code):
        self.assertTrue(
            any(item.startswith(code + ":") for item in problems),
            f"expected {code}, got {problems}",
        )

    def test_positive_contract(self):
        self.assertEqual([], self.problems())

    def test_mutable_source_ref_is_refused(self):
        self.pin["source"]["commit"] = "main"
        self.assertCode(self.problems(), "PIN_COMMIT")

    def test_machine_local_interface_path_is_refused(self):
        self.pin["interfaces"][0]["path"] = "/Users/neon/private.md"
        self.assertCode(self.problems(), "PIN_INTERFACE_PATH")

    def test_binding_must_use_exact_source(self):
        self.binding["source"]["tree"] = "f" * 40
        self.assertCode(self.problems(), "REL_SOURCE")

    def test_requirements_digest_must_be_current(self):
        self.binding["requirements_sha256"] = "f" * 64
        self.assertCode(self.problems(), "REL_REQUIREMENTS_DIGEST")

    def test_selected_skills_must_equal_requirements(self):
        self.binding["skills"].pop()
        self.assertCode(self.problems(), "REL_SHARED_SKILLS")

    def test_entrypoint_cannot_point_to_consumer_copy(self):
        self.binding["skills"][0]["entrypoint"] = ".agents/skills/alpha/SKILL.md"
        self.assertCode(self.problems(), "BINDING_ENTRYPOINT")

    def test_binding_content_digest_is_recomputed(self):
        self.binding["content_sha256"] = "0" * 64
        self.assertCode(self.problems(), "REL_BINDING_DIGEST")

    def test_consumer_surface_must_be_repo_relative(self):
        self.requirements["surfaces"]["claude"] = "/home/user/.claude/skills"
        self.assertCode(self.problems(), "REQ_SURFACE_PATH")

    def test_cli_selftest(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--selftest"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr or completed.stdout)

    def test_exact_source_readback(self):
        with tempfile.TemporaryDirectory() as directory:
            shared = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=shared, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=shared, check=True)
            subprocess.run(["git", "config", "user.name", "test"], cwd=shared, check=True)
            subprocess.run(
                ["git", "remote", "add", "origin", "https://github.com/ed3c/skills-shared.git"],
                cwd=shared,
                check=True,
            )
            interface = shared / self.pin["interfaces"][0]["path"]
            generator = shared / self.pin["generator"]["path"]
            interface.parent.mkdir(parents=True)
            generator.parent.mkdir(parents=True)
            interface.write_text(
                "# Domain Decoupling\n\n"
                "Document ID: `DOMAIN-DECOUPLING-V1`\n"
                "Document Role: `CANONICAL_METHOD`\n"
                "Repository Plane: `INSTRUCTION`\n",
                encoding="utf-8",
            )
            generator.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
            subprocess.run(["git", "add", "--all"], cwd=shared, check=True)
            subprocess.run(["git", "commit", "-qm", "fixture"], cwd=shared, check=True)
            self.pin["source"]["commit"] = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=shared, text=True
            ).strip()
            self.pin["source"]["tree"] = subprocess.check_output(
                ["git", "rev-parse", "HEAD^{tree}"], cwd=shared, text=True
            ).strip()
            self.pin["interfaces"][0]["blob"] = subprocess.check_output(
                ["git", "rev-parse", f"HEAD:{self.pin['interfaces'][0]['path']}"],
                cwd=shared,
                text=True,
            ).strip()
            self.pin["generator"]["blob"] = subprocess.check_output(
                ["git", "rev-parse", f"HEAD:{self.pin['generator']['path']}"],
                cwd=shared,
                text=True,
            ).strip()
            self.assertEqual([], gate.validate_shared_root(self.pin, shared))


if __name__ == "__main__":
    unittest.main()
