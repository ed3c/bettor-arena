#!/usr/bin/env python3
"""Validate the portable Agent Skills core plus explicit Bettor house rules.

The gate deliberately separates two namespaces in its diagnostics:

* ``SPEC-*``: Agent Skills specification requirements;
* ``BETTOR-*``: this repository's portability or maintainability policy.

It uses a dependency-free parser for the deliberately small frontmatter
profile admitted by bettor-arena. Host-only fields belong in a host projection,
not in the canonical SKILL.md.

Exit codes: 0 checked-clean; 2 contract violations; 64 usage/read failure.
``--selftest`` runs one positive control and independent planted mutations.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any


PORTABLE_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TOP_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):(.*)$")
MAP_KEY_RE = re.compile(r"^\s+([^:#][^:]*):(.*)$")
BLOCK_MARKERS = {"|", "|-", "|+", ">", ">-", ">+"}


class FrontmatterError(ValueError):
    pass


def _scalar(raw: str) -> str:
    value = raw.strip()
    if not value:
        return ""
    if value.startswith('"'):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as exc:
            raise FrontmatterError(f"invalid double-quoted scalar: {exc}") from exc
        if not isinstance(decoded, str):
            raise FrontmatterError("frontmatter scalar must decode to a string")
        return decoded
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise FrontmatterError("unterminated single-quoted scalar")
        return value[1:-1].replace("''", "'")
    if value.startswith("[") or value.startswith("{"):
        raise FrontmatterError("flow collections are outside the Bettor profile")
    if ": " in value or " #" in value:
        raise FrontmatterError(
            "plain scalar contains YAML-significant text; quote it or use a block scalar"
        )
    if re.fullmatch(
        r"(?i:null|true|false|yes|no|on|off)|~|[-+]?(?:\d+(?:\.\d*)?|\.\d+)",
        value,
    ):
        raise FrontmatterError(
            "implicit YAML non-string scalar must be quoted in the Bettor profile"
        )
    return value


def _block(lines: list[str], marker: str) -> str:
    nonblank = [len(line) - len(line.lstrip()) for line in lines if line.strip()]
    indent = min(nonblank) if nonblank else 0
    content = [line[indent:] if line.strip() else "" for line in lines]
    if marker.startswith("|"):
        value = "\n".join(content)
    else:
        parts: list[str] = []
        for line in content:
            if not line:
                parts.append("\n")
            elif parts and parts[-1] != "\n":
                parts.append(" " + line)
            else:
                parts.append(line)
        value = "".join(parts)
    if marker.endswith("-"):
        return value.rstrip("\n")
    return value + ("\n" if content else "")


def parse_frontmatter(text: str) -> tuple[dict[str, Any], list[str]]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise FrontmatterError("SKILL.md must begin with an exact '---' line")
    try:
        closing = lines.index("---", 1)
    except ValueError as exc:
        raise FrontmatterError("frontmatter has no closing '---' line") from exc

    fm_lines = lines[1:closing]
    values: dict[str, Any] = {}
    i = 0
    while i < len(fm_lines):
        line = fm_lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if line[:1].isspace():
            raise FrontmatterError(
                f"unexpected indentation at frontmatter line {i + 2}"
            )
        match = TOP_KEY_RE.match(line)
        if not match:
            raise FrontmatterError(f"invalid frontmatter line {i + 2}: {line!r}")
        key, raw = match.group(1), match.group(2).strip()
        if key in values:
            raise FrontmatterError(f"duplicate frontmatter field: {key}")

        nested: list[str] = []
        j = i + 1
        while j < len(fm_lines):
            candidate = fm_lines[j]
            if candidate and not candidate[:1].isspace():
                break
            nested.append(candidate)
            j += 1

        if raw in BLOCK_MARKERS:
            values[key] = _block(nested, raw)
            i = j
            continue
        if key == "metadata" and not raw:
            mapping: dict[str, str] = {}
            for offset, item in enumerate(nested, start=i + 3):
                if not item.strip() or item.lstrip().startswith("#"):
                    continue
                pair = MAP_KEY_RE.match(item)
                if not pair:
                    raise FrontmatterError(
                        f"metadata must be a one-level string map (line {offset})"
                    )
                map_key = pair.group(1).strip()
                if map_key in mapping:
                    raise FrontmatterError(f"duplicate metadata key: {map_key}")
                mapping[map_key] = _scalar(pair.group(2))
            values[key] = mapping
            i = j
            continue
        if nested and any(item.strip() for item in nested):
            raise FrontmatterError(f"field {key!r} has unexpected nested content")
        values[key] = _scalar(raw)
        i = j
    return values, lines[closing + 1 :]


def validate_skill(path: Path) -> list[str]:
    relative = str(path)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"SPEC-UNREADABLE {relative}: {exc}"]
    try:
        fm, body = parse_frontmatter(text)
    except FrontmatterError as exc:
        return [f"SPEC-FRONTMATTER {relative}: {exc}"]

    failures: list[str] = []
    unknown = sorted(set(fm) - PORTABLE_FIELDS)
    for field in unknown:
        failures.append(
            f"BETTOR-HOST-FIELD {relative}: {field!r} belongs in a host projection"
        )
    for required in ("name", "description"):
        if required not in fm:
            failures.append(f"SPEC-REQUIRED {relative}: missing {required!r}")

    name = fm.get("name")
    if name is not None:
        if not isinstance(name, str) or not 1 <= len(name) <= 64:
            failures.append(
                f"SPEC-NAME-LENGTH {relative}: name must be 1..64 characters"
            )
        elif not NAME_RE.fullmatch(name):
            failures.append(
                f"SPEC-NAME-SYNTAX {relative}: use lower-case letters, digits, single hyphens"
            )
        elif name != path.parent.name:
            failures.append(
                f"SPEC-NAME-DIRECTORY {relative}: {name!r} != {path.parent.name!r}"
            )

    description = fm.get("description")
    if description is not None and (
        not isinstance(description, str) or not 1 <= len(description) <= 1024
    ):
        failures.append(
            f"SPEC-DESCRIPTION-LENGTH {relative}: description must be 1..1024 characters"
        )

    compatibility = fm.get("compatibility")
    if compatibility is not None and (
        not isinstance(compatibility, str) or len(compatibility) > 500
    ):
        failures.append(
            f"SPEC-COMPATIBILITY-LENGTH {relative}: compatibility must be at most 500 characters"
        )

    for field in ("license", "allowed-tools"):
        if field in fm and not isinstance(fm[field], str):
            failures.append(f"SPEC-FIELD-TYPE {relative}: {field} must be a string")
    metadata = fm.get("metadata")
    if metadata is not None and (
        not isinstance(metadata, dict)
        or any(
            not isinstance(k, str) or not isinstance(v, str)
            for k, v in metadata.items()
        )
    ):
        failures.append(f"SPEC-METADATA-TYPE {relative}: metadata must be a string map")

    entrypoint_budget: int | None = None
    if isinstance(metadata, dict) and "entrypoint-line-budget" in metadata:
        raw_budget = metadata["entrypoint-line-budget"]
        try:
            entrypoint_budget = int(raw_budget)
        except (TypeError, ValueError):
            failures.append(
                f"BETTOR-ENTRYPOINT-BUDGET {relative}: metadata.entrypoint-line-budget must be an integer string"
            )
        else:
            if not 1 <= entrypoint_budget <= 500:
                failures.append(
                    f"BETTOR-ENTRYPOINT-BUDGET {relative}: budget must be 1..500 lines"
                )

    if len(body) > 500:
        failures.append(
            f"BETTOR-BODY-LIMIT {relative}: body has {len(body)} lines; house limit is 500"
        )
    if (
        entrypoint_budget is not None
        and 1 <= entrypoint_budget <= 500
        and len(body) > entrypoint_budget
    ):
        failures.append(
            f"BETTOR-ENTRYPOINT-BUDGET {relative}: body has {len(body)} lines; declared budget is {entrypoint_budget}"
        )
    return failures


def discover(root: Path) -> list[Path]:
    """Find packages through repository-owned ``.agents/skills`` surfaces.

    The lexical discovery entry supplies skill identity. This matters for the
    repo-owned ``openwiki-port`` pointer: its content lives at
    ``kb-ingest/skill``, but the official package name is the
    ``.agents/skills/openwiki-port`` entry. Absolute links into the external
    shared-skills checkout are intentionally skipped; a staged-tree gate must
    not depend on a sibling checkout being installed on the runner.
    """
    found: list[Path] = []
    for discovery in sorted(root.rglob(".agents/skills")):
        if not discovery.is_dir() or ".git" in discovery.parts:
            continue
        for entry in sorted(discovery.iterdir()):
            package = entry / "SKILL.md"
            if not package.is_file():
                continue
            if entry.is_symlink():
                try:
                    entry.resolve().relative_to(root.resolve())
                except (OSError, ValueError):
                    continue
            found.append(package)
    return found


def run(root: Path, selected: list[str] | None = None, quiet: bool = False) -> int:
    if not root.is_dir():
        if not quiet:
            print(f"check_skill_conformance: missing root: {root}", file=sys.stderr)
        return 64
    paths = [root / item for item in selected] if selected else discover(root)
    if not paths or any(not path.is_file() for path in paths):
        if not quiet:
            print(
                "check_skill_conformance: no readable SKILL.md targets", file=sys.stderr
            )
        return 64
    failures: list[str] = []
    for path in paths:
        failures.extend(validate_skill(path))
    if failures:
        if not quiet:
            print("\n".join(failures), file=sys.stderr)
            print(f"FAIL: {len(failures)} conformance violation(s)", file=sys.stderr)
        return 2
    if not quiet:
        print(
            f"PASS: {len(paths)} SKILL.md file(s) conform to portable core + Bettor policy"
        )
    return 0


def _skill(name: str = "good-skill", **fields: str) -> str:
    base = {
        "name": name,
        "description": "Does deterministic validation. Use when checking a skill package.",
    }
    base.update(fields)
    rows = ["---"]
    for key, value in base.items():
        rows.append(f"{key}: {value}")
    rows.extend(["---", "# Procedure", "Run the checker."])
    return "\n".join(rows) + "\n"


def _fixture(base: Path, text: str, directory: str = "good-skill") -> Path:
    root = base / "repo"
    target = root / ".agents/skills" / directory
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text(text, encoding="utf-8")
    return root


def selftest() -> int:
    cases: list[tuple[str, int, int]] = []

    def exercise(
        label: str, text: str, expected: int, directory: str = "good-skill"
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            actual = run(_fixture(Path(td), text, directory), quiet=True)
        cases.append((label, actual, expected))

    exercise(
        "valid-block-colon-green",
        "---\nname: good-skill\ndescription: |\n  Does: deterministic validation.\n  Use when: checking a package.\nmetadata:\n  owner: bettor\n  version: '1'\n---\n# Procedure\nRun it.\n",
        0,
    )
    exercise("missing-description-red", "---\nname: good-skill\n---\n", 2)
    exercise("directory-mismatch-red", _skill(name="other-skill"), 2)
    exercise("consecutive-hyphen-red", _skill(name="good--skill"), 2, "good--skill")
    exercise("name-too-long-red", _skill(name="a" * 65), 2, "a" * 65)
    exercise("description-too-long-red", _skill(description="x" * 1025), 2)
    exercise("compatibility-too-long-red", _skill(compatibility="x" * 501), 2)
    exercise("host-field-red", _skill(**{"argument-hint": "[path]"}), 2)
    exercise(
        "plain-colon-red",
        "---\nname: good-skill\ndescription: Does checks: use when authoring.\n---\n",
        2,
    )
    exercise(
        "metadata-non-string-red",
        "---\nname: good-skill\ndescription: Use when validating.\nmetadata:\n  enabled: false\n---\n",
        2,
    )
    exercise("body-house-limit-red", _skill() + ("line\n" * 501), 2)
    exercise(
        "declared-entrypoint-budget-red",
        "---\nname: good-skill\ndescription: Use when validating.\nmetadata:\n  entrypoint-line-budget: '2'\n---\n# One\nline\nline\n",
        2,
    )
    exercise(
        "invalid-entrypoint-budget-red",
        "---\nname: good-skill\ndescription: Use when validating.\nmetadata:\n  entrypoint-line-budget: many\n---\n# One\n",
        2,
    )

    bad = [
        (label, actual, expected)
        for label, actual, expected in cases
        if actual != expected
    ]
    if bad:
        for label, actual, expected in bad:
            print(
                f"SELFTEST FAIL {label}: got {actual}, expected {expected}",
                file=sys.stderr,
            )
        return 1
    print(
        f"SELFTEST GREEN: {len(cases)} controls (1 positive, {len(cases) - 1} mutations)"
    )
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--skill",
        action="append",
        help="repo-relative SKILL.md path; repeat to select multiple targets",
    )
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    return run(args.root.resolve(), args.skill)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
