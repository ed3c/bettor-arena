from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RECEIPT = ROOT / "mcp/context-pack/benchmarks/receipts/m1-pro-2026-07-29.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BenchmarkReceiptTests(unittest.TestCase):
    def test_replay_inputs_match_receipt_hashes(self) -> None:
        receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
        binding = receipt["replay_binding"]
        expected = {
            "benchmark_script_sha256": ROOT / "mcp/context-pack/benchmarks/compare_extractors.py",
            "engine_sha256": ROOT / "mcp/context-pack/src/context_pack_mcp/engine.py",
            "fixture_sha256": ROOT / "mcp/context-pack/tests/fixtures/sample_service.py",
            "uv_lock_sha256": ROOT / "mcp/context-pack/uv.lock",
        }
        for field, path in expected.items():
            with self.subTest(field=field):
                self.assertEqual(binding[field], sha256_file(path))


if __name__ == "__main__":
    unittest.main()
