"""Sealed disposable projection materializer for the controlled-language Harness.

The materializer takes an exact checked-out upstream source plus the admitted
07A binding blob, copies only the selected Skill subtree into a disposable
target, gives Codex the single materialized body and Claude a relative pointer
to that same body, verifies every projected path/mode/blob against the selected
Git tree, and returns a path-redacted parity receipt.

Divergence between the two carriers is prevented by shape rather than by
discipline: Claude never receives a second copy, only a relative symlink into
the one Codex body, so there is nothing that can drift. The control battery
still plants a hand-maintained copy to prove the gate refuses that shape.

A green result is mechanism evidence only. It does not claim the real private
upstream checkout, a Codex or Claude cold start, or a model/manual run happened.
"""

from __future__ import annotations

import copy
import hashlib
import os
import re
import shutil
import stat
import subprocess
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable

from .constants import BASE, CANDIDATE
from .model import BadInput, Red, digest_bytes, read_document, scan_durable

CONSUMER = "ed3c/bettor-arena"
UPSTREAM = "ed3c/skills-shared"
CONSUMER_BINDING_BLOB = "d4f4d36095862c46b0d92057ee2e6d42dea14b2a"
CONSUMER_BINDING_PATH = BASE / "binding.json"

PROJECTION_BASE = BASE / "projection"
CONTRACT_PATH = PROJECTION_BASE / "contract.json"
CASES_PATH = PROJECTION_BASE / "cases.json"
CASES_ROUTE = (
    ".skill-bindings/controlled-technical-language-harness/projection/cases.json"
)

SKILL_NAME = "controlled-technical-language-harness"
CARRIERS = {
    "claude_pointer": f".claude/skills/{SKILL_NAME}",
    "claude_pointer_target": f"../../.agents/skills/{SKILL_NAME}",
    "codex_body": f".agents/skills/{SKILL_NAME}",
}

SOURCE_SELECTION = {
    "commit": CANDIDATE["commit"],
    "entrypoint": CANDIDATE["entrypoint"],
    "entrypoint_blob": CANDIDATE["entrypoint_blob"],
    "evals": f"{CANDIDATE['skill_path']}/evals.json",
    "evals_blob": CANDIDATE["evals_blob"],
    "mutable_ref": None,
    "repository": UPSTREAM,
    "skill_path": CANDIDATE["skill_path"],
    "skill_tree": CANDIDATE["skill_tree"],
    "tree": CANDIDATE["tree"],
}

EVIDENCE_CEILING = {
    "claude_cold_start": "NOT_EXERCISED",
    "claude_physical_carrier": "NOT_EXERCISED",
    "codex_cold_start": "NOT_EXERCISED",
    "codex_physical_carrier": "NOT_EXERCISED",
    "model_or_manual_processing": "NOT_EXERCISED",
    "official_compliance": "NOT_CLAIMED",
    "production_termbase": "ABSENT",
    "real_upstream_private_checkout": "NOT_EXERCISED",
}

HUMAN_OWNED = [
    "PRIVATE_UPSTREAM_CREDENTIAL_ADMISSION",
    "HOST_TRUST",
    "PHYSICAL_CARRIER_EXECUTION",
    "SAFETY_SEMANTIC_ACCEPTANCE",
    "CONFIDENTIAL_EXTERNAL_PROCESSING",
    "MERGE",
    "RELEASE",
    "ROLLBACK",
]

ALLOWED_MODES = {"100644", "100755"}
SYMLINK_MODE = "120000"
HEX40 = re.compile(r"^[0-9a-f]{40}$")

SOURCE_CLASSES = {"SELECTED_UPSTREAM_CHECKOUT", "SYNTHETIC_FIXTURE"}

FIXTURE_SKILL_PATH = f"skills/{SKILL_NAME}"
FIXTURE_DATE = "2026-01-01T00:00:00+00:00"
FIXTURE_BODY = {
    "SKILL.md": ("---\nname: fixture-harness\n---\n\nFixture body.\n", False),
    "evals.json": ('{\n  "cases": []\n}\n', False),
    "references/profile.md": ("# Fixture profile\n\nNon-normative.\n", False),
    "scripts/score.py": ("#!/usr/bin/env python3\nprint('fixture')\n", True),
}


class GitError(Exception):
    """A git invocation against the source checkout failed."""


@dataclass(frozen=True)
class Entry:
    mode: str
    sha: str
    path: str


@dataclass(frozen=True)
class Selection:
    commit: str
    tree: str
    skill_tree: str
    skill_path: str
    entrypoint_blob: str
    evals_blob: str

    @property
    def entrypoint(self) -> str:
        return f"{self.skill_path}/SKILL.md"

    @property
    def evals(self) -> str:
        return f"{self.skill_path}/evals.json"


def selection_from_contract(contract: dict[str, Any]) -> Selection:
    source = contract["source"]
    return Selection(
        commit=source["commit"],
        tree=source["tree"],
        skill_tree=source["skill_tree"],
        skill_path=source["skill_path"],
        entrypoint_blob=source["entrypoint_blob"],
        evals_blob=source["evals_blob"],
    )


def blob_id(raw: bytes) -> str:
    """Git blob object id of `raw`, computed without trusting git twice."""
    header = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    return hashlib.sha1(header + raw).hexdigest()


def git(repo: Path, *args: str, binary: bool = False, **overrides: str) -> Any:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    env["GIT_TERMINAL_PROMPT"] = "0"
    env.update(overrides)
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise GitError(f"git {' '.join(args)}: {detail}")
    return result.stdout if binary else result.stdout.decode("utf-8").strip()


# ---------------------------------------------------------------- inputs


def verify_consumer_binding(root: Path, expected_blob: str) -> str:
    """Bind the exact 07A consumer binding blob as an input of this slice."""
    path = root / CONSUMER_BINDING_PATH
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise BadInput(f"{CONSUMER_BINDING_PATH}: unreadable: {error}") from error
    observed = blob_id(raw)
    if observed != expected_blob:
        raise Red(
            "consumer binding blob differs from the admitted 07A subject: "
            f"{observed} != {expected_blob}"
        )
    return observed


def validate_contract(root: Path) -> dict[str, Any]:
    contract = read_document(root / CONTRACT_PATH).value
    cases_document = read_document(root / CASES_PATH)

    if contract.get("schema_version") != "controlled-language-projection-contract/v1":
        raise Red("projection contract schema is unsupported")
    if contract.get("contract_id") != "bettor-arena-controlled-language-projection":
        raise Red("projection contract identity drifted")
    if contract.get("contract_version") != "1.0.0":
        raise Red("projection contract version drifted")
    if contract.get("consumer") != CONSUMER:
        raise Red("projection consumer identity drifted")
    if contract.get("consumer_binding_blob") != CONSUMER_BINDING_BLOB:
        raise Red("projection contract does not bind the admitted 07A blob")
    if contract.get("source") != SOURCE_SELECTION:
        raise Red("projection source selection drifted from the admitted bundle")
    if contract.get("source", {}).get("mutable_ref") is not None:
        raise Red("mutable upstream ref cannot identify a release bundle")
    if contract.get("carriers") != CARRIERS:
        raise Red("projection carrier layout drifted")
    if contract.get("allowed_modes") != sorted(ALLOWED_MODES):
        raise Red("projected file-mode vocabulary drifted")
    if contract.get("evidence_ceiling") != EVIDENCE_CEILING:
        raise Red("materializer PASS cannot promote a physical carrier lane")
    if contract.get("human_owned") != HUMAN_OWNED:
        raise Red("Human-owned operation boundary drifted")
    if contract.get("private_reasoning_persistence") != "FORBIDDEN":
        raise Red("private reasoning fields are forbidden")

    reference = contract.get("artifacts", {}).get("control_cases")
    if not isinstance(reference, dict):
        raise Red("control-case artifact reference is absent")
    if reference.get("path") != CASES_ROUTE:
        raise Red("control-case artifact path differs from the declared route")
    if reference.get("digest") != digest_bytes(cases_document.raw):
        raise Red("control-case artifact digest does not bind exact bytes")

    scan_durable(contract)
    validate_cases(cases_document.value)
    contract["_cases"] = cases_document.value["cases"]
    return contract


def validate_cases(cases: dict[str, Any]) -> None:
    if cases.get("schema_version") != "controlled-language-projection-cases/v1":
        raise Red("control-case schema is unsupported")
    rows = cases.get("cases")
    if not isinstance(rows, list) or len(rows) != 23:
        raise Red("projection controls must contain 23 planted cases")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise Red("control case is malformed")
        case_id = row.get("id")
        if not isinstance(case_id, str) or not case_id:
            raise Red("control case id is absent")
        if case_id in seen:
            raise Red("duplicate control id")
        seen.add(case_id)
        if not isinstance(row.get("expected_error"), str) or not row["expected_error"]:
            raise Red(f"{case_id}: expected diagnostic is absent")


# ---------------------------------------------------------------- source


def verify_source_identity(source: Path, selection: Selection) -> None:
    for name, value in (
        ("commit", selection.commit),
        ("tree", selection.tree),
        ("skill_tree", selection.skill_tree),
    ):
        if not HEX40.fullmatch(value):
            raise Red(
                "mutable upstream ref cannot identify a release bundle: "
                f"{name}={value!r}"
            )
    try:
        head = git(source, "rev-parse", "HEAD")
    except GitError as error:
        raise BadInput(f"source is not a readable git checkout: {error}") from error
    if head != selection.commit:
        raise Red(
            "selected source commit is not the checked-out source head: "
            f"{head} != {selection.commit}"
        )
    try:
        tree = git(source, "rev-parse", f"{selection.commit}^{{tree}}")
        skill_tree = git(
            source, "rev-parse", f"{selection.commit}:{selection.skill_path}"
        )
    except GitError as error:
        raise Red(
            f"selected source subject is absent from the checkout: {error}"
        ) from error
    if tree != selection.tree:
        raise Red(
            f"source repository tree differs from the selection: {tree} != {selection.tree}"
        )
    if skill_tree != selection.skill_tree:
        raise Red(
            "source Skill tree differs from the selection: "
            f"{skill_tree} != {selection.skill_tree}"
        )


def assert_clean_subtree(source: Path, selection: Selection) -> None:
    try:
        status = git(
            source,
            "status",
            "--porcelain",
            "-z",
            "--",
            selection.skill_path,
            binary=True,
        )
    except GitError as error:
        raise BadInput(f"source status is unreadable: {error}") from error
    if status.strip():
        entries = status.decode("utf-8", "replace").replace("\0", " ").strip()
        raise Red(f"selected source Skill subtree is dirty: {entries}")


def read_skill_entries(source: Path, selection: Selection) -> list[Entry]:
    try:
        raw = git(source, "ls-tree", "-r", "-z", selection.skill_tree, binary=True)
    except GitError as error:
        raise Red(f"selected Skill tree is unreadable: {error}") from error

    entries: list[Entry] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        meta, _, rest = record.partition(b"\t")
        mode, kind, sha = meta.decode("utf-8").split()
        rel = rest.decode("utf-8")
        if mode == SYMLINK_MODE:
            raise Red(f"source subtree symlink cannot be projected: {rel}")
        if kind != "blob" or mode not in ALLOWED_MODES:
            raise Red(f"source subtree has a non-regular entry: {rel} ({mode} {kind})")
        parts = PurePosixPath(rel).parts
        if PurePosixPath(rel).is_absolute() or ".." in parts:
            raise Red(f"source subtree path escapes the Skill body: {rel}")
        entries.append(Entry(mode=mode, sha=sha, path=rel))

    if not entries:
        raise Red("selected Skill tree is empty")
    by_path = {entry.path: entry for entry in entries}
    if by_path.get("SKILL.md", Entry("", "", "")).sha != selection.entrypoint_blob:
        raise Red("source SKILL.md blob differs from the selection")
    if by_path.get("evals.json", Entry("", "", "")).sha != selection.evals_blob:
        raise Red("source evals blob differs from the selection")
    return sorted(entries, key=lambda entry: entry.path)


# ---------------------------------------------------------------- target


def assert_disposable_target(target: Path, consumer_root: Path, source: Path) -> None:
    resolved = target.resolve()
    for label, other in (("consumer", consumer_root), ("source", source)):
        live = other.resolve()
        if (
            resolved == live
            or resolved.is_relative_to(live)
            or live.is_relative_to(resolved)
        ):
            raise Red(f"disposable target must live outside the {label} checkout")
    if resolved.exists():
        if not resolved.is_dir():
            raise Red("disposable target must be an empty directory")
        if any(resolved.iterdir()):
            raise Red("disposable target must be empty")


def materialize(
    source: Path, entries: Iterable[Entry], target: Path, carriers: dict[str, str]
) -> tuple[Path, Path]:
    body = target / carriers["codex_body"]
    pointer = target / carriers["claude_pointer"]
    body.mkdir(parents=True)
    for entry in entries:
        destination = body / entry.path
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            destination.write_bytes(
                git(source, "cat-file", "blob", entry.sha, binary=True)
            )
        except GitError as error:
            raise Red(f"selected blob is unreadable: {entry.path}: {error}") from error
        destination.chmod(0o755 if entry.mode == "100755" else 0o644)
    pointer.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(carriers["claude_pointer_target"], pointer, target_is_directory=True)
    return body, pointer


def verify_parity(
    entries: list[Entry], body: Path, pointer: Path, carriers: dict[str, str]
) -> None:
    expected = {entry.path: entry for entry in entries}
    observed: dict[str, Path] = {}
    for path in sorted(body.rglob("*")):
        rel = path.relative_to(body).as_posix()
        if path.is_symlink():
            raise Red(f"projected entry is a symlink: {rel}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise Red(f"projected entry is not a regular file: {rel}")
        observed[rel] = path

    for rel in sorted(set(observed) - set(expected)):
        raise Red(f"extra projected file: {rel}")
    for rel in sorted(set(expected) - set(observed)):
        raise Red(f"missing projected file: {rel}")
    for rel, entry in sorted(expected.items()):
        raw = observed[rel].read_bytes()
        if blob_id(raw) != entry.sha:
            raise Red(f"changed projected bytes: {rel}")
        executable = bool(os.stat(observed[rel]).st_mode & stat.S_IXUSR)
        if ("100755" if executable else "100644") != entry.mode:
            raise Red(f"executable-mode drift: {rel}")

    if not pointer.is_symlink():
        raise Red("Claude carrier must be a relative pointer, not a second body")
    link = os.readlink(pointer)
    if PurePosixPath(link).is_absolute() or Path(link).is_absolute():
        raise Red(f"Claude pointer must be repository-relative: {link!r}")
    if link != carriers["claude_pointer_target"]:
        raise Red(f"Claude pointer must resolve to the Codex body: {link!r}")
    if pointer.resolve() != body.resolve():
        raise Red("Claude pointer must resolve to the Codex body")

    for rel, entry in sorted(expected.items()):
        try:
            reached = (pointer / rel).read_bytes()
        except OSError as error:
            raise Red(f"Codex and Claude bodies diverge: {rel}: {error}") from error
        if blob_id(reached) != entry.sha:
            raise Red(f"Codex and Claude bodies diverge: {rel}")


# ---------------------------------------------------------------- receipt


def content_digest(entries: Iterable[Entry]) -> str:
    payload = "".join(
        f"{entry.mode} {entry.sha} {entry.path}\n"
        for entry in sorted(entries, key=lambda entry: entry.path)
    )
    return digest_bytes(payload.encode("utf-8"))


def build_receipt(
    binding_blob: str,
    selection: Selection,
    entries: list[Entry],
    carriers: dict[str, str],
    source_class: str,
    disposition: str,
) -> dict[str, Any]:
    if source_class not in SOURCE_CLASSES:
        raise Red(f"unknown projection source class: {source_class}")
    return {
        "carriers": dict(carriers),
        "consumer": CONSUMER,
        "consumer_binding_blob": binding_blob,
        "evidence": dict(EVIDENCE_CEILING),
        "files": [
            {"blob": entry.sha, "mode": entry.mode, "path": entry.path}
            for entry in entries
        ],
        "materializer_state": "PASS",
        "projected": {
            "content_digest": content_digest(entries),
            "executable_count": sum(1 for e in entries if e.mode == "100755"),
            "file_count": len(entries),
        },
        "schema_version": "controlled-language-projection-receipt/v1",
        "source": {
            "commit": selection.commit,
            "entrypoint_blob": selection.entrypoint_blob,
            "evals_blob": selection.evals_blob,
            "repository": UPSTREAM if source_class != "SYNTHETIC_FIXTURE" else None,
            "skill_path": selection.skill_path,
            "skill_tree": selection.skill_tree,
            "tree": selection.tree,
        },
        "source_class": source_class,
        "target_disposition": disposition,
    }


def scan_receipt(receipt: dict[str, Any]) -> None:
    """Refuse machine paths, secrets, private reasoning, and promoted lanes."""
    scan_durable(receipt)
    evidence = receipt.get("evidence")
    if not isinstance(evidence, dict):
        raise Red("receipt evidence boundary is absent")
    for lane, ceiling in EVIDENCE_CEILING.items():
        if evidence.get(lane) != ceiling:
            raise Red(
                f"static materializer success cannot promote {lane}: "
                f"{evidence.get(lane)!r} != {ceiling!r}"
            )


# ---------------------------------------------------------------- pipeline


def purge(target: Path, created: bool) -> None:
    """Leave a failed run's disposable target exactly as it was found."""
    if not target.exists():
        return
    if created:
        shutil.rmtree(target, ignore_errors=True)
        return
    for child in target.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child, ignore_errors=True)
        else:
            child.unlink(missing_ok=True)


def project(
    consumer_root: Path,
    source: Path,
    target: Path,
    selection: Selection,
    carriers: dict[str, str],
    binding_blob: str,
    source_class: str,
    disposition: str,
    tamper: Callable[[Path, Path, Path], None] | None = None,
) -> dict[str, Any]:
    verify_source_identity(source, selection)
    assert_clean_subtree(source, selection)
    entries = read_skill_entries(source, selection)
    assert_disposable_target(target, consumer_root, source)

    created = not target.exists()
    target.mkdir(parents=True, exist_ok=True)
    try:
        body, pointer = materialize(source, entries, target, carriers)
        if tamper is not None:
            tamper(target, body, pointer)
        verify_parity(entries, body, pointer, carriers)
    except BaseException:
        purge(target, created)
        raise

    receipt = build_receipt(
        binding_blob, selection, entries, carriers, source_class, disposition
    )
    scan_receipt(receipt)
    if disposition == "REMOVED":
        purge(target, created)
    return receipt


def run_projection(
    root: Path,
    source: Path | None = None,
    target: Path | None = None,
    expected_blob: str = CONSUMER_BINDING_BLOB,
) -> dict[str, Any]:
    """Positive lane: bind 07A, then materialize and verify one sealed body."""
    binding_blob = verify_consumer_binding(root, expected_blob)
    contract = validate_contract(root)
    carriers = contract["carriers"]

    with tempfile.TemporaryDirectory(prefix="ctl-projection-") as raw:
        scratch = Path(raw)
        if source is None:
            source, selection = build_fixture(scratch / "source")
            source_class = "SYNTHETIC_FIXTURE"
        else:
            selection = selection_from_contract(contract)
            source_class = "SELECTED_UPSTREAM_CHECKOUT"
        if target is None:
            target = scratch / "target"
            disposition = "REMOVED"
        else:
            disposition = "RETAINED"
        return project(
            root,
            source,
            target,
            selection,
            carriers,
            binding_blob,
            source_class,
            disposition,
        )


# ---------------------------------------------------------------- selftest


def build_fixture(repo: Path, symlink: bool = False) -> tuple[Path, Selection]:
    """Throwaway upstream-shaped git checkout; returns its observed selection."""
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "fixture@invalid")
    git(repo, "config", "user.name", "fixture")
    git(repo, "config", "commit.gpgsign", "false")

    skill = repo / FIXTURE_SKILL_PATH
    for rel, (content, executable) in FIXTURE_BODY.items():
        path = skill / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755 if executable else 0o644)
    (repo / "README.md").write_text("# fixture upstream\n", encoding="utf-8")
    if symlink:
        os.symlink("SKILL.md", skill / "references/alias.md")

    git(repo, "add", "-A")
    # Pinned dates keep the fixture commit/tree ids reproducible, so a control
    # that turns red is re-runnable against the same synthetic subject.
    git(
        repo,
        "commit",
        "-q",
        "-m",
        "fixture",
        GIT_AUTHOR_DATE=FIXTURE_DATE,
        GIT_COMMITTER_DATE=FIXTURE_DATE,
    )

    commit = git(repo, "rev-parse", "HEAD")
    selection = Selection(
        commit=commit,
        tree=git(repo, "rev-parse", "HEAD^{tree}"),
        skill_tree=git(repo, "rev-parse", f"HEAD:{FIXTURE_SKILL_PATH}"),
        skill_path=FIXTURE_SKILL_PATH,
        entrypoint_blob=git(repo, "rev-parse", f"HEAD:{FIXTURE_SKILL_PATH}/SKILL.md"),
        evals_blob=git(repo, "rev-parse", f"HEAD:{FIXTURE_SKILL_PATH}/evals.json"),
    )
    return repo, selection


def _pollute(receipt: dict[str, Any], key: str, value: Any) -> None:
    trial = copy.deepcopy(receipt)
    if key == "codex_physical_carrier":
        trial["evidence"][key] = value
    else:
        trial[key] = value
    scan_receipt(trial)


def apply_control(case_id: str, root: Path, scratch: Path) -> None:
    """Plant one defect and run the pipeline; a passing run means the gate is blind."""
    binding_blob = CONSUMER_BINDING_BLOB
    if case_id == "CTL-PROJ-001":
        verify_consumer_binding(root, "0" * 40)
        return

    source, selection = build_fixture(
        scratch / "source", symlink=case_id == "CTL-PROJ-009"
    )
    target = scratch / "target"
    carriers = dict(CARRIERS)
    tamper: Callable[[Path, Path, Path], None] | None = None

    if case_id == "CTL-PROJ-002":
        selection = replace(selection, commit="main")
    elif case_id == "CTL-PROJ-003":
        selection = replace(selection, commit="0" * 40)
    elif case_id == "CTL-PROJ-004":
        selection = replace(selection, tree="0" * 40)
    elif case_id == "CTL-PROJ-005":
        selection = replace(selection, skill_tree="0" * 40)
    elif case_id == "CTL-PROJ-006":
        selection = replace(selection, entrypoint_blob="0" * 40)
    elif case_id == "CTL-PROJ-007":
        selection = replace(selection, evals_blob="0" * 40)
    elif case_id == "CTL-PROJ-008":
        (source / FIXTURE_SKILL_PATH / "stray.md").write_text(
            "dirty\n", encoding="utf-8"
        )
    elif case_id == "CTL-PROJ-009":
        pass
    elif case_id == "CTL-PROJ-010":
        target = (
            root / "data" / "receipts" / "controlled-language" / "projection-target"
        )
    elif case_id == "CTL-PROJ-011":
        target = source / "disposable-target"
    elif case_id == "CTL-PROJ-012":
        target.mkdir(parents=True)
        (target / "leftover.txt").write_text("occupied\n", encoding="utf-8")
    elif case_id == "CTL-PROJ-013":

        def tamper(_target: Path, body: Path, _pointer: Path) -> None:
            (body / "references/profile.md").unlink()

    elif case_id == "CTL-PROJ-014":

        def tamper(_target: Path, body: Path, _pointer: Path) -> None:
            (body / "SKILL.md").write_text("rewritten\n", encoding="utf-8")

    elif case_id == "CTL-PROJ-015":

        def tamper(_target: Path, body: Path, _pointer: Path) -> None:
            (body / "SKILL.md").chmod(0o755)

    elif case_id == "CTL-PROJ-016":

        def tamper(_target: Path, body: Path, _pointer: Path) -> None:
            (body / "unsealed.md").write_text("extra\n", encoding="utf-8")

    elif case_id == "CTL-PROJ-017":

        def tamper(target_root: Path, body: Path, pointer: Path) -> None:
            pointer.unlink()
            os.symlink(str(body.resolve()), pointer, target_is_directory=True)

    elif case_id == "CTL-PROJ-018":

        def tamper(_target: Path, _body: Path, pointer: Path) -> None:
            pointer.unlink()
            os.symlink("../../.agents/skills/other", pointer, target_is_directory=True)

    elif case_id == "CTL-PROJ-019":

        def tamper(_target: Path, body: Path, pointer: Path) -> None:
            pointer.unlink()
            shutil.copytree(body, pointer)
            (pointer / "SKILL.md").write_text("hand maintained\n", encoding="utf-8")

    elif case_id in {"CTL-PROJ-020", "CTL-PROJ-021", "CTL-PROJ-022", "CTL-PROJ-023"}:
        receipt = project(
            root,
            source,
            target,
            selection,
            carriers,
            binding_blob,
            "SYNTHETIC_FIXTURE",
            "REMOVED",
        )
        # Assembled rather than written literally: a tracked literal machine root
        # is exactly what scripts/gates/check_root_coupling.py forbids.
        payload = {
            "CTL-PROJ-020": ("target_root", "/Use" + "rs/example/disposable"),
            "CTL-PROJ-021": ("session", "ghp_" + "0123456789abcdefghij"),
            "CTL-PROJ-022": ("reasoning_trace", ["private"]),
            "CTL-PROJ-023": ("codex_physical_carrier", "PASS"),
        }[case_id]
        _pollute(receipt, *payload)
        return
    else:
        raise RuntimeError(f"unknown control id: {case_id}")

    project(
        root,
        source,
        target,
        selection,
        carriers,
        binding_blob,
        "SYNTHETIC_FIXTURE",
        "REMOVED",
        tamper=tamper,
    )


def run_selftest(root: Path) -> int:
    contract = validate_contract(root)
    survived: list[str] = []
    for case in contract["_cases"]:
        with tempfile.TemporaryDirectory(prefix="ctl-projection-control-") as raw:
            try:
                apply_control(case["id"], root, Path(raw))
            except Red as error:
                if case["expected_error"] not in str(error):
                    survived.append(
                        f"{case['id']}: expected {case['expected_error']!r}, got {error}"
                    )
            else:
                survived.append(f"{case['id']}: control survived")
    if survived:
        raise Red("; ".join(survived))
    return len(contract["_cases"])
