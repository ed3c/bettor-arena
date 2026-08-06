#!/usr/bin/env python3
"""Probe one Codex-configured stdio MCP through the real JSON-RPC transport."""

from __future__ import annotations

import argparse
import json
import os
import re
import selectors
import shutil
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO


PROTOCOL_VERSION = "2025-06-18"


class ProbeError(RuntimeError):
    """A fail-closed stdio probe error."""


@dataclass(frozen=True)
class Server:
    command: str
    args: tuple[str, ...]
    env: dict[str, str]
    enabled_tools: frozenset[str]
    startup_timeout: float
    tool_timeout: float


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProbeError(message)


def load_server(config_path: Path, server_name: str) -> Server:
    try:
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ProbeError(f"cannot parse Codex config {config_path}: {exc}") from exc
    payload = config.get("mcp_servers", {}).get(server_name)
    _require(isinstance(payload, dict), f"missing MCP server config: {server_name}")
    _require(payload.get("enabled") is True, f"MCP server is not enabled: {server_name}")
    command = payload.get("command")
    args = payload.get("args")
    enabled_tools = payload.get("enabled_tools")
    _require(isinstance(command, str) and command, f"missing command: {server_name}")
    _require(
        isinstance(args, list) and all(isinstance(value, str) for value in args),
        f"invalid args: {server_name}",
    )
    _require(
        isinstance(enabled_tools, list)
        and enabled_tools
        and all(isinstance(value, str) for value in enabled_tools)
        and len(enabled_tools) == len(set(enabled_tools)),
        f"enabled_tools must be a non-empty exact allowlist: {server_name}",
    )
    env = payload.get("env", {})
    _require(
        isinstance(env, dict)
        and all(isinstance(key, str) and isinstance(value, str) for key, value in env.items()),
        f"invalid env: {server_name}",
    )
    startup_timeout = payload.get("startup_timeout_sec")
    tool_timeout = payload.get("tool_timeout_sec")
    _require(
        isinstance(startup_timeout, (int, float)) and startup_timeout > 0,
        f"invalid startup timeout: {server_name}",
    )
    _require(
        isinstance(tool_timeout, (int, float)) and tool_timeout > 0,
        f"invalid tool timeout: {server_name}",
    )
    return Server(
        command=command,
        args=tuple(args),
        env=dict(env),
        enabled_tools=frozenset(enabled_tools),
        startup_timeout=float(startup_timeout),
        tool_timeout=float(tool_timeout),
    )


class Client:
    def __init__(self, process: subprocess.Popen[str]) -> None:
        self.process = process
        self.next_id = 1

    def send(self, method: str, params: dict[str, Any] | None = None) -> int:
        request_id = self.next_id
        self.next_id += 1
        self._write(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params or {},
            }
        )
        return request_id

    def notify(self, method: str) -> None:
        self._write({"jsonrpc": "2.0", "method": method, "params": {}})

    def _write(self, payload: dict[str, Any]) -> None:
        _require(self.process.stdin is not None, "MCP stdin is unavailable")
        self.process.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def receive(self, request_id: int, timeout: float) -> dict[str, Any]:
        _require(self.process.stdout is not None, "MCP stdout is unavailable")
        selector = selectors.DefaultSelector()
        selector.register(self.process.stdout, selectors.EVENT_READ)
        deadline = time.monotonic() + timeout
        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ProbeError(
                        f"MCP request id={request_id} timed out after {timeout:.0f}s"
                    )
                if not selector.select(remaining):
                    continue
                line = self.process.stdout.readline()
                if not line:
                    stderr = _read_available(self.process.stderr)
                    raise ProbeError(
                        f"MCP exited before id={request_id}; "
                        f"rc={self.process.poll()} stderr={stderr!r}"
                    )
                try:
                    response = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ProbeError(f"MCP stdout is not JSON-RPC: {line[:200]!r}") from exc
                if response.get("id") != request_id:
                    continue
                if "error" in response:
                    raise ProbeError(f"MCP id={request_id} failed: {response['error']}")
                result = response.get("result")
                _require(isinstance(result, dict), f"MCP id={request_id} result is not an object")
                return result
        finally:
            selector.close()


def _read_available(stream: TextIO | None) -> str:
    if stream is None:
        return ""
    try:
        return stream.read(1000)
    except (OSError, ValueError):
        return ""


def _stop(process: subprocess.Popen[str]) -> None:
    if process.stdin is not None and not process.stdin.closed:
        process.stdin.close()
    process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)
    for stream in (process.stdout, process.stderr):
        if stream is not None and not stream.closed:
            stream.close()


def _spawn(repo_root: Path, server: Server) -> subprocess.Popen[str]:
    env = os.environ.copy()
    env.update(server.env)
    executable = shutil.which(server.command, path=env.get("PATH"))
    _require(executable is not None, f"MCP command not found: {server.command}")
    return subprocess.Popen(
        [executable, *server.args],
        cwd=repo_root,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )


def _searchable_result(result: dict[str, Any]) -> str:
    parts = [json.dumps(result, ensure_ascii=False, sort_keys=True)]
    for item in result.get("content", []):
        if isinstance(item, dict) and isinstance(item.get("text"), str):
            parts.append(item["text"])
    structured = result.get("structuredContent")
    if structured is not None:
        parts.append(json.dumps(structured, ensure_ascii=False, sort_keys=True))
    return "\n".join(parts)


def probe(
    *,
    repo_root: Path,
    config_path: Path,
    server_name: str,
    tool_name: str = "",
    arguments: dict[str, Any] | None = None,
    require_regex: str = "",
    exact_surface: bool = True,
) -> dict[str, Any]:
    root = repo_root.resolve(strict=True)
    server = load_server(config_path.resolve(strict=True), server_name)
    if tool_name:
        _require(tool_name in server.enabled_tools, f"called tool is not allowlisted: {tool_name}")
    process = _spawn(root, server)
    client = Client(process)
    try:
        initialize_id = client.send(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "mcp-production-probe", "version": "1"},
            },
        )
        initialized = client.receive(initialize_id, server.startup_timeout)
        protocol = initialized.get("protocolVersion")
        _require(isinstance(protocol, str) and protocol, "initialize omitted protocolVersion")
        client.notify("notifications/initialized")

        tools_id = client.send("tools/list")
        tools = client.receive(tools_id, server.tool_timeout).get("tools")
        _require(isinstance(tools, list), "tools/list omitted tools")
        runtime_tools = {
            item.get("name")
            for item in tools
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        }
        surface_valid = (
            runtime_tools == server.enabled_tools
            if exact_surface
            else server.enabled_tools <= runtime_tools
        )
        _require(
            surface_valid,
            f"{server_name} tool surface drift: "
            f"configured={sorted(server.enabled_tools)} runtime={sorted(runtime_tools)}",
        )

        called = None
        if tool_name:
            call_id = client.send(
                "tools/call",
                {"name": tool_name, "arguments": arguments or {}},
            )
            call_result = client.receive(call_id, server.tool_timeout)
            rendered = _searchable_result(call_result)
            _require(
                call_result.get("isError") is not True,
                f"tool returned isError: {tool_name}: {rendered[:500]}",
            )
            if require_regex:
                _require(
                    re.search(require_regex, rendered) is not None,
                    f"tool canary miss for {tool_name}: /{require_regex}/",
                )
            called = tool_name
        return {
            "status": "pass",
            "server": server_name,
            "protocol_version": protocol,
            "runtime_tools": sorted(runtime_tools),
            "configured_tools": sorted(server.enabled_tools),
            "called_tool": called,
        }
    finally:
        _stop(process)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--server", required=True)
    parser.add_argument("--tool", default="")
    parser.add_argument("--arguments", default="{}")
    parser.add_argument("--require-regex", default="")
    parser.add_argument("--allow-runtime-superset", action="store_true")
    args = parser.parse_args()
    try:
        arguments = json.loads(args.arguments)
        _require(isinstance(arguments, dict), "--arguments must decode to an object")
        report = probe(
            repo_root=args.repo_root,
            config_path=args.config,
            server_name=args.server,
            tool_name=args.tool,
            arguments=arguments,
            require_regex=args.require_regex,
            exact_surface=not args.allow_runtime_superset,
        )
    except (ProbeError, OSError, json.JSONDecodeError) as exc:
        print(f"MCP stdio probe failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
