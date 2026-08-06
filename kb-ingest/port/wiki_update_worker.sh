#!/usr/bin/env bash
# wiki_update_worker.sh — digestion station for wiki-update requests (ISSUE-23).
#
#   wiki_update_worker.sh <request.json> --dry-run   # deterministic chain proof
#   wiki_update_worker.sh <request.json>             # real run: LLM regenerate ->
#                                                    # real gates -> live finalize
#   wiki_update_worker.sh --selftest                 # fixture-driven good/broken proof
#
# Reads one request emitted by the factory delivery terminus
# (loop_wiki/evolve-perfect-seed-repo-factory/trigger.sh), then walks the
# official update pipeline: parse -> preflight -> LLM regenerate (claude -p,
# official update prompts, model pinned sonnet, writes gated to openwiki/) ->
# review gates (openwiki_subagent.sh: delta-scoped finder + verifier batches,
# every verdict must be PASS) -> post passes (openwiki_post.py migrate +
# finalize on the live wiki, .last-update.json gitHead asserted) -> receipt
# back-linking the request id into data/wiki-update/.
#
# --dry-run exercises every deterministic seam with the REAL components:
#   - the LLM segment is skipped by name (no model turn);
#   - gates run under OPENWIKI_DRY_RUN (sandbox assembly + shape assertions);
#     critic is recorded "skipped-no-skeleton" when the update flow has no
#     _skeleton.md — a named absence, not a silent pass;
#   - post passes run against a scratch COPY of openwiki/; the live wiki is
#     byte-compared before/after and any mutation fails loud.
#
# Env: WIKI_WORKER_ROOT — override the arena root (selftest fixtures only).
#      WIKI_UPDATE_CLAUDE_BIN — claude binary override (selftest seam).
# Exit: 0 ok · 2 contract fail (incl. red gates / boundary strays) ·
#       64 FATAL (absent input/tool, receipt collision)
# This script needs bash (process substitution in the write-boundary gate);
# invoked as `sh worker.sh`, POSIX sh would silently neuter that gate — the
# guard below re-execs into bash instead of running degraded.
[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@"
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SCHEMA="bettor-arena-wiki-update-request@1.0.0"
RECEIPT_SCHEMA="bettor-arena-wiki-update-receipt@1.0.0"
# WIKI_UPDATE_CLAUDE_BIN — selftest seam (same convention as driver_smoke.sh).
CLAUDE_BIN="${WIKI_UPDATE_CLAUDE_BIN:-claude}"

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

  # -- stage 3: LLM regeneration (official update mode, host-native) ----------
  # dry-run: skipped by name — the deterministic chain proof spends no model
  # turn. Real run: claude -p drives the official update prompts (system =
  # update.system.md official text + host-runtime.md adapter appendix; user =
  # user.update.md with the request's delta as runtime context). Model is
  # pinned (tier-dispatch: sonnet authors). Pages may change ONLY under
  # openwiki/ — a git-status boundary GATE after the run, not a promise.
  local regenerate_state
  if [ "$mode" = dry-run ]; then
    regenerate_state="skipped-dry-run"
    echo "[dry-run] LLM regeneration skipped by name (no model turn)"
  else
    command -v "$CLAUDE_BIN" >/dev/null 2>&1 \
      || fatal "claude CLI absent ($CLAUDE_BIN) — LLM regeneration cannot run"
    local prompts regen_rc dirty_before dirty_after new_changes stray wiki_changed
    prompts=$(mktemp -d "${TMPDIR:-/tmp}/wiki-update-regen.XXXXXX")
    python3 - "$root" "$request" "$prompts" <<'PY' || { rm -rf "$prompts"; fail "prompt composition failed"; }
import json, re, sys
from pathlib import Path

root, request, outdir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
req = json.loads(request.read_text(encoding="utf-8"))

def official(rel):
    text = (root / rel).read_text(encoding="utf-8")
    m = re.search(r"<!-- OPENWIKI-OFFICIAL:BEGIN -->\n(.*)\n<!-- OPENWIKI-OFFICIAL:END -->",
                  text, re.S)
    # Fixture stubs carry no markers; the whole file is then the prompt. A real
    # asset without markers would have failed sync_prompts --check long before.
    return m.group(1) if m else text

adapter = (root / "kb-ingest/port/host-runtime.md").read_text(encoding="utf-8")
(outdir / "system.md").write_text(
    official("kb-ingest/openwiki/update.system.md") + "\n\n---\n\n" + adapter,
    encoding="utf-8")

goal_file = root / "openwiki/INSTRUCTIONS.md"
goal = (goal_file.read_text(encoding="utf-8").strip() if goal_file.is_file()
        else "Keep this repository's openwiki knowledge base accurate and useful "
             "for humans and future agents.")
delta = req["iteration_auto_context"]
changed = "\n".join(f"- {p}" for p in delta.get("changed_files", [])) or "- (none listed)"
runtime = (
    f"Factory delivery context (request {req['request_id']}):\n"
    f"- route_result: {req['route_result']['path']}\n"
    f"- last documented gitHead: {delta.get('last_update_git_head')}\n"
    f"- delta_status: {delta['delta_status']}\n"
    f"- changed files since the last documented gitHead:\n{changed}\n"
    f"- emergent backlog pointer: {req.get('emergent_prompt_context')}\n")
user = official("kb-ingest/openwiki/user.update.md")
user = user.replace("{WIKI_GOAL}", goal)
user = user.replace("{ADDITIONAL_USER_REQUEST}", "")
user = user.replace("{RUNTIME_CONTEXT}", runtime)
(outdir / "user.md").write_text(user, encoding="utf-8")
PY
    dirty_before=$(git -C "$root" status --porcelain | sort)
    # Authorization rides CLI flags per loop_wiki convention (acceptEdits +
    # wiki dir); read-only git/rg allowlist mirrors openwiki_subagent.sh so the
    # official prompt's git-evidence path works without a blanket Bash grant.
    ( cd "$root" && "$CLAUDE_BIN" -p "$(cat "$prompts/user.md")" \
        --system-prompt "$(cat "$prompts/system.md")" \
        --model sonnet \
        --permission-mode acceptEdits --add-dir "$root/openwiki" \
        --allowedTools 'Bash(git log:*)' 'Bash(git show:*)' 'Bash(git diff:*)' \
          'Bash(git rev-parse:*)' 'Bash(rg:*)' 'Bash(ls:*)' \
        --output-format json < /dev/null >"$prompts/regen.json" 2>"$prompts/regen.err" )
    regen_rc=$?
    if [ "$regen_rc" -ne 0 ]; then
      tail -5 "$prompts/regen.err" >&2
      rm -rf "$prompts"
      fail "LLM regeneration run failed (exit $regen_rc)"
    fi
    dirty_after=$(git -C "$root" status --porcelain | sort)
    # porcelain v1 = 2 status chars + space + path; cut -c4- yields the path.
    new_changes=$(comm -13 <(printf '%s\n' "$dirty_before") <(printf '%s\n' "$dirty_after") | cut -c4-)
    stray=$(printf '%s\n' "$new_changes" | grep -v -e '^$' -e '^openwiki/' || true)
    if [ -n "$stray" ]; then
      rm -rf "$prompts"
      fail "LLM regeneration strayed outside openwiki/: $(echo "$stray" | tr '\n' ' ')"
    fi
    wiki_changed=$(printf '%s\n' "$new_changes" | grep -c '^openwiki/' || true)
    # Preserve the run transcript in the (gitignored) wiki-update ledger AFTER
    # the boundary snapshot, so the log itself never reads as a stray write.
    mkdir -p "$root/data/wiki-update"
    mv "$prompts/regen.json" "$root/data/wiki-update/regen-$packet_id.json"
    rm -rf "$prompts"
    regenerate_state="ran:model=sonnet,changed=$wiki_changed"
    echo "[regenerate] model=sonnet changed_wiki_paths=$wiki_changed transcript=data/wiki-update/regen-$packet_id.json"
  fi

  # -- stage 4: review gates via the real runner ------------------------------
  # dry-run: sandbox assembly + shape assertions only (OPENWIKI_DRY_RUN).
  # Real run: finder generates delta-scoped questions from source (no wiki in
  # its sandbox), verifier answers them from the wiki alone in batches of <=3;
  # any verdict that is not PASS is a red gate with the findings printed, so
  # the caller can repair the named pages and rerun. Critic belongs to the
  # init flow: an update run has no _skeleton.md, and that absence is named.
  local payload gate_finder gate_verifier gate_critic
  if [ "$mode" = dry-run ]; then
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
  else
    [ ! -f "$root/openwiki/_skeleton.md" ] \
      || fail "unexpected _skeleton.md in an update flow — finish or clean the init run first"
    gate_critic="skipped-no-skeleton"
    payload=$(mktemp "${TMPDIR:-/tmp}/wiki-update-payload.XXXXXX")
    {
      echo "Maintenance update verification for $request_id."
      echo "The wiki was just updated for repository changes since the last documented gitHead."
      echo "Focus the question set on source areas touched by these changed files:"
      python3 -c 'import json,sys; [print("-", p) for p in json.load(open(sys.argv[1]))["iteration_auto_context"]["changed_files"]]' "$request"
      echo "Generate the question set per your instructions."
    } >"$payload"
    local finder_out finder_review batches_dir n_batches i batch_rc red_questions
    finder_out=$(OPENWIKI_HOST=claude "$HERE/openwiki_subagent.sh" finder "$root" "$payload")
    gate_finder=$?
    rm -f "$payload"
    finder_review=$(printf '%s\n' "$finder_out" | tail -1)
    { [ "$gate_finder" -eq 0 ] && [ -s "$finder_review" ]; } \
      || fail "finder gate failed (exit $gate_finder)"
    batches_dir=$(mktemp -d "${TMPDIR:-/tmp}/wiki-update-batches.XXXXXX")
    n_batches=$(python3 - "$finder_review" "$batches_dir" <<'PY'
import re, sys
from pathlib import Path
text = Path(sys.argv[1]).read_text(encoding="utf-8")
outdir = Path(sys.argv[2])
starts = [m.start() for m in re.finditer(r"^\[Q-\d+\]:", text, re.M)]
blocks = [text[a:b].strip() for a, b in zip(starts, starts[1:] + [len(text)])]
for i in range(0, len(blocks), 3):
    (outdir / f"batch-{i // 3 + 1}.txt").write_text(
        "Verify the following questions against the wiki:\n\n"
        + "\n\n".join(blocks[i:i + 3]) + "\n", encoding="utf-8")
print((len(blocks) + 2) // 3)
PY
) || { rm -rf "$batches_dir"; fail "finder output parsing failed"; }
    [ "$n_batches" -gt 0 ] || { rm -rf "$batches_dir"; fail "finder returned no [Q-NN] questions: $finder_review"; }
    gate_verifier=0
    for i in $(seq 1 "$n_batches"); do
      OPENWIKI_HOST=claude OPENWIKI_LABEL="b$i" \
        "$HERE/openwiki_subagent.sh" verifier "$root" "$batches_dir/batch-$i.txt" >/dev/null
      batch_rc=$?
      [ "$batch_rc" -eq 0 ] || { echo "verifier batch $i run failed (exit $batch_rc)" >&2; gate_verifier=$batch_rc; }
    done
    rm -rf "$batches_dir"
    [ "$gate_verifier" -eq 0 ] || fail "verifier gate run failed (exit $gate_verifier)"
    # Verdict judgement: every result must be PASS; a missing or shapeless
    # review is a FAIL of its own, never an implicit green.
    red_questions=$(python3 - "$root" "$n_batches" <<'PY'
import re, sys
from pathlib import Path
root, n = Path(sys.argv[1]), int(sys.argv[2])
red = []
for i in range(1, n + 1):
    path = root / ".openwiki-review" / f"verifier-b{i}-latest.txt"
    if not path.is_file():
        print(f"FAIL: missing verifier output {path}", file=sys.stderr); sys.exit(2)
    text = path.read_text(encoding="utf-8")
    results = re.findall(
        r'<result id="(Q-\d+)" status="(\w+)">\s*<missing>(.*?)</missing>', text, re.S)
    if not results:
        print(f"FAIL: no <result> blocks in {path}", file=sys.stderr); sys.exit(2)
    for qid, status, missing in results:
        if status != "PASS":
            red.append(f"[b{i}] {qid} {status}: {' '.join(missing.split())}")
print("\n".join(red))
PY
) || fail "verifier verdict parsing failed"
    if [ -n "$red_questions" ]; then
      printf '%s\n' "$red_questions" >&2
      fail "verifier gate RED — repair the named pages per the findings above, then rerun"
    fi
  fi
  echo "[gates] finder=$gate_finder verifier=$gate_verifier critic=$gate_critic"

  # -- stage 5: official post passes ------------------------------------------
  # dry-run: on a scratch copy, live wiki byte-compared untouched. Real run:
  # on the LIVE wiki — finalize rewrites .last-update.json with the current
  # gitHead, asserted before announcing.
  local scratch post_migrate post_finalize
  if [ "$mode" = dry-run ]; then
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
  else
    python3 "$HERE/openwiki_post.py" migrate "$root/openwiki" >/dev/null
    post_migrate=$?
    python3 "$HERE/openwiki_post.py" finalize "$root/openwiki" --target "$root" \
      --command update --model "claude-code+sonnet" --status success --normalize-backlog >/dev/null
    post_finalize=$?
    [ "$post_migrate" -eq 0 ] || fail "openwiki_post migrate failed (exit $post_migrate)"
    [ "$post_finalize" -eq 0 ] || fail "openwiki_post finalize failed (exit $post_finalize)"
    # Upstream removes the temporary plan file after the run; mirror that here.
    rm -f "$root/openwiki/_plan.md"
    local head recorded
    head=$(git -C "$root" rev-parse HEAD)
    recorded=$(sed -n 's/.*"gitHead": *"\([0-9a-f]\{40\}\)".*/\1/p' "$root/openwiki/.last-update.json" | head -1)
    [ "$recorded" = "$head" ] || fail ".last-update.json gitHead ${recorded:-absent} != HEAD $head"
    echo "[post] migrate=$post_migrate finalize=$post_finalize gitHead=$recorded"
  fi

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
  local base fixture request rc red=0 err fake
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
  # Real-run negative controls for the wired LLM segment — both die before any
  # model turn, so the selftest stays deterministic.
  # 1) absent claude is a NAMED FATAL 64 (tool absence, not a TODO).
  err=$( (WIKI_WORKER_ROOT="$fixture" WIKI_UPDATE_CLAUDE_BIN=/nonexistent/host-cli "$0" "$request") 2>&1 >/dev/null )
  expect "real-run-absent-claude-is-fatal-64" 64 $?
  if ! echo "$err" | grep -q "claude CLI absent"; then
    echo "SELFTEST case failed — absent-claude does not name the missing tool: $err" >&2; red=1
  fi
  # 2) a regeneration that strays outside openwiki/ must FAIL 2, never pass.
  fake="$base/fake-claude"
  printf '#!/bin/sh\necho stray > stray.txt\nexit 0\n' >"$fake"
  chmod +x "$fake"
  (WIKI_WORKER_ROOT="$fixture" WIKI_UPDATE_CLAUDE_BIN="$fake" "$0" "$request") >/dev/null 2>&1
  expect "real-run-stray-write-is-fail-2" 2 $?
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
