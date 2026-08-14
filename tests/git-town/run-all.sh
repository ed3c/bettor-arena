#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
PYTHON=${PYTHON:-python3}
GT="$ROOT/scripts/git-town"

"$PYTHON" "$GT/gittownctl.py" check --root "$ROOT"
"$PYTHON" "$GT/gittownctl.py" selftest --root "$ROOT"
"$PYTHON" "$GT/control_git_town.py"

TMP=$(mktemp -d)
cleanup() { chmod -R u+w "$TMP" 2>/dev/null || true; find "$TMP" -mindepth 1 -delete 2>/dev/null || true; rmdir "$TMP" 2>/dev/null || true; }
trap cleanup EXIT

# The executable is not installed. That is 70 -- the provider is unavailable --
# and it is neither 0 nor 2: nothing ran, so nothing disagreed and nothing passed.
set +e
"$PYTHON" "$GT/gittownctl.py" probe --root "$ROOT" --output "$TMP/probe.json" >/dev/null 2>&1
rc=$?
set -e
test "$rc" = "70" || { echo "an absent executable exited $rc, expected 70" >&2; exit 2; }
echo "git-town-runtime port PASS: an absent executable exits 70, not 0 and not 2"

# There is no subcommand that runs a sync, continues, skips, undoes or ships.
for forbidden in sync continue skip undo ship push merge; do
  set +e
  "$PYTHON" "$GT/gittownctl.py" "$forbidden" >/dev/null 2>&1
  rc=$?
  set -e
  test "$rc" = "64" || {
    echo "the port answered '$forbidden' with exit $rc, expected 64" >&2; exit 2; }
done
echo "git-town-runtime port PASS: no sync/continue/skip/undo/ship/push/merge route exists"

"$PYTHON" - "$TMP/probe.json" "$GT" <<'PY'
import json, sys
from pathlib import Path

sys.path.insert(0, sys.argv[2])
from gt_admit import admit, modes_for
from gt_common import MODES
from gt_publish import publication_decision, require_separate_operation
from gt_selftest import ADMISSION, PROFILE

found = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if found["state"] != "EXECUTABLE_ABSENT":
    raise SystemExit(
        f"the probe reports {found['state']}; the checked-in receipts say "
        "EXECUTABLE_ABSENT and would be describing a different machine"
    )

result = admit(found, ADMISSION, PROFILE, live_local_reviewed=True)
if result["state"] != "EXECUTABLE_ABSENT" or result["modes_available"]:
    raise SystemExit("an absent executable was admitted, or unlocked a mode")
if not result["publication_is_separate_gate"] or not result["human_admit_required"]:
    raise SystemExit("the admission dropped a gate")

sync = MODES["sync_local_no_push"]
for flag in ("--stack", "--non-interactive", "--no-auto-resolve", "--no-push"):
    if flag not in sync:
        raise SystemExit(f"the non-negotiable command shape lost {flag}")
for flag in ("--continue", "--skip", "--undo", "--push", "--force", "--ship"):
    if flag in sync:
        raise SystemExit(f"the sync argv carries {flag}")

decision = publication_decision(
    admit(
        {**found, "state": "EXECUTABLE_PRESENT_NOT_ADMITTED", "reported_version": "git-town 21.1.0"},
        ADMISSION,
        PROFILE,
        True,
    ),
    "a" * 40,
    "a" * 40,
)
require_separate_operation(decision)
if decision["performed"]:
    raise SystemExit("a publication decision performed a publication")
if sorted(decision["receipt_kinds"]) != ["HUMAN_ADMIT", "LOCAL_SYNC", "LOCAL_VERIFICATION", "PUBLICATION"]:
    raise SystemExit("the receipt kinds were folded together")

print(
    f"git-town-runtime documents PASS: {found['state']}, "
    f"{len(modes_for('EXECUTABLE_ABSENT'))} modes available, "
    f"{len(decision['receipt_kinds'])} separate receipt kinds"
)
PY

"$PYTHON" -m py_compile \
  "$GT/gt_common.py" \
  "$GT/gt_admit.py" \
  "$GT/gt_invariants.py" \
  "$GT/gt_fixture.py" \
  "$GT/gt_publish.py" \
  "$GT/gt_contract.py" \
  "$GT/gt_selftest.py" \
  "$GT/gittownctl.py" \
  "$GT/control_git_town.py"

"$PYTHON" - "$ROOT" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
paths = sorted((root / ".github-delivery/git-town").glob("*.json"))
if not paths:
    raise SystemExit("no git-town JSON contracts found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"git-town-runtime JSON PASS: {len(paths)} files")
PY
