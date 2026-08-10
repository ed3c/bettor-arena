#!/bin/sh
set -u

ROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel) || exit 64
TMP=$(mktemp -d "${TMPDIR:-/tmp}/bettor-ctg-local.XXXXXX") || exit 64
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

MANIFEST="$TMP/generic-domain.json"
python3 - "$MANIFEST" <<'PY'
import json
import sys
from pathlib import Path

Path(sys.argv[1]).write_text(
    json.dumps(
        {
            "slice_id": "generic-local-fixture",
            "title": "Generic domain truth graph",
            "snapshot": {"sha": "FIXTURE", "generated_at": "2026-08-09T00:00:00Z"},
            "scope": {"mode": "demo", "synthetic": True, "repo": "fixture/generic"},
            "artifacts": {"html": "generic-truth-graph.html"},
            "hard_truth_rule": "Fixture evidence cannot settle external truth.",
            "manual_static": {
                "nodes": [
                    {
                        "id": "rule:generic",
                        "kind": "static_rule",
                        "label": "Generic rule",
                        "method": "DOCUMENT",
                        "evidence_id": "ev-generic",
                        "source": "fixture-owned",
                        "summary": "Generic domain knowledge is manifest-owned",
                        "authority": "fixture",
                        "environment_class": "synthetic",
                    },
                    {
                        "id": "generic:target",
                        "kind": "domain_target",
                        "label": "Generic target",
                    }
                ],
                "edges": [],
            },
            "static": {},
            "lsp": {
                "tool_profile": "bindings-only-v1",
                "bindings": [
                    {
                        "source_selector": {"id": "rule:generic"},
                        "target_selector": {"id": "generic:target"},
                        "kind": "SUPPORTS",
                        "method": "LSP_REFERENCE",
                        "status": "observed",
                        "source_ref": "fixture-owned-semantic-index",
                        "summary": "Generic typed semantic binding",
                        "authority": "deterministic",
                        "environment_class": "synthetic",
                        "evidence_id": "ev-generic-semantic",
                    }
                ],
            },
            "sandbox": {},
            "production": {},
            "sessions": [],
            "critical_path": {},
            "invariants": [],
        },
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)
PY

git -C "$TMP" init -q || exit 64
git -C "$TMP" config user.name ctg-local-test
git -C "$TMP" config user.email ctg-local-test@example.invalid
git -C "$TMP" add generic-domain.json
git -C "$TMP" commit -qm 'fixture: pin generic local manifest' || exit 64

sh "$ROOT/loopctl/loopctl.sh" ctg build-local \
  --manifest "$MANIFEST" \
  --output "$TMP/output" >/dev/null || exit 1

python3 - "$TMP/output" <<'PY' || exit 1
import json
import sys
from pathlib import Path

output = Path(sys.argv[1])
report = json.loads((output / "verification-report.json").read_text(encoding="utf-8"))
receipt = json.loads((output / "ctg-local-build-receipt.json").read_text(encoding="utf-8"))
graph = json.loads((output / "code-truth-graph.json").read_text(encoding="utf-8"))
assert report["ok"] is True, report
assert report["html"] == "generic-truth-graph.html", report
assert report["hard_truth_rule"] == "Fixture evidence cannot settle external truth.", report
assert (output / report["html"]).is_file(), report
for name in ("entities.csv", "relationships.csv", "text_units.csv"):
    assert (output / "graphrag" / name).is_file(), name
assert receipt["schema_version"] == "ctg-local-build-receipt@1.0.0", receipt
assert receipt["subject"]["manifest_ref"] == "generic-domain.json", receipt
assert receipt["subject"]["dirty_before_run"] is False, receipt
assert receipt["subject"]["input_files"] == [], receipt
assert len(receipt["subject"]["input_closure_sha256"]) == 64, receipt
assert receipt["overall"] == {"state": "PASSED"}, receipt
edge = next(item for item in graph["edges"] if item["kind"] == "SUPPORTS")
assert edge["evidence_ids"] == ["ev-generic-semantic"], edge
for node_id in ("rule:generic", "generic:target"):
    node = next(item for item in graph["nodes"] if item["id"] == node_id)
    assert "ev-generic-semantic" in node["evidence_ids"], node
PY

PYTHONPATH="$ROOT/loop_wiki/code-truth-graph/src" python3 - "$TMP/output/ctg-local-build-receipt.json" <<'PY' || exit 1
import copy
import json
import sys
from pathlib import Path

from code_truth_graph.local_cli import validate_local_receipt

receipt = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
for label, mutate in (
    ("extra", lambda value: value.__setitem__("unexpected", True)),
    ("missing", lambda value: value.pop("claim_boundary")),
    ("wrong-type", lambda value: value["subject"].__setitem__("dirty_before_run", "false")),
):
    candidate = copy.deepcopy(receipt)
    mutate(candidate)
    try:
        validate_local_receipt(candidate)
    except ValueError:
        continue
    raise AssertionError(f"local receipt schema accepted {label} mutation")
PY

cp "$MANIFEST" "$TMP/toctou.json"
PYTHONPATH="$ROOT/loop_wiki/code-truth-graph/src" python3 - \
  "$TMP/toctou.json" "$TMP/toctou-output" <<'PY' || exit 1
import sys
from pathlib import Path

from code_truth_graph import local_cli

original = local_cli.build_graph


def mutate_after_read(manifest: Path, *, output_dir: Path):
    report = original(manifest, output_dir=output_dir)
    manifest.write_text(manifest.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    return report


local_cli.build_graph = mutate_after_read
rc = local_cli.main(["--manifest", sys.argv[1], "--output", sys.argv[2]])
assert rc == 64, rc
assert not (Path(sys.argv[2]) / "ctg-local-build-receipt.json").exists()
PY

if sh "$ROOT/loopctl/loopctl.sh" ctg build-local \
  --manifest relative.json \
  --output "$TMP/relative-output" >/dev/null 2>&1; then
  echo "CTG LOCAL BUILD failed — relative manifest path passed" >&2
  exit 1
else
  RC=$?
fi
[ "$RC" -eq 64 ] || exit 1

python3 - "$MANIFEST" "$TMP/unsafe-lsp.json" "$TMP/blocked-static.json" "$TMP/path-escape.json" "$TMP/unresolved-binding.json" <<'PY'
import json
import sys
from pathlib import Path

base = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
unsafe = dict(base)
unsafe["lsp"] = {"command": ["python3", "caller.py"]}
Path(sys.argv[2]).write_text(json.dumps(unsafe) + "\n", encoding="utf-8")
blocked = dict(base)
blocked["static"] = {"root": "missing", "source_globs": ["**/*.java"]}
Path(sys.argv[3]).write_text(json.dumps(blocked) + "\n", encoding="utf-8")
escaped = dict(base)
escaped["production"] = {"logs": [{"path": "/etc/hosts"}]}
Path(sys.argv[4]).write_text(json.dumps(escaped) + "\n", encoding="utf-8")
unresolved = dict(base)
unresolved["post_static_bindings"] = [
    {
        "source_selector": {"id": "missing:source"},
        "target_selector": {"id": "generic:target"},
        "kind": "SUPPORTS",
    }
]
Path(sys.argv[5]).write_text(json.dumps(unresolved) + "\n", encoding="utf-8")
PY

if sh "$ROOT/loopctl/loopctl.sh" ctg build-local \
  --manifest "$TMP/unsafe-lsp.json" \
  --output "$TMP/unsafe-output" >/dev/null 2>&1; then
  echo "CTG LOCAL BUILD failed — caller-controlled LSP command passed" >&2
  exit 1
else
  RC=$?
fi
[ "$RC" -eq 64 ] || exit 1

if sh "$ROOT/loopctl/loopctl.sh" ctg build-local \
  --manifest "$TMP/unresolved-binding.json" \
  --output "$TMP/unresolved-binding-output" >/dev/null 2>&1; then
  echo "CTG LOCAL BUILD failed — unresolved post-static binding returned exit 0" >&2
  exit 1
else
  RC=$?
fi
[ "$RC" -eq 2 ] || exit 1

if sh "$ROOT/loopctl/loopctl.sh" ctg build-local \
  --manifest "$TMP/path-escape.json" \
  --output "$TMP/path-escape-output" >/dev/null 2>&1; then
  echo "CTG LOCAL BUILD failed — raw evidence path escaped the subject root" >&2
  exit 1
else
  RC=$?
fi
[ "$RC" -eq 64 ] || exit 1

if sh "$ROOT/loopctl/loopctl.sh" ctg build-local \
  --manifest "$TMP/blocked-static.json" \
  --output "$TMP/blocked-output" >/dev/null 2>&1; then
  echo "CTG LOCAL BUILD failed — BLOCKED static stage returned exit 0" >&2
  exit 1
else
  RC=$?
fi
[ "$RC" -eq 2 ] || exit 1
python3 - "$TMP/blocked-output" <<'PY' || exit 1
import json
import sys
from pathlib import Path

output = Path(sys.argv[1])
report = json.loads((output / "verification-report.json").read_text(encoding="utf-8"))
receipt = json.loads((output / "ctg-local-build-receipt.json").read_text(encoding="utf-8"))
assert report["blocked_stages"] == ["static"], report
assert receipt["overall"] == {"state": "FAILED"}, receipt
PY

if sh "$ROOT/loopctl/loopctl.sh" mcp tools | rg -q 'loopctl_ctg_build_local'; then
  echo "CTG LOCAL BUILD failed — host-path ingress escaped into MCP" >&2
  exit 1
fi

if rg -n 'OOBECeremony|REOOBE|softKey|RegistrationHelper|GF-11|accounts/registration' \
  "$ROOT/loop_wiki/code-truth-graph/src/code_truth_graph" >/dev/null; then
  echo "CTG LOCAL BUILD failed — bettor mechanism embeds ix domain knowledge" >&2
  exit 1
fi

echo "CTG LOCAL BUILD TEST GREEN"
