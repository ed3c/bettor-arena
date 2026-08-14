#!/usr/bin/env python3
# ruff: noqa: F401,F403,F405  # this module family composes through star imports; the names ruff reads as unused are deliberate re-exports the downstream modules import through.
"""Validate LoopX Contract v1 documents and fixture bundles (0/2/64)."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

OK, BAD, USAGE = 0, 2, 64
SCHEMAS = {
    "command.schema.json": "loopx/command/v1",
    "event.schema.json": "loopx/event/v1",
    "gate-definition.schema.json": "loopx/gate-definition/v1",
    "snapshot.schema.json": "loopx/snapshot/v1",
    "task-state.schema.json": "loopx/task-state/v1",
}
BUNDLE = {
    "schema_version",
    "evidence_scope",
    "fixture",
    "subject",
    "gate_definitions",
    "task_state",
    "commands",
    "events",
    "snapshot",
}
SUBJECT = {"repository", "commit", "tree", "task_id"}
ART = {"artifact_id", "kind", "path", "digest", "bytes", "media_type", "producer"}
GATE = {
    "schema_version",
    "gate_id",
    "name",
    "severity",
    "observation_class",
    "execution",
    "oracle",
    "artifacts",
}
GEXEC = {"executable", "argv", "cwd", "env_allowlist", "timeout_ms", "network"}
STATE = {
    "schema_version",
    "subject",
    "state_revision",
    "ledger_head_digest",
    "lifecycle",
    "objective",
    "current_todo_id",
    "todos",
    "evidence",
    "quota",
    "human_decision_refs",
}
TODO = {
    "todo_id",
    "title",
    "status",
    "depends_on",
    "gate_ids",
    "gate_results",
    "evidence_refs",
    "attempts",
    "last_failure_ref",
    "exception_ref",
}
GRES = {"gate_id", "attempt", "verdict", "observation_ref", "evaluator_digest"}
COMMAND = {
    "schema_version",
    "command_id",
    "subject",
    "expected_state_revision",
    "kind",
    "actor",
    "payload",
}
CPAY = {"todo_id", "request_ref", "reason_ref", "human_decision"}
EVENT = {
    "schema_version",
    "event_id",
    "subject",
    "sequence",
    "previous_event_digest",
    "event_digest",
    "occurred_at",
    "type",
    "actor",
    "payload",
}
EPAY = {
    "todo_id",
    "command_id",
    "request_ref",
    "worker_result_ref",
    "gate_observation",
    "quota_delta",
    "human_decision",
    "transition",
}
HDEC = {
    "decision_id",
    "signer_ref",
    "signature_ref",
    "action",
    "scope",
    "expires_at",
    "rationale_ref",
    "required_revalidation_gate_ids",
    "non_waivable_acknowledged",
}
SNAP = {
    "schema_version",
    "subject",
    "reducer",
    "state_revision",
    "ledger",
    "canonical_authority",
    "rebuildable",
    "state",
    "state_digest",
    "content_digest",
}
ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
H40 = re.compile(r"^[0-9a-f]{40}$")
DG = re.compile(r"^sha256:[0-9a-f]{64}$")
ENV = re.compile(r"^[A-Z_][A-Z0-9_]*$")
SECRET = re.compile(
    r"(?:^|_)(?:TOKEN|SECRET|PASSWORD|COOKIE|CREDENTIAL|PRIVATE_KEY|API_KEY)(?:_|$)"
)
PRIVATE = {
    "thought",
    "thought_stream",
    "chain_of_thought",
    "private_reasoning",
    "raw_thought",
}
CMD_FORBID = PRIVATE | {
    "status",
    "verdict",
    "gate_passed",
    "state_revision",
    "ledger_head",
    "event_digest",
    "sequence",
    "human_admit",
    "promote",
    "promotion",
    "rollback",
    "merge",
    "force_skip",
    "shell",
    "raw_command",
    "command",
    "cwd",
}
ALLOWED_TRANSITIONS = {
    ("DRAFT", "READY"),
    ("READY", "ACTIVE"),
    ("PENDING", "READY"),
    ("READY", "DISPATCHED"),
    ("DISPATCHED", "RUNNING"),
    ("RUNNING", "RETRY"),
    ("RETRY", "DISPATCHED"),
    ("RUNNING", "HITL_PENDING"),
    ("RETRY", "HITL_PENDING"),
    ("HITL_PENDING", "READY"),
    ("HITL_PENDING", "CANCELLED"),
    ("RUNNING", "COMPLETED"),
    ("RUNNING", "COMPLETED_WITH_EXCEPTION"),
    ("READY", "CANCELLED"),
    ("ACTIVE", "HITL_PENDING"),
    ("ACTIVE", "COMPLETED"),
    ("ACTIVE", "COMPLETED_WITH_EXCEPTION"),
    ("ACTIVE", "FAILED"),
    ("ACTIVE", "CANCELLED"),
    ("HITL_PENDING", "ACTIVE"),
    ("HITL_PENDING", "FAILED"),
    ("HITL_PENDING", "CANCELLED"),
}


class Violation(ValueError):
    pass


class Input(ValueError):
    pass


def canonical(x: Any) -> bytes:
    return json.dumps(
        x, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()


def digest(x: Any) -> str:
    return (
        "sha256:"
        + hashlib.sha256(
            x if isinstance(x, (bytes, bytearray)) else canonical(x)
        ).hexdigest()
    )


def load(p: Path) -> Any:
    try:
        return json.loads(p.read_text())
    except FileNotFoundError as e:
        raise Input(f"missing JSON: {p}") from e
    except (OSError, json.JSONDecodeError) as e:
        raise Input(f"unreadable JSON: {p}: {e}") from e


def obj(x: Any, keys: set[str], name: str) -> dict[str, Any]:
    if not isinstance(x, dict):
        raise Violation(f"{name} must be an object")
    if set(x) != keys:
        raise Violation(
            f"{name} fields drifted; missing={sorted(keys - set(x))}, extra={sorted(set(x) - keys)}"
        )
    return x


def text(x: Any, name: str, n: int = 4096) -> str:
    if not isinstance(x, str) or not x.strip() or len(x) > n or "\0" in x:
        raise Violation(f"{name} must be a non-empty bounded string")
    return x


def sid(x: Any, name: str) -> str:
    s = text(x, name, 128)
    if not ID.fullmatch(s):
        raise Violation(f"{name} is not a stable lower-kebab identifier")
    return s


def sha(x: Any, name: str, null: bool = False) -> str | None:
    if x is None and null:
        return None
    if not isinstance(x, str) or not DG.fullmatch(x):
        raise Violation(f"{name} must be sha256:<64 lower-hex>")
    return x


def path(x: Any, name: str, dot: bool = True) -> str:
    s = text(x, name, 512)
    if s == "." and dot:
        return s
    p = PurePosixPath(s)
    if "\\" in s or p.is_absolute() or any(q in {"", ".", ".."} for q in p.parts):
        raise Violation(f"{name} must be a normalized relative path")
    if any(
        q.lower() in {".git", ".env", "credentials", "cookies", "auth.json", "keychain"}
        for q in p.parts
    ):
        raise Violation(f"{name} enters a forbidden secret/control path")
    return s


def same(a: Any, b: Any, name: str) -> None:
    if a != b:
        raise Violation(f"{name} subject/state mismatch")


def subject(x: Any, name: str) -> dict[str, Any]:
    v = obj(x, SUBJECT, name)
    if not REPO.fullmatch(text(v["repository"], name + ".repository", 256)):
        raise Violation(f"{name}.repository must be owner/name")
    for k in ("commit", "tree"):
        if not isinstance(v[k], str) or not H40.fullmatch(v[k]):
            raise Violation(f"{name}.{k} must be exact 40-hex")
    sid(v["task_id"], name + ".task_id")
    return v


def artifact(x: Any, name: str) -> dict[str, Any]:
    v = obj(x, ART, name)
    sid(v["artifact_id"], name + ".artifact_id")
    if v["kind"] not in {
        "STDOUT",
        "STDERR",
        "GIT_DIFF",
        "LSP_DIAGNOSTICS",
        "LINTER_REPORT",
        "TEST_REPORT",
        "FILE",
        "TRACE",
        "HUMAN_DECISION",
    }:
        raise Violation(f"{name}.kind unsupported")
    path(v["path"], name + ".path", False)
    sha(v["digest"], name + ".digest")
    if type(v["bytes"]) is not int or not 0 <= v["bytes"] <= 104857600:
        raise Violation(f"{name}.bytes outside budget")
    text(v["media_type"], name + ".media_type", 128)
    sid(v["producer"], name + ".producer")
    return v


def forbidden(x: Any, keys: set[str], name: str) -> None:
    if isinstance(x, dict):
        for k, v in x.items():
            if str(k).lower() in keys:
                raise Violation(f"{name} contains forbidden key: {k}")
            forbidden(v, keys, f"{name}.{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            forbidden(v, keys, f"{name}[{i}]")


def schema_docs(root: Path) -> None:
    d = root / "contracts"
    m = obj(
        load(d / "manifest.json"),
        {
            "schema_version",
            "interface_version",
            "authority_law",
            "schemas",
            "evidence_states",
            "runtime_state_path",
            "runtime_state_checked_in",
        },
        "manifest",
    )
    if (
        m["schema_version"] != "loopx/contract-manifest/v1"
        or m["interface_version"] != "1.0.0"
    ):
        raise Violation("contract manifest version drifted")
    if (
        m["runtime_state_path"] != ".loopx/"
        or m["runtime_state_checked_in"] is not False
    ):
        raise Violation("runtime state must remain untracked under .loopx/")
    if m["authority_law"] != [
        "strategy proposes",
        "worker executes",
        "gates observe",
        "LoopX reducer commits canonical state",
        "Human admits scoped decisions",
    ]:
        raise Violation("authority law drifted")
    if m["evidence_states"] != [
        "PASS",
        "FAIL",
        "ABSENT",
        "NOT_IMPLEMENTED",
        "NOT_EXERCISED",
        "SKIPPED_BY_POLICY",
    ]:
        raise Violation("evidence vocabulary drifted")
    if not isinstance(m["schemas"], list) or len(m["schemas"]) != 5:
        raise Violation("manifest must enumerate five schemas")
    seen = set()
    for i, e in enumerate(m["schemas"]):
        e = obj(e, {"id", "path", "sha256"}, f"manifest.schemas[{i}]")
        p = path(e["path"], f"manifest.schemas[{i}].path", False)
        if p in seen or p not in SCHEMAS:
            raise Violation(f"unexpected/duplicate schema: {p}")
        seen.add(p)
        raw = (
            (d / p).read_bytes()
            if (d / p).exists()
            else (_ for _ in ()).throw(Input(f"missing schema: {d / p}"))
        )
        if e["sha256"] != hashlib.sha256(raw).hexdigest():
            raise Violation(f"schema digest drift: {p}")
        s = load(d / p)
        if (
            s.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
            or s.get("$id") != e["id"]
            or not e["id"].endswith("/" + p)
        ):
            raise Violation(f"schema identity drift: {p}")
        if (
            s.get("type") != "object"
            or s.get("additionalProperties") is not False
            or s.get("properties", {}).get("schema_version", {}).get("const")
            != SCHEMAS[p]
        ):
            raise Violation(f"schema fail-closed/version drift: {p}")
        forbidden(s.get("properties", {}), {"shell", "raw_command"}, p)
    if seen != set(SCHEMAS):
        raise Violation("schema coverage drifted")


def gate(x: Any, name: str) -> dict[str, Any]:
    v = obj(x, GATE, name)
    if v["schema_version"] != "loopx/gate-definition/v1":
        raise Violation(f"{name}.schema_version drifted")
    sid(v["gate_id"], name + ".gate_id")
    text(v["name"], name + ".name", 160)
    if v["severity"] not in {"CRITICAL", "ADVISORY"}:
        raise Violation(f"{name}.severity unsupported")
    if v["observation_class"] not in {
        "EXIT_CODE",
        "LSP_DIAGNOSTICS",
        "LINTER_REPORT",
        "TEST_REPORT",
        "DIFF_ALLOWLIST",
        "ARTIFACT_DIGEST",
        "JSON_SCHEMA",
    }:
        raise Violation(f"{name}.observation_class unsupported")
    e = obj(v["execution"], GEXEC, name + ".execution")
    exe = path(e["executable"], name + ".execution.executable", False)
    if not isinstance(e["argv"], list) or len(e["argv"]) > 128:
        raise Violation(f"{name}.execution.argv invalid")
    for i, a in enumerate(e["argv"]):
        text(a, f"{name}.execution.argv[{i}]")
    if (
        PurePosixPath(exe).name.lower()
        in {
            "sh",
            "bash",
            "zsh",
            "fish",
            "cmd",
            "cmd.exe",
            "powershell",
            "powershell.exe",
            "pwsh",
        }
        and e["argv"]
        and e["argv"][0].lower()
        in {"-c", "/c", "-command", "--command", "-encodedcommand"}
    ):
        raise Violation(f"{name} exposes shell command string")
    path(e["cwd"], name + ".execution.cwd")
    if (
        not isinstance(e["env_allowlist"], list)
        or len(e["env_allowlist"]) != len(set(e["env_allowlist"]))
        or len(e["env_allowlist"]) > 32
    ):
        raise Violation(f"{name}.env_allowlist invalid")
    for z in e["env_allowlist"]:
        if not isinstance(z, str) or not ENV.fullmatch(z) or SECRET.search(z):
            raise Violation(f"{name} secret/invalid env allowlist")
    if (
        type(e["timeout_ms"]) is not int
        or not 1 <= e["timeout_ms"] <= 3600000
        or e["network"] not in {"DENY", "ALLOWLISTED", "INHERIT"}
    ):
        raise Violation(f"{name}.execution policy invalid")
    o = obj(v["oracle"], {"type", "expected"}, name + ".oracle")
    if o["type"] not in {
        "EXIT_CODE_EQUALS",
        "DIAGNOSTIC_COUNT",
        "JUNIT_FAILURE_COUNT",
        "DIFF_PATH_ALLOWLIST",
        "ARTIFACT_SHA256",
        "JSON_SCHEMA",
    }:
        raise Violation(f"{name}.oracle unsupported")
    if not isinstance(v["artifacts"], list) or len(v["artifacts"]) > 64:
        raise Violation(f"{name}.artifacts invalid")
    ids = set()
    ps = set()
    for i, a in enumerate(v["artifacts"]):
        a = obj(
            a,
            {"artifact_id", "path", "required", "max_bytes", "media_type"},
            f"{name}.artifacts[{i}]",
        )
        ai = sid(a["artifact_id"], f"{name}.artifacts[{i}].id")
        ap = path(a["path"], f"{name}.artifacts[{i}].path", False)
        if (
            ai in ids
            or ap in ps
            or type(a["required"]) is not bool
            or type(a["max_bytes"]) is not int
            or not 1 <= a["max_bytes"] <= 104857600
        ):
            raise Violation(f"{name}.artifact invalid/duplicate")
        ids.add(ai)
        ps.add(ap)
        text(a["media_type"], f"{name}.artifacts[{i}].media_type", 128)
    return v


def gate_result(x: Any, name: str, gates: dict[str, dict[str, Any]]) -> dict[str, Any]:
    v = obj(x, GRES, name)
    gid = sid(v["gate_id"], name + ".gate_id")
    if (
        gid not in gates
        or type(v["attempt"]) is not int
        or v["attempt"] < 1
        or v["verdict"] not in {"PASS", "FAIL", "NOT_RUN", "SKIPPED_BY_POLICY"}
    ):
        raise Violation(f"{name} invalid gate result")
    artifact(v["observation_ref"], name + ".observation_ref")
    sha(v["evaluator_digest"], name + ".evaluator_digest")
    return v


def human(x: Any, name: str) -> dict[str, Any]:
    v = obj(x, HDEC, name)
    sid(v["decision_id"], name + ".decision_id")
    text(v["signer_ref"], name + ".signer_ref", 256)
    if artifact(v["signature_ref"], name + ".signature_ref")[
        "kind"
    ] != "HUMAN_DECISION" or v["action"] not in {
        "RETRY_AFTER_FIX",
        "UPDATE_CONTRACT",
        "CANCEL",
        "SCOPED_EXCEPTION",
    }:
        raise Violation(f"{name} invalid Human action/signature")
    sc = obj(v["scope"], {"todo_id", "gate_ids", "assertion_ids"}, name + ".scope")
    if sc["todo_id"] is not None:
        sid(sc["todo_id"], name + ".scope.todo_id")
    for k in ("gate_ids", "assertion_ids"):
        if not isinstance(sc[k], list) or len(sc[k]) != len(set(sc[k])):
            raise Violation(f"{name}.scope.{k} invalid")
        for z in sc[k]:
            sid(z, f"{name}.scope.{k}")
    if sc["todo_id"] is None and not sc["gate_ids"] and not sc["assertion_ids"]:
        raise Violation(f"{name}.scope is empty")
    try:
        dt = datetime.strptime(
            text(v["expires_at"], name + ".expires_at", 32), "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)
    except ValueError as e:
        raise Violation(f"{name}.expires_at invalid") from e
    if dt.year < 2000:
        raise Violation(f"{name}.expires_at implausible")
    artifact(v["rationale_ref"], name + ".rationale_ref")
    if (
        not isinstance(v["required_revalidation_gate_ids"], list)
        or not v["required_revalidation_gate_ids"]
        or len(v["required_revalidation_gate_ids"])
        != len(set(v["required_revalidation_gate_ids"]))
    ):
        raise Violation(f"{name}.revalidation invalid")
    for z in v["required_revalidation_gate_ids"]:
        sid(z, name + ".revalidation")
    if v["non_waivable_acknowledged"] is not True or (
        v["action"] == "SCOPED_EXCEPTION"
        and not (sc["gate_ids"] or sc["assertion_ids"])
    ):
        raise Violation(f"{name} invalid exception boundary")
    forbidden(v, PRIVATE | {"force_skip"}, name)
    return v
