#!/bin/sh
# Public seam: runtime-env must expose the technical-equivalence actor ×
# browser-transport contract without pretending unlike execution planes are
# interchangeable.
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
MATRIX="$ROOT/loop_wiki/evolve-technical-equivalence-research/carrier-capabilities.json"
CHECK="$ROOT/scripts/runtime-env/check-carrier-contract.py"

python3 "$CHECK" --matrix "$MATRIX" --selftest
python3 "$CHECK" --matrix "$MATRIX"

python3 -c '
import json, sys
value = json.load(open(sys.argv[1], encoding="utf-8"))
assert value["schema_version"] == "technical-equivalence-carrier-capabilities@1.0.0"

actors = value["actors"]
assert actors["claude-code"]["kind"] == "agent-actor"
assert actors["codex-cli"]["native_browser"] is False
assert actors["agy"]["capabilities"] == ["independent-replay"]

transports = value["browser_transports"]
assert transports["chatgpt-chrome-extension"]["host"] == "chatgpt-desktop-app"
assert transports["playwright-cdp"]["engine"] == "playwright"
assert transports["stealth-browser-playwright"]["engine"] == "playwright"
assert transports["antigravity-puppeteer-cdp"]["engine"] == "puppeteer-core"

cases = {item["id"]: item for item in value["acceptance_cases"]}
assert cases["codex-cli--chatgpt-chrome-extension"]["status"] == "unsupported"
assert cases["codex-cli--playwright-cdp"]["status"] == "supported"
assert cases["claude-code--claude-in-chrome"]["status"] == "supported"
assert cases["agy--gemini-dr-browser"]["status"] == "unsupported"
' "$MATRIX"

echo "PASS: technical-equivalence carrier matrix is typed and fail-closed"
