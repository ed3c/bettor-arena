#!/bin/sh
# control_harness_coverage.sh — is the instrument itself measured?
#
#   sh loopctl/loopctl.sh harness test
#
# The check that would have caught the gap it was written for. Every tracked file
# under proof_workflow/ must be hashed by some proof at this commit, or declared
# out of scope by name. Until this existed, eleven of seventeen were covered by
# nothing: editing lib/prove.sh moved no digest, and the lineage hook — which
# reads the manifest built FROM these receipts — stayed silent about a change to
# the thing that computes every digest in the repo.
#
# The distinction this enforces is the one that was conflated: the CLI's pairing
# check asks whether a mechanism DECLARES both halves, which is a fact about
# contract.json. This asks whether the harness's own bytes are COVERED, which is
# a fact about the receipts. A mechanism can declare both and still hash none of
# its own files.
#
# Self-coverage is legitimate and is not the workflow.lock cycle: a script's own
# bytes do not move when the digest moves, so a proof hashing itself settles on
# the first pass. workflow.lock is derived FROM the digest, which is why it is
# excluded by name instead.
#
# Exit: 0 every file covered or declared · 2 something uncovered · 64 FATAL
set -u

CAPTURE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$CAPTURE_HOME/lib/capture.sh"
capture_init harness-coverage
ROOT=$CAPTURE_ROOT

RED=0
expect() { # name got want
  if [ "$2" = "$3" ]; then echo "  [ok]   $1 — $2"; else echo "  [RED]  $1 — got $2, want $3" >&2; RED=1; fi
}

capture coverage-scan -- python3 "$CAPTURE_HOME/lib/harness_coverage.py" "$ROOT"
SCAN_RC=$?
SCAN_OUT="$RUNDIR/streams/$CAPTURE_SEQ-coverage-scan.out"
sed 's/^/  /' "$SCAN_OUT"
expect "every-harness-file-is-covered-or-declared" "$SCAN_RC" 0

# --- planted defect: a new uncovered file must be caught ---------------------
# Without this the scan could be passing because it finds nothing rather than
# because everything is covered — the empty-set failure this repo has hit twice.
PLANT="$ROOT/proof_workflow/.control-uncovered-probe.sh"
printf '#!/bin/sh\n# planted by control_harness_coverage.sh\nexit 0\n' >"$PLANT"
git -C "$ROOT" add -f "$PLANT" >/dev/null 2>&1
capture coverage-scan-with-plant -- python3 "$CAPTURE_HOME/lib/harness_coverage.py" "$ROOT"
PLANT_RC=$?
git -C "$ROOT" rm -q --cached "$PLANT" >/dev/null 2>&1
mv "$PLANT" "$RUNDIR/planted-probe.sh"
expect "an-uncovered-file-is-caught" "$PLANT_RC" 2

echo "control[harness-coverage] trace=proof_workflow/data/$RUN_ID"
if [ "$RED" -eq 0 ]; then
  echo "PASS: the instrument is measured, and the scan is demonstrably able to say otherwise"
  exit 0
fi
echo "FAIL: part of the proof machinery is hashed by nothing — a change to it would move no digest" >&2
exit 2
