#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
PYTHON=${PYTHON:-python3}
GATE="$ROOT/scripts/gates/ci_parity"

"$PYTHON" "$GATE/ci_parity.py" check --root "$ROOT"
"$PYTHON" "$GATE/ci_parity.py" selftest --root "$ROOT"
"$PYTHON" "$GATE/control_ci_parity.py"

TMP=$(mktemp -d)
cleanup() { chmod -R u+w "$TMP" 2>/dev/null || true; find "$TMP" -mindepth 1 -delete 2>/dev/null || true; rmdir "$TMP" 2>/dev/null || true; }
trap cleanup EXIT

HEAD=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
cat > "$TMP/local.json" <<EOF
{"workflow":"modular-contracts.yml","commit":"$HEAD","jobs":{"contracts":"PASS"},"runner":"local-native"}
EOF
cat > "$TMP/remote.json" <<EOF
{"workflow":"modular-contracts.yml","commit":"$HEAD","jobs":{"contracts":"success"},"run_id":1,"runner":"ubuntu-latest"}
EOF

"$PYTHON" "$GATE/ci_parity.py" compare --local "$TMP/local.json" --remote "$TMP/remote.json" \
  --head "$HEAD" --covers contracts --output "$TMP/parity.json" >/dev/null 2>&1
"$PYTHON" "$GATE/ci_parity.py" compare --local "$TMP/local.json" \
  --head "$HEAD" --covers contracts --output "$TMP/local-only.json" >/dev/null 2>&1

# An unknown subcommand is unusable input, not a refusal. 64, never 2.
set +e
"$PYTHON" "$GATE/ci_parity.py" declare-verified --pr 1 >/dev/null 2>&1
rc=$?
set -e
test "$rc" = "64" || { echo "an unknown subcommand exited $rc, expected 64" >&2; exit 2; }
echo "ci-parity port PASS: unusable input exits 64, not 0 and not 2"

"$PYTHON" - "$TMP/parity.json" "$TMP/local-only.json" <<'PY'
import json, sys
from pathlib import Path

both, local_only = (json.loads(Path(p).read_text(encoding="utf-8")) for p in sys.argv[1:3])

if both["verdict"] != "PARITY":
    raise SystemExit(f"two agreeing sides produced {both['verdict']}")
if local_only["verdict"] != "NOT_EXERCISED":
    raise SystemExit(
        f"a local run with no GitHub run produced {local_only['verdict']}; a local "
        "green with nothing to compare against is not a verified head"
    )
for receipt in (both, local_only):
    if receipt["local_proxies_remote"] is not False:
        raise SystemExit("a receipt claimed the local run proxies the remote")
    if "BILLING" not in receipt["github_only_surfaces"]:
        raise SystemExit("a receipt dropped a GitHub-only surface")
if local_only["publication"]["may_claim_remote_verified"]:
    raise SystemExit("a NOT_EXERCISED verdict permitted a remote-verified claim")
if local_only["publication"]["owner"] != "HUMAN_OR_TRUSTED_OPERATOR":
    raise SystemExit("publication ownership drifted out of the receipt")
print(
    f"ci-parity documents PASS: {both['verdict']} with both sides, "
    f"{local_only['verdict']} with one"
)
PY

"$PYTHON" -m py_compile \
  "$GATE/cp_common.py" \
  "$GATE/cp_index.py" \
  "$GATE/cp_parity.py" \
  "$GATE/cp_policy.py" \
  "$GATE/cp_simulator.py" \
  "$GATE/cp_contract.py" \
  "$GATE/cp_selftest.py" \
  "$GATE/ci_parity.py" \
  "$GATE/control_ci_parity.py"

"$PYTHON" - "$ROOT" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
paths = sorted((root / ".github-delivery/ci-parity").glob("*.json")) + sorted(
    (root / "data/ci-parity").glob("*.json")
)
if not paths:
    raise SystemExit("no ci-parity JSON contracts found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"ci-parity JSON PASS: {len(paths)} files")
PY
