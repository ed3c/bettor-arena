#!/usr/bin/env python3
"""Zero-network README coverage gate. Exit 0=pass, 2=red, 64=fatal."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote

SCHEMA = "bettor-arena/readme-coverage/v1"
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
REMOTE = ("http://", "https://", "mailto:", "tel:", "data:")


class Fatal(ValueError):
    pass


def json_obj(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Fatal(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise Fatal(f"not a JSON object: {path}")
    return value


def safe(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise Fatal(f"unsafe relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() in {"", "."}:
        raise Fatal(f"unsafe relative path: {value}")
    return path.as_posix()


def load_contract(path: Path) -> dict:
    cfg = json_obj(path)
    keys = {
        "schema",
        "minimum_bytes",
        "required_readmes",
        "module_manifest_root",
        "module_manifest_name",
        "module_readme_name",
        "required_markers",
        "forbidden_patterns",
        "check_relative_links",
    }
    if set(cfg) != keys or cfg.get("schema") != SCHEMA:
        raise Fatal("README coverage contract shape/schema drifted")
    if not isinstance(cfg["minimum_bytes"], int) or cfg["minimum_bytes"] < 1:
        raise Fatal("minimum_bytes must be positive")
    names = cfg["required_readmes"]
    if not isinstance(names, list) or not names or len(names) != len(set(names)):
        raise Fatal("required_readmes must be unique and non-empty")
    cfg["required_readmes"] = [safe(name) for name in names]
    if any(PurePosixPath(name).name.lower() != "readme.md" for name in names):
        raise Fatal("required_readmes must name README.md")
    cfg["module_manifest_root"] = safe(cfg["module_manifest_root"])
    for key in ("module_manifest_name", "module_readme_name"):
        value = cfg[key]
        if not isinstance(value, str) or not value or "/" in value or "\\" in value:
            raise Fatal(f"{key} must be one filename")
    markers = cfg["required_markers"]
    if not isinstance(markers, dict):
        raise Fatal("required_markers must be an object")
    for name, values in markers.items():
        if safe(name) not in cfg["required_readmes"]:
            raise Fatal(f"marker target not required: {name}")
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(value, str) or not value for value in values)
        ):
            raise Fatal(f"bad marker list: {name}")
    patterns = cfg["forbidden_patterns"]
    if not isinstance(patterns, list) or any(
        not isinstance(value, str) for value in patterns
    ):
        raise Fatal("forbidden_patterns must be strings")
    try:
        cfg["patterns"] = [re.compile(value) for value in patterns]
    except re.error as exc:
        raise Fatal(f"bad forbidden regex: {exc}") from exc
    if not isinstance(cfg["check_relative_links"], bool):
        raise Fatal("check_relative_links must be boolean")
    return cfg


def tracked(root: Path, manifest: Path | None) -> set[str]:
    if manifest:
        try:
            records = manifest.read_bytes().split(b"\0")
        except OSError as exc:
            raise Fatal(f"cannot read index manifest: {exc}") from exc
        result = set()
        for record in records:
            if not record:
                continue
            try:
                meta, name = record.decode().split("\t", 1)
            except (UnicodeDecodeError, ValueError) as exc:
                raise Fatal("malformed index manifest") from exc
            fields = meta.split()
            if len(fields) < 3:
                raise Fatal("malformed index metadata")
            if fields[2] == "0":
                result.add(safe(name))
    else:
        run = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"], capture_output=True
        )
        if run.returncode:
            raise Fatal(run.stderr.decode(errors="replace").strip() or "git failed")
        result = {item.decode() for item in run.stdout.split(b"\0") if item}
    if not result:
        raise Fatal("tracked path set is empty")
    return result


def modules(cfg: dict, files: set[str]) -> tuple[set[str], set[str]]:
    root = PurePosixPath(cfg["module_manifest_root"])
    manifests, readmes = set(), set()
    for name in files:
        path = PurePosixPath(name)
        try:
            tail = path.relative_to(root)
        except ValueError:
            continue
        if len(tail.parts) != 2:
            continue
        if tail.name == cfg["module_manifest_name"]:
            manifests.add(name)
        if tail.name == cfg["module_readme_name"]:
            readmes.add(name)
    return manifests, readmes


def link_error(root: Path, source: str, target: str, files: set[str]) -> str | None:
    raw = target
    target = target.strip().strip("<>")
    if not target or target.startswith("#") or target.lower().startswith(REMOTE):
        return None
    target = unquote(target.split("#", 1)[0].split("?", 1)[0])
    parts = []
    for part in PurePosixPath(source).parent.joinpath(target).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not parts:
                return f"LINK-ESCAPES-ROOT {source}: {raw}"
            parts.pop()
        else:
            parts.append(part)
    name = PurePosixPath(*parts).as_posix()
    if not name:
        return None
    path = root / name
    if path.is_dir():
        prefix = name.rstrip("/") + "/"
        if any(item.startswith(prefix) for item in files):
            return None
    elif name in files and path.is_file():
        return None
    return f"BROKEN-LINK {source}: {raw} -> {name}"


def readme_errors(root: Path, name: str, cfg: dict, files: set[str]) -> list[str]:
    if name not in files:
        return [f"UNTRACKED-README {name}"]
    try:
        raw = (root / name).read_bytes()
        text = raw.decode()
    except (OSError, UnicodeDecodeError) as exc:
        return [f"UNREADABLE-README {name}: {exc}"]
    errors = []
    if len(raw.strip()) < cfg["minimum_bytes"]:
        errors.append(f"THIN-README {name}")
    first = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if not first.startswith("# "):
        errors.append(f"MISSING-H1 {name}")
    for marker in cfg["required_markers"].get(name, []):
        if marker not in text:
            errors.append(f"MISSING-MARKER {name}: {marker}")
    for pattern in cfg["patterns"]:
        match = pattern.search(text)
        if match:
            errors.append(f"FORBIDDEN-PATH {name}: {match.group(0)!r}")
    if cfg["check_relative_links"]:
        errors.extend(
            error
            for target in LINK.findall(text)
            if (error := link_error(root, name, target, files))
        )
    return errors


def check(root: Path, config: Path, files: set[str]) -> list[str]:
    cfg = load_contract(config)
    manifests, readmes = modules(cfg, files)
    errors = [] if manifests else ["NO-MODULE-MANIFESTS"]
    required = set(cfg["required_readmes"])
    for manifest in manifests:
        sibling = str(PurePosixPath(manifest).with_name(cfg["module_readme_name"]))
        required.add(sibling)
        if sibling not in readmes:
            errors.append(f"MISSING-MODULE-README {manifest}: expected {sibling}")
    for readme in readmes:
        sibling = str(PurePosixPath(readme).with_name(cfg["module_manifest_name"]))
        if sibling not in manifests:
            errors.append(f"ORPHAN-MODULE-README {readme}: missing {sibling}")
    for name in sorted(required):
        errors.extend(readme_errors(root, name, cfg, files))
    return errors


def selftest() -> None:
    cfg = {
        "schema": SCHEMA,
        "minimum_bytes": 20,
        "required_readmes": [
            "README.md",
            ".arena/README.md",
            ".arena/modules/README.md",
        ],
        "module_manifest_root": ".arena/modules",
        "module_manifest_name": "module.json",
        "module_readme_name": "README.md",
        "required_markers": {
            "README.md": ["ROOT"],
            ".arena/modules/README.md": ["module.json"],
        },
        "forbidden_patterns": [r"/Use[r]s/"],
        "check_relative_links": True,
    }
    data = {
        "README.md": "# root\n\nROOT [control](.arena/README.md)\n",
        ".arena/README.md": "# control\n\n[modules](modules/README.md)\n",
        ".arena/modules/README.md": "# modules\n\n`module.json` [one](one/README.md)\n",
        ".arena/modules/one/module.json": "{}\n",
        ".arena/modules/one/README.md": "# one\n\n[manifest](module.json)\n",
        "contract.json": json.dumps(cfg),
    }
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        for name, text in data.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        files = set(data)
        if check(root, root / "contract.json", files):
            raise Fatal("positive fixture failed")
        module = ".arena/modules/one/README.md"
        (root / module).unlink()
        if not any(
            error.startswith("MISSING-MODULE-README")
            for error in check(root, root / "contract.json", files - {module})
        ):
            raise Fatal("missing module README control failed")
        (root / module).write_text(data[module])
        (root / module).write_text("# one\n\n[bad](missing.md)\n")
        if not any(
            error.startswith("BROKEN-LINK")
            for error in check(root, root / "contract.json", files)
        ):
            raise Fatal("broken link control failed")
        (root / module).write_text(data[module])
        bad_home = "/Use" + "rs/x"
        (root / "README.md").write_text(data["README.md"] + bad_home + "\n")
        if not any(
            error.startswith("FORBIDDEN-PATH")
            for error in check(root, root / "contract.json", files)
        ):
            raise Fatal("machine path control failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("docs/architecture/readme-coverage.contract.json"),
    )
    parser.add_argument("--index-manifest", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    try:
        if args.selftest:
            selftest()
            print("SELFTEST GREEN: README coverage")
            return 0
        root = args.root.resolve()
        config = args.contract if args.contract.is_absolute() else root / args.contract
        files = tracked(root, args.index_manifest)
        errors = check(root, config, files)
        if errors:
            for error in errors:
                print(f"README-COVERAGE-RED {error}", file=sys.stderr)
            return 2
        count = len(modules(load_contract(config), files)[0])
        print(f"PASS README coverage: {count} module guide(s) plus navigation")
        return 0
    except (Fatal, OSError) as exc:
        print(f"README coverage FATAL: {exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
