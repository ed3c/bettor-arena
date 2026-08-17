#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BLIND = ROOT / "loop_wiki/code-truth-graph-v2/scripts/blindspots.py"
FUNNEL = ROOT / "loop_wiki/code-truth-graph-v2/scripts/context_funnel.py"


def run(argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=False)


def git(repo: Path, *args: str) -> str:
    completed = run(["git", "-C", str(repo), *args])
    if completed.returncode:
        raise AssertionError(completed.stderr)
    return completed.stdout.strip()


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def request(subject: dict[str, str]) -> dict:
    return {
        "schema": "bettor-arena/context-funnel-request/v1",
        "subject": subject,
        "language": "python",
        "targets": ["app.run"],
        "providers": [
            {
                "name": "grepai",
                "role": "intent-discovery",
                "required": False,
                "state": "PASS",
            },
            {
                "name": "scip-lsp",
                "role": "semantic-fact",
                "required": False,
                "state": "NOT_EXERCISED",
            },
            {
                "name": "tree-sitter",
                "role": "syntax-slice",
                "required": False,
                "state": "NOT_EXERCISED",
            },
            {"name": "sqlite", "role": "projection", "required": True, "state": "PASS"},
            {
                "name": "code-graph-rag",
                "role": "projection",
                "required": False,
                "state": "REJECTED",
            },
        ],
        "required_lenses": ["source", "grepai", "scip-lsp", "tree-sitter"],
        "limits": {
            "max_depth": 3,
            "max_nodes": 32,
            "max_paths": 32,
            "max_output_bytes": 32768,
        },
    }


def main() -> int:
    controls: list[str] = []
    with tempfile.TemporaryDirectory(prefix="context-funnel-") as tmp:
        temp = Path(tmp)
        repo = temp / "repo"
        repo.mkdir()
        for argv in (
            ["git", "init", "-q", str(repo)],
            ["git", "-C", str(repo), "config", "user.email", "fixture@example.invalid"],
            ["git", "-C", str(repo), "config", "user.name", "Fixture"],
        ):
            completed = run(list(argv))
            assert completed.returncode == 0, completed.stderr

        files = {
            "app.py": "from util import helper\n\ndef run():\n    return helper()\n",
            "util.py": "def helper():\n    return 1\n",
            "tests/test_app.py": "from app import run\n\ndef test_run():\n    assert run() == 1\n",
        }
        for path, text in files.items():
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        assert run(["git", "-C", str(repo), "add", "."]).returncode == 0
        assert run(["git", "-C", str(repo), "commit", "-qm", "fixture"]).returncode == 0
        subject = {
            "repository": "ed3c/fixture",
            "commit": git(repo, "rev-parse", "HEAD"),
            "tree": git(repo, "rev-parse", "HEAD^{tree}"),
        }

        coverage = [
            {
                "lens": lens,
                "language": "python",
                "state": "COMPLETE",
                "freshness": "FRESH",
                "tool_identity": f"fixture:{lens}:v1",
            }
            for lens in ("source", "grepai", "scip-lsp", "tree-sitter", "test")
        ]
        observations = [
            {
                "path": "app.py",
                "source_sha256": sha(files["app.py"]),
                "language": "python",
                "lens": "source",
                "tool_identity": "fixture:source:v1",
                "source": "app.run",
                "target": "util.helper",
                "relation": "SUPPORTS_FLOW",
                "readback": "CONFIRMED",
            },
            {
                "path": "util.py",
                "source_sha256": sha(files["util.py"]),
                "language": "python",
                "lens": "scip-lsp",
                "tool_identity": "fixture:scip:v1",
                "source": "util.helper",
                "target": "builtins.int",
                "relation": "SUPPORTS_FLOW",
                "readback": "CONFIRMED",
            },
            {
                "path": "app.py",
                "source_sha256": sha(files["app.py"]),
                "language": "python",
                "lens": "tree-sitter",
                "tool_identity": "fixture:tree-sitter:v1",
                "source": "app.run",
                "target": "util.helper",
                "relation": "SUPPORTS_FLOW",
                "readback": "CONFIRMED",
            },
            {
                "path": "tests/test_app.py",
                "source_sha256": sha(files["tests/test_app.py"]),
                "language": "python",
                "lens": "test",
                "tool_identity": "fixture:test:v1",
                "source": "tests.test_run",
                "target": "app.run",
                "relation": "SUPPORTS_FLOW",
                "readback": "CONFIRMED",
            },
            {
                "path": "app.py",
                "source_sha256": sha(files["app.py"]),
                "language": "python",
                "lens": "grepai",
                "tool_identity": "fixture:grepai:v1",
                "source": "intent:run helper",
                "target": "app.run",
                "relation": "CANDIDATE",
                "readback": "MISSING",
            },
        ]
        bundle = {
            "schema": "bettor-arena/blindspots-observation-bundle/v1",
            "subject": subject,
            "coverage": coverage,
            "observations": observations,
        }
        bundle_path = temp / "bundle.json"
        bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
        db = temp / "blindspots.sqlite"
        imported = run(
            [
                sys.executable,
                str(BLIND),
                "import",
                "--db",
                str(db),
                "--bundle",
                str(bundle_path),
            ]
        )
        assert imported.returncode == 0, imported.stderr

        req = request(subject)
        req_path = temp / "request.json"
        req_path.write_text(json.dumps(req), encoding="utf-8")
        positive = run(
            [
                sys.executable,
                str(FUNNEL),
                "compile",
                "--repo",
                str(repo),
                "--db",
                str(db),
                "--request",
                str(req_path),
            ]
        )
        assert positive.returncode == 0, positive.stderr
        result = json.loads(positive.stdout)
        assert result["state"] == "PASS"
        assert result["context_plan"]["target_full_source"] == [
            "app.py",
            "tests/test_app.py",
        ]
        assert result["context_plan"]["dependency_signatures"]
        assert result["context_plan"]["downstream_callsites"]
        assert result["context_plan"]["tests"] == ["tests/test_app.py"]
        assert result["context_plan"]["candidate_anchors"]
        assert result["authority"]["advances_state"] is False

        with sqlite3.connect(db) as con:
            con.execute("UPDATE coverage SET freshness='STALE' WHERE lens='scip-lsp'")
        stale = run(
            [
                sys.executable,
                str(FUNNEL),
                "compile",
                "--repo",
                str(repo),
                "--db",
                str(db),
                "--request",
                str(req_path),
            ]
        )
        assert stale.returncode == 2
        assert json.loads(stale.stdout)["state"] == "UNKNOWN"
        controls.append("stale-index-unknown")
        with sqlite3.connect(db) as con:
            con.execute("UPDATE coverage SET freshness='FRESH' WHERE lens='scip-lsp'")

        with sqlite3.connect(db) as con:
            con.execute(
                "UPDATE observations SET source_sha256=? WHERE lens='scip-lsp'",
                ("f" * 64,),
            )
        drifted = run(
            [
                sys.executable,
                str(FUNNEL),
                "compile",
                "--repo",
                str(repo),
                "--db",
                str(db),
                "--request",
                str(req_path),
            ]
        )
        assert drifted.returncode == 2
        assert "source-drift" in drifted.stdout
        controls.append("source-drift-unknown")
        with sqlite3.connect(db) as con:
            con.execute(
                "UPDATE observations SET source_sha256=? WHERE lens='scip-lsp'",
                (sha(files["util.py"]),),
            )

        wrong = request(subject)
        wrong["subject"]["commit"] = "9" * 40
        wrong_path = temp / "wrong.json"
        wrong_path.write_text(json.dumps(wrong), encoding="utf-8")
        mismatch = run(
            [
                sys.executable,
                str(FUNNEL),
                "compile",
                "--repo",
                str(repo),
                "--db",
                str(db),
                "--request",
                str(wrong_path),
            ]
        )
        assert mismatch.returncode == 2
        controls.append("subject-mismatch")

        unbounded = request(subject)
        unbounded["limits"]["max_depth"] = 9
        unbounded_path = temp / "unbounded.json"
        unbounded_path.write_text(json.dumps(unbounded), encoding="utf-8")
        assert (
            run(
                [
                    sys.executable,
                    str(FUNNEL),
                    "compile",
                    "--repo",
                    str(repo),
                    "--db",
                    str(db),
                    "--request",
                    str(unbounded_path),
                ]
            ).returncode
            == 64
        )
        controls.append("unbounded-depth")

        corrupted = temp / "corrupt.sqlite"
        corrupted.write_text("not sqlite", encoding="utf-8")
        assert (
            run(
                [
                    sys.executable,
                    str(FUNNEL),
                    "compile",
                    "--repo",
                    str(repo),
                    "--db",
                    str(corrupted),
                    "--request",
                    str(req_path),
                ]
            ).returncode
            == 70
        )
        controls.append("mechanism-error")

        assert (
            run(
                [
                    sys.executable,
                    str(FUNNEL),
                    "compile",
                    "--repo",
                    str(repo),
                    "--db",
                    str(db),
                    "--request",
                    str(temp / "absent.json"),
                ]
            ).returncode
            == 64
        )
        controls.append("invalid-input")

    assert len(controls) == 6
    print(f"context-funnel PASS: {len(controls)} controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
