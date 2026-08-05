#!/bin/sh
# Seam: MCP surface files + production engine CLI + bootstrap doctor probes.
# Every green here has its red: the engine-hash check is driven to failure on
# a tampered profile, and the doctor WARNs are driven to fire and to clear.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
fail() { echo "FAIL: $1" >&2; exit 1; }

# --- .mcp.json: valid JSON declaring the three portable servers -------------
[ -f "$ROOT/.mcp.json" ] || fail ".mcp.json missing"
python3 - "$ROOT/.mcp.json" <<'EOF' || fail ".mcp.json invalid or missing servers"
import json, sys
cfg = json.load(open(sys.argv[1]))
assert {"grepai", "repo-context-pack", "serena"} <= set(cfg["mcpServers"])
EOF

# --- production engine: --help runs, profile binds to THIS repo -------------
ENGINE="$ROOT/mcp/production/migrate.py"
PROFILE="$ROOT/mcp/production/profile.json"
[ -f "$ENGINE" ] || fail "mcp/production/migrate.py missing"
python3 "$ENGINE" --help >/dev/null || fail "engine --help exited $?"
python3 - "$PROFILE" "$ENGINE" <<'EOF' || fail "profile does not bind to bettor-arena"
import hashlib, json, sys
p = json.load(open(sys.argv[1]))
assert p["repo_id"] == "bettor-arena", p["repo_id"]
assert p["engine_sha256"] == hashlib.sha256(open(sys.argv[2], "rb").read()).hexdigest()
paths = {m["path"] for m in p["managed_files"]}
assert {".mcp.json", ".codex/config.toml"} <= paths, paths
EOF
python3 "$ENGINE" --repo-root "$ROOT" --profile mcp/production/profile.json plan \
  >/dev/null || fail "engine plan RED against real repo"

# Negative control: a tampered engine hash must be refused, loudly.
mkdir -p "$TMP/badprofile"
python3 - "$PROFILE" "$TMP/badprofile/profile.json" <<'EOF'
import json, sys
p = json.load(open(sys.argv[1]))
p["engine_sha256"] = "0" * 64
json.dump(p, open(sys.argv[2], "w"))
EOF
cp "$TMP/badprofile/profile.json" "$ROOT/mcp/production/profile.tampered.json"
set +e
python3 "$ENGINE" --repo-root "$ROOT" --profile mcp/production/profile.tampered.json plan 2>/dev/null
RC=$?
set -e
rm -f "$ROOT/mcp/production/profile.tampered.json"
[ "$RC" -ne 0 ] || fail "engine accepted a tampered engine_sha256"

# --- context-pack: locked env, real unit tests (uv is opt-in toolchain) -----
if command -v uv >/dev/null 2>&1; then
  (cd "$ROOT" && uv run --project mcp/context-pack --frozen \
      python -m unittest discover -s mcp/context-pack/tests -p 'test_*.py') \
    >/dev/null 2>&1 || fail "context-pack unit tests RED under frozen uv env"
else
  echo "WARN: uv absent, context-pack tests skipped (MCP is opt-in)" >&2
fi

# --- bootstrap doctor probes: WARNs fire when absent, clear when present ----
cp -R "$ROOT/scripts" "$TMP/scripts"
cp -R "$ROOT/.githooks" "$TMP/.githooks" 2>/dev/null || mkdir "$TMP/.githooks"
cp "$ROOT/bootstrap.sh" "$TMP/bootstrap.sh"
git -C "$TMP" init -q -b main

OUT=$(sh "$TMP/bootstrap.sh" 2>&1) || fail "bootstrap exited $? on probe copy"
echo "$OUT" | grep -q 'grepai index absent' || fail "missing grepai index raised no WARN"
echo "$OUT" | grep -qi 'ollama' || fail "ollama probe left no trace in output"

mkdir -p "$TMP/.grepai" && touch "$TMP/.grepai/index.gob"
OUT=$(sh "$TMP/bootstrap.sh" 2>&1) || fail "bootstrap not idempotent with index present"
echo "$OUT" | grep -q 'grepai index absent' && fail "grepai WARN fires even with an index"

# uv WARN must fire when uv is off PATH (bun kept so FATALs stay quiet).
mkdir "$TMP/bin"
ln -s "$(command -v bun)" "$TMP/bin/bun"
OUT=$(env PATH="$TMP/bin:/usr/bin:/bin" sh "$TMP/bootstrap.sh" 2>&1) \
  || fail "bootstrap FATALed on missing uv; uv must be WARN only"
echo "$OUT" | grep -q 'WARN.*uv' || fail "missing uv raised no WARN"

echo "PASS: MCP surface contract holds"
