#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$ROOT/scripts/check_blindspot_hybrid.py"
BINDING="$ROOT/.skill-bindings/repo-agent-native/blindspot-hybrid.json"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
python3 -m py_compile "$SCRIPT"
python3 "$SCRIPT" --binding "$BINDING" --receipt "$TMP/receipt.json" >"$TMP/pass.json"
python3 - "$BINDING" "$TMP" <<'PY'
import copy,json,pathlib,sys
base=json.load(open(sys.argv[1])); root=pathlib.Path(sys.argv[2])
mutations={}
value=copy.deepcopy(base); value['active_lanes']['code-graph-rag']={'role':'graph-truth'}; mutations['active-graph']=value
value=copy.deepcopy(base); value['active_lanes']['lancedb']['authority']=True; mutations['vector-authority']=value
value=copy.deepcopy(base); value['authority']['source_claim_admission']=[]; mutations['no-readback']=value
value=copy.deepcopy(base); value['active_lanes']['scip']['source_commit']='main'; mutations['mutable-pin']=value
for name,value in mutations.items(): (root/f'{name}.json').write_text(json.dumps(value,indent=2)+'\n')
PY
expect_fail(){ local file="$1" code="$2"; set +e; python3 "$SCRIPT" --binding "$file" >"$TMP/out" 2>"$TMP/err"; local s=$?; set -e; test "$s" -eq 2; grep -q "$code" "$TMP/err"; }
expect_fail "$TMP/active-graph.json" CODE_GRAPH_RAG_ACTIVE
expect_fail "$TMP/vector-authority.json" LANCEDB_AUTHORITY_VIOLATION
expect_fail "$TMP/no-readback.json" SOURCE_READBACK_GATE_INVALID
expect_fail "$TMP/mutable-pin.json" SOURCE_PIN_INVALID
echo "bettor blindspot-hybrid binding PASS"
