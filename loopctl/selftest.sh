#!/bin/sh
# selftest.sh — loopctl's cheap verification surface, sourced by `loopctl.sh --selftest`.
#
# Split out because loopctl.sh dispatches on its own argv, and a selftest that
# lived inside it would have to run every case as a subprocess of the file it is
# testing while that file is mid-parse. Kept here it is plain assertions.
#
# What it holds down, in order of what actually goes wrong:
#   1. surface and wiring name the same commands, in BOTH directions — the
#      failure this CLI exists to prevent is a command that exists on one side
#      only, which shows up as a caller reaching past the CLI.
#   2. every declared target file is really there.
#   3. usage violations are refused, not forwarded: unknown loop, unknown mode,
#      missing required flag, and — the one that matters — an undeclared flag,
#      because forwarding those is how a caller starts depending on a target's
#      private switches.
#   4. exit codes pass through unchanged, checked against the target run
#      directly rather than against a number written here.
#
# Every derivation below is asserted non-empty before it is compared. The first
# version of this file printed GREEN while two of its own checks had died on a
# syntax error inside command substitution: an extraction that fails silently
# yields an empty set, and an empty set compares equal to anything. A check that
# did not run must never read as a check that passed.

loopctl_selftest() {
  _red=0
  _tmp=$(mktemp -d "${TMPDIR:-/tmp}/loopctl-selftest.XXXXXX")
  _case() { # name got want
    [ "$3" = "$2" ] || { echo "SELFTEST case failed — $1: got $2, want $3" >&2; _red=1; }
  }
  _nonempty() { # name file
    [ -s "$2" ] || { echo "SELFTEST case failed — $1 produced nothing; the check did not run" >&2; _red=1; return 1; }
    return 0
  }
  _root=$(git -C "$HERE" rev-parse --show-toplevel)
  _cli="$HERE/loopctl.sh"

  python3 - "$CONTRACT" "$_tmp" <<'PY' || { echo "SELFTEST: contract is unreadable" >&2; _red=1; }
import json, sys
from pathlib import Path

contract = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = Path(sys.argv[2])
cmds = contract["commands"]
(out / "declared.txt").write_text(
    "".join(sorted(f"{c['loop']}/{c['mode']}\n" for c in cmds)), encoding="utf-8"
)
(out / "targets.txt").write_text(
    "".join(sorted({c["target"] + "\n" for c in cmds})), encoding="utf-8"
)
PY

  # 1. surface <-> wiring, both directions.
  # grep -oE, not sed: BSD sed has no \| alternation, so the sed form silently
  # matched nothing on macOS — which is how the first version of this file
  # reported GREEN with this very check dead.
  # Two dispatch shapes, both extracted: the loops go through `case $LOOP/$MODE`,
  # while workflow's subcommands sit in their own nested case. Extracting only the
  # first shape made a declared command look unwired and sent the fix at the
  # contract instead of at the extraction.
  {
    grep -oE '^  (macro|micro|openwiki)/(run|prove|test)\)' "$_cli" | tr -d ' )'
    # The nested subcommands are listed, not extracted. Their labels repeat
    # across branches — `test)` under four of them, `prove)` under two — and a
    # shape-based grep cannot say which branch a label belongs to: it prefixed
    # policy's `prove)` as container/prove and reported a declared command as
    # wired-twice. Listing them keeps this check honest about what it can see,
    # and the target-exists check below still catches a name with no script.
    printf '%s\n' \
      workflow/lock workflow/trailer workflow/replay workflow/test workflow/prove \
      mcp/serve mcp/tools mcp/test mcp/prove \
      container/build container/preflight container/prove container/test \
      policy/prove policy/test
  } | sort >"$_tmp/wired.txt"
  if _nonempty "declared-commands" "$_tmp/declared.txt" && _nonempty "wired-commands" "$_tmp/wired.txt"; then
    _only_contract=$(comm -23 "$_tmp/declared.txt" "$_tmp/wired.txt")
    _only_wired=$(comm -13 "$_tmp/declared.txt" "$_tmp/wired.txt")
    [ -z "$_only_contract" ] || { echo "SELFTEST case failed — declared but not wired: $_only_contract" >&2; _red=1; }
    [ -z "$_only_wired" ] || { echo "SELFTEST case failed — wired but not declared: $_only_wired" >&2; _red=1; }
  fi

  # 2. every declared target exists.
  if _nonempty "declared-targets" "$_tmp/targets.txt"; then
    while IFS= read -r _t; do
      [ -f "$_root/$_t" ] || { echo "SELFTEST case failed — declared target missing: $_t" >&2; _red=1; }
    done <"$_tmp/targets.txt"
  fi

  # 3. usage violations are refused.
  sh "$_cli" nosuchloop run >/dev/null 2>&1; _case "unknown-loop" $? 64
  sh "$_cli" macro nosuchmode >/dev/null 2>&1; _case "unknown-mode" $? 64
  sh "$_cli" micro run --packet /dev/null >/dev/null 2>&1; _case "missing-required-flag" $? 64
  sh "$_cli" macro run --sneaky >/dev/null 2>&1; _case "undeclared-flag-refused" $? 64
  sh "$_cli" >/dev/null 2>&1; _case "no-args-is-usage" $? 64
  sh "$_cli" contract >/dev/null 2>&1; _case "contract-prints" $? 0
  sh "$_cli" contract 2>/dev/null | grep -q '^contract_sha256: [0-9a-f]\{64\}$' \
    || { echo "SELFTEST case failed — contract output carries no sha256" >&2; _red=1; }

  # 3b. every mechanism carries BOTH halves. A proof without a control records
  # which bytes a claim covered and never drives it; a control without a proof
  # shows a property holding and never says what it held for. Derived from the
  # contract rather than from a directory layout or a filename convention: the
  # names are not 1:1 (prove_macro_loop.sh pairs with control_macro_entry.sh,
  # prove_policy.sh with control_sandbox_policy.sh), so any file-based pairing
  # would need a second list to keep in sync — which is the failure this repo
  # keeps removing, not adding.
  python3 - "$CONTRACT" <<'PY'
import json, sys
from pathlib import Path

contract = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
modes = {}
for c in contract["commands"]:
    modes.setdefault(c["loop"], set()).add(c["mode"])
unpaired = []
for loop, have in sorted(modes.items()):
    if "prove" in have and "test" not in have:
        unpaired.append(f"{loop}: has prove, no test — a claim nobody drives")
    if "test" in have and "prove" not in have:
        unpaired.append(f"{loop}: has test, no prove — a green with no record of what it covered")
for line in unpaired:
    print(f"SELFTEST case failed — unpaired mechanism, {line}", file=sys.stderr)
raise SystemExit(1 if unpaired else 0)
PY
  _case "every-mechanism-has-both-halves" $? 0

  # 4. the external promise is where the lock says it is. Internal iteration does
  # not reach this check — target, writes and wiring are excluded from the digest
  # by construction — so a red here means the surface itself moved.
  python3 "$HERE/surface_digest.py" --selftest >/dev/null 2>&1
  _case "surface-digest-selftest" $? 0
  python3 "$HERE/surface_digest.py" check "$CONTRACT" "$HERE/surface.lock"
  _case "surface-matches-lock" $? 0

  # 5. exit-code pass-through, measured against the target rather than asserted.
  # An absent packet makes trigger.sh fail early and cheaply; whatever code it
  # chooses, loopctl must return the same one.
  _direct_rc=0
  sh "$_root/loop_wiki/evolve-perfect-seed-repo-factory/trigger.sh" \
     "$_tmp/absent-packet.json" "$_tmp/out" >/dev/null 2>&1 || _direct_rc=$?
  _via_rc=0
  sh "$_cli" micro run --packet "$_tmp/absent-packet.json" --output "$_tmp/out" >/dev/null 2>&1 || _via_rc=$?
  _case "exit-code-passthrough" "$_via_rc" "$_direct_rc"
  [ "$_direct_rc" -ne 0 ] || { echo "SELFTEST case failed — the pass-through probe did not fail, so it proves nothing" >&2; _red=1; }

  rm -rf "$_tmp"
  echo "SELFTEST $([ "$_red" = 0 ] && echo GREEN || echo RED)"
  return "$_red"
}
