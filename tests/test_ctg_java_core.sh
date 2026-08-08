#!/bin/sh
set -u

ROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel) || exit 64
TMP=$(mktemp -d "${TMPDIR:-/tmp}/bettor-ctg-java.XXXXXX") || exit 64
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
F="$ROOT/loop_wiki/code-truth-graph"
PACKET=$(PYTHONPATH="$F/src" python3 -m code_truth_graph.fixture --out "$TMP/bundle") || exit 64

python3 - "$TMP/bundle" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

bundle = Path(sys.argv[1])


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> str:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sha(path)


old = bundle / "subject/files/rules.txt"
old.unlink()
source = bundle / "subject/files/Demo.java"
source.write_text(
    "package fixture;\npublic final class Demo {\n"
    "  public int clamp(int value) { return Math.max(0, value); }\n}\n",
    encoding="utf-8",
)
path = "subject/files/Demo.java"
snapshot_path = bundle / "subject-snapshot.json"
snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
snapshot["scope"] = [path]
snapshot["files"] = [{"path": path, "sha256": sha(source)}]
snapshot_sha = write(snapshot_path, snapshot)

profile_path = bundle / "domain-profile.json"
profile = json.loads(profile_path.read_text(encoding="utf-8"))
profile["tool_profile"] = "java-compiler-v1"
profile_sha = write(profile_path, profile)

packet_path = bundle / "ctg-input.json"
packet = json.loads(packet_path.read_text(encoding="utf-8"))
packet["subject_snapshot"]["sha256"] = snapshot_sha
packet["subject_snapshot"]["scope"] = [path]
packet["subject_snapshot"]["file_manifest_digest"] = hashlib.sha256(
    f"{path}\0{sha(source)}\n".encode()
).hexdigest()
packet["domain_profile"]["sha256"] = profile_sha
packet["source_refs"] = [
    {
        "repo": "fixture/ledger",
        "commit": "1" * 40,
        "path": path,
        "anchor": "Demo#clamp",
        "sha256": sha(source),
    }
]
write(packet_path, packet)
PY

if sh "$ROOT/loopctl/loopctl.sh" ctg run --packet "$PACKET" --output "$TMP/output" >/dev/null; then
  RC=0
else
  RC=$?
fi
[ "$RC" -eq 0 ] || {
  echo "CTG JAVA CORE failed — public CLI exited $RC" >&2
  exit 1
}

python3 - "$TMP/output/code-truth-graph.json" <<'PY' || exit 1
import json
import sys
from pathlib import Path

graph = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert any(node["kind"] in {"class", "method", "constructor"} for node in graph["nodes"]), graph
assert any(item["method"] == "JAVA_AST" for item in graph["evidence"]), graph
assert any(edge["kind"] == "AFFECTS_INVARIANT" for edge in graph["edges"]), graph
PY

echo "CTG JAVA CORE TEST GREEN"
