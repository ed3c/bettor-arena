#!/usr/bin/env bash
# wiki_update_worker.sh — digestion station for wiki-update requests (ISSUE-23).
#
#   wiki_update_worker.sh <request.json> --dry-run   # deterministic chain proof
#   wiki_update_worker.sh <request.json>             # real run: FATAL 64 until the
#                                                    # LLM segment is wired (TODO below)
#   wiki_update_worker.sh --selftest                 # fixture-driven good/broken proof
#
# Reads one request emitted by the factory delivery terminus
# (loop_wiki/evolve-perfect-seed-repo-factory/trigger.sh), then walks the
# official update pipeline: parse -> preflight -> [LLM regenerate: TODO] ->
# review gates (openwiki_subagent.sh) -> post passes (openwiki_post.py) ->
# receipt back-linking the request id into data/wiki-update/.
#
# --dry-run exercises every deterministic seam with the REAL components:
#   - gates run under OPENWIKI_DRY_RUN (sandbox assembly + shape assertions,
#     no model turn); critic is recorded "skipped-no-skeleton" when the update
#     flow has no _skeleton.md — a named absence, not a silent pass.
#   - post passes run against a scratch COPY of openwiki/; the live wiki is
#     byte-compared before/after and any mutation fails loud.
#
# Env: WIKI_WORKER_ROOT — override the arena root (selftest fixtures only).
# Exit: 0 ok · 2 contract fail · 64 FATAL (absent input/tool, unwired LLM segment)
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SCHEMA="bettor-arena-wiki-update-request@1.0.0"
RECEIPT_SCHEMA="bettor-arena-wiki-update-receipt@1.0.0"

fail() { echo "FAIL: $*" >&2; exit 2; }
fatal() { echo "FATAL: $*" >&2; exit 64; }

run_worker() {
  local request="$1" mode="$2"
  [ -f "$request" ] || fatal "request file not found: $request"
  command -v python3 >/dev/null 2>&1 || fatal "python3 not on PATH"
  local root
  root="${WIKI_WORKER_ROOT:-$(git -C "$HERE" rev-parse --show-toplevel)}" || fatal "cannot resolve arena root"

  # -- stage 1: parse (typed contract; every miss is a named exit 2) ----------
  local parsed
  parsed=$(python3 - "$request" <<'PY'
import json, sys
from pathlib import Path

SCHEMA = "bettor-arena-wiki-update-request@1.0.0"
try:
    req = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
except json.JSONDecodeError as err:
    print(f"FAIL: request is not JSON: {err}", file=sys.stderr); sys.exit(2)
if req.get("schema_version") != SCHEMA:
    print(f"FAIL: schema_version {req.get('schema_version')!r} != {SCHEMA!r}", file=sys.stderr); sys.exit(2)
required = ["request_id", "packet_id", "git_head", "route_result",
            "fixed_prompt_context", "iteration_auto_context", "emergent_prompt_context"]
missing = [key for key in required if key not in req]
if missing:
    print(f"FAIL: request missing fields: {missing}", file=sys.stderr); sys.exit(2)
route_path = req["route_result"].get("path")
if not route_path:
    print("FAIL: route_result.path missing", file=sys.stderr); sys.exit(2)
fixed = req["fixed_prompt_context"]
if not isinstance(fixed, list) or not fixed:
    print("FAIL: fixed_prompt_context must be a non-empty list of pointers", file=sys.stderr); sys.exit(2)
delta = req["iteration_auto_context"].get("delta_status")
if delta not in {"computed", "no-last-update", "unresolvable-last-head"}:
    print(f"FAIL: unrecognized delta_status {delta!r}", file=sys.stderr); sys.exit(2)
print("REQUEST_ID", req["request_id"])
print("PACKET_ID", req["packet_id"])
print("ROUTE_RESULT_PATH", route_path)
print("DELTA_STATUS", delta)
print("FIXED", " ".join(fixed))
PY
  ) || exit 2
  local request_id packet_id route_result_path delta_status fixed_ctx key rest
  while read -r key rest; do
    case "$key" in
      REQUEST_ID) request_id=$rest ;;
      PACKET_ID) packet_id=$rest ;;
      ROUTE_RESULT_PATH) route_result_path=$rest ;;
      DELTA_STATUS) delta_status=$rest ;;
      FIXED) fixed_ctx=$rest ;;
    esac
  done <<<"$parsed"
  echo "[parse] request_id=$request_id delta_status=$delta_status"

  # -- stage 2: preflight (interface contracts, not our own logic) ------------
  local pointer
  for pointer in $fixed_ctx; do
    [ -f "$root/$pointer" ] || fail "fixed_prompt_context pointer missing: $root/$pointer"
  done
  [ -d "$root/openwiki" ] || fail "no wiki at $root/openwiki"
  [ -f "$root/$route_result_path" ] || fail "route_result missing: $root/$route_result_path"
  [ -x "$HERE/openwiki_subagent.sh" ] || fatal "gate runner missing: $HERE/openwiki_subagent.sh"
  [ -f "$HERE/openwiki_post.py" ] || fatal "post processor missing: $HERE/openwiki_post.py"
  echo "[preflight] pointers + wiki + route_result present"

  # -- stage 3: LLM regeneration --------------------------------------------
  # TODO(ISSUE-23 follow-up): regenerate the changed pages per the official
  # update mode (fixed_prompt_context pointers + iteration delta), in the host
  # CLI session. Until wired, a real run is an absent tool, not a green.
  local regenerate_state
  if [ "$mode" = dry-run ]; then
    regenerate_state="todo-not-run"
    echo "[dry-run] TODO: LLM regeneration of changed pages not executed"
  else
    fatal "LLM regeneration segment not wired yet (TODO ISSUE-23 follow-up); run with --dry-run"
  fi

  # -- stage 4: review gates via the real runner (dry-run sandbox proof) ------
  local payload gate_finder gate_verifier gate_critic
  payload=$(mktemp "${TMPDIR:-/tmp}/wiki-update-payload.XXXXXX")
  echo "dry-run shape probe for $request_id" >"$payload"
  OPENWIKI_DRY_RUN=1 "$HERE/openwiki_subagent.sh" finder "$root" "$payload" >/dev/null
  gate_finder=$?
  OPENWIKI_DRY_RUN=1 "$HERE/openwiki_subagent.sh" verifier "$root" "$payload" >/dev/null
  gate_verifier=$?
  if [ -f "$root/openwiki/_skeleton.md" ]; then
    OPENWIKI_DRY_RUN=1 "$HERE/openwiki_subagent.sh" critic "$root" "$payload" >/dev/null
    gate_critic=$?
  else
    gate_critic="skipped-no-skeleton"
  fi
  rm -f "$payload"
  [ "$gate_finder" -eq 0 ] || fail "finder gate dry-run failed (exit $gate_finder)"
  [ "$gate_verifier" -eq 0 ] || fail "verifier gate dry-run failed (exit $gate_verifier)"
  [ "$gate_critic" = "skipped-no-skeleton" ] || [ "$gate_critic" -eq 0 ] || fail "critic gate dry-run failed (exit $gate_critic)"
  echo "[gates] finder=$gate_finder verifier=$gate_verifier critic=$gate_critic"

  # -- stage 5: official post passes on a scratch copy ------------------------
  local scratch post_migrate post_finalize
  scratch=$(mktemp -d "${TMPDIR:-/tmp}/wiki-update-post.XXXXXX")
  cp -R "$root/openwiki" "$scratch/openwiki"
  cp -R "$root/openwiki" "$scratch/live-before"
  python3 "$HERE/openwiki_post.py" migrate "$scratch/openwiki" >/dev/null
  post_migrate=$?
  python3 "$HERE/openwiki_post.py" finalize "$scratch/openwiki" --target "$root" \
    --command update --model "$mode" --status "$mode" --normalize-backlog >/dev/null
  post_finalize=$?
  [ "$post_migrate" -eq 0 ] || { rm -rf "$scratch"; fail "openwiki_post migrate failed (exit $post_migrate)"; }
  [ "$post_finalize" -eq 0 ] || { rm -rf "$scratch"; fail "openwiki_post finalize failed (exit $post_finalize)"; }
  [ -f "$scratch/openwiki/.last-update.json" ] || { rm -rf "$scratch"; fail "finalize left no .last-update.json in scratch"; }
  # Assert before announcing: the LIVE wiki must be byte-identical.
  diff -r "$root/openwiki" "$scratch/live-before" >/dev/null || { rm -rf "$scratch"; fail "dry-run mutated the live wiki"; }
  rm -rf "$scratch"
  echo "[post] migrate=$post_migrate finalize=$post_finalize live wiki untouched"

  # -- stage 6: receipt back-linking the request id ---------------------------
  local receipt
  mkdir -p "$root/data/wiki-update"
  receipt="$root/data/wiki-update/receipt-$packet_id.json"
  # Receipts are frozen evidence (CONTEXT.md; house rule set by #19): a rerun
  # must declare its intent, never silently rewrite history.
  if [ -e "$receipt" ] && [ "${WIKI_UPDATE_FORCE_RECEIPT:-0}" != "1" ]; then
    fatal "receipt already exists: $receipt — rerun with WIKI_UPDATE_FORCE_RECEIPT=1 to overwrite explicitly"
  fi
  RECEIPT_PATH="$receipt" REQUEST_ID="$request_id" REQUEST_PATH="$request" MODE="$mode" \
  GATE_FINDER="$gate_finder" GATE_VERIFIER="$gate_verifier" GATE_CRITIC="$gate_critic" \
  REGENERATE="$regenerate_state" POST_MIGRATE="$post_migrate" POST_FINALIZE="$post_finalize" \
  RECEIPT_SCHEMA="$RECEIPT_SCHEMA" python3 - <<'PY'
import datetime, json, os
receipt = {
    "schema_version": os.environ["RECEIPT_SCHEMA"],
    "request_id": os.environ["REQUEST_ID"],
    "request_path": os.environ["REQUEST_PATH"],
    "mode": os.environ["MODE"],
    "stages": {
        "parse": 0,
        "preflight": 0,
        "llm_regenerate": os.environ["REGENERATE"],
        "gate_finder": int(os.environ["GATE_FINDER"]),
        "gate_verifier": int(os.environ["GATE_VERIFIER"]),
        "gate_critic": os.environ["GATE_CRITIC"],
        "post_migrate": int(os.environ["POST_MIGRATE"]),
        "post_finalize": int(os.environ["POST_FINALIZE"]),
    },
    "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
with open(os.environ["RECEIPT_PATH"], "w", encoding="utf-8") as handle:
    json.dump(receipt, handle, indent=2)
    handle.write("\n")
PY
  # Assert before announcing.
  [ -s "$receipt" ] || fail "receipt missing after run: $receipt"
  python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$receipt" || fail "receipt is not valid JSON: $receipt"
  echo "PASS: mode=$mode receipt=$receipt request_id=$request_id"
}

# ---------------------------------------------------------------- selftest
selftest() {
  local base fixture request rc red=0
  base=$(mktemp -d "${TMPDIR:-/tmp}/wiki-update-selftest.XXXXXX")
  # Expanded now: the EXIT trap fires outside this function's scope.
  trap "rm -rf '$base'" EXIT

  fixture="$base/arena"
  mkdir -p "$fixture/openwiki" "$fixture/kb-ingest/openwiki" "$fixture/kb-ingest/port" \
    "$fixture/loop_wiki/evolve-perfect-seed-repo-factory/packets/outbox"
  echo "# fixture wiki" >"$fixture/openwiki/index.md"
  printf '# Quickstart\n\n## Backlog\n' >"$fixture/openwiki/quickstart.md"
  echo "stub" >"$fixture/kb-ingest/openwiki/update.system.md"
  echo "stub" >"$fixture/kb-ingest/openwiki/user.update.md"
  echo "stub" >"$fixture/kb-ingest/port/host-runtime.md"
  echo '{"schema_version":"perfect-seed-route-result@1.0.0"}' \
    >"$fixture/loop_wiki/evolve-perfect-seed-repo-factory/packets/outbox/route-result.fx.json"
  git -C "$fixture" init -q
  git -C "$fixture" add -A
  git -C "$fixture" -c user.name=fixture -c user.email=fixture@test commit -qm fixture

  request="$base/request.json"
  cat >"$request" <<EOF
{
  "schema_version": "$SCHEMA",
  "request_id": "fx@0000000000000000000000000000000000000000",
  "packet_id": "fx",
  "git_head": "0000000000000000000000000000000000000000",
  "route_result": {"path": "loop_wiki/evolve-perfect-seed-repo-factory/packets/outbox/route-result.fx.json"},
  "fixed_prompt_context": ["kb-ingest/openwiki/update.system.md", "kb-ingest/openwiki/user.update.md", "kb-ingest/port/host-runtime.md"],
  "iteration_auto_context": {"last_update_git_head": null, "delta_status": "no-last-update", "changed_files": []},
  "emergent_prompt_context": "openwiki/quickstart.md#backlog"
}
EOF

  expect() { # <name> <want-rc> <got-rc>
    if [ "$3" -ne "$2" ]; then echo "SELFTEST case failed — $1: got $3, want $2" >&2; red=1; fi
  }

  ("$0" "$base/absent.json" --dry-run) >/dev/null 2>&1; expect "absent-request-is-fatal-64" 64 $?
  echo "{not json" >"$base/broken.json"
  ("$0" "$base/broken.json" --dry-run) >/dev/null 2>&1; expect "non-json-request" 2 $?
  sed 's/@1\.0\.0/@9.9.9/' "$request" >"$base/foreign.json"
  ("$0" "$base/foreign.json" --dry-run) >/dev/null 2>&1; expect "foreign-schema" 2 $?
  grep -v '"packet_id"' "$request" >"$base/hollow.json"
  ("$0" "$base/hollow.json" --dry-run) >/dev/null 2>&1; expect "missing-field" 2 $?
  (WIKI_WORKER_ROOT="$fixture" "$0" "$request") >/dev/null 2>&1; expect "real-run-unwired-llm-is-fatal-64" 64 $?
  (WIKI_WORKER_ROOT="$fixture" "$0" "$request" --dry-run) >"$base/good.out" 2>&1
  rc=$?
  expect "good-dry-run" 0 $rc
  if [ "$rc" -eq 0 ]; then
    if [ ! -s "$fixture/data/wiki-update/receipt-fx.json" ]; then
      echo "SELFTEST case failed — good-dry-run: no receipt written" >&2; red=1
    elif ! grep -q '"request_id": "fx@0000000000000000000000000000000000000000"' \
        "$fixture/data/wiki-update/receipt-fx.json"; then
      echo "SELFTEST case failed — good-dry-run: receipt does not back-link the request id" >&2; red=1
    fi
  else
    tail -5 "$base/good.out" >&2
  fi

  # Frozen-evidence rule: a rerun over an existing receipt refuses (64) unless
  # the overwrite intent is explicit; with it, the rerun succeeds.
  (WIKI_WORKER_ROOT="$fixture" "$0" "$request" --dry-run) >/dev/null 2>&1
  expect "receipt-collision-refused" 64 $?
  (WIKI_WORKER_ROOT="$fixture" WIKI_UPDATE_FORCE_RECEIPT=1 "$0" "$request" --dry-run) >/dev/null 2>&1
  expect "receipt-collision-forced" 0 $?

  echo "SELFTEST $([ "$red" -eq 0 ] && echo GREEN || echo RED)"
  return "$red"
}

case "${1:-}" in
  --selftest) selftest; exit $? ;;
  ""|-h|--help)
    sed -n '2,12p' "$0" >&2
    exit 64 ;;
esac
case "${2:-}" in
  ""|--dry-run) ;;
  *) fatal "unknown flag: $2" ;;
esac
run_worker "$1" "$([ "${2:-}" = --dry-run ] && echo dry-run || echo full)"
