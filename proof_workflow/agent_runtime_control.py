#!/usr/bin/env python3
"""Build and mutate a disposable agent-runtime control fixture."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def canonical(value: dict) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def sign(value: dict) -> None:
    value.pop("content_sha256", None)
    value["content_sha256"] = hashlib.sha256(canonical(value)).hexdigest()


def skill_digest(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(entry for entry in path.rglob("*") if entry.is_file()):
        digest.update(item.relative_to(path).as_posix().encode())
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def make(source: Path, target: Path) -> None:
    target.mkdir(parents=True)
    for relative in (
        ".agents/module-set.json",
        ".agents/shared-skills.requirements.json",
        ".agents/bindings/bettor-arena.json",
        ".runtime-env/requirements.json",
        ".runtime-env/bindings/bettor-arena-local.json",
        ".runtime-env/workloads/bettor-arena-local.json",
        ".runtime-env/policies/claude-code-native-isolation.json",
        ".runtime-env/policies/codex-cli-native-isolation.json",
        ".runtime-env/policies/codex-openshell-chatgpt-placeholder.json",
        "scripts/agent_runtime.py",
    ):
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, destination)
    fixture_body = (
        b"---\nname: fixture-skill\ndescription: control fixture\n---\nbody\n"
    )
    for surface in (".agents/skills", ".claude/skills"):
        skill = target / surface / "fixture-skill"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_bytes(fixture_body)
    requirements_path = target / ".agents/shared-skills.requirements.json"
    requirements = json.loads(requirements_path.read_text())
    requirements["shared"] = ["fixture-skill"]
    requirements["repo_owned"] = []
    requirements_path.write_text(
        json.dumps(requirements, indent=2, sort_keys=True) + "\n"
    )
    binding_path = target / ".agents/bindings/bettor-arena.json"
    binding = json.loads(binding_path.read_text())
    binding["repo_owned"] = []
    binding["requirements_sha256"] = hashlib.sha256(
        requirements_path.read_bytes()
    ).hexdigest()
    binding["skills"] = [
        {
            "content_sha256": skill_digest(target / ".agents/skills/fixture-skill"),
            "entrypoint": "skills/fixture-skill/SKILL.md",
            "name": "fixture-skill",
        }
    ]
    sign(binding)
    binding_path.write_text(json.dumps(binding, indent=2, sort_keys=True) + "\n")
    subprocess.run(["git", "-C", str(target), "init", "-q"], check=True)
    subprocess.run(
        ["git", "-C", str(target), "config", "user.name", "fixture"], check=True
    )
    subprocess.run(
        ["git", "-C", str(target), "config", "user.email", "fixture@example.invalid"],
        check=True,
    )
    subprocess.run(["git", "-C", str(target), "add", "."], check=True)
    subprocess.run(["git", "-C", str(target), "commit", "-qm", "fixture"], check=True)


def mutate(target: Path, kind: str) -> None:
    if kind == "shared-binding":
        path = target / ".agents/bindings/bettor-arena.json"
        value = json.loads(path.read_text())
        value["skills"][0]["content_sha256"] = "0" * 64
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    elif kind == "runtime-requirements":
        path = target / ".runtime-env/requirements.json"
        path.write_text(path.read_text() + "\n")
    elif kind == "claude-surface":
        shutil.rmtree(target / ".claude/skills/fixture-skill")
    elif kind == "codex-surface":
        shutil.rmtree(target / ".agents/skills/fixture-skill")
    else:
        raise SystemExit(f"unknown mutation: {kind}")


def main() -> int:
    if len(sys.argv) < 4 or sys.argv[1] not in {"make", "mutate"}:
        print(
            "usage: agent_runtime_control.py make <source> <target> | mutate <target> <kind>",
            file=sys.stderr,
        )
        return 64
    if sys.argv[1] == "make":
        make(Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve())
    else:
        mutate(Path(sys.argv[2]).resolve(), sys.argv[3])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
