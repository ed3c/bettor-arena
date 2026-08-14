#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}

"$PYTHON" "$ROOT/scripts/contextasm.py" check --root "$ROOT"
"$PYTHON" "$ROOT/scripts/contextasm.py" selftest --root "$ROOT"
"$PYTHON" "$ROOT/scripts/control_contextasm.py"

TMP=$(mktemp -d)
cleanup() { chmod -R u+w "$TMP" 2>/dev/null || true; find "$TMP" -mindepth 1 -delete 2>/dev/null || true; rmdir "$TMP" 2>/dev/null || true; }
trap cleanup EXIT

"$PYTHON" "$ROOT/scripts/contextasm.py" assemble --root "$ROOT" --output "$TMP/assembly.json" >/dev/null
"$PYTHON" "$ROOT/scripts/contextasm.py" emit --dir "$TMP/projections" --output "$TMP/emit.json" >/dev/null

# An unknown subcommand is unusable input, not a refusal. 64, never 2.
set +e
"$PYTHON" "$ROOT/scripts/contextasm.py" render-one --host claude >/dev/null 2>&1
rc=$?
set -e
test "$rc" = "64" || { echo "an unknown subcommand exited $rc, expected 64" >&2; exit 2; }
echo "loopx-context-assembly port PASS: unusable input exits 64, not 0 and not 2"

"$PYTHON" - "$TMP/assembly.json" "$TMP/projections" <<'PY'
import json, sys
from pathlib import Path

result = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
projections = Path(sys.argv[2])

hosts = [p["host"] for p in result["projections"]]
if hosts != ["ante", "claude", "codex", "grok-build", "opencode", "pi"]:
    raise SystemExit(f"one IR did not render six host projections: {hosts}")
if result["law_matrix"]["distinct_law_digests"] != 1:
    raise SystemExit("the six projections do not carry the same normative law")
if len({p["projection_digest"] for p in result["projections"]}) != 6:
    raise SystemExit("the projections are byte-identical, so the law check proves nothing")
for p in result["projections"]:
    if p["authority"] != "PRESENTATION_ONLY":
        raise SystemExit(f"the {p['host']} projection claimed authority: {p['authority']}")
if not result["suffix"]["budget_report"]["complete"]:
    raise SystemExit("the reference suffix did not fit its own budget")
if result["suffix"]["budget_report"]["evidence_anchors_dropped"] != 0:
    raise SystemExit("an evidence anchor was dropped to fit a budget")

written = sorted(p.stem for p in projections.glob("*.md"))
if written != sorted(hosts):
    raise SystemExit(f"emit wrote {written}")
print(
    f"loopx-context-assembly documents PASS: {len(hosts)} projections, 1 law, "
    f"{len(result['state_trace'])} states to {result['state_trace'][-1]}"
)
PY

"$PYTHON" -m py_compile \
  "$ROOT/scripts/ca_common.py" \
  "$ROOT/scripts/ca_ir.py" \
  "$ROOT/scripts/ca_project.py" \
  "$ROOT/scripts/ca_pipeline.py" \
  "$ROOT/scripts/ca_contract.py" \
  "$ROOT/scripts/ca_selftest.py" \
  "$ROOT/scripts/contextasm.py" \
  "$ROOT/scripts/control_contextasm.py"

"$PYTHON" - "$ROOT" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
paths = sorted(root.rglob("*.json"))
if not paths:
    raise SystemExit("no context-assembly JSON contracts found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"loopx-context-assembly JSON PASS: {len(paths)} files")
PY
