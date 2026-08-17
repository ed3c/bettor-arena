#!/usr/bin/env python3
"""Subject-bound SQLite Blindspots evidence ledger.

SQLite stores normalized observations and coverage for one immutable repository
subject. It is disposable and rebuildable. Provider/model candidates remain
below source/test/runtime authority and an empty result is never absence proof.

Exit codes: 0 PASS, 2 deterministic refusal, 64 invalid input, 70 mechanism error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any

OK, REFUSED, INVALID, MECHANISM = 0, 2, 64, 70
BUNDLE_SCHEMA = "bettor-arena/blindspots-observation-bundle/v1"
RESULT_SCHEMA = "bettor-arena/blindspots-query-result/v1"
LENSES = {"source", "grepai", "scip-lsp", "tree-sitter", "test", "runtime"}
COVERAGE_STATES = {"COMPLETE", "PARTIAL", "UNSUPPORTED", "ABSENT"}
FRESHNESS = {"FRESH", "STALE", "UNKNOWN"}
RELATIONS = {"SUPPORTS_FLOW", "DENIES_FLOW", "CANDIDATE"}
READBACK = {"CONFIRMED", "MISSING", "DRIFTED", "NOT_REQUIRED"}
SHA40 = 40
SHA256 = 64


class Refusal(ValueError):
    pass


class Invalid(ValueError):
    pass


def require(condition: bool, message: str, *, invalid: bool = False) -> None:
    if condition:
        return
    if invalid:
        raise Invalid(message)
    raise Refusal(message)


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256(value: Any) -> str:
    data = value if isinstance(value, bytes) else canonical(value).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Invalid(f"ABSENT: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise Invalid(f"UNREADABLE_JSON: {path}: {exc}") from exc


def valid_hex(value: Any, size: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == size
        and all(c in "0123456789abcdef" for c in value)
    )


def validate_bundle(value: Any) -> dict[str, Any]:
    require(isinstance(value, dict), "bundle must be an object", invalid=True)
    require(value.get("schema") == BUNDLE_SCHEMA, "bundle schema drift", invalid=True)
    subject = value.get("subject")
    require(isinstance(subject, dict), "subject missing", invalid=True)
    require(
        isinstance(subject.get("repository"), str) and subject["repository"],
        "subject.repository missing",
        invalid=True,
    )
    require(
        valid_hex(subject.get("commit"), SHA40), "subject.commit invalid", invalid=True
    )
    require(valid_hex(subject.get("tree"), SHA40), "subject.tree invalid", invalid=True)
    coverage = value.get("coverage")
    observations = value.get("observations")
    require(isinstance(coverage, list), "coverage must be a list", invalid=True)
    require(isinstance(observations, list), "observations must be a list", invalid=True)
    seen_coverage: set[tuple[str, str]] = set()
    for index, item in enumerate(coverage):
        require(isinstance(item, dict), f"coverage[{index}] invalid", invalid=True)
        lens, language = item.get("lens"), item.get("language")
        require(lens in LENSES, f"coverage[{index}].lens invalid", invalid=True)
        require(
            isinstance(language, str) and language,
            f"coverage[{index}].language invalid",
            invalid=True,
        )
        require(
            item.get("state") in COVERAGE_STATES,
            f"coverage[{index}].state invalid",
            invalid=True,
        )
        require(
            item.get("freshness") in FRESHNESS,
            f"coverage[{index}].freshness invalid",
            invalid=True,
        )
        require(
            isinstance(item.get("tool_identity"), str) and item["tool_identity"],
            f"coverage[{index}].tool_identity invalid",
            invalid=True,
        )
        key = (lens, language)
        require(key not in seen_coverage, f"duplicate coverage: {key}")
        seen_coverage.add(key)
    for index, item in enumerate(observations):
        require(isinstance(item, dict), f"observations[{index}] invalid", invalid=True)
        require(
            isinstance(item.get("path"), str)
            and item["path"]
            and not Path(item["path"]).is_absolute()
            and ".." not in Path(item["path"]).parts,
            f"observations[{index}].path invalid",
            invalid=True,
        )
        require(
            valid_hex(item.get("source_sha256"), SHA256),
            f"observations[{index}].source_sha256 invalid",
            invalid=True,
        )
        require(
            item.get("lens") in LENSES,
            f"observations[{index}].lens invalid",
            invalid=True,
        )
        require(
            isinstance(item.get("language"), str) and item["language"],
            f"observations[{index}].language invalid",
            invalid=True,
        )
        require(
            isinstance(item.get("tool_identity"), str) and item["tool_identity"],
            f"observations[{index}].tool_identity invalid",
            invalid=True,
        )
        require(
            isinstance(item.get("source"), str) and item["source"],
            f"observations[{index}].source invalid",
            invalid=True,
        )
        require(
            isinstance(item.get("target"), str) and item["target"],
            f"observations[{index}].target invalid",
            invalid=True,
        )
        require(
            item.get("relation") in RELATIONS,
            f"observations[{index}].relation invalid",
            invalid=True,
        )
        require(
            item.get("readback") in READBACK,
            f"observations[{index}].readback invalid",
            invalid=True,
        )
        if (
            item["lens"] in {"grepai", "scip-lsp", "tree-sitter"}
            and item["relation"] != "CANDIDATE"
        ):
            require(
                item["readback"] == "CONFIRMED",
                f"observations[{index}]: promoted analyzer relation lacks source readback",
            )
    return value


def connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def initialize(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS meta (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS coverage (
              lens TEXT NOT NULL,
              language TEXT NOT NULL,
              state TEXT NOT NULL,
              freshness TEXT NOT NULL,
              tool_identity TEXT NOT NULL,
              PRIMARY KEY (lens, language)
            );
            CREATE TABLE IF NOT EXISTS observations (
              observation_id TEXT PRIMARY KEY,
              path TEXT NOT NULL,
              source_sha256 TEXT NOT NULL,
              language TEXT NOT NULL,
              lens TEXT NOT NULL,
              tool_identity TEXT NOT NULL,
              source TEXT NOT NULL,
              target TEXT NOT NULL,
              relation TEXT NOT NULL,
              readback TEXT NOT NULL,
              span TEXT,
              note TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_observation_pair ON observations(source, target);
            CREATE INDEX IF NOT EXISTS idx_observation_lens ON observations(lens, language);
            """
        )


def db_subject(db: sqlite3.Connection) -> dict[str, str] | None:
    rows = {
        row["key"]: row["value"]
        for row in db.execute(
            "SELECT key, value FROM meta WHERE key IN ('repository','commit','tree')"
        )
    }
    if not rows:
        return None
    require(set(rows) == {"repository", "commit", "tree"}, "partial database subject")
    return rows


def bind_subject(db: sqlite3.Connection, subject: dict[str, str]) -> None:
    existing = db_subject(db)
    if existing is not None:
        require(existing == subject, "database subject mismatch")
        return
    db.executemany("INSERT INTO meta(key,value) VALUES (?,?)", sorted(subject.items()))


def import_bundle(db_path: Path, bundle: dict[str, Any]) -> dict[str, Any]:
    validate_bundle(bundle)
    initialize(db_path)
    with connect(db_path) as db:
        bind_subject(db, bundle["subject"])
        for item in bundle["coverage"]:
            existing = db.execute(
                "SELECT state,freshness,tool_identity FROM coverage WHERE lens=? AND language=?",
                (item["lens"], item["language"]),
            ).fetchone()
            incoming = (item["state"], item["freshness"], item["tool_identity"])
            if existing is not None:
                require(
                    tuple(existing) == incoming,
                    f"coverage conflict: {item['lens']}/{item['language']}",
                )
                continue
            db.execute(
                "INSERT INTO coverage(lens,language,state,freshness,tool_identity) VALUES (?,?,?,?,?)",
                (item["lens"], item["language"], *incoming),
            )
        inserted = 0
        for item in bundle["observations"]:
            identity = {
                key: item.get(key)
                for key in (
                    "path",
                    "source_sha256",
                    "language",
                    "lens",
                    "tool_identity",
                    "source",
                    "target",
                    "relation",
                    "readback",
                    "span",
                    "note",
                )
            }
            oid = sha256(identity)
            row = db.execute(
                "SELECT * FROM observations WHERE observation_id=?", (oid,)
            ).fetchone()
            if row is not None:
                continue
            db.execute(
                "INSERT INTO observations(observation_id,path,source_sha256,language,lens,tool_identity,source,target,relation,readback,span,note) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    oid,
                    item["path"],
                    item["source_sha256"],
                    item["language"],
                    item["lens"],
                    item["tool_identity"],
                    item["source"],
                    item["target"],
                    item["relation"],
                    item["readback"],
                    item.get("span"),
                    item.get("note"),
                ),
            )
            inserted += 1
        db.execute(
            "INSERT OR REPLACE INTO meta(key,value) VALUES ('bundle_digest',?)",
            (sha256(bundle),),
        )
        count = db.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    return {
        "status": "PASS",
        "inserted": inserted,
        "observations": count,
        "subject": bundle["subject"],
    }


def query(
    db_path: Path, source: str, target: str, language: str, required_lenses: list[str]
) -> dict[str, Any]:
    require(db_path.exists(), f"ABSENT: {db_path}", invalid=True)
    require(
        bool(source and target and language),
        "source/target/language required",
        invalid=True,
    )
    require(
        bool(required_lenses), "at least one required lens is required", invalid=True
    )
    require(
        len(required_lenses) == len(set(required_lenses)),
        "duplicate required lens",
        invalid=True,
    )
    require(set(required_lenses) <= LENSES, "unknown required lens", invalid=True)
    with connect(db_path) as db:
        subject = db_subject(db)
        require(subject is not None, "database subject absent")
        rows = [
            dict(row)
            for row in db.execute(
                "SELECT * FROM observations WHERE source=? AND target=? AND language=? ORDER BY observation_id",
                (source, target, language),
            )
        ]
        coverage = {
            row["lens"]: dict(row)
            for row in db.execute(
                "SELECT * FROM coverage WHERE language=?", (language,)
            )
        }
    usable = [row for row in rows if row["readback"] in {"CONFIRMED", "NOT_REQUIRED"}]
    support = [row for row in usable if row["relation"] == "SUPPORTS_FLOW"]
    deny = [row for row in usable if row["relation"] == "DENIES_FLOW"]
    candidates = [row for row in rows if row["relation"] == "CANDIDATE"]
    missing_lenses: list[str] = []
    for lens in required_lenses:
        item = coverage.get(lens)
        if item is None or item["state"] != "COMPLETE" or item["freshness"] != "FRESH":
            missing_lenses.append(lens)
    if support and deny:
        verdict = "CONTESTED"
        reason = "fresh read-back evidence disagrees"
    elif support:
        verdict = "FOUND"
        reason = "source-admissible support observed"
    elif deny and not missing_lenses:
        verdict = "NO_FLOW"
        reason = "all required lenses are fresh and complete with no supporting flow"
    elif not rows and not missing_lenses:
        verdict = "NO_FLOW"
        reason = (
            "all required lenses are fresh and complete and produced no supporting flow"
        )
    else:
        verdict = "UNKNOWN"
        reason = "coverage/readback is incomplete or only candidate evidence exists"
    return {
        "schema": RESULT_SCHEMA,
        "subject": subject,
        "query": {
            "source": source,
            "target": target,
            "language": language,
            "required_lenses": required_lenses,
        },
        "verdict": verdict,
        "reason": reason,
        "coverage_complete": not missing_lenses,
        "missing_or_unfresh_lenses": missing_lenses,
        "support_ids": [row["observation_id"] for row in support],
        "deny_ids": [row["observation_id"] for row in deny],
        "candidate_ids": [row["observation_id"] for row in candidates],
        "absence_proof": "COMPLETE_REQUIRED_LENSES" if verdict == "NO_FLOW" else "NONE",
    }


def export_db(db_path: Path) -> dict[str, Any]:
    require(db_path.exists(), f"ABSENT: {db_path}", invalid=True)
    with connect(db_path) as db:
        subject = db_subject(db)
        require(subject is not None, "database subject absent")
        coverage = [
            dict(row)
            for row in db.execute(
                "SELECT lens,language,state,freshness,tool_identity FROM coverage ORDER BY lens,language"
            )
        ]
        observations = [
            dict(row)
            for row in db.execute(
                "SELECT observation_id,path,source_sha256,language,lens,tool_identity,source,target,relation,readback,span,note FROM observations ORDER BY observation_id"
            )
        ]
    value = {
        "schema": "bettor-arena/blindspots-export/v1",
        "subject": subject,
        "coverage": coverage,
        "observations": observations,
    }
    value["content_sha256"] = sha256(value)
    return value


def fixture(
    subject: dict[str, str],
    *,
    complete: bool = True,
    disagreement: bool = False,
    candidate_only: bool = False,
) -> dict[str, Any]:
    coverage = []
    for lens in ["source", "grepai", "scip-lsp", "tree-sitter"]:
        coverage.append(
            {
                "lens": lens,
                "language": "python",
                "state": "COMPLETE" if complete or lens != "tree-sitter" else "PARTIAL",
                "freshness": "FRESH",
                "tool_identity": f"fixture:{lens}:v1",
            }
        )
    obs: list[dict[str, Any]] = []
    if candidate_only:
        obs.append(
            {
                "path": "app.py",
                "source_sha256": "a" * 64,
                "language": "python",
                "lens": "grepai",
                "tool_identity": "fixture:grepai:v1",
                "source": "A",
                "target": "B",
                "relation": "CANDIDATE",
                "readback": "MISSING",
            }
        )
    else:
        obs.append(
            {
                "path": "app.py",
                "source_sha256": "a" * 64,
                "language": "python",
                "lens": "source",
                "tool_identity": "fixture:source:v1",
                "source": "A",
                "target": "B",
                "relation": "SUPPORTS_FLOW",
                "readback": "CONFIRMED",
            }
        )
        if disagreement:
            obs.append(
                {
                    "path": "app.py",
                    "source_sha256": "a" * 64,
                    "language": "python",
                    "lens": "scip-lsp",
                    "tool_identity": "fixture:scip-lsp:v1",
                    "source": "A",
                    "target": "B",
                    "relation": "DENIES_FLOW",
                    "readback": "CONFIRMED",
                }
            )
    return {
        "schema": BUNDLE_SCHEMA,
        "subject": subject,
        "coverage": coverage,
        "observations": obs,
    }


def residue(path: Path) -> list[str]:
    return [
        str(p)
        for p in (
            Path(str(path) + "-wal"),
            Path(str(path) + "-shm"),
            Path(str(path) + "-journal"),
        )
        if p.exists()
    ]


def selftest() -> dict[str, Any]:
    subject = {"repository": "ed3c/bettor-arena", "commit": "1" * 40, "tree": "2" * 40}
    controls: list[str] = []
    with tempfile.TemporaryDirectory(prefix="blindspots-") as tmp:
        root = Path(tmp)
        db = root / "evidence.sqlite"
        import_bundle(db, fixture(subject))
        require(
            query(
                db, "A", "B", "python", ["source", "grepai", "scip-lsp", "tree-sitter"]
            )["verdict"]
            == "FOUND",
            "positive FOUND failed",
        )
        q = query(
            db, "X", "Y", "python", ["source", "grepai", "scip-lsp", "tree-sitter"]
        )
        require(
            q["verdict"] == "NO_FLOW"
            and q["absence_proof"] == "COMPLETE_REQUIRED_LENSES",
            "complete coverage NO_FLOW failed",
        )
        export1 = export_db(db)
        export2 = export_db(db)
        require(canonical(export1) == canonical(export2), "export is non-deterministic")
        try:
            import_bundle(db, fixture({**subject, "commit": "3" * 40}))
        except Refusal:
            controls.append("stale-subject")
        else:
            raise Refusal("stale-subject control passed")
        partial = root / "partial.sqlite"
        import_bundle(partial, fixture(subject, complete=False, candidate_only=True))
        require(
            query(
                partial,
                "A",
                "B",
                "python",
                ["source", "grepai", "scip-lsp", "tree-sitter"],
            )["verdict"]
            == "UNKNOWN",
            "partial coverage became absence",
        )
        controls.append("partial-coverage-unknown")
        candidate = root / "candidate.sqlite"
        import_bundle(candidate, fixture(subject, candidate_only=True))
        require(
            query(
                candidate,
                "A",
                "B",
                "python",
                ["source", "grepai", "scip-lsp", "tree-sitter"],
            )["verdict"]
            == "UNKNOWN",
            "candidate without readback promoted",
        )
        controls.append("candidate-without-readback")
        contested = root / "contested.sqlite"
        import_bundle(contested, fixture(subject, disagreement=True))
        require(
            query(
                contested,
                "A",
                "B",
                "python",
                ["source", "grepai", "scip-lsp", "tree-sitter"],
            )["verdict"]
            == "CONTESTED",
            "disagreement not contested",
        )
        controls.append("disagreement-contested")
        for path in (db, partial, candidate, contested):
            require(not residue(path), f"database residue: {residue(path)}")
        controls.append("no-wal-shm-residue")
    return {"status": "PASS", "controls": controls, "control_count": len(controls)}


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p_init = sub.add_parser("init")
    p_init.add_argument("--db", type=Path, required=True)
    p_import = sub.add_parser("import")
    p_import.add_argument("--db", type=Path, required=True)
    p_import.add_argument("--bundle", type=Path, required=True)
    p_query = sub.add_parser("query")
    p_query.add_argument("--db", type=Path, required=True)
    p_query.add_argument("--source", required=True)
    p_query.add_argument("--target", required=True)
    p_query.add_argument("--language", required=True)
    p_query.add_argument("--required-lens", action="append", required=True)
    p_export = sub.add_parser("export")
    p_export.add_argument("--db", type=Path, required=True)
    p_export.add_argument("--output", type=Path)
    sub.add_parser("selftest")
    args = parser.parse_args()
    try:
        if args.command == "init":
            initialize(args.db)
            out = {"status": "PASS", "db": str(args.db)}
        elif args.command == "import":
            out = import_bundle(args.db, load_json(args.bundle))
        elif args.command == "query":
            out = query(
                args.db, args.source, args.target, args.language, args.required_lens
            )
        elif args.command == "export":
            out = export_db(args.db)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(
                    json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )
        else:
            out = selftest()
        print(json.dumps(out, sort_keys=True))
        return OK
    except Refusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return REFUSED
    except Invalid as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return INVALID
    except (OSError, sqlite3.Error) as exc:
        print(f"MECHANISM_ERROR: {exc}", file=sys.stderr)
        return MECHANISM


if __name__ == "__main__":
    raise SystemExit(main())
