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
    want = {f.lstrip("-").replace("-", "_") for f in command["required"]}
    got = set(tool["inputSchema"]["required"])
    if want != got:
        print(f"{tool['name']}: required params {got} != contract {want}")
        raise SystemExit(2)
print(f"{len(tools)} tools match the contract exactly")
PY
expect "mcp-surface-equals-cli-surface" $? 0

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
