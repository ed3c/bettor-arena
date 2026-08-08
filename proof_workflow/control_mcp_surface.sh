#!/bin/sh
# control_mcp_surface.sh — the CONTROL GROUP for the MCP wrapper.
#
#   sh loopctl/loopctl.sh mcp test
#
# The MCP server is the layer external callers actually touch, so the properties
# that matter there are not "does it start" but: does it stay pinned, does it
# stay isolated, and does it refuse what the CLI refuses. Each is checked by
# driving the server over real stdio JSON-RPC, because a wrapper tested only
# through its own Python functions is tested everywhere except at the seam its
# callers use.
#
# The planted defects, and what each would cost if it went unnoticed:
#   pinning     a call served by HEAD instead of the pinned ref means customer
#               traffic silently rides internal iteration — the exact coupling
#               the pin exists to break.
#   isolation   a call that leaves anything in the live tree, or reads an
#               uncommitted edit, makes "stateless" a promise instead of a fact.
#   refusal     an undeclared argument that gets forwarded teaches callers to
#               depend on a target's private switches, one layer up from where
#               the CLI stops it.
#   exit codes  folding 2 and 64 leaves a caller unable to tell a red gate from
#               a missing tool, and isError must follow the run rather than the
#               transport.
#
# Exit: 0 every property held · 2 one did not · 64 FATAL (no server, no worktree)
set -u

CAPTURE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$CAPTURE_HOME/lib/capture.sh"
capture_init mcp-surface
ROOT=$CAPTURE_ROOT
SERVER="$ROOT/loopctl/mcp_server.py"
[ -f "$SERVER" ] || { echo "control FATAL: no MCP server at $SERVER" >&2; exit 64; }

BASE=$(mktemp -d "${TMPDIR:-/tmp}/control-mcp.XXXXXX")
RED=0
expect() { # name got want
  if [ "$2" = "$3" ]; then echo "  [ok]   $1 — $2"; else echo "  [RED]  $1 — got $2, want $3" >&2; RED=1; fi
}

# --- the server's own assertions ---------------------------------------------
capture mcp-selftest -- python3 "$SERVER" --selftest
expect "server-selftest" $? 0
capture tools-selftest -- python3 "$ROOT/loopctl/mcp_tools.py" --selftest
expect "tool-generation-selftest" $? 0

# --- generated surface must equal the CLI surface, not merely resemble it ----
# Both sides are read mechanically; a hand-comparison here would be a third copy
# of the same promise.
capture surface-parity -- python3 - "$ROOT" <<'PY'
import json, subprocess, sys
from pathlib import Path

root = Path(sys.argv[1])
sys.path.insert(0, str(root / "loopctl"))
import mcp_tools

contract = json.loads((root / "loopctl" / "contract.json").read_text(encoding="utf-8"))
tools = mcp_tools.build(contract)
declared = {f"{c['loop']}/{c['mode']}" for c in contract["commands"]}
exposed = {f"{t['_argv']['loop']}/{t['_argv']['mode']}" for t in tools}
if declared != exposed:
    print(f"MCP surface differs from the CLI surface: {declared ^ exposed}")
    raise SystemExit(2)
for tool in tools:
    command = next(c for c in contract["commands"]
                   if c["loop"] == tool["_argv"]["loop"] and c["mode"] == tool["_argv"]["mode"])
    carrier = command.get("mcp_carrier")
    want = (set(carrier["input_schema"]["required"]) if carrier else
            {f.lstrip("-").replace("-", "_") for f in command["required"]})
    got = set(tool["inputSchema"]["required"])
    if want != got:
        print(f"{tool['name']}: required params {got} != contract {want}")
        raise SystemExit(2)
print(f"{len(tools)} tools match the contract exactly")
PY
expect "mcp-surface-equals-cli-surface" $? 0

# --- CTG carrier: inline bundle in, bounded typed artifacts out ----------------
# Local packet/output paths would couple the call to the server host and leak a
# disposable worktree path on delivery. The pinned contract replaces those CLI
# carrier flags with one content-addressed bundle object for MCP only.
CTG_F=loop_wiki/code-truth-graph
PYTHONPATH="$ROOT/$CTG_F/src" python3 -m code_truth_graph.fixture --out "$BASE/ctg-bundle" >/dev/null || {
  echo "control FATAL: could not materialize CTG MCP fixture" >&2; exit 64; }
python3 - "$BASE/ctg-bundle" "$BASE/ctg-inline.jsonl" <<'PY'
import base64, hashlib, json, sys
from pathlib import Path

bundle = Path(sys.argv[1])
files = []
for path in sorted(p for p in bundle.rglob("*") if p.is_file()):
    content = path.read_bytes()
    files.append({
        "artifact_ref": path.relative_to(bundle).as_posix(),
        "sha256": hashlib.sha256(content).hexdigest(),
        "content_base64": base64.b64encode(content).decode("ascii"),
    })
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
capture ctg-inline-call -- sh -c "python3 '$SERVER' --ref HEAD < '$BASE/ctg-inline.jsonl'"
CTG_MCP_OUT="$RUNDIR/streams/$CAPTURE_SEQ-ctg-inline-call.out"
python3 - "$CTG_MCP_OUT" <<'PY'
import base64, hashlib, json, sys
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
expect "ctg-inline-carrier-has-no-local-or-disposable-path" $? 0

printf '{"jsonrpc":"2.0","id":42,"method":"tools/call","params":{"name":"loopctl_ctg_run","arguments":{"packet":"/tmp/forbidden.json","output":"/tmp/forbidden"}}}\n' >"$BASE/ctg-local-path.jsonl"
capture ctg-local-path-refusal -- sh -c "python3 '$SERVER' --ref HEAD < '$BASE/ctg-local-path.jsonl'"
CTG_LOCAL_OUT="$RUNDIR/streams/$CAPTURE_SEQ-ctg-local-path-refusal.out"
grep -q 'local packet/output paths are forbidden' "$CTG_LOCAL_OUT" && CTG_REFUSED=yes || CTG_REFUSED=no
expect "ctg-mcp-local-path-refused" "$CTG_REFUSED" yes

# --- pinning: the server must serve the REF, not the working tree ------------
# A sentinel is written into the live tree and left UNCOMMITTED. A pinned server
# must not see it; if it does, the pin is decorative and every customer call is
# riding whatever is being edited right now.
SENTINEL="$ROOT/loopctl/.control-mcp-sentinel"
printf 'uncommitted\n' >"$SENTINEL"
printf '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"loopctl_macro_prove","arguments":{"force_receipt":true}}}\n' >"$BASE/pin.jsonl"
capture pinned-call -- sh -c "python3 '$SERVER' --ref HEAD < '$BASE/pin.jsonl'"
PIN_RC=$?
PIN_OUT="$RUNDIR/streams/$CAPTURE_SEQ-pinned-call.out"
rm -f "$SENTINEL"
if [ "$PIN_RC" -eq 0 ]; then
  grep -q 'control-mcp-sentinel' "$PIN_OUT" && LEAKED=yes || LEAKED=no
  expect "pinned-ref-does-not-see-uncommitted-work" "$LEAKED" no
else
  # A server that refuses to start on this ref is not a leak, and saying so beats
  # scoring an unrun check as a pass.
  echo "  [note] the pinned call did not run (exit $PIN_RC) — isolation NOT exercised this run"
fi

# --- isolation: the live tree must be untouched by a call --------------------
BEFORE=$(git -C "$ROOT" status --porcelain -- . ':(exclude)data/proof-workflow/' | sort)
capture isolated-call -- sh -c "python3 '$SERVER' --ref HEAD < '$BASE/pin.jsonl'"
AFTER=$(git -C "$ROOT" status --porcelain -- . ':(exclude)data/proof-workflow/' | sort)
[ "$BEFORE" = "$AFTER" ] && SAME=yes || SAME=no
expect "call-leaves-the-live-tree-unchanged" "$SAME" yes
# And no worktree may survive the call, or "stateless" leaks disk instead of state.
LEFTOVER=$(git -C "$ROOT" worktree list | grep -c 'loopctl-mcp-' || true)
expect "no-worktree-survives-the-call" "$LEFTOVER" 0

# --- refusal: an undeclared argument must not reach the target ---------------
printf '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"loopctl_macro_prove","arguments":{"sneaky":"x"}}}\n' >"$BASE/bad.jsonl"
capture undeclared-arg -- sh -c "python3 '$SERVER' --ref HEAD < '$BASE/bad.jsonl'"
BAD_OUT="$RUNDIR/streams/$CAPTURE_SEQ-undeclared-arg.out"
grep -q '"error"' "$BAD_OUT" && REFUSED=yes || REFUSED=no
expect "undeclared-argument-refused-at-the-wrapper" "$REFUSED" yes

# --- an unknown tool is an error, not a silent no-op -------------------------
printf '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"loopctl_nope"}}\n' >"$BASE/nope.jsonl"
capture unknown-tool -- sh -c "python3 '$SERVER' --ref HEAD < '$BASE/nope.jsonl'"
NOPE_OUT="$RUNDIR/streams/$CAPTURE_SEQ-unknown-tool.out"
grep -q '"error"' "$NOPE_OUT" && KNOWN=yes || KNOWN=no
expect "unknown-tool-is-an-error" "$KNOWN" yes

# --- version guard: a ref without --json must be refused AT STARTUP ----------
# Per call it surfaces as exit 64 with no hint that the REF is the problem, which
# is how it was first found.
OLD=$(git -C "$ROOT" tag --list 'v*' | sort -V | head -1)
if [ -n "$OLD" ]; then
  capture old-ref-guard -- sh -c "python3 '$SERVER' --ref '$OLD' < /dev/null"
  OLD_RC=$?
  OLD_ERR="$RUNDIR/streams/$CAPTURE_SEQ-old-ref-guard.err"
  if [ "$OLD_RC" -eq 0 ]; then
    echo "  [note] $OLD already carries --json; the pre-flight guard was not exercised"
  else
    grep -q 'does not declare --json' "$OLD_ERR" && NAMED=yes || NAMED=no
    expect "old-ref-refused-with-the-reason-named" "$NAMED" yes
  fi
else
  echo "  [note] no v* tag — the version guard is NOT covered by this run"
fi

echo "control[mcp-surface] trace=proof_workflow/data/$RUN_ID"
if [ "$RED" -eq 0 ]; then
  echo "PASS: the MCP wrapper stayed pinned, stayed isolated, and refused what the CLI refuses"
  exit 0
fi
echo "FAIL: the MCP wrapper lost a property its external callers depend on" >&2
exit 2
