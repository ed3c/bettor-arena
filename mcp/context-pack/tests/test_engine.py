from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from context_pack_mcp.engine import ContextPackError, RepositoryContextEngine


class RepositoryContextEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.engine = RepositoryContextEngine(self.root, cache_entries=2)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write(self, relative_path: str, text: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_extracts_signature_and_implementation_evidence(self) -> None:
        self.write(
            "service.py",
            """\
class Ledger:
    async def settle(self, amount: int, hook_name: str) -> int:
        if amount <= 0:
            raise ValueError(\"amount must be positive\")
        self.balance += amount
        hook = getattr(self, hook_name)
        hook(amount)
        return self.balance
""",
        )

        pack = self.engine.build_python_context_pack(
            "service.py", symbol="Ledger.settle", max_bytes=8_000
        )

        kinds = {item["kind"] for item in pack["evidence"]}
        self.assertEqual(
            kinds,
            {"signature", "guard", "raise", "mutation", "unresolved_dynamic_call", "call", "return"},
        )
        self.assertEqual(pack["completeness"], "partial")
        self.assertEqual(len(pack["source_sha256"]), 64)
        self.assertLessEqual(pack["context_bytes"], pack["max_bytes"])
        self.assertTrue(all(item["source_ref"].startswith("service.py:") for item in pack["evidence"]))

    def test_rejects_absolute_traversal_and_symlink_escape(self) -> None:
        outside = Path(self.tempdir.name).parent / "context-pack-outside.py"
        outside.write_text("def outside(): pass\n", encoding="utf-8")
        self.addCleanup(outside.unlink, missing_ok=True)
        (self.root / "escape.py").symlink_to(outside)

        outside_dir = Path(self.tempdir.name).parent / "context-pack-outside-dir"
        outside_dir.mkdir(exist_ok=True)
        (outside_dir / "nested.py").write_text("def outside(): pass\n", encoding="utf-8")
        self.addCleanup(outside_dir.rmdir)
        self.addCleanup((outside_dir / "nested.py").unlink, missing_ok=True)
        (self.root / "escape-dir").symlink_to(outside_dir, target_is_directory=True)

        for candidate in (
            str(outside),
            "../context-pack-outside.py",
            "escape.py",
            "escape-dir/nested.py",
        ):
            with self.subTest(candidate=candidate):
                with self.assertRaises(ContextPackError):
                    self.engine.build_python_context_pack(candidate)

    def test_rejects_unsupported_source_and_missing_symbol(self) -> None:
        self.write("notes.md", "# no\n")
        self.write("service.py", "def known():\n    return 1\n")
        with self.assertRaisesRegex(ContextPackError, "only .py"):
            self.engine.build_python_context_pack("notes.md")
        with self.assertRaisesRegex(ContextPackError, "symbol not found"):
            self.engine.build_python_context_pack("service.py", symbol="missing")

    def test_hash_and_cache_change_with_source_bytes(self) -> None:
        path = self.write("service.py", "def value():\n    return 1\n")
        first = self.engine.build_python_context_pack("service.py")
        second = self.engine.build_python_context_pack("service.py")
        self.assertEqual(first, second)
        self.assertEqual(self.engine.status()["cache_entries"]["current"], 1)

        path.write_text("def value():\n    return 2\n", encoding="utf-8")
        changed = self.engine.build_python_context_pack("service.py")
        self.assertNotEqual(first["source_sha256"], changed["source_sha256"])

    def test_budget_retains_mandatory_facts_and_reports_truncation(self) -> None:
        calls = "\n".join(f"    step_{index}()" for index in range(40))
        self.write(
            "service.py",
            "def run(name: str):\n    callback = getattr(registry, name)\n" + calls + "\n    return callback()\n",
        )
        pack = self.engine.build_python_context_pack("service.py", symbol="run", max_bytes=1_500)
        kinds = [item["kind"] for item in pack["evidence"]]
        self.assertIn("signature", kinds)
        self.assertIn("unresolved_dynamic_call", kinds)
        self.assertTrue(pack["truncated"])
        self.assertGreater(pack["omitted_evidence_count"], 0)
        self.assertLessEqual(pack["context_bytes"], 1_500)

    def test_rejects_out_of_range_budget(self) -> None:
        self.write("service.py", "def value():\n    return 1\n")
        with self.assertRaisesRegex(ContextPackError, "between"):
            self.engine.build_python_context_pack("service.py", max_bytes=1_000)

    def test_mandatory_signature_is_never_silently_truncated(self) -> None:
        annotation = "X" * 400
        self.write("service.py", f"def run(value: '{annotation}'):\n    return value\n")
        pack = self.engine.build_python_context_pack("service.py", symbol="run", max_bytes=8_000)
        signature = next(item for item in pack["evidence"] if item["kind"] == "signature")
        self.assertGreater(len(signature["text"]), 280)
        self.assertFalse(signature["text_truncated"])


if __name__ == "__main__":
    unittest.main()
