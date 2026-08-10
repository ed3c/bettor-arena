#!/bin/sh
# control_notebooklm_entry.sh — the CONTROL GROUP for the NotebookLM harvest loop.
#
#   sh loopctl/loopctl.sh notebooklm test [--live]
#
# The proof records which bytes a traversal covered. This runs the mechanism and
# asks whether it can DISAGREE — because a selftest that has only ever been seen
# printing GREEN is not known to be able to print anything else, and that is the
# entire value of the green.
#
# Every offline check is a PLANTED DEFECT applied to a copy of the committed
# workflow.py inside a disposable worktree at HEAD. The live tree is never
# edited. Each plant removes exactly one guard that a real failure hid behind,
# and the selftest must go RED for it:
#
#   1. the pure-JSON refusal        — measured: a partial id makes the upstream
#                                     CLI prepend `Matched: ...` before the JSON
#   2. the ASCII-boundary regex     — measured: Python's \b drops every Chinese
#                                     AI title, which looks like an empty notebook
#   3. the scratch-notebook cleanup — a failed follow must still delete it
#   4. the empty-link-set refusal   — an empty set compares equal to anything
#
# Plus three properties that need no plant: the harness must go GREEN unplanted
# (a control that only ever fails proves nothing), an absent binary must exit 64
# rather than 2, and loopctl must refuse a flag the contract does not declare.
#
# All of it is OFFLINE. The one arm that needs the real Google account is
# `--live`, and without it that arm prints NOT EXERCISED by name — which is not
# a pass. Defaulting it on would make a control group that cannot run without
# somebody's cookies, and a control nobody can run is a control nobody runs.
#
# Exit: 0 every planted defect caught and every honest case passed
#       2 the mechanism missed something it must catch
#       64 FATAL (no worktree, no entry point at HEAD to test against)
set -u

CAPTURE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$CAPTURE_HOME/lib/capture.sh"
capture_init notebooklm-entry
ROOT=$CAPTURE_ROOT

BASE=$(mktemp -d "${TMPDIR:-/tmp}/control-notebooklm.XXXXXX")
WT="$BASE/repo"
cleanup() { git -C "$ROOT" worktree remove --force "$WT" >/dev/null 2>&1; }
trap cleanup EXIT
git -C "$ROOT" worktree add --detach "$WT" HEAD >/dev/null 2>&1 || {
  echo "control FATAL: could not create the worktree — the planted defects would have to go in the live tree" >&2
  exit 64; }
ENTRY="$WT/notebooklm/workflow.py"
[ -f "$ENTRY" ] || {
  echo "control FATAL: no notebooklm/workflow.py at HEAD — there is no committed mechanism to plant into." >&2
  echo "               This control tests what is COMMITTED, so a red here before the first commit is honest." >&2
  exit 64; }

RED=0
expect() { # name got want
  if [ "$2" = "$3" ]; then
    echo "  [ok]   $1 — $2"
  else
    echo "  [RED]  $1 — got $2, want $3" >&2
    RED=1
  fi
}

# --- 0. positive control: unplanted, the selftest must be green --------------
# Without this every red below could just mean the harness is broken for an
# unrelated reason, and each plant would look like it was caught.
CAPTURE_CWD="$WT"
capture selftest-unplanted -- python3 "$ENTRY" --selftest
BASE_RC=$?
CAPTURE_CWD=""
expect "unplanted-selftest-is-green" "$BASE_RC" 0

# --- 1-4. one guard removed at a time ----------------------------------------
# Applied by python rather than sed: BSD sed has no \| alternation and its
# escaping differs from GNU's, and a plant that silently fails to apply leaves
# the case testing the unmodified file — which reads as GREEN and means nothing.
# So each plant ASSERTS its anchor was found before the case is allowed to run.
plant() { # id anchor replacement
  python3 - "$ENTRY" "$BASE/planted.py" "$2" "$3" <<'PY'
import pathlib, sys
src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
anchor, repl = sys.argv[3], sys.argv[4]
if anchor not in src:
    print("ANCHOR-NOT-FOUND", file=sys.stderr)
    raise SystemExit(3)
pathlib.Path(sys.argv[2]).write_text(src.replace(anchor, repl, 1), encoding="utf-8")
PY
  _prc=$?
  if [ "$_prc" -ne 0 ]; then
    echo "  [RED]  $1 — the plant did not apply (anchor gone); an unapplied plant tests the unmodified file and always looks caught" >&2
    RED=1
    return 1
  fi
  return 0
}

run_planted() { # id
  CAPTURE_CWD="$WT"
  capture "planted-$1" -- python3 "$BASE/planted.py" --selftest
  _rc=$?
  CAPTURE_CWD=""
  # 0 means the removed guard was never being checked. Anything non-zero means
  # the instrument noticed, which is the whole property under test.
  if [ "$_rc" -eq 0 ]; then expect "planted-$1-goes-red" green red
  else expect "planted-$1-goes-red" red red; fi
}

if plant pure-json 'if not head.startswith(("{", "[")):' 'if False:'; then
  run_planted pure-json
fi
if plant ascii-boundary \
  'r"(?<![A-Za-z])(?:AI|LLM|GPT|RAG|ML)(?![A-Za-z])"' \
  'r"\b(?:AI|LLM|GPT|RAG|ML)\b"'; then
  run_planted ascii-boundary
fi
if plant scratch-cleanup \
  '    finally:
        _run([BIN,' \
  '    except BaseException:
        raise
    else:
        _run([BIN,'; then
  run_planted scratch-cleanup
fi
if plant empty-link-set \
  '        raise Red(
            "no-doc-urls: --follow was requested' \
  '        pass
    if False:
        raise Red(
            "no-doc-urls: --follow was requested'; then
  run_planted empty-link-set
fi
# 5. "the library is not installed" and "Drive refused this document" are
#    repaired in completely different places, so collapsing them must go red.
if plant library-vs-refusal '        if rc == 3:' '        if False:'; then
  run_planted library-vs-refusal
fi
# 6. the drive helper's stdout gets the same purity rule as the CLI's.
if plant drive-json-purity '        if not head.startswith("{"):' '        if False:'; then
  run_planted drive-json-purity
fi

# --- 5. absent tool must be 64, never 2 --------------------------------------
# The two absences are repaired at different layers (install vs re-authenticate),
# so a run that cannot tell them apart sends the repair to the wrong place.
#
# The emptied PATH goes through `env` and reaches ONLY the interpreter, hence
# the absolute python3. Writing `PATH=/nonexistent capture ...` instead looks
# like a one-command prefix and is not: a variable assignment before a shell
# FUNCTION persists in the calling shell afterwards, so it emptied PATH for
# capture.sh's own basename/sha256sum/cut and for every later case, which
# arrived as exit 127 in two places and read like two broken mechanisms.
PY3=$(command -v python3) || { echo "control FATAL: no python3 on PATH" >&2; exit 64; }
CAPTURE_CWD="$WT"
capture absent-binary -- env PATH=/nonexistent "$PY3" "$ENTRY" run \
  --notebook-title "control-absent-tool" --out "$BASE/absent"
ABSENT_RC=$?
CAPTURE_CWD=""
expect "absent-binary-is-64-not-2" "$ABSENT_RC" 64

# --- 6. the CLI must refuse what the contract does not declare ----------------
# Forwarding an unknown flag is how a caller starts depending on the target's
# private switches, which is the drift loopctl exists to stop.
CAPTURE_CWD="$WT"
capture undeclared-flag -- sh "$WT/loopctl/loopctl.sh" notebooklm run \
  --notebook-title x --sneaky
SNEAKY_RC=$?
CAPTURE_CWD=""
expect "undeclared-flag-refused" "$SNEAKY_RC" 64

# --- 7. missing subject must be refused before the account is touched ---------
CAPTURE_CWD="$WT"
capture no-subject -- python3 "$ENTRY" run --out "$BASE/nosubject"
NOSUBJ_RC=$?
CAPTURE_CWD=""
expect "neither-target-nor-title-is-64" "$NOSUBJ_RC" 64

# --- 8. the registry's pins must name notebooks, offline ----------------------
# A registry whose targets point at notebooks it does not itself declare would
# make every pin check silently vacuous, and a vacuous check reads as a passing one.
CAPTURE_CWD="$WT"
capture registry-is-coherent -- python3 -c '
import json, sys
reg = json.load(open(sys.argv[1], encoding="utf-8"))
titles = {n["title"] for n in reg["notebooks"]}
targets = reg["targets"]
assert targets, "registry declares no targets; an empty set satisfies anything"
assert titles, "registry declares no notebooks; every pin check would be vacuous"
missing = [t["name"] for t in targets if t["notebook_title"] not in titles]
assert not missing, f"targets name undeclared notebooks: {missing}"
print(f"{len(targets)} target(s), {len(titles)} pinned notebook(s)")
' "$WT/notebooklm/registry.json"
REG_RC=$?
CAPTURE_CWD=""
expect "registry-targets-are-pinned" "$REG_RC" 0

# --- 8b. hop 2 must not regress to the anonymous URL path ---------------------
# A STATIC arrival, deliberately independent of the runs above: the planted
# defects all exercise stage_follow's error handling, and none of them would
# notice if `source add <url>` came back as the mechanism. That regression is
# invisible while the account happens to hold public documents and fails for
# everyone else — which is exactly the shape that made this path necessary
# (every linked document answers 401 to an anonymous fetch; a nonexistent id
# answers 404, which is how "gated" was told apart from "not there").
CAPTURE_CWD="$WT"
capture hop2-not-anonymous -- "$PY3" -c '
import re, sys
src = open(sys.argv[1], encoding="utf-8").read()
body = src.split("def stage_follow(", 1)
assert len(body) == 2, "stage_follow is gone; this assertion is now vacuous"
body = body[1].split("\ndef ", 1)[0]
assert "drive" in body.lower(), "stage_follow no longer mentions the Drive path"
bad = re.search(r"\"source\",\s*\"add\"", body)
assert not bad, "stage_follow is back on the CLI source-add path, which is an ANONYMOUS fetch and cannot reach a signed-in-only document"
print("hop2 goes by Drive file id, not by anonymous URL ingestion")
' "$ENTRY"
STATIC_RC=$?
CAPTURE_CWD=""
expect "hop2-is-not-anonymous-url-ingestion" "$STATIC_RC" 0

# --- 9. the live arm, opt-in --------------------------------------------------
if [ "${CONTROL_NOTEBOOKLM_LIVE:-0}" = "1" ]; then
  # Read-only by construction: --dry-run stops before the first fetch, so this
  # spends a real auth turn and a real notebook resolution and writes nothing.
  CAPTURE_CWD="$WT"
  capture live-dry-run -- python3 "$ENTRY" run --target ai-monetization \
    --dry-run --out "$BASE/live"
  LIVE_RC=$?
  CAPTURE_CWD=""
  expect "live-dry-run-resolves-the-pinned-notebook" "$LIVE_RC" 0
  if [ -f "$BASE/live/module.json" ]; then
    grep -q '"pin_checked": true' "$BASE/live/module.json" && PINNED=yes || PINNED=no
    expect "live-run-checked-the-registry-pin" "$PINNED" yes
  else
    expect "live-run-wrote-a-receipt" no yes
  fi
else
  echo "  [note] live arm NOT EXERCISED — needs the signed-in Google account."
  echo "         Run \`sh loopctl/loopctl.sh notebooklm test --live\` to cover it."
  echo "         NOT EXERCISED is not a pass; nothing below reads it as one."
fi

echo "control[notebooklm-entry] trace=proof_workflow/data/$RUN_ID"
if [ "$RED" -eq 0 ]; then
  echo "PASS: the harvest loop caught every planted defect and passed every honest case"
  exit 0
fi
echo "FAIL: the harvest loop missed something it must catch — fix the mechanism, not the instrument" >&2
exit 2
