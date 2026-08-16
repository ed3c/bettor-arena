#!/usr/bin/env python3
"""Shared fixed-argv mechanics for exact-subject provider canaries."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import queue
import re
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from typing import Any


SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SECRET = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]"
    r"|\b(?:ghp|github_pat|sk)-[A-Za-z0-9_-]{12,}"
)


class CanaryError(ValueError):
    """Checked contract or live-canary failure."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CanaryError(message)


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def digest_value(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CanaryError(f"ABSENT {label}: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise CanaryError(f"INVALID {label}: {exc}") from exc
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def strict_keys(
    value: Any,
    *,
    required: set[str],
    optional: set[str] | None = None,
    label: str,
) -> None:
    require(isinstance(value, dict), f"{label} must be an object")
    optional = optional or set()
    missing = required - set(value)
    unexpected = set(value) - required - optional
    require(not missing, f"{label} missing keys: {sorted(missing)}")
    require(not unexpected, f"{label} unexpected keys: {sorted(unexpected)}")


def safe_relative(value: str) -> bool:
    if not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and all(part not in {"", "."} for part in path.parts)
    )


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise CanaryError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def repository_subject(root: Path, expected_repository: str) -> dict[str, str]:
    top = Path(git(root, "rev-parse", "--show-toplevel")).resolve()
    require(top == root.resolve(), "canary must run from the owning repository root")
    require(
        not git(root, "status", "--porcelain", "--untracked-files=no"),
        "tracked working tree must be clean before a live canary",
    )
    commit = git(root, "rev-parse", "HEAD")
    tree = git(root, "rev-parse", "HEAD^{tree}")
    require(SHA40.fullmatch(commit) is not None, "invalid Git commit identity")
    require(SHA40.fullmatch(tree) is not None, "invalid Git tree identity")
    require(
        REPOSITORY.fullmatch(expected_repository) is not None,
        "invalid repository identity",
    )
    return {"repository": expected_repository, "commit": commit, "tree": tree}


def coverage_manifest(root: Path, paths: list[str]) -> dict[str, Any]:
    require(paths and len(paths) == len(set(paths)), "coverage paths must be unique")
    entries: list[dict[str, Any]] = []
    for relative in paths:
        require(safe_relative(relative), f"unsafe coverage path: {relative}")
        source = root / relative
        require(
            source.is_file() and not source.is_symlink(), f"ABSENT source: {relative}"
        )
        git(root, "ls-files", "--error-unmatch", relative)
        raw = source.read_bytes()
        entries.append(
            {"path": relative, "sha256": digest_bytes(raw), "bytes": len(raw)}
        )
    value: dict[str, Any] = {"complete": False, "files": entries}
    value["digest"] = digest_value(value)
    return value


def materialize_coverage(
    root: Path, destination: Path, coverage: dict[str, Any]
) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    for entry in coverage["files"]:
        relative = entry["path"]
        source = root / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        require(digest_file(target) == entry["sha256"], f"copy drift: {relative}")


def coverage_is_current(project: Path, coverage: dict[str, Any]) -> bool:
    for entry in coverage["files"]:
        path = project / entry["path"]
        if not path.is_file() or digest_file(path) != entry["sha256"]:
            return False
    return True


def safe_environment(extra: dict[str, str] | None = None) -> dict[str, str]:
    allowed = ("PATH", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "NO_COLOR")
    environment = {key: os.environ[key] for key in allowed if key in os.environ}
    environment.setdefault("PATH", "/usr/local/bin:/usr/bin:/bin")
    if extra:
        environment.update(extra)
    return environment


def executable_identity(command: str, expected_sha256: str) -> dict[str, str]:
    path_value = shutil.which(command)
    require(path_value is not None, f"ABSENT executable: {command}")
    path = Path(path_value)
    real = path.resolve()
    observed = digest_file(path)
    require(
        SHA256.fullmatch(expected_sha256) is not None,
        "invalid pinned executable digest",
    )
    require(observed == expected_sha256, f"{command} executable digest drift")
    return {
        "command": command,
        "real_name": real.name,
        "sha256": observed,
    }


@dataclass
class Completed:
    exit: int
    stdout: str
    stderr: str
    elapsed_ms: int


def run_fixed(
    argv: list[str],
    *,
    cwd: Path,
    timeout: int,
    environment: dict[str, str],
) -> Completed:
    require(
        argv and all(isinstance(item, str) and item for item in argv),
        "fixed argv required",
    )
    started = time.monotonic()
    try:
        result = subprocess.run(
            argv,
            cwd=cwd,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise CanaryError(f"ABSENT executable: {argv[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise CanaryError(f"command timed out: {argv[0]}") from exc
    return Completed(
        exit=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        elapsed_ms=round((time.monotonic() - started) * 1000),
    )


class ManagedProcess:
    """Fixed process group with bounded logs and deterministic termination."""

    def __init__(
        self,
        argv: list[str],
        *,
        cwd: Path,
        environment: dict[str, str],
        log_root: Path,
        name: str,
    ) -> None:
        require(
            argv and all(isinstance(item, str) and item for item in argv),
            "fixed argv required",
        )
        log_root.mkdir(parents=True, exist_ok=True)
        self.stdout_path = log_root / f"{name}.stdout.log"
        self.stderr_path = log_root / f"{name}.stderr.log"
        self._stdout = self.stdout_path.open("w+", encoding="utf-8")
        self._stderr = self.stderr_path.open("w+", encoding="utf-8")
        self.process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=self._stdout,
            stderr=self._stderr,
            text=True,
            start_new_session=True,
        )

    def alive(self) -> bool:
        return self.process.poll() is None

    def close(self) -> None:
        if self.process.poll() is None:
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(self.process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                self.process.wait(timeout=5)
        self._stdout.close()
        self._stderr.close()

    def log_receipt(self) -> dict[str, Any]:
        for handle in (self._stdout, self._stderr):
            handle.flush()
        stdout = self.stdout_path.read_bytes()
        stderr = self.stderr_path.read_bytes()
        return {
            "stdout_bytes": len(stdout),
            "stdout_sha256": digest_bytes(stdout),
            "stderr_bytes": len(stderr),
            "stderr_sha256": digest_bytes(stderr),
        }


class McpStdioClient:
    """Small newline-delimited MCP stdio client with fixed process ownership."""

    def __init__(
        self,
        argv: list[str],
        *,
        cwd: Path,
        environment: dict[str, str],
        timeout: int,
        log_root: Path,
        name: str,
    ) -> None:
        require(
            argv and all(isinstance(item, str) and item for item in argv),
            "fixed MCP argv required",
        )
        self.timeout = timeout
        log_root.mkdir(parents=True, exist_ok=True)
        self.stderr_path = log_root / f"{name}.stderr.log"
        self._stderr = self.stderr_path.open("w+", encoding="utf-8")
        self.process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self._stderr,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
        require(
            self.process.stdin is not None and self.process.stdout is not None,
            "MCP pipes absent",
        )
        self._messages: queue.Queue[str | None] = queue.Queue()
        self._reader = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader.start()
        self._next_id = 1
        self.request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "bettor-provider-canary", "version": "1"},
            },
        )
        self.notify("notifications/initialized", {})

    def _read_stdout(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            self._messages.put(line)
        self._messages.put(None)

    def _send(self, value: dict[str, Any]) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(value, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        self._send(
            {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        )
        deadline = time.monotonic() + self.timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CanaryError(f"MCP request timed out: {method}")
            try:
                line = self._messages.get(timeout=remaining)
            except queue.Empty as exc:
                raise CanaryError(f"MCP request timed out: {method}") from exc
            if line is None:
                raise CanaryError(f"MCP server exited during: {method}")
            try:
                message = json.loads(line)
            except json.JSONDecodeError as exc:
                raise CanaryError("MCP server wrote non-JSON stdout") from exc
            if message.get("id") != request_id:
                continue
            if "error" in message:
                detail = message["error"].get("message", "unknown error")
                raise CanaryError(f"MCP {method} failed: {detail}")
            result = message.get("result")
            require(isinstance(result, dict), f"MCP {method} result must be an object")
            return result

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def list_tools(self) -> list[dict[str, Any]]:
        result = self.request("tools/list", {})
        tools = result.get("tools")
        require(isinstance(tools, list), "MCP tools/list omitted tools")
        return tools

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.request("tools/call", {"name": name, "arguments": arguments})

    def close(self) -> None:
        if self.process.stdin is not None and not self.process.stdin.closed:
            self.process.stdin.close()
        if self.process.poll() is None:
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(self.process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                self.process.wait(timeout=5)
        self._reader.join(timeout=2)
        self._stderr.close()

    def stderr_receipt(self) -> dict[str, Any]:
        self._stderr.flush()
        raw = self.stderr_path.read_bytes()
        return {"bytes": len(raw), "sha256": digest_bytes(raw)}


def tool_text(result: dict[str, Any], *, allow_error: bool = False) -> str:
    if result.get("isError") is True and not allow_error:
        raise CanaryError("MCP tool returned isError=true")
    content = result.get("content")
    require(isinstance(content, list), "MCP tool omitted content")
    values = [
        item.get("text", "")
        for item in content
        if isinstance(item, dict) and item.get("type") == "text"
    ]
    text = "\n".join(value for value in values if isinstance(value, str))
    require(text or allow_error, "MCP tool returned no text")
    return text


def secret_free(value: str) -> bool:
    return SECRET.search(value) is None


def bounded_observation(text: str, max_bytes: int) -> dict[str, Any]:
    raw = text.encode("utf-8")
    require(len(raw) <= max_bytes, "provider result exceeded max_bytes")
    require(secret_free(text), "provider result contained secret-shaped data")
    return {"bytes": len(raw), "sha256": digest_bytes(raw)}


def validate_output(root: Path, provider: str, value: str) -> Path:
    relative = PurePosixPath(value)
    require(safe_relative(value), "output must be repository-relative")
    expected = PurePosixPath("data") / "provider-canaries" / provider
    require(relative.is_relative_to(expected), "output escaped provider receipt root")
    require(relative.suffix == ".json", "output must be JSON")
    path = (root / relative).resolve()
    require(not path.exists(), "output receipt already exists")
    return path


def validate_common_workload(value: dict[str, Any], provider: str) -> None:
    strict_keys(
        value,
        required={
            "schema",
            "provider_id",
            "source",
            "executable",
            "subject",
            "coverage",
            "limits",
            "policy",
            "provider",
        },
        label="workload",
    )
    require(
        value["schema"] == "bettor-arena/provider-canary-workload/v1", "workload schema"
    )
    require(value["provider_id"] == provider, "provider id drift")
    strict_keys(
        value["source"],
        required={"repository", "commit", "version", "license"},
        label="source",
    )
    require(SHA40.fullmatch(value["source"]["commit"]) is not None, "source commit")
    require(value["source"]["license"] == "MIT", "license must be MIT")
    strict_keys(
        value["executable"],
        required={"command", "sha256"},
        label="executable",
    )
    require(
        SHA256.fullmatch(value["executable"]["sha256"]) is not None, "executable sha256"
    )
    strict_keys(value["subject"], required={"repository"}, label="subject")
    require(
        REPOSITORY.fullmatch(value["subject"]["repository"]) is not None,
        "subject repository",
    )
    require(
        isinstance(value["coverage"], list)
        and value["coverage"]
        and all(
            isinstance(item, str) and safe_relative(item) for item in value["coverage"]
        ),
        "coverage paths",
    )
    strict_keys(
        value["limits"],
        required={"timeout_seconds", "max_results", "max_bytes", "max_index_bytes"},
        label="limits",
    )
    for key in ("timeout_seconds", "max_results", "max_bytes", "max_index_bytes"):
        require(
            isinstance(value["limits"][key], int) and value["limits"][key] > 0,
            f"limit {key}",
        )
    strict_keys(
        value["policy"],
        required={
            "candidate_only",
            "source_readback_required",
            "external_network",
            "external_spend_usd",
            "secrets",
            "cleanup_required",
        },
        label="policy",
    )
    require(value["policy"]["candidate_only"] is True, "candidate-only policy")
    require(
        value["policy"]["source_readback_required"] is True, "source-readback policy"
    )
    require(value["policy"]["external_network"] == "DENIED", "external network policy")
    require(value["policy"]["external_spend_usd"] == 0, "external spend policy")
    require(value["policy"]["secrets"] == "DENIED", "secret policy")
    require(value["policy"]["cleanup_required"] is True, "cleanup policy")


def common_selftest() -> int:
    checks = 0
    require(safe_relative("scripts/example.py"), "safe path rejected")
    checks += 1
    require(not safe_relative("../outside"), "path traversal accepted")
    checks += 1
    require(secret_free("candidate result"), "safe result rejected")
    checks += 1
    require(
        not secret_free("api_key=abcdefghijklmnop"), "secret-shaped result accepted"
    )
    checks += 1
    with tempfile.TemporaryDirectory(prefix="provider-canary-selftest-") as tmp:
        root = Path(tmp)
        server = root / "fake_mcp.py"
        server.write_text(
            """import json
import sys

for line in sys.stdin:
    request = json.loads(line)
    request_id = request.get("id")
    method = request.get("method")
    if request_id is None:
        continue
    if method == "initialize":
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "serverInfo": {"name": "fake", "version": "1"},
        }
    elif method == "tools/list":
        result = {"tools": [{"name": "echo", "inputSchema": {"type": "object"}}]}
    else:
        result = {
            "content": [{"type": "text", "text": "ok"}],
            "isError": False,
        }
    print(json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}), flush=True)
""",
            encoding="utf-8",
        )
        client = McpStdioClient(
            [os.sys.executable, "-u", str(server)],
            cwd=root,
            environment=safe_environment(),
            timeout=5,
            log_root=root / "logs",
            name="fake",
        )
        try:
            require(client.list_tools()[0]["name"] == "echo", "MCP tool list drift")
            require(tool_text(client.call_tool("echo", {})) == "ok", "MCP call drift")
            checks += 2
        finally:
            client.close()
        require(client.process.poll() is not None, "MCP process residue")
        checks += 1
    return checks
