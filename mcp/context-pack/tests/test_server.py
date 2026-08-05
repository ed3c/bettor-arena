from __future__ import annotations

import asyncio
import json
import sys
import tomllib
import unittest
from pathlib import Path

from mcp import Client
from mcp.client.stdio import StdioServerParameters, stdio_client

from context_pack_mcp.server import mcp


class MCPServerTests(unittest.TestCase):
    def test_in_process_tools_list_and_call(self) -> None:
        async def exercise() -> None:
            async with Client(mcp) as client:
                tools = await client.list_tools()
                names = {tool.name for tool in tools.tools}
                self.assertEqual(names, {"build_python_context_pack", "context_pack_status"})
                result = await client.call_tool(
                    "build_python_context_pack",
                    {
                        "relative_path": "mcp/context-pack/tests/fixtures/sample_service.py",
                        "symbol": "Ledger.settle",
                        "max_bytes": 8_000,
                    },
                )
                payload = result.structured_content
                self.assertIsNotNone(payload)
                assert payload is not None
                self.assertEqual(payload["relative_path"], "mcp/context-pack/tests/fixtures/sample_service.py")
                self.assertEqual(payload["completeness"], "partial")

        asyncio.run(exercise())

    def test_real_stdio_subprocess(self) -> None:
        async def exercise() -> None:
            root = Path(__file__).resolve().parents[3]
            parameters = StdioServerParameters(
                command=sys.executable,
                args=["-m", "context_pack_mcp.server"],
                cwd=root,
            )
            async with Client(stdio_client(parameters), read_timeout_seconds=10) as client:
                result = await client.call_tool("context_pack_status", {})
                payload = result.structured_content
                self.assertIsNotNone(payload)
                assert payload is not None
                self.assertEqual(payload["status"], "ready")
                self.assertTrue(payload["read_only"])

        asyncio.run(exercise())

    def test_host_configured_command_from_nested_directory(self) -> None:
        async def exercise() -> None:
            root = Path(__file__).resolve().parents[3]
            config = json.loads((root / ".mcp.json").read_text())["mcpServers"][
                "repo-context-pack"
            ]
            parameters = StdioServerParameters(
                command=config["command"],
                args=config["args"],
                cwd=root / "docs",
            )
            async with Client(stdio_client(parameters), read_timeout_seconds=20) as client:
                result = await client.call_tool(
                    "build_python_context_pack",
                    {
                        "relative_path": "mcp/context-pack/tests/fixtures/sample_service.py",
                        "symbol": "Ledger.settle",
                        "max_bytes": 8_000,
                    },
                )
                payload = result.structured_content
                self.assertIsNotNone(payload)
                assert payload is not None
                self.assertEqual(len(payload["source_sha256"]), 64)
                self.assertLessEqual(payload["context_bytes"], 8_000)

        asyncio.run(exercise())

    def test_codex_and_claude_use_same_context_pack_launcher(self) -> None:
        root = Path(__file__).resolve().parents[3]
        claude = json.loads((root / ".mcp.json").read_text())["mcpServers"][
            "repo-context-pack"
        ]
        with (root / ".codex/config.toml").open("rb") as config_file:
            codex = tomllib.load(config_file)["mcp_servers"]["repo-context-pack"]

        self.assertEqual(codex["command"], claude["command"])
        self.assertEqual(codex["args"], claude["args"])


if __name__ == "__main__":
    unittest.main()
