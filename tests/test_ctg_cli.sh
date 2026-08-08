#!/bin/sh
set -u

ROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel) || exit 64
TMP=$(mktemp -d "${TMPDIR:-/tmp}/bettor-ctg-cli.XXXXXX") || exit 64
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

BUNDLE="$TMP/bundle"
OUTPUT="$TMP/output"
mkdir -p "$BUNDLE/subject/files" "$BUNDLE/evidence"
printf '%s\n' 'account balance must not become negative' >"$BUNDLE/subject/files/rules.txt"
printf '%s\n' 'fixture evidence for INV-DEMO' >"$BUNDLE/evidence/inv-demo.txt"

python3 - "$BUNDLE" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

bundle = Path(sys.argv[1])


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> str:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sha256(path)


source = bundle / "subject/files/rules.txt"
snapshot_sha = write_json(
    bundle / "subject-snapshot.json",
    {
        "schema_version": "ctg-subject-snapshot@1.0.0",
        "repo_id": "fixture/ledger",
        "commit": "1" * 40,
        "tree": "2" * 40,
        "dirty": False,
        "dirty_digest": None,
        "scope": ["subject/files/rules.txt"],
        "files": [
            {
                "path": "subject/files/rules.txt",
                "sha256": sha256(source),
            }
        ],
    },
)
profile_sha = write_json(
    bundle / "domain-profile.json",
    {
        "schema_version": "ctg-domain-profile@1.0.0",
        "profile_id": "fixture-ledger-v1",
        "tool_profile": "builtin-text-v1",
        "invariants": [
            {
                "invariant_id": "INV-DEMO",
                "statement": "balance remains non-negative",
                "claim_boundary": "structure-only demo",
            }
        ],
    },
)
evidence = bundle / "evidence/inv-demo.txt"
file_manifest_digest = hashlib.sha256(
    f"subject/files/rules.txt\0{sha256(source)}\n".encode("utf-8")
).hexdigest()
write_json(
    bundle / "ctg-input.json",
    {
        "schema_version": "ctg-input@1.0.0",
        "packet_id": "ctg-fixture-001",
        "packet_state": "admitted_for_measurement",
        "observation_id": "obs-fixture-001",
        "expected_runner": {
            "surface_version": "2.5.0",
            "runtime_ref": "ctg-runtime@1.0.0",
        },
        "subject_snapshot": {
            "artifact_ref": "subject-snapshot.json",
            "sha256": snapshot_sha,
            "repo_id": "fixture/ledger",
            "commit": "1" * 40,
            "tree": "2" * 40,
            "dirty": False,
            "dirty_digest": None,
            "scope": ["subject/files/rules.txt"],
            "file_manifest_digest": file_manifest_digest,
        },
        "domain_profile": {
            "schema_version": "ctg-domain-profile@1.0.0",
            "artifact_ref": "domain-profile.json",
            "sha256": profile_sha,
        },
        "source_refs": [
            {
                "repo": "fixture/ledger",
                "commit": "1" * 40,
                "path": "subject/files/rules.txt",
                "anchor": "1",
                "sha256": sha256(source),
            }
        ],
        "evidence": [
            {
                "evidence_id": "evidence-inv-demo",
                "kind": "fixture",
                "artifact_ref": "evidence/inv-demo.txt",
                "sha256": sha256(evidence),
                "observed_at": "2026-08-09T00:00:00Z",
                "environment_class": "synthetic",
                "authority": "control-group",
                "freshness": "current",
            }
        ],
        "reach_requirements": {
            "STATIC": "required",
            "SANDBOX": "not_requested",
            "PROD": "not_requested",
        },
        "context": {
            "fixed": ["domain_profile"],
            "iteration": "first-public-cli-tracer",
            "emergent": [],
        },
        "human_gate": "required_before_invariant_admit",
    },
)
PY

RESPONSE="$TMP/loopctl-response.json"
if sh "$ROOT/loopctl/loopctl.sh" ctg run \
  --packet "$BUNDLE/ctg-input.json" \
  --output "$OUTPUT" \
  --json >"$RESPONSE"; then
  RC=0
else
  RC=$?
fi

if [ "$RC" -ne 0 ]; then
  echo "CTG CLI case failed — valid packet exited $RC, want 0" >&2
  [ ! -s "$RESPONSE" ] || cat "$RESPONSE" >&2
  exit 1
fi

python3 - "$RESPONSE" "$OUTPUT" <<'PY' || exit 1
import json
import sys
from pathlib import Path

response_path = Path(sys.argv[1])
output = Path(sys.argv[2])
response = json.loads(response_path.read_text(encoding="utf-8"))
assert response["loop"] == "ctg", response
assert response["mode"] == "run", response
assert response["exit"] == 0, response

result_path = output / "ctg-route-result.json"
graph_path = output / "code-truth-graph.json"
assert result_path.is_file(), result_path
assert graph_path.is_file(), graph_path

graph = json.loads(graph_path.read_text(encoding="utf-8"))
assert graph["schema_version"] == "1.1.0", graph
assert graph["invariants"][0]["id"] == "INV-DEMO", graph
assert graph["invariants"][0]["current_status"] == "DEMO_ONLY", graph
assert graph["closure"]["invariants"] == {"DEMO_ONLY": 1}, graph
for name in ("entities.csv", "relationships.csv", "text_units.csv"):
    assert (output / "graphrag" / name).is_file(), name
assert (output / "report.html").is_file(), output

result = json.loads(result_path.read_text(encoding="utf-8"))
assert result["schema_version"] == "ctg-route-result@1.0.0", result
assert result["packet_id"] == "ctg-fixture-001", result
assert result["observation_id"] == "obs-fixture-001", result
assert result["overall"]["exit"] == 0, result
assert result["human_gate"] == "required_before_invariant_admit", result
assert result["claim_boundary"] == "structure-only demo", result
assert set(result["actual_runner"]) == {
    "repo_commit", "repo_tree", "runtime_ref", "runtime_sha256", "surface_version"
}, result
assert set(result["digests"]) == {
    "delivery", "domain_profile", "execution_argv", "input", "subject_snapshot"
}, result
stages = {stage["name"]: stage for stage in result["stages"]}
assert stages["STATIC"]["state"] == "PASSED", stages
assert stages["SANDBOX"]["state"] == "NOT_REQUESTED", stages
assert stages["PROD"]["state"] == "NOT_REQUESTED", stages
assert all("bettor-arena-ctg-runtime" not in item["artifact_ref"] for item in result["artifacts"]), result
assert any(item["artifact_ref"] == "report.html" for item in result["artifacts"]), result
PY

OUTPUT_REPEAT="$TMP/output-repeat"
sh "$ROOT/loopctl/loopctl.sh" ctg run \
  --packet "$BUNDLE/ctg-input.json" \
  --output "$OUTPUT_REPEAT" >/dev/null || exit 1
cmp "$OUTPUT/code-truth-graph.json" "$OUTPUT_REPEAT/code-truth-graph.json" >/dev/null || {
  echo "CTG CLI case failed — identical input produced a different graph" >&2
  exit 1
}
cmp "$OUTPUT/ctg-route-result.json" "$OUTPUT_REPEAT/ctg-route-result.json" >/dev/null || {
  echo "CTG CLI case failed — identical input produced a different route-result" >&2
  exit 1
}

UNKNOWN_PACKET="$BUNDLE/ctg-input-unknown-key.json"
python3 - "$BUNDLE/ctg-input.json" "$UNKNOWN_PACKET" <<'PY'
import json
import sys
from pathlib import Path

packet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
packet["quietly_ignored_policy"] = "this must be rejected"
Path(sys.argv[2]).write_text(json.dumps(packet) + "\n", encoding="utf-8")
PY
if sh "$ROOT/loopctl/loopctl.sh" ctg run \
  --packet "$UNKNOWN_PACKET" \
  --output "$TMP/unknown-output" >/dev/null 2>&1; then
  echo "CTG CLI case failed — unknown packet key was accepted" >&2
  exit 1
else
  RC=$?
fi
[ "$RC" -eq 64 ] || {
  echo "CTG CLI case failed — unknown packet key exited $RC, want 64" >&2
  exit 1
}

UNSAFE_PACKET="$BUNDLE/ctg-input-unsafe-path.json"
python3 - "$BUNDLE/ctg-input.json" "$UNSAFE_PACKET" "$BUNDLE" <<'PY'
import hashlib
import json
import shutil
import sys
from pathlib import Path

source = Path(sys.argv[3]) / "subject-snapshot.json"
unsafe = Path(sys.argv[3]) / "subject-snapshot;ignored.json"
shutil.copyfile(source, unsafe)
packet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
packet["subject_snapshot"]["artifact_ref"] = unsafe.name
packet["subject_snapshot"]["sha256"] = hashlib.sha256(unsafe.read_bytes()).hexdigest()
Path(sys.argv[2]).write_text(json.dumps(packet) + "\n", encoding="utf-8")
PY
if sh "$ROOT/loopctl/loopctl.sh" ctg run \
  --packet "$UNSAFE_PACKET" \
  --output "$TMP/unsafe-output" >/dev/null 2>&1; then
  echo "CTG CLI case failed — shell metacharacter in artifact_ref was accepted" >&2
  exit 1
else
  RC=$?
fi
[ "$RC" -eq 64 ] || {
  echo "CTG CLI case failed — unsafe artifact_ref exited $RC, want 64" >&2
  exit 1
}

UNPINNED_PROFILE="$BUNDLE/domain-profile-unpinned.json"
UNPINNED_PACKET="$BUNDLE/ctg-input-unpinned-tool.json"
python3 - "$BUNDLE/domain-profile.json" "$UNPINNED_PROFILE" "$BUNDLE/ctg-input.json" "$UNPINNED_PACKET" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

profile = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
profile["tool_profile"] = "shell-command:curl example.invalid"
Path(sys.argv[2]).write_text(json.dumps(profile) + "\n", encoding="utf-8")
packet = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
packet["domain_profile"]["artifact_ref"] = Path(sys.argv[2]).name
packet["domain_profile"]["sha256"] = hashlib.sha256(Path(sys.argv[2]).read_bytes()).hexdigest()
Path(sys.argv[4]).write_text(json.dumps(packet) + "\n", encoding="utf-8")
PY
if sh "$ROOT/loopctl/loopctl.sh" ctg run \
  --packet "$UNPINNED_PACKET" \
  --output "$TMP/unpinned-tool-output" >/dev/null 2>&1; then
  echo "CTG CLI case failed — unpinned tool profile was accepted" >&2
  exit 1
else
  RC=$?
fi
[ "$RC" -eq 64 ] || {
  echo "CTG CLI case failed — unpinned tool profile exited $RC, want 64" >&2
  exit 1
}

BAD_EVIDENCE_PACKET="$BUNDLE/ctg-input-bad-evidence.json"
python3 - "$BUNDLE/ctg-input.json" "$BAD_EVIDENCE_PACKET" <<'PY'
import json
import sys
from pathlib import Path

packet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
packet["evidence"][0]["sha256"] = "0" * 64
Path(sys.argv[2]).write_text(json.dumps(packet) + "\n", encoding="utf-8")
PY
BAD_EVIDENCE_OUTPUT="$TMP/bad-evidence-output"
if sh "$ROOT/loopctl/loopctl.sh" ctg run \
  --packet "$BAD_EVIDENCE_PACKET" \
  --output "$BAD_EVIDENCE_OUTPUT" >/dev/null 2>&1; then
  echo "CTG CLI case failed — bad evidence digest was accepted" >&2
  exit 1
else
  RC=$?
fi
[ "$RC" -eq 2 ] || {
  echo "CTG CLI case failed — bad evidence exited $RC, want 2" >&2
  exit 1
}
python3 - "$BAD_EVIDENCE_OUTPUT/ctg-route-result.json" <<'PY' || exit 1
import json
import sys
from pathlib import Path

result = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert result["overall"] == {"exit": 2, "state": "FAILED"}, result
assert result["stages"][0]["name"] == "STATIC", result
assert result["stages"][0]["state"] == "FAILED", result
assert result["artifacts"] == [], result
PY

DUPLICATE_PACKET="$BUNDLE/ctg-input-duplicate-key.json"
python3 - "$BUNDLE/ctg-input.json" "$DUPLICATE_PACKET" <<'PY'
import sys
from pathlib import Path

body = Path(sys.argv[1]).read_text(encoding="utf-8")
needle = '  "schema_version": "ctg-input@1.0.0",'
replacement = needle + '\n  "schema_version": "ctg-input@1.0.0",'
assert body.count(needle) == 1
Path(sys.argv[2]).write_text(body.replace(needle, replacement), encoding="utf-8")
PY
if sh "$ROOT/loopctl/loopctl.sh" ctg run \
  --packet "$DUPLICATE_PACKET" \
  --output "$TMP/duplicate-output" >/dev/null 2>&1; then
  echo "CTG CLI case failed — duplicate JSON key was accepted" >&2
  exit 1
else
  RC=$?
fi
[ "$RC" -eq 64 ] || {
  echo "CTG CLI case failed — duplicate JSON key exited $RC, want 64" >&2
  exit 1
}

STALE_PACKET="$BUNDLE/ctg-input-stale-subject.json"
python3 - "$BUNDLE/ctg-input.json" "$STALE_PACKET" <<'PY'
import json
import sys
from pathlib import Path

packet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
packet["subject_snapshot"]["commit"] = "3" * 40
Path(sys.argv[2]).write_text(json.dumps(packet) + "\n", encoding="utf-8")
PY
if sh "$ROOT/loopctl/loopctl.sh" ctg run \
  --packet "$STALE_PACKET" \
  --output "$TMP/stale-output" >/dev/null 2>&1; then
  echo "CTG CLI case failed — stale subject identity was accepted" >&2
  exit 1
else
  RC=$?
fi
[ "$RC" -eq 2 ] || {
  echo "CTG CLI case failed — stale subject exited $RC, want 2" >&2
  exit 1
}

NESTED_UNKNOWN_PACKET="$BUNDLE/ctg-input-nested-unknown.json"
python3 - "$BUNDLE/ctg-input.json" "$NESTED_UNKNOWN_PACKET" <<'PY'
import json
import sys
from pathlib import Path

packet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
packet["evidence"][0]["ambient_authority"] = "must not be inferred"
Path(sys.argv[2]).write_text(json.dumps(packet) + "\n", encoding="utf-8")
PY
if sh "$ROOT/loopctl/loopctl.sh" ctg run \
  --packet "$NESTED_UNKNOWN_PACKET" \
  --output "$TMP/nested-unknown-output" >/dev/null 2>&1; then
  echo "CTG CLI case failed — nested unknown key was accepted" >&2
  exit 1
else
  RC=$?
fi
[ "$RC" -eq 64 ] || {
  echo "CTG CLI case failed — nested unknown key exited $RC, want 64" >&2
  exit 1
}

python3 - "$ROOT/loop_wiki/code-truth-graph/schemas" <<'PY' || exit 1
import json
import sys
from pathlib import Path

schemas = Path(sys.argv[1])
for name in ("ctg-input.schema.json", "ctg-route-result.schema.json"):
    schema = json.loads((schemas / name).read_text(encoding="utf-8"))
    assert schema["additionalProperties"] is False, (name, schema)
    assert set(schema["required"]) == set(schema["properties"]), (name, schema)
PY

sh "$ROOT/loop_wiki/code-truth-graph/portability.sh" >/dev/null || {
  echo "CTG CLI case failed — relocated runtime did not pass" >&2
  exit 1
}

TRIGGER_OUTPUT="$TMP/trigger-output"
sh "$ROOT/loop_wiki/code-truth-graph/trigger.sh" \
  "$BUNDLE/ctg-input.json" "$TRIGGER_OUTPUT" >/dev/null || {
  echo "CTG CLI case failed — positional trigger did not pass" >&2
  exit 1
}
if sh "$ROOT/loop_wiki/code-truth-graph/trigger.sh" "$BUNDLE/ctg-input.json" >/dev/null 2>&1; then
  echo "CTG CLI case failed — trigger accepted missing output argument" >&2
  exit 1
else
  RC=$?
fi
[ "$RC" -eq 64 ] || {
  echo "CTG CLI case failed — trigger usage exited $RC, want 64" >&2
  exit 1
}

echo "CTG CLI TEST GREEN"
