from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


PROBE = Path(__file__).resolve().parents[1] / "probe_stdio.py"
SPEC = importlib.util.spec_from_file_location("mcp_production_probe_stdio", PROBE)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


FAKE_SERVER = r'''#!/usr/bin/env python3
import json
import sys

TOOLS = ["status", "search"]
for line in sys.stdin:
    request = json.loads(line)
    if "id" not in request:
        continue
    if request["method"] == "initialize":
        result = {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "serverInfo": {"name": "fake", "version": "1"},
        }
    elif request["method"] == "tools/list":
        result = {
            "tools": [
                {"name": name, "description": name, "inputSchema": {"type": "object"}}
                for name in TOOLS
            ]
        }
    else:
        result = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "ready": True,
                            "arguments": request["params"]["arguments"],
                        }
                    ),
                }
            ]
        }
    print(json.dumps({"jsonrpc": "2.0", "id": request["id"], "result": result}), flush=True)
'''


class StdioProbeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.server = self.root / "fake_server.py"
        self.server.write_text(FAKE_SERVER, encoding="utf-8")
        self.server.chmod(0o755)
        self.config = self.root / "config.toml"
        self.config.write_text(
            textwrap.dedent(
                f"""
                [mcp_servers.fixture]
                command = {json.dumps(sys.executable)}
                args = [{json.dumps(str(self.server))}]
                enabled = true
                startup_timeout_sec = 5
                tool_timeout_sec = 5
                enabled_tools = ["status", "search"]
                """
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_initialize_exact_tool_surface_and_live_call(self) -> None:
        report = MODULE.probe(
            repo_root=self.root,
            config_path=self.config,
            server_name="fixture",
            tool_name="status",
            arguments={"format": "json"},
            require_regex=r'"ready":\s*true',
        )
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["runtime_tools"], ["search", "status"])
        self.assertEqual(report["called_tool"], "status")

    def test_runtime_surface_drift_is_rejected(self) -> None:
        self.config.write_text(
            self.config.read_text().replace(
                'enabled_tools = ["status", "search"]',
                'enabled_tools = ["status"]',
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(MODULE.ProbeError, "tool surface drift"):
            MODULE.probe(
                repo_root=self.root,
                config_path=self.config,
                server_name="fixture",
            )

    def test_host_allowlist_can_filter_a_runtime_superset(self) -> None:
        self.config.write_text(
            self.config.read_text().replace(
                'enabled_tools = ["status", "search"]',
                'enabled_tools = ["status"]',
            ),
            encoding="utf-8",
        )
        report = MODULE.probe(
            repo_root=self.root,
            config_path=self.config,
            server_name="fixture",
            exact_surface=False,
        )
        self.assertEqual(report["configured_tools"], ["status"])


if __name__ == "__main__":
    unittest.main()
