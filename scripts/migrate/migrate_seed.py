#!/usr/bin/env python3
"""migrate_seed — migration engine v2: move manifest-declared subtrees between repos.

Contract (S2, ts-skill-bettor issue #4):
- The manifest (data/migration/manifest.json) holds repo-relative paths only;
  zero absolute-path fields. The only user-supplied absolute path is
  --target-root. The source root is derived at runtime: `git rev-parse
  --show-toplevel` of --source-root (or of this engine's own tree when the
  flag is absent).
- Same root (or target nested in source) refuses to run: exit 64.
- Dry-run is the default and writes zero bytes anywhere. --apply writes.
  --stats prints the JSON payload.
- Text files (rewrite_suffixes) get the source-root absolute string rewritten
  to the {REPO_ROOT} token. Files under an evidence_allowlist prefix are
  copied verbatim (rewriting evidence is forging evidence) and are declared
  in the target's root-coupling allowlist ledger instead.
- After --apply the engine writes a stats receipt (no absolute paths) to
  <target>/data/migration/last-migration-report.json and, when the target
  carries scripts/gates/check_root_coupling.py, requires that gate green.

Exit codes: 0 ok · 2 post-apply target gate red · 64 usage/precondition
(same root, non-git source, bad manifest) · anything else is a crash.
Selftest: --selftest builds throwaway git fixtures and proves every exit
path above, including that dry-run leaves the target byte-identical.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT_TOKEN_DEFAULT = "{REPO_ROOT}"
RECEIPT_REL = "data/migration/last-migration-report.json"
TARGET_GATE_REL = "scripts/gates/check_root_coupling.py"
TARGET_ALLOWLIST_REL = "scripts/gates/root_coupling_allowlist.txt"
# Assembled so this file never contains a literal match for what it polices.
HOME_PATTERNS = tuple(a + b for a, b in (("/Use", "rs/"), ("/ho", "me/"), ("C:\\Use", "rs\\")))
GIT_ENUMERATION_ARGV = ("ls-files", "-co", "--exclude-standard", "-z")


@dataclass(frozen=True)
class Operation:
    component_id: str
    rel: str          # source-root-relative posix path
    source: Path
    target: Path
    size: int
    rewrite: bool
    evidence: bool
    link: str | None = None  # relative symlink payload, recreated as-is


# ---------------------------------------------------------------- helpers

def git_toplevel(path: Path) -> Path | None:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        text=True, capture_output=True)
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def git_head(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else "no-commit"


def git_visible_paths(root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "-C", str(root), *GIT_ENUMERATION_ARGV], capture_output=True)
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"git enumeration failed at {root}: {detail}")
    paths = [p for p in completed.stdout.decode("utf-8").split("\0") if p]
    if not paths:
        raise ValueError(f"git enumeration listed zero files at {root}")
    return paths


def _require_repo_relative(value: str, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"manifest field {field} must be a non-empty string")
    if os.path.isabs(value) or value.startswith("~") or any(h in value for h in HOME_PATTERNS):
        raise ValueError(f"manifest field {field} must be repo-relative, got: {value}")
    if ".." in Path(value).parts:
        raise ValueError(f"manifest field {field} must not traverse upward: {value}")


def load_manifest(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"unreadable manifest {path}: {exc}") from exc
    for key in ("schema", "root_token", "rewrite_suffixes", "excluded_path_parts",
                "components", "evidence_allowlist"):
        if key not in data:
            raise ValueError(f"manifest missing key: {key}")
    for component in data["components"]:
        for key in ("id", "kind", "source", "target"):
            if key not in component:
                raise ValueError(f"component missing key {key}: {component}")
        if component["kind"] not in ("directory", "file"):
            raise ValueError(f"unsupported component kind: {component['kind']}")
        _require_repo_relative(component["source"], f"components[{component['id']}].source")
        _require_repo_relative(component["target"], f"components[{component['id']}].target")
        for prefix in component.get("exclude_prefixes", []):
            _require_repo_relative(prefix, f"components[{component['id']}].exclude_prefixes")
    for entry in data["evidence_allowlist"]:
        if "prefix" not in entry or "reason" not in entry:
            raise ValueError(f"evidence_allowlist entry needs prefix+reason: {entry}")
        _require_repo_relative(entry["prefix"], "evidence_allowlist.prefix")
    return data


def _prefix_match(rel: str, prefix: str) -> bool:
    return rel == prefix or (prefix.endswith("/") and rel.startswith(prefix))


def is_evidence(rel: str, manifest: dict) -> bool:
    return any(_prefix_match(rel, e["prefix"]) for e in manifest["evidence_allowlist"])


# ---------------------------------------------------------------- planning

def build_operations(source_root: Path, target_root: Path, manifest: dict) -> list[Operation]:
    suffixes = set(manifest["rewrite_suffixes"])
    excluded_parts = set(manifest["excluded_path_parts"])
    visible = git_visible_paths(source_root)
    visible_set = set(visible)
    operations: list[Operation] = []
    for component in manifest["components"]:
        source_prefix = component["source"].rstrip("/")
        if component["kind"] == "file":
            rels = [component["source"]] if component["source"] in visible_set else []
        else:
            rels = [r for r in visible if r.startswith(source_prefix + "/")]
        rels = [
            r for r in rels
            if not any(_prefix_match(r, p) for p in component.get("exclude_prefixes", []))
            and not any(part in excluded_parts for part in Path(r).parts)
        ]
        if not rels and component.get("required", False):
            raise ValueError(f"required migration component empty or missing: {component['source']}")
        for rel in sorted(rels):
            source = source_root / rel
            if component["kind"] == "file":
                target = target_root / component["target"]
            else:
                target = target_root / component["target"] / Path(rel).relative_to(source_prefix)
            evidence = is_evidence(rel, manifest)
            if source.is_symlink():
                link = os.readlink(source)
                if os.path.isabs(link):
                    raise ValueError(f"absolute symlink in payload re-couples the target: {rel} -> {link}")
                operations.append(Operation(
                    component_id=component["id"], rel=rel, source=source, target=target,
                    size=0, rewrite=False, evidence=evidence, link=link))
                continue
            if not source.is_file():
                continue  # git listed it but it is gone from the work tree
            operations.append(Operation(
                component_id=component["id"], rel=rel, source=source, target=target,
                size=source.stat().st_size,
                rewrite=(not evidence and source.suffix in suffixes),
                evidence=evidence))
    return operations


def apply_operations(operations: list[Operation], manifest: dict,
                     source_root: Path) -> int:
    root_str = str(source_root)
    token = manifest["root_token"]
    written = 0
    for op in operations:
        op.target.parent.mkdir(parents=True, exist_ok=True)
        if op.link is not None:
            if op.target.is_symlink() or op.target.exists():
                op.target.unlink()
            os.symlink(op.link, op.target)
            written += 1
            continue
        if op.rewrite:
            try:
                text = op.source.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                shutil.copy2(op.source, op.target)
            else:
                rewritten = text.replace(root_str, token)
                # replace() removed the source root; what can still leak is any
                # OTHER home root (foreign machine paths) — scan for those.
                leftover = next((p for p in HOME_PATTERNS if p in rewritten), None)
                if leftover is not None:
                    raise ValueError(
                        f"rewrite left a home-root residue in {op.rel} "
                        f"(pattern {leftover!r}): declare it as evidence or fix the source")
                op.target.write_text(rewritten, encoding="utf-8")
        else:
            shutil.copy2(op.source, op.target)
        if op.source.stat().st_mode & 0o111:
            op.target.chmod(0o755)
        written += 1
    return written


def stats_payload(manifest: dict, operations: list[Operation],
                  source_root: Path, target_root: Path, mode: str) -> dict:
    suffix_counts: dict[str, int] = {}
    component_counts: dict[str, int] = {}
    for op in operations:
        suffix = op.source.suffix or "<none>"
        suffix_counts[suffix] = suffix_counts.get(suffix, 0) + 1
        component_counts[op.component_id] = component_counts.get(op.component_id, 0) + 1
    # Deliberately no absolute paths: the receipt lands inside the target tree
    # and must never re-couple it to a machine (target-side root-coupling gate).
    return {
        "schema": "bettor-arena-migration-stats@2.0.0",
        "manifest_schema": manifest["schema"],
        "mode": mode,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_root_name": source_root.name,
        "target_root_name": target_root.name,
        "source_commit": git_head(source_root),
        "files_planned": len(operations),
        "bytes_planned": sum(op.size for op in operations),
        "rewrite_planned": sum(1 for op in operations if op.rewrite),
        "evidence_planned": sum(1 for op in operations if op.evidence),
        "symlink_planned": sum(1 for op in operations if op.link is not None),
        "suffix_counts": dict(sorted(suffix_counts.items())),
        "component_file_counts": dict(sorted(component_counts.items())),
    }


def ensure_target_allowlist(target_root: Path, manifest: dict) -> list[str]:
    """Declare evidence prefixes in the target's root-coupling ledger; return lines added."""
    allowlist = target_root / TARGET_ALLOWLIST_REL
    gate = target_root / TARGET_GATE_REL
    if not allowlist.exists() and not gate.exists():
        return []  # target carries no root-coupling gate surface; nothing to declare into
    existing = allowlist.read_text(encoding="utf-8") if allowlist.exists() else ""
    declared = {line.split()[0] for line in existing.splitlines()
                if line.strip() and not line.lstrip().startswith("#")}
    added = []
    for entry in manifest["evidence_allowlist"]:
        if entry["prefix"] not in declared:
            added.append(f"{entry['prefix']} {entry['reason'].replace(' ', '-')}")
    if added:
        allowlist.parent.mkdir(parents=True, exist_ok=True)
        body = existing + ("" if not existing or existing.endswith("\n") else "\n")
        allowlist.write_text(body + "\n".join(added) + "\n", encoding="utf-8")
    return added


def run_target_gate(target_root: Path) -> str:
    """Run the target's own root-coupling gate. 'pass' | 'fail' | 'absent'."""
    gate = target_root / TARGET_GATE_REL
    if not gate.is_file():
        return "absent"
    result = subprocess.run([sys.executable, str(gate)], cwd=str(target_root),
                            text=True, capture_output=True)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
    return "pass" if result.returncode == 0 else "fail"


# ---------------------------------------------------------------- main

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path,
                        help="manifest path (default: <engine repo>/data/migration/manifest.json)")
    parser.add_argument("--source-root", type=Path,
                        help="any path inside the source tree; git derives its toplevel")
    parser.add_argument("--target-root", type=Path,
                        help="absolute target root (the only user-supplied absolute path)")
    parser.add_argument("--apply", action="store_true", help="write files (default: dry-run)")
    parser.add_argument("--stats", action="store_true", help="print the JSON stats payload")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()
    try:
        if args.target_root is None:
            raise ValueError("--target-root is required")
        source_root = git_toplevel(args.source_root or Path(__file__).resolve().parent)
        if source_root is None:
            raise ValueError("source root is not a git work tree")
        target_root = args.target_root.expanduser().resolve()
        if target_root == source_root:
            raise ValueError("target root must differ from source root")
        if target_root.exists() and git_toplevel(target_root) == source_root:
            raise ValueError("target root is nested inside the source tree")
        manifest_path = args.manifest
        if manifest_path is None:
            engine_root = git_toplevel(Path(__file__).resolve().parent)
            if engine_root is None:
                raise ValueError("engine tree is not a git work tree; pass --manifest")
            manifest_path = engine_root / "data" / "migration" / "manifest.json"
        manifest = load_manifest(manifest_path)

        operations = build_operations(source_root, target_root, manifest)
        mode = "apply" if args.apply else "dry-run"
        payload = stats_payload(manifest, operations, source_root, target_root, mode)
        if args.apply:
            payload["files_written"] = apply_operations(operations, manifest, source_root)
            payload["allowlist_entries_added"] = ensure_target_allowlist(target_root, manifest)
            gate_status = run_target_gate(target_root)
            payload["root_coupling_gate"] = gate_status
            receipt = target_root / RECEIPT_REL
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
            if gate_status == "fail":
                print(f"FAIL: target gate {TARGET_GATE_REL} red after apply", file=sys.stderr)
                return 2
        if args.stats:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"{mode.upper()}: {payload['files_planned']} files planned "
                  f"({payload['rewrite_planned']} rewrite, {payload['evidence_planned']} evidence)"
                  + (f", {payload['files_written']} written" if args.apply else ", 0 bytes written"))
        return 0
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 64


# ---------------------------------------------------------------- selftest

def _snapshot(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            out[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def _run_cli(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(Path(__file__).resolve()), *args],
                          text=True, capture_output=True)


def _make_source_fixture(base: Path) -> tuple[Path, str]:
    repo = base / "src"
    repo.mkdir(parents=True)
    subprocess.run(["git", "-C", str(repo), "init", "-q", "-b", "main"], check=True)
    root = git_toplevel(repo)
    assert root is not None
    root_str = str(root)
    foreign = HOME_PATTERNS[0] + "otherbox/elsewhere"
    files = {
        "code/tool.py": f'ROOT = "{root_str}"\nprint(ROOT)\n',
        "code/node_modules/skip.py": "print('never migrated')\n",
        "docs/note.md": f"see {root_str}/docs\n",
        "evidence/trace.md": f"receipt at {root_str}/x and {foreign}/y\n",
        "bin/run.sh": "#!/bin/sh\necho hi\n",
    }
    for rel, content in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    (repo / "blob.bin").write_bytes(b"\x00\x01\x02")
    (repo / "bin/run.sh").chmod(0o755)
    os.symlink("../docs", repo / "code/alias_docs")  # tracked repo-internal symlink
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", "fixture"], check=True)
    return root, root_str


def _fixture_manifest(base: Path) -> Path:
    manifest = {
        "schema": "bettor-arena-migration@2.0.0",
        "root_token": ROOT_TOKEN_DEFAULT,
        "rewrite_suffixes": [".py", ".md", ".sh"],
        "excluded_path_parts": ["node_modules"],
        "components": [
            {"id": "code", "kind": "directory", "source": "code", "target": "code", "required": True},
            {"id": "docs", "kind": "directory", "source": "docs", "target": "docs", "required": True},
            {"id": "evidence", "kind": "directory", "source": "evidence", "target": "evidence", "required": True},
            {"id": "bin", "kind": "directory", "source": "bin", "target": "bin", "required": True},
            {"id": "blob", "kind": "file", "source": "blob.bin", "target": "blob.bin", "required": True},
        ],
        "evidence_allowlist": [
            {"prefix": "evidence/", "reason": "fixture-historical-evidence"},
        ],
    }
    path = base / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def _selftest() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        if not ok:
            failures.append(f"{name}: {detail}")

    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        src, src_str = _make_source_fixture(base)
        manifest_path = _fixture_manifest(base)
        tgt = base / "tgt"
        tgt.mkdir()
        common = ["--manifest", str(manifest_path), "--source-root", str(src),
                  "--target-root", str(tgt)]

        # positive control: dry-run writes nothing and its stats equal apply's writes
        before = _snapshot(tgt)
        dry = _run_cli([*common, "--stats"])
        check("dry-run-exit", dry.returncode == 0, f"exit {dry.returncode}: {dry.stderr}")
        check("dry-run-no-writes", _snapshot(tgt) == before, "target tree changed on dry-run")
        planned = -1
        if dry.returncode == 0:
            payload = json.loads(dry.stdout)
            planned = payload["files_planned"]
            check("dry-run-planned", planned == 6, f"files_planned={planned}")
            check("dry-run-symlink-planned", payload["symlink_planned"] == 1,
                  f"symlink_planned={payload.get('symlink_planned')}")
            check("dry-run-rewrite-planned", payload["rewrite_planned"] == 3,
                  f"rewrite_planned={payload['rewrite_planned']}")
            check("dry-run-evidence-planned", payload["evidence_planned"] == 1,
                  f"evidence_planned={payload['evidence_planned']}")
            check("dry-run-no-abs-paths", src_str not in dry.stdout, "payload leaks source root")

        # pre-seed the target allowlist ledger so apply must append the evidence entry
        allowlist = tgt / TARGET_ALLOWLIST_REL
        allowlist.parent.mkdir(parents=True)
        allowlist.write_text("# ledger\n", encoding="utf-8")

        applied = _run_cli([*common, "--apply", "--stats"])
        check("apply-exit", applied.returncode == 0, f"exit {applied.returncode}: {applied.stderr}")
        if applied.returncode == 0:
            payload = json.loads(applied.stdout)
            check("apply-count-matches-dry-run", payload["files_written"] == planned,
                  f"written={payload['files_written']} planned={planned}")
            tool = (tgt / "code/tool.py").read_text(encoding="utf-8")
            check("rewrite-token", ROOT_TOKEN_DEFAULT in tool and src_str not in tool,
                  f"tool.py content: {tool!r}")
            check("evidence-verbatim",
                  (tgt / "evidence/trace.md").read_bytes() == (src / "evidence/trace.md").read_bytes(),
                  "evidence file was rewritten")
            check("excluded-part-skipped", not (tgt / "code/node_modules/skip.py").exists(),
                  "excluded_path_parts file migrated")
            check("exec-bit", (tgt / "bin/run.sh").stat().st_mode & stat.S_IXUSR != 0,
                  "exec bit lost")
            alias = tgt / "code/alias_docs"
            check("symlink-recreated", alias.is_symlink() and os.readlink(alias) == "../docs",
                  f"alias_docs missing or wrong: {alias.is_symlink()}")
            receipt = tgt / RECEIPT_REL
            check("receipt-exists", receipt.is_file(), str(receipt))
            if receipt.is_file():
                check("receipt-no-abs-paths", src_str not in receipt.read_text(encoding="utf-8"),
                      "receipt leaks source root")
            ledger = allowlist.read_text(encoding="utf-8")
            check("allowlist-appended", "evidence/ fixture-historical-evidence" in ledger,
                  f"ledger: {ledger!r}")

        # target whose own gate is a permanently-red stub: the exit-2 branch of
        # run_target_gate must actually fire, not just exist in the source.
        tgt_red = base / "tgt_red"
        red_gate = tgt_red / TARGET_GATE_REL
        red_gate.parent.mkdir(parents=True)
        red_gate.write_text("import sys\nsys.stderr.write('stub gate: always red\\n')\nsys.exit(2)\n",
                            encoding="utf-8")
        red = _run_cli(["--manifest", str(manifest_path), "--source-root", str(src),
                        "--target-root", str(tgt_red), "--apply"])
        check("target-gate-red-exit-2", red.returncode == 2, f"exit {red.returncode}: {red.stderr}")
        check("target-gate-red-receipt",
              (tgt_red / RECEIPT_REL).is_file()
              and '"root_coupling_gate": "fail"' in (tgt_red / RECEIPT_REL).read_text(encoding="utf-8"),
              "receipt missing or does not record the red gate")

        # negative controls
        # a foreign home root surviving rewrite must refuse, not ship coupling
        (src / "code/foreign.py").write_text(
            f'OTHER = "{HOME_PATTERNS[0]}otherbox/elsewhere"\n', encoding="utf-8")
        subprocess.run(["git", "-C", str(src), "add", "code/foreign.py"], check=True)
        tgt_residue = base / "tgt_residue"
        tgt_residue.mkdir()
        residue = _run_cli(["--manifest", str(manifest_path), "--source-root", str(src),
                            "--target-root", str(tgt_residue), "--apply"])
        check("home-residue-refused", residue.returncode == 64,
              f"exit {residue.returncode}: {residue.stderr}")
        check("home-residue-named", "foreign.py" in residue.stderr,
              f"stderr does not name the leaking file: {residue.stderr!r}")
        subprocess.run(["git", "-C", str(src), "rm", "-q", "--cached", "code/foreign.py"], check=True)
        (src / "code/foreign.py").unlink()

        os.symlink(str(src / "docs/note.md"), src / "code/abs_link")
        subprocess.run(["git", "-C", str(src), "add", "code/abs_link"], check=True)
        abslink = _run_cli([*common])
        check("absolute-symlink-refused", abslink.returncode == 64, f"exit {abslink.returncode}")
        subprocess.run(["git", "-C", str(src), "rm", "-q", "--cached", "code/abs_link"], check=True)
        (src / "code/abs_link").unlink()

        same = _run_cli(["--manifest", str(manifest_path), "--source-root", str(src),
                         "--target-root", str(src)])
        check("same-root-refused", same.returncode == 64, f"exit {same.returncode}")

        nongit = base / "plain"
        nongit.mkdir()
        ng = _run_cli(["--manifest", str(manifest_path), "--source-root", str(nongit),
                       "--target-root", str(tgt)])
        check("non-git-source-refused", ng.returncode == 64, f"exit {ng.returncode}")

        broken = base / "broken.json"
        broken.write_text("{not json", encoding="utf-8")
        bad = _run_cli(["--manifest", str(broken), "--source-root", str(src),
                        "--target-root", str(tgt)])
        check("bad-manifest-refused", bad.returncode == 64, f"exit {bad.returncode}")

        abs_manifest = base / "abs.json"
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        data["components"][0]["source"] = src_str + "/code"
        abs_manifest.write_text(json.dumps(data), encoding="utf-8")
        absres = _run_cli(["--manifest", str(abs_manifest), "--source-root", str(src),
                           "--target-root", str(tgt)])
        check("abs-path-manifest-refused", absres.returncode == 64, f"exit {absres.returncode}")

    for line in failures:
        print(f"SELFTEST case failed — {line}", file=sys.stderr)
    print("SELFTEST " + ("GREEN" if not failures else "RED"))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
