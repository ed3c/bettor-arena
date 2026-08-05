#!/bin/sh
# Seam: host config files + rm_guard CLI exit codes. Both directions — the
# guard must block an escape (2) and pass an inside delete (0), or its green
# proves nothing.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
fail() { echo "FAIL: $1" >&2; exit 1; }

S="$ROOT/.claude/settings.json"
G="$ROOT/.claude/hooks/rm_guard.py"
C="$ROOT/.codex/config.toml"

[ -f "$S" ] || fail ".claude/settings.json missing"
python3 -m json.tool "$S" >/dev/null || fail "settings.json is not valid JSON"
grep -q 'CLAUDE_PROJECT_DIR' "$S" || fail "hook command must use \$CLAUDE_PROJECT_DIR"
grep -q 'rm_guard\.py' "$S" || fail "settings.json does not register rm_guard"
python3 - "$S" <<'EOF' || fail "no PreToolUse Bash hook registered"
import json, sys
cfg = json.load(open(sys.argv[1]))
hooks = cfg["hooks"]["PreToolUse"]
assert any(h.get("matcher") == "Bash" for h in hooks)
EOF

[ -f "$G" ] || fail "rm_guard.py missing"
python3 "$G" --selftest >/dev/null || fail "rm_guard --selftest RED"

# Hook seam: outside delete blocks (2), inside delete passes (0).
payload() { printf '{"tool_name":"Bash","cwd":"%s","tool_input":{"command":"%s"}}' "$ROOT" "$1"; }
set +e
payload "rm ../escape.txt" | python3 "$G"; RC=$?
set -e
[ "$RC" -eq 2 ] || fail "outside rm exited $RC, want block 2"
payload "rm inside.txt" | python3 "$G" || fail "inside rm blocked; guard cries wolf"

[ -f "$C" ] || fail ".codex/config.toml missing"
python3 - "$C" <<'EOF' || fail ".codex/config.toml invalid or missing MCP servers"
import sys, tomllib
cfg = tomllib.load(open(sys.argv[1], "rb"))
assert {"grepai", "repo-context-pack", "serena"} <= set(cfg["mcp_servers"])
EOF
grep -qi 'host' "$C" || fail "config.toml lacks the host-section-pending comment"

# bootstrap must end by telling the human how to approve MCP, never approving.
OUT=$(sh "$ROOT/bootstrap.sh") || fail "bootstrap exited $?"
echo "$OUT" | grep -qi 'MCP' || fail "bootstrap prints no MCP approval guidance"

echo "PASS: host config contract holds"
