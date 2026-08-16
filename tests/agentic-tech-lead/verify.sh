#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$ROOT/scripts/agentic_tech_lead.py"
CONFIG="$ROOT/.agents/bindings/agentic-tech-lead.example.json"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
python3 -m py_compile "$SCRIPT"
python3 "$SCRIPT" --config "$CONFIG" verify-config >"$TMP/config.json"
mkdir -p "$TMP/shared/skills/git-town-stacked-pr-worker/scripts" "$TMP/shared/skills/repo-agent-native/scripts"
cat > "$TMP/shared/skills/git-town-stacked-pr-worker/scripts/plan_tech_lead_stack.py" <<'PY'
#!/usr/bin/env python3
import argparse,json,pathlib
p=argparse.ArgumentParser(); s=p.add_subparsers(dest='cmd',required=True)
v=s.add_parser('verify'); v.add_argument('--plan',required=True)
c=s.add_parser('compile'); c.add_argument('--plan',required=True); c.add_argument('--output',required=True)
a=p.parse_args()
if a.cmd=='compile': pathlib.Path(a.output).mkdir(parents=True,exist_ok=True); pathlib.Path(a.output,'compiled').write_text('ok')
print(json.dumps({'state':'PASS','cmd':a.cmd}))
PY
cat > "$TMP/shared/skills/repo-agent-native/scripts/blindspot_contract.py" <<'PY'
#!/usr/bin/env python3
import argparse,json
p=argparse.ArgumentParser(); s=p.add_subparsers(dest='cmd',required=True); v=s.add_parser('verify'); v.add_argument('--db',required=True); a=p.parse_args(); print(json.dumps({'state':'PASS','cmd':a.cmd}))
PY
printf '{}\n' > "$TMP/plan.json"; : > "$TMP/run.sqlite"
python3 "$SCRIPT" --config "$CONFIG" --shared-root "$TMP/shared" --receipt "$TMP/plan-receipt.json" verify-plan --plan "$TMP/plan.json"
python3 "$SCRIPT" --config "$CONFIG" --shared-root "$TMP/shared" compile-plan --plan "$TMP/plan.json" --output "$TMP/out"
test -f "$TMP/out/compiled"
python3 "$SCRIPT" --config "$CONFIG" --shared-root "$TMP/shared" verify-blindspot --db "$TMP/run.sqlite"
set +e
python3 "$SCRIPT" --config "$CONFIG" --shared-root "$TMP/missing" verify-plan --plan "$TMP/plan.json" >"$TMP/out.log" 2>"$TMP/err.log"; s=$?
set -e
test "$s" -eq 64; grep -q SHARED_CONTRACT_ABSENT "$TMP/err.log"
python3 - "$CONFIG" "$TMP/bad.json" <<'PY'
import json,sys
v=json.load(open(sys.argv[1])); v['effects']['spawn_agents']=True; open(sys.argv[2],'w').write(json.dumps(v))
PY
set +e
python3 "$SCRIPT" --config "$TMP/bad.json" verify-config >"$TMP/out.log" 2>"$TMP/err.log"; s=$?
set -e
test "$s" -eq 2; grep -q EFFECT_OVERCLAIM "$TMP/err.log"
echo "agentic-tech-lead adapter PASS"
