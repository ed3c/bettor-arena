from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ENGINE = Path(__file__).resolve().parents[1] / "migrate.py"
SPEC = importlib.util.spec_from_file_location("mcp_production_migrate", ENGINE)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def run_git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


class MigrationEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        run_git(self.root, "init", "-b", "migration-test")
        run_git(self.root, "config", "user.name", "MCP Test")
        run_git(self.root, "config", "user.email", "mcp-test@example.invalid")
        (self.root / "source.json").write_text(
            json.dumps({"mcpServers": {"safe": {"command": "python3"}}}) + "\n",
            encoding="utf-8",
        )
        (self.root / "target.json").write_text(
            json.dumps({"mcpServers": {"stale": {"command": "python3"}}}) + "\n",
            encoding="utf-8",
        )
        self.profile_path = self.root / "profile.json"
        self.profile_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "repo_id": "fixture",
                    "engine_sha256": MODULE._sha256_file(ENGINE),
                    "protected_branches": ["main", "master"],
                    "receipt_dir": "receipts",
                    "backup_dir": ".runtime/backups",
                    "managed_files": [
                        {"path": "source.json", "format": "json"},
                        {"path": "target.json", "format": "json"},
                    ],
                    "mirrors": [
                        {
                            "source": "source.json",
                            "target": "target.json",
                            "comparison": "json",
                        }
                    ],
                    "forbidden_paths": [".mcp.json"],
                    "capabilities": [
                        {
                            "id": "repo-agent-native",
                            "registration": "always",
                            "surface_residency": "resident",
                            "payload_residency": "demand_pull",
                            "heavy_executor": True,
                        }
                    ],
                    "probes": [
                        {
                            "id": "python-ready",
                            "argv": ["{python}", "-c", "print('ready')"],
                            "cwd": ".",
                            "timeout_sec": 5,
                        }
                    ],
                    "human_gates": [
                        {
                            "id": "claude-project-approval",
                            "description": "Human approves the project MCP and opens a new chat.",
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        run_git(self.root, "add", ".")
        run_git(self.root, "commit", "-m", "test: seed migration fixture")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def load(self):
        return MODULE.load_profile(self.root, self.profile_path)

    def test_plan_detects_json_mirror_drift(self) -> None:
        plan = MODULE.build_plan(self.load())
        self.assertEqual(plan[0].status, "drift")

    def test_repository_profile_never_mirrors_host_codex_permissions(self) -> None:
        repository_profile = json.loads(
            (ENGINE.parent / "profile.json").read_text(encoding="utf-8")
        )
        targets = {mirror["target"] for mirror in repository_profile["mirrors"]}
        self.assertNotIn(".codex/config.toml", targets)
        managed = {
            item["path"]: item for item in repository_profile["managed_files"]
        }
        self.assertIn("[mcp_servers.grepai]", managed[".codex/config.toml"]["contains"])

    def test_apply_refuses_dirty_destination(self) -> None:
        (self.root / "target.json").write_text('{"locally":"edited"}\n', encoding="utf-8")
        with self.assertRaisesRegex(MODULE.MigrationError, "dirty destination"):
            MODULE.apply_plan(self.load())

    def test_apply_mirrors_and_writes_append_only_receipt(self) -> None:
        plan = MODULE.apply_plan(self.load())
        self.assertEqual(plan[0].status, "applied")
        self.assertEqual(
            json.loads((self.root / "source.json").read_text()),
            json.loads((self.root / "target.json").read_text()),
        )
        receipts = sorted((self.root / "receipts").glob("*.json"))
        self.assertEqual(len(receipts), 1)
        self.assertEqual(json.loads(receipts[0].read_text())["action"], "apply")

    def test_apply_restores_prior_targets_when_a_later_write_fails(self) -> None:
        (self.root / "source2.json").write_text('{"source":2}\n', encoding="utf-8")
        (self.root / "target2.json").write_text('{"target":2}\n', encoding="utf-8")
        payload = json.loads(self.profile_path.read_text())
        payload["managed_files"] += [
            {"path": "source2.json", "format": "json"},
            {"path": "target2.json", "format": "json"},
        ]
        payload["mirrors"].append(
            {
                "source": "source2.json",
                "target": "target2.json",
                "comparison": "json",
            }
        )
        self.profile_path.write_text(json.dumps(payload), encoding="utf-8")
        run_git(self.root, "add", ".")
        run_git(self.root, "commit", "-m", "test: add second mirror")
        target1_before = (self.root / "target.json").read_bytes()
        target2_before = (self.root / "target2.json").read_bytes()
        atomic_write = MODULE._atomic_write

        def fail_second_target(root: Path, path: Path, content: bytes) -> None:
            if path.name == "target2.json" and path.parent == self.root.resolve():
                raise OSError("injected second target failure")
            atomic_write(root, path, content)

        MODULE._atomic_write = fail_second_target
        self.addCleanup(setattr, MODULE, "_atomic_write", atomic_write)

        with self.assertRaisesRegex(MODULE.MigrationError, "transaction failed"):
            MODULE.apply_plan(self.load())

        self.assertEqual((self.root / "target.json").read_bytes(), target1_before)
        self.assertEqual((self.root / "target2.json").read_bytes(), target2_before)
        self.assertFalse((self.root / "receipts").exists())

    def test_receipts_form_hash_chain_without_overwrite(self) -> None:
        profile = self.load()
        first = MODULE.write_receipt(profile, "verify", {"status": "pass"})
        second = MODULE.write_receipt(profile, "verify", {"status": "pass"})
        self.assertNotEqual(first, second)
        report = MODULE.check_receipt_chain(profile)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["receipt_count"], 2)

    def test_receipt_chain_rejects_tampering(self) -> None:
        profile = self.load()
        first = MODULE.write_receipt(profile, "verify", {"status": "pass"})
        MODULE.write_receipt(profile, "verify", {"status": "pass"})
        payload = json.loads(first.read_text())
        payload["details"]["status"] = "forged"
        first.chmod(0o644)
        first.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(MODULE.MigrationError, "broken receipt chain"):
            MODULE.check_receipt_chain(profile)

    def test_rollback_restores_exact_pre_apply_content(self) -> None:
        before = (self.root / "target.json").read_bytes()
        MODULE.apply_plan(self.load())
        apply_receipt = sorted((self.root / "receipts").glob("*.json"))[-1]
        MODULE.rollback(self.load(), apply_receipt)
        self.assertEqual((self.root / "target.json").read_bytes(), before)
        self.assertEqual(
            json.loads(sorted((self.root / "receipts").glob("*.json"))[-1].read_text())["action"],
            "rollback",
        )

    def test_apply_refuses_protected_branch(self) -> None:
        payload = json.loads(self.profile_path.read_text())
        payload["protected_branches"].append("migration-test")
        self.profile_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(MODULE.MigrationError, "protected branch"):
            MODULE.apply_plan(self.load())

    def test_receipt_write_refuses_protected_branch(self) -> None:
        payload = json.loads(self.profile_path.read_text())
        payload["protected_branches"].append("migration-test")
        self.profile_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(MODULE.MigrationError, "protected branch"):
            MODULE.write_receipt(self.load(), "verify", {"status": "pass"})

    def test_rollback_rejects_apply_shaped_file_outside_receipt_chain(self) -> None:
        forged = self.root / "forged.json"
        forged.write_text(
            json.dumps({"action": "apply", "details": {"changes": []}}),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(MODULE.MigrationError, "receipt directory"):
            MODULE.rollback(self.load(), forged)

    def test_verify_passes_technical_checks_but_keeps_human_gate_pending(self) -> None:
        (self.root / "target.json").write_bytes((self.root / "source.json").read_bytes())
        report = MODULE.verify_profile(self.load(), run_probes=True)
        self.assertEqual(report["status"], "technical_pass_human_pending")
        self.assertEqual(report["human_gates"][0]["status"], "pending")
        self.assertEqual(report["probes"][0]["status"], "pass")

    def test_verify_rejects_probe_that_mutates_a_managed_mirror(self) -> None:
        (self.root / "target.json").write_bytes((self.root / "source.json").read_bytes())
        payload = json.loads(self.profile_path.read_text())
        payload["probes"][0]["argv"] = [
            "{python}",
            "-c",
            "from pathlib import Path; Path('target.json').write_text('{\\\"changed\\\":true}\\n')",
        ]
        self.profile_path.write_text(json.dumps(payload), encoding="utf-8")

        report = MODULE.verify_profile(self.load(), run_probes=True)

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["post_probe_mirrors"][0]["status"], "drift")

    def test_verify_rejects_probe_that_creates_a_forbidden_path(self) -> None:
        (self.root / "target.json").write_bytes((self.root / "source.json").read_bytes())
        payload = json.loads(self.profile_path.read_text())
        payload["probes"][0]["argv"] = [
            "{python}",
            "-c",
            "from pathlib import Path; Path('.mcp.json').write_text('{}')",
        ]
        self.profile_path.write_text(json.dumps(payload), encoding="utf-8")

        report = MODULE.verify_profile(self.load(), run_probes=True)

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["post_probe_forbidden_paths"], [".mcp.json"])

    def test_skipping_declared_probes_is_not_a_pass(self) -> None:
        (self.root / "target.json").write_bytes((self.root / "source.json").read_bytes())
        report = MODULE.verify_profile(self.load(), run_probes=False)
        self.assertEqual(report["status"], "not_run")

    def test_secret_like_literal_is_rejected(self) -> None:
        (self.root / "source.json").write_text(
            json.dumps({"env": {"API_TOKEN": "literal-production-secret"}}),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(MODULE.MigrationError, "secret-like literal"):
            MODULE.verify_profile(self.load(), run_probes=False)

    def test_secret_like_literal_in_text_config_is_rejected(self) -> None:
        (self.root / "settings.yml").write_text(
            "api_token: literal-production-secret\n",
            encoding="utf-8",
        )
        payload = json.loads(self.profile_path.read_text())
        payload["managed_files"].append(
            {"path": "settings.yml", "format": "text"}
        )
        self.profile_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(MODULE.MigrationError, "secret-like literal"):
            MODULE.verify_profile(self.load(), run_probes=False)

    def test_profile_path_cannot_escape_repository(self) -> None:
        payload = json.loads(self.profile_path.read_text())
        payload["managed_files"][0]["path"] = "../outside.json"
        self.profile_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(MODULE.MigrationError, "escapes repository"):
            self.load()

    def test_profile_rejects_unknown_fields(self) -> None:
        payload = json.loads(self.profile_path.read_text())
        payload["proebs"] = payload["probes"]
        self.profile_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(MODULE.MigrationError, "unknown profile fields"):
            self.load()

    def test_profile_rejects_engine_hash_mismatch(self) -> None:
        payload = json.loads(self.profile_path.read_text())
        payload["engine_sha256"] = "0" * 64
        self.profile_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(MODULE.MigrationError, "engine hash mismatch"):
            self.load()

    def test_probe_arguments_cannot_embed_secret_literal(self) -> None:
        payload = json.loads(self.profile_path.read_text())
        payload["probes"][0]["argv"] += ["--token", "literal-production-secret"]
        self.profile_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(MODULE.MigrationError, "secret-like literal"):
            self.load()

    def test_managed_path_cannot_traverse_ancestor_symlink(self) -> None:
        outside = self.root.parent / f"{self.root.name}-outside"
        outside.mkdir()
        self.addCleanup(lambda: outside.rmdir())
        (self.root / "linked").symlink_to(outside, target_is_directory=True)
        payload = json.loads(self.profile_path.read_text())
        payload["managed_files"][0]["path"] = "linked/config.json"
        self.profile_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(MODULE.MigrationError, "escapes repository"):
            self.load()

    def test_atomic_write_rejects_ancestor_replaced_after_path_validation(self) -> None:
        inside = self.root / "inside"
        inside.mkdir()
        outside = self.root.parent / f"{self.root.name}-outside-swap"
        outside.mkdir()
        self.addCleanup(lambda: outside.rmdir())
        target = MODULE._repo_path(self.root.resolve(), "inside/value.txt")
        moved = self.root / "inside-before-swap"
        inside.rename(moved)
        inside.symlink_to(outside, target_is_directory=True)

        with self.assertRaisesRegex(MODULE.MigrationError, "symlink"):
            MODULE._atomic_write(self.root.resolve(), target, b"unsafe")

        self.assertFalse((outside / "value.txt").exists())

    def test_atomic_write_rejects_parent_namespace_rebind_during_replace(self) -> None:
        inside = self.root / "inside"
        inside.mkdir()
        outside = self.root.parent / f"{self.root.name}-outside-rebind"
        outside.mkdir()
        self.addCleanup(lambda: outside.rmdir())
        target = MODULE._repo_path(self.root.resolve(), "inside/value.txt")
        moved = self.root / "inside-before-rebind"
        replace = MODULE.os.replace
        rebound = False

        def rebind_then_replace(*args, **kwargs) -> None:
            nonlocal rebound
            if not rebound:
                rebound = True
                inside.rename(moved)
                inside.symlink_to(outside, target_is_directory=True)
            replace(*args, **kwargs)

        MODULE.os.replace = rebind_then_replace
        self.addCleanup(setattr, MODULE.os, "replace", replace)

        with self.assertRaisesRegex(MODULE.MigrationError, "namespace changed"):
            MODULE._atomic_write(self.root.resolve(), target, b"safe")

        self.assertFalse((outside / "value.txt").exists())

    def test_exclusive_receipt_write_removes_partial_file_on_fsync_failure(self) -> None:
        receipt = self.root.resolve() / "receipts" / "partial.json"
        fsync = MODULE.os.fsync
        failed = False

        def fail_fsync(_fd: int) -> None:
            nonlocal failed
            if not failed:
                failed = True
                raise OSError("injected fsync failure")
            fsync(_fd)

        MODULE.os.fsync = fail_fsync
        self.addCleanup(setattr, MODULE.os, "fsync", fsync)

        with self.assertRaisesRegex(OSError, "injected fsync failure"):
            MODULE._exclusive_write(self.root.resolve(), receipt, b"partial", 0o444)

        self.assertFalse(receipt.exists())

    def test_exclusive_receipt_rejects_parent_rebind_during_publication(self) -> None:
        receipt_dir = self.root.resolve() / "receipts"
        receipt = receipt_dir / "published.json"
        outside = self.root.parent / f"{self.root.name}-receipt-rebind"
        outside.mkdir()
        self.addCleanup(lambda: outside.rmdir())
        link = MODULE.os.link
        rebound = False

        def rebind_then_link(*args, **kwargs) -> None:
            nonlocal rebound
            if not rebound:
                rebound = True
                receipt_dir.rename(self.root.resolve() / "receipts-before-rebind")
                receipt_dir.symlink_to(outside, target_is_directory=True)
            link(*args, **kwargs)

        MODULE.os.link = rebind_then_link
        self.addCleanup(setattr, MODULE.os, "link", link)

        with self.assertRaisesRegex(MODULE.MigrationError, "namespace changed"):
            MODULE._exclusive_write(
                self.root.resolve(), receipt, b'{"complete":true}\n', 0o444
            )

        self.assertFalse(receipt.exists())
        self.assertFalse((outside / "published.json").exists())

    def test_heavy_executor_cannot_claim_resident_payload(self) -> None:
        payload = json.loads(self.profile_path.read_text())
        payload["capabilities"][0]["payload_residency"] = "resident"
        self.profile_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(MODULE.MigrationError, "heavy executor payload"):
            self.load()


if __name__ == "__main__":
    unittest.main()
