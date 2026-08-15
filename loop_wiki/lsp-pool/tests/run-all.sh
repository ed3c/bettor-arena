#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}

"$PYTHON" "$ROOT/scripts/lsppool.py" check --root "$ROOT"
"$PYTHON" "$ROOT/scripts/lsppool.py" selftest --root "$ROOT"
"$PYTHON" "$ROOT/scripts/control_lsppool.py" --root "$ROOT" >/dev/null
echo "lsp-pool physical control PASS: 4 controls on real server processes"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# The three answers, through the real port, as three separate documents. Read
# from files rather than from one object so the states cannot be compared inside
# the interpreter that produced them.
"$PYTHON" "$ROOT/scripts/lsppool.py" query --root "$ROOT" --output "$TMP/normal.json" >/dev/null
"$PYTHON" "$ROOT/scripts/lsppool.py" query --root "$ROOT" --behaviour crash \
  --output "$TMP/crash.json" >/dev/null
"$PYTHON" "$ROOT/scripts/lsppool.py" query --root "$ROOT" --behaviour empty-on-fail \
  --output "$TMP/unindexed.json" >/dev/null
"$PYTHON" - "$TMP/normal.json" "$TMP/crash.json" "$TMP/unindexed.json" <<'PY'
import json, sys
from pathlib import Path
load = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
normal, crash, unindexed = (load(p) for p in sys.argv[1:4])
states = {
    "normal": normal["result"]["state"],
    "crash": crash["result"]["state"],
    "unindexed": unindexed["result"]["state"],
}
if states["normal"] != "FINDINGS":
    raise SystemExit(f"a TODO produced {states['normal']}")
if states["crash"] != "SERVER_FAILED":
    raise SystemExit(f"a crashed server produced {states['crash']}")
if states["unindexed"] != "UNKNOWN":
    raise SystemExit(f"an unindexed path produced {states['unindexed']}")
for name in ("crash", "unindexed"):
    doc = crash if name == "crash" else unindexed
    if doc["result"]["findings"]:
        raise SystemExit(f"the {name} result carries findings")
if normal["state_trace"][-1] != "SHUTDOWN_RESIDUE_CHECK":
    raise SystemExit(f"the query ended at {normal['state_trace'][-1]!r}")
print(
    f"lsp-pool port PASS: {len(normal['state_trace'])} states, "
    f"three empty-findings cases land in {sorted(set(states.values()))}"
)
PY

"$PYTHON" - "$ROOT" "$TMP/crash.json" <<'PY'
import json, subprocess, sys
from pathlib import Path
root, crash_path = sys.argv[1], sys.argv[2]
crash = json.loads(Path(crash_path).read_text(encoding="utf-8"))
result_file = Path(crash_path).with_name("result-only.json")
result_file.write_text(json.dumps(crash["result"]), encoding="utf-8")
out = subprocess.run(
    [sys.executable, f"{root}/scripts/lsppool.py", "to-graph", "--result", str(result_file)],
    capture_output=True, text=True, check=True,
)
graph = json.loads(out.stdout)
if graph["admitted"]:
    raise SystemExit("a crashed server's silence was admitted to the Code Truth Graph")
if graph["evidence"] != "NONE":
    raise SystemExit("a non-evidence state was handed over as evidence")
print("lsp-pool graph PASS: a SERVER_FAILED result is not admitted as evidence")
PY

"$PYTHON" -m py_compile \
  "$ROOT/scripts/lsp_common.py" \
  "$ROOT/scripts/lsp_pool.py" \
  "$ROOT/scripts/lsp_query.py" \
  "$ROOT/scripts/lsp_fallback.py" \
  "$ROOT/scripts/lsp_pipeline.py" \
  "$ROOT/scripts/lsp_contract.py" \
  "$ROOT/scripts/lsp_selftest.py" \
  "$ROOT/scripts/lsppool.py" \
  "$ROOT/scripts/control_lsppool.py" \
  "$ROOT/scripts/probe_controls.py" \
  "$ROOT/tests/fake_server.py"

"$PYTHON" - "$ROOT" <<'PY'
from __future__ import annotations
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
paths = sorted(root.rglob("*.json"))
if not paths:
    raise SystemExit("no LSP pool JSON contracts or fixtures found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"lsp-pool JSON PASS: {len(paths)} files")
PY
