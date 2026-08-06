from __future__ import annotations

import ast
import hashlib
import json
import os
import platform
import statistics
import subprocess
import time
import tracemalloc
from pathlib import Path

from context_pack_mcp.engine import RepositoryContextEngine


ROOT = Path(__file__).resolve().parents[3]
FIXTURE = "mcp/context-pack/tests/fixtures/sample_service.py"
EXPECTED_KINDS = {"guard", "raise", "mutation", "unresolved_dynamic_call", "call", "return"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature_only(source: str) -> dict[str, object]:
    tree = ast.parse(source)
    signatures: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            signatures.append(f"class {node.name}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
            signatures.append(f"{prefix} {node.name}({ast.unparse(node.args)})")
    return {"signatures": signatures}


def measure(callable_, iterations: int = 500) -> dict[str, int]:
    durations: list[int] = []
    tracemalloc.start()
    for _ in range(iterations):
        start = time.perf_counter_ns()
        callable_()
        durations.append(time.perf_counter_ns() - start)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    durations.sort()
    return {
        "iterations": iterations,
        "p50_ns": int(statistics.median(durations)),
        "p95_ns": durations[int(iterations * 0.95) - 1],
        "tracemalloc_peak_bytes": peak,
    }


def main() -> None:
    source = (ROOT / FIXTURE).read_text(encoding="utf-8")
    engine = RepositoryContextEngine(ROOT, cache_entries=0)

    signature_payload = signature_only(source)
    evidence_payload = engine.build_python_context_pack(FIXTURE, symbol="Ledger.settle", max_bytes=8_000)
    evidence_kinds = {item["kind"] for item in evidence_payload["evidence"]}
    warm_engine = RepositoryContextEngine(ROOT)
    warm_engine.build_python_context_pack(FIXTURE, symbol="Ledger.settle", max_bytes=8_000)

    receipt = {
        "schema_version": "context-pack-comparison/v1",
        "scope": "pinned sample_service.py fixture; results do not generalize to arbitrary repositories",
        "machine": {
            "architecture": platform.machine(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "page_size_bytes": os.sysconf("SC_PAGE_SIZE"),
        },
        "replay_binding": {
            "repository_head": subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip(),
            "benchmark_script_sha256": sha256_file(Path(__file__)),
            "engine_sha256": sha256_file(
                ROOT / "mcp/context-pack/src/context_pack_mcp/engine.py"
            ),
            "fixture_sha256": sha256_file(ROOT / FIXTURE),
            "uv_lock_sha256": sha256_file(ROOT / "mcp/context-pack/uv.lock"),
        },
        "source_bytes": len(source.encode("utf-8")),
        "signature_only": {
            "context_bytes": len(json.dumps(signature_payload, sort_keys=True).encode("utf-8")),
            "semantic_recall": 0.0,
            "measurement": measure(lambda: signature_only(source)),
        },
        "evidence_budget": {
            "context_bytes": evidence_payload["context_bytes"],
            "semantic_recall": len(EXPECTED_KINDS & evidence_kinds) / len(EXPECTED_KINDS),
            "source_sha256": evidence_payload["source_sha256"],
            "cold_measurement": measure(
                lambda: RepositoryContextEngine(ROOT, cache_entries=0).build_python_context_pack(
                    FIXTURE, symbol="Ledger.settle", max_bytes=8_000
                )
            ),
            "warm_measurement": measure(
                lambda: warm_engine.build_python_context_pack(
                    FIXTURE, symbol="Ledger.settle", max_bytes=8_000
                )
            ),
        },
        "conclusion": (
            "Signature-only is smaller but omits all pinned implementation-semantic categories; "
            "evidence-budget preserves them with explicit partial completeness and source binding."
        ),
        "non_claims": [
            "Local page alignment does not control remote prompt caching.",
            "This fixture does not establish a fixed process-RAM ceiling.",
            "This benchmark does not claim TypeScript support.",
        ],
    }
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
