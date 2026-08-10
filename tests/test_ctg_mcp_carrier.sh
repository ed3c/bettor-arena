#!/bin/sh
# Focused public-seam test for the CTG MCP carrier.
set -u

ROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel) || exit 64
SERVER="$ROOT/loopctl/mcp_server.py"
REF=${CTG_MCP_REF:-$(git -C "$ROOT" rev-parse HEAD)}
TMP=$(mktemp -d "${TMPDIR:-/tmp}/bettor-ctg-mcp.XXXXXX") || exit 64
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

[ -f "$SERVER" ] || {
  echo "CTG MCP TEST FATAL: missing server $SERVER" >&2
  exit 64
}

F=loop_wiki/code-truth-graph
PYTHONPATH="$ROOT/$F/src" python3 -m code_truth_graph.fixture \
  --out "$TMP/bundle" >/dev/null || exit 64

python3 - "$TMP/bundle" "$TMP/request.jsonl" <<'PY' || exit 64
import base64
import hashlib
import json
import sys
from pathlib import Path

bundle = Path(sys.argv[1])
files = []
for path in sorted(item for item in bundle.rglob("*") if item.is_file()):
    content = path.read_bytes()
    files.append(
        {
            "artifact_ref": path.relative_to(bundle).as_posix(),
            "sha256": hashlib.sha256(content).hexdigest(),
            "content_base64": base64.b64encode(content).decode("ascii"),
        }
    )
request = {
    "jsonrpc": "2.0",
    "id": 41,
    "method": "tools/call",
    "params": {
        "name": "loopctl_ctg_run",
        "arguments": {"bundle": {"packet_ref": "ctg-input.json", "files": files}},
    },
}
Path(sys.argv[2]).write_text(json.dumps(request) + "\n", encoding="utf-8")
PY

python3 "$SERVER" --ref "$REF" \
  <"$TMP/request.jsonl" >"$TMP/response.jsonl" 2>"$TMP/server.err" || {
  cat "$TMP/server.err" >&2
  exit 2
}
python3 - "$TMP/response.jsonl" <<'PY' || exit 2
import base64
import hashlib
import json
import sys
from pathlib import Path

response = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
result = response["result"]
assert result["isError"] is False, response
payload = json.loads(result["content"][0]["text"])
delivery = payload["ctg_delivery"]
assert delivery["route_result"]["overall"]["exit"] == 0, payload
assert payload["artifacts"] == [], payload
assert "loopctl-mcp-" not in json.dumps(payload), payload
assert delivery["artifacts"], payload
for item in delivery["artifacts"]:
    content = base64.b64decode(item["content_base64"], validate=True)
    assert hashlib.sha256(content).hexdigest() == item["sha256"], item
    assert "artifact_ref" not in item, item
PY

printf '%s\n' '{"jsonrpc":"2.0","id":42,"method":"tools/call","params":{"name":"loopctl_ctg_run","arguments":{"packet":"/tmp/forbidden.json","output":"/tmp/forbidden"}}}' \
  >"$TMP/local-path.jsonl"
python3 "$SERVER" --ref "$REF" \
  <"$TMP/local-path.jsonl" >"$TMP/local-path-response.jsonl" 2>"$TMP/local-path.err" || exit 2
grep -q 'local packet/output paths are forbidden' "$TMP/local-path-response.jsonl" || {
  echo "CTG MCP TEST failed — local packet/output path carrier was not refused" >&2
  exit 2
}

python3 - "$TMP/request.jsonl" "$TMP/bad-digest.jsonl" <<'PY' || exit 64
import json
import sys
from pathlib import Path

request = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
request["id"] = 43
request["params"]["arguments"]["bundle"]["files"][0]["sha256"] = "0" * 64
Path(sys.argv[2]).write_text(json.dumps(request) + "\n", encoding="utf-8")
PY
python3 "$SERVER" --ref "$REF" \
  <"$TMP/bad-digest.jsonl" >"$TMP/bad-digest-response.jsonl" 2>"$TMP/bad-digest.err" || exit 2
grep -q 'inline artifact digest mismatch' "$TMP/bad-digest-response.jsonl" || {
  echo "CTG MCP TEST failed — tampered inline artifact digest was not refused" >&2
  exit 2
}

if sh "$ROOT/loopctl/loopctl.sh" mcp tools | rg -q 'loopctl_ctg_build_local'; then
  echo "CTG MCP TEST failed — trusted-local ingress escaped into MCP" >&2
  exit 2
fi

echo "CTG MCP CARRIER TEST GREEN"
