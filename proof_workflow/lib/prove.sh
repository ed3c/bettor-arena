#!/bin/sh
# prove.sh — shared recorder for the proof_workflow traversal proofs.
#
# The contract-declared loop proofs each walk their own mechanism from its entry
# point to its terminal artifact. This file owns the one thing all of them must
# do identically: record every step, hash every file
# on the path, and fold those hashes into a single molecular digest that moves
# if any traversed byte moves.
#
# Step kinds — every step is exactly one of these, nothing else is recorded:
#   context  a document the PROBABILISTIC lane reads at this step (official
#            prompt, passive context, packet field). Hashed, never executed.
#            Absent = FATAL 64: a prompt that is not there cannot be the one
#            that ran.
#   harness  a DETERMINISTIC script on the path. With a `--` command it is
#            executed and its exit code recorded; without one it is hashed and
#            recorded state=hashed-not-run — for mutating entry points a proof
#            must not fire. hashed-not-run is a named absence of execution and
#            never counts as green (the summary counts it separately).
#   artifact terminal evidence the mechanism physically left behind. Absent =
#            named state `absent` + overall FAIL, never a silent pass.
#            Hashed at HEAD when the path is tracked (state present-at-head),
#            from the worktree only when it is not (present-untracked). That
#            split is not cosmetic: a harness step earlier in the same
#            traversal can rewrite a tracked artifact — the micro loop's
#            verify.sh rewrites packets/outbox/route-result.fixture-dr.json via
#            seed_factory.test.ts — and hashing the worktree there let the act
#            of measuring move the measurement, so two identical runs produced
#            two different digests. A tracked terminus belongs to the commit;
#            judge it there. Tracked-but-deleted-in-the-worktree is its own
#            named FAIL, so HEAD bytes can never cover for a local deletion.
#   optional a host asset the entry point tolerates the absence of — hashed as
#            present-optional when it is there, recorded absent-optional when it
#            is not, and never a failure either way. This kind exists because
#            `.grepai/index.gob` has no honest home in the others: artifact makes
#            its absence a red, context makes it a FATAL, and note drops it out
#            of the digest so its state stops being evidence at all. The obvious
#            abuse — call anything load-bearing "optional" and stay green — is
#            what the control group closes: it classifies by experiment, and the
#            comparator fails when something it measured as required is carried
#            here. Do not use this kind for anything the control has not measured.
#   note     something on the path that is deliberately NOT hashed, and why.
#            Bounding what a proof covers is fine; doing it silently is not —
#            a dropped path must read as dropped, never as covered.
#
# Caller shape:
#   PROVE_HOME=$(cd "$(dirname "$0")" && pwd -P); . "$PROVE_HOME/lib/prove.sh"
#   prove_init macro "bootstrap.sh -> .githooks/*"
#   prove_context claude-md CLAUDE.md "repo -> host session passive context"
#   prove_harness placement scripts/gates/check_placement.py "staged -> exit" \
#     -- python3 scripts/gates/check_placement.py --selftest
#   prove_artifact receipt data/receipts/x.json "post-commit -> ledger"
#   prove_emit
#
# Callers run under `set -u` only, deliberately NOT `set -e`: a traversal proof
# must finish the traversal and report every red, not abort on the first one.
# prove_emit is what carries the verdict out (0 pass / 2 fail).
#
# Receipt: data/proof-workflow/<loop>-<commit12>[-dirty].json. Collision =
# FATAL 64 unless PROVE_FORCE_RECEIPT=1 — receipts are frozen evidence
# (CONTEXT.md), so a rerun has to declare its intent. A dirty worktree hashes
# bytes HEAD does not carry, so the proof says so in the file name, in
# worktree_dirty, and in its claim boundary.
#
# Exit: 0 pass · 2 a step went red / a terminus is absent · 64 FATAL (absent
# context or harness script, receipt collision, not a git work tree).
#
# Cheap verification surface:  sh proof_workflow/lib/prove.sh --selftest
# Negative controls for the instrument itself — a red step must land red, a
# changed byte must move the digest, an absent context must FATAL.

# ------------------------------------------------------------------ helpers

prove_sha256() {
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1
  else sha256sum "$1" | cut -d' ' -f1; fi
}

prove_sha256_stdin() {
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 | cut -d' ' -f1
  else sha256sum | cut -d' ' -f1; fi
}

prove_fatal() { echo "prove FATAL: $*" >&2; exit 64; }

_prove_esc() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'; }

# Appends one step record. sha and exit arrive pre-formatted as JSON scalars
# so both can be `null` without a second code path.
_prove_record() { # kind id path sha exit state dataflow
  PROVE_SEQ=$((PROVE_SEQ + 1))
  printf '{"seq":%d,"kind":"%s","id":"%s","path":"%s","sha256":%s,"exit":%s,"state":"%s","dataflow":"%s"}\n' \
    "$PROVE_SEQ" "$1" "$2" "$(_prove_esc "$3")" "$4" "$5" "$6" "$(_prove_esc "$7")" \
    >>"$PROVE_TMP/steps"
}

# Hashes a repo-relative path into the molecular manifest and prints the sha as
# a quoted JSON scalar. Returns 1 (prints nothing) when the file is absent —
# every caller decides for itself what that absence means.
_prove_hash() {
  [ -f "$PROVE_ROOT/$1" ] || return 1
  _s=$(prove_sha256 "$PROVE_ROOT/$1")
  printf '%s  %s\n' "$_s" "$1" >>"$PROVE_TMP/manifest"
  printf '"%s"' "$_s"
}

# --------------------------------------------------------------------- API

prove_init() { # loop-id entry-point-description
  PROVE_LOOP=$1
  PROVE_ENTRY=$2
  PROVE_ROOT=$(git -C "${PROVE_HOME:?PROVE_HOME must be set before sourcing prove.sh}" \
    rev-parse --show-toplevel 2>/dev/null) \
    || prove_fatal "not inside a git work tree: $PROVE_HOME"
  PROVE_COMMIT=$(git -C "$PROVE_ROOT" rev-parse HEAD)
  PROVE_TREE=$(git -C "$PROVE_ROOT" rev-parse "HEAD^{tree}")
  # The receipt directory is excluded: it holds this tool's OWN output, and the
  # first proof of a run would otherwise make every later proof read the tree as
  # dirty — a clean stamp would be unreachable for all but one loop. Excluding it
  # weakens no claim, because nothing under it is ever hashed into a digest. Same
  # shape as bootstrap.sh excluding openwiki/ from its own staleness diff.
  if [ -n "$(git -C "$PROVE_ROOT" status --porcelain -- . ':(exclude)data/proof-workflow/')" ]; then
    PROVE_DIRTY=true
  else
    PROVE_DIRTY=false
  fi
  PROVE_TMP=$(mktemp -d "${TMPDIR:-/tmp}/proof-workflow.XXXXXX")
  trap 'rm -rf "$PROVE_TMP"' EXIT
  : >"$PROVE_TMP/steps"
  : >"$PROVE_TMP/manifest"
  PROVE_SEQ=0
  PROVE_RAN=0
  PROVE_NOTRUN=0
  PROVE_STATUS=passed
  echo "proof[$PROVE_LOOP] commit=$PROVE_COMMIT dirty=$PROVE_DIRTY"
  echo "proof[$PROVE_LOOP] entry: $PROVE_ENTRY"
}

prove_context() { # id repo-relative-path dataflow
  _sha=$(_prove_hash "$2") || prove_fatal \
    "context document absent: $2 ($1) — the probabilistic lane reads it at this step; an absent prompt cannot be the one that ran"
  _prove_record context "$1" "$2" "$_sha" null read "$3"
  echo "  [context ] $1 — $2"
}

prove_harness() { # id repo-relative-path|- dataflow [-- cmd...]
  _id=$1
  _path=$2
  _flow=$3
  shift 3
  if [ "$_path" = "-" ]; then
    _sha=null
  else
    _sha=$(_prove_hash "$_path") || prove_fatal "harness script absent: $_path ($_id)"
  fi
  if [ "${1:-}" != "--" ]; then
    PROVE_NOTRUN=$((PROVE_NOTRUN + 1))
    _prove_record harness "$_id" "$_path" "$_sha" null hashed-not-run "$_flow"
    echo "  [harness ] $_id — hashed-not-run — $_path"
    return 0
  fi
  shift
  ( cd "$PROVE_ROOT" && "$@" ) >"$PROVE_TMP/$_id.log" 2>&1
  _rc=$?
  PROVE_RAN=$((PROVE_RAN + 1))
  if [ "$_rc" -eq 0 ]; then
    _prove_record harness "$_id" "$_path" "$_sha" 0 ran "$_flow"
    echo "  [harness ] $_id — exit 0 — $_path"
  else
    _prove_record harness "$_id" "$_path" "$_sha" "$_rc" ran "$_flow"
    PROVE_STATUS=failed
    echo "  [harness ] $_id — exit $_rc RED — $_path" >&2
    tail -15 "$PROVE_TMP/$_id.log" | sed 's/^/             | /' >&2
  fi
  return 0
}

prove_artifact() { # id repo-relative-path dataflow
  if git -C "$PROVE_ROOT" cat-file -e "HEAD:$2" 2>/dev/null; then
    # Tracked: the commit owns this terminus, so judge its committed bytes. A
    # harness step in this same traversal may have rewritten the worktree copy.
    if [ ! -f "$PROVE_ROOT/$2" ]; then
      _prove_record artifact "$1" "$2" null null absent-in-worktree "$3"
      PROVE_STATUS=failed
      echo "  [artifact] $1 — ABSENT IN WORKTREE — $2 (tracked at HEAD, deleted locally)" >&2
      return 0
    fi
    _s=$(git -C "$PROVE_ROOT" cat-file blob "HEAD:$2" | prove_sha256_stdin)
    printf '%s  %s\n' "$_s" "$2" >>"$PROVE_TMP/manifest"
    _prove_record artifact "$1" "$2" "\"$_s\"" null present-at-head "$3"
    echo "  [artifact] $1 — present-at-head — $2"
  elif _sha=$(_prove_hash "$2"); then
    # Untracked terminus (a gitignored ledger entry): the worktree is the only
    # place it exists, and the receipt says so rather than implying HEAD carries it.
    _prove_record artifact "$1" "$2" "$_sha" null present-untracked "$3"
    echo "  [artifact] $1 — present-untracked — $2"
  else
    _prove_record artifact "$1" "$2" null null absent "$3"
    PROVE_STATUS=failed
    echo "  [artifact] $1 — ABSENT — $2 (the mechanism left no terminus here)" >&2
  fi
  return 0
}

prove_optional() { # id repo-relative-path dataflow
  if _sha=$(_prove_hash "$2"); then
    _prove_record optional "$1" "$2" "$_sha" null present-optional "$3"
    echo "  [optional] $1 — present-optional — $2"
  else
    # No hash, but the state is still recorded and still moves the digest by way
    # of the manifest staying one line shorter — absence is a fact about this
    # commit, not a gap in the record.
    _prove_record optional "$1" "$2" null null absent-optional "$3"
    echo "  [optional] $1 — absent-optional — $2 (tolerated; the entry point exits 0 without it)"
  fi
  return 0
}

prove_note() { # id [repo-relative-path-or-ledger] why-this-path-is-not-hashed
  # With two arguments the note is prose. With three, the middle one is the path
  # or ledger being excluded, and it lands in the receipt as a DECLARED exclusion
  # rather than as a sentence — which is what lets the control group tell "this
  # output is deliberately out of scope, here is why" apart from "nobody noticed
  # this output exists". The control honours the declaration for produced paths
  # only; a required input can never be declared away, or the kind would become a
  # way to stay green.
  PROVE_SEQ=$((PROVE_SEQ + 1))
  if [ "$#" -ge 3 ]; then
    printf '{"seq":%d,"kind":"note","id":"%s","path":"%s","sha256":null,"exit":null,"state":"excluded","dataflow":"%s"}\n' \
      "$PROVE_SEQ" "$1" "$(_prove_esc "$2")" "$(_prove_esc "$3")" >>"$PROVE_TMP/steps"
    echo "  [note    ] $1 — excluded — $2 — $3"
  else
    printf '{"seq":%d,"kind":"note","id":"%s","path":null,"sha256":null,"exit":null,"state":"excluded","dataflow":"%s"}\n' \
      "$PROVE_SEQ" "$1" "$(_prove_esc "$2")" >>"$PROVE_TMP/steps"
    echo "  [note    ] $1 — excluded — $2"
  fi
  return 0
}

prove_emit() {
  sort "$PROVE_TMP/manifest" >"$PROVE_TMP/manifest.sorted"
  _digest=$(prove_sha256 "$PROVE_TMP/manifest.sorted")
  _files=$(wc -l <"$PROVE_TMP/manifest.sorted" | tr -d ' ')
  _name="$PROVE_LOOP-$(printf %.12s "$PROVE_COMMIT")"
  [ "$PROVE_DIRTY" = true ] && _name="$_name-dirty"
  _dir="$PROVE_ROOT/data/proof-workflow"
  mkdir -p "$_dir"
  _receipt="$_dir/$_name.json"
  if [ -e "$_receipt" ] && [ "${PROVE_FORCE_RECEIPT:-0}" != "1" ]; then
    prove_fatal "receipt already exists: ${_receipt#"$PROVE_ROOT"/} — rerun with PROVE_FORCE_RECEIPT=1 to overwrite explicitly (receipts are frozen evidence)"
  fi
  _steps=$(awk 'NR>1{printf ","} {printf "%s", $0}' "$PROVE_TMP/steps")
  cat >"$_receipt" <<EOF
{
  "schema_version": "bettor-arena-proof-workflow-receipt@1.0.0",
  "loop": "$PROVE_LOOP",
  "entry_point": "$(_prove_esc "$PROVE_ENTRY")",
  "utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "$PROVE_STATUS",
  "commit": "$PROVE_COMMIT",
  "tree": "$PROVE_TREE",
  "worktree_dirty": $PROVE_DIRTY,
  "counts": { "steps": $PROVE_SEQ, "harness_ran": $PROVE_RAN, "harness_hashed_not_run": $PROVE_NOTRUN, "hashed_files": $_files },
  "molecular_hardening": {
    "algo": "sha256",
    "digest_input": "the sorted, LF-terminated '<sha256>  <repo-relative path>' lines of every context/harness/artifact file traversed below; context and harness bytes come from the worktree (that is what was read and what ran), tracked artifact bytes come from HEAD (state present-at-head) so a harness step cannot move its own evidence",
    "proof_digest": "$_digest"
  },
  "claim_boundary": "traversal-of-the-mechanism-at-this-commit-not-a-quality-axis-claim",
  "steps": [$_steps]
}
EOF
  # Assert before announcing: the receipt must exist and parse.
  [ -s "$_receipt" ] || prove_fatal "receipt missing after write: $_receipt"
  python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$_receipt" \
    || prove_fatal "receipt is not valid JSON: $_receipt"
  echo "proof[$PROVE_LOOP] digest=$_digest files=$_files receipt=${_receipt#"$PROVE_ROOT"/}"
  if [ "$PROVE_STATUS" = passed ]; then
    echo "PASS: $PROVE_LOOP traversal — $PROVE_RAN harness ran, $PROVE_NOTRUN hashed-not-run, $PROVE_SEQ steps at $PROVE_COMMIT"
    return 0
  fi
  echo "FAIL: $PROVE_LOOP traversal — see the RED steps above; receipt ${_receipt#"$PROVE_ROOT"/}" >&2
  return 2
}

# ------------------------------------------------------------------ selftest
# Sourced files never reach this: $0 is the caller's path when sourced, and
# only this file's own path ends in /lib/prove.sh.

_prove_selftest() {
  red=0
  # Hermetic against the caller's environment. PROVE_FORCE_RECEIPT inherited from
  # a parent turned the receipt-collision case green — the check kept running and
  # kept reporting, and only its VERDICT changed, which is worse than failing to
  # run. Surfaced the moment prove_harness.sh invoked this selftest under a
  # --force-receipt of its own. A selftest whose answer depends on who called it
  # is measuring the caller.
  unset PROVE_FORCE_RECEIPT
  expect() { # name want got
    [ "$3" = "$2" ] || { echo "SELFTEST case failed — $1: got $3, want $2" >&2; red=1; }
  }
  base=$(mktemp -d "${TMPDIR:-/tmp}/prove-selftest.XXXXXX")
  trap 'rm -rf "$base"' EXIT
  repo="$base/repo"
  mkdir -p "$repo"
  git -C "$repo" init -q -b main
  printf 'doc\n' >"$repo/doc.md"
  printf '#!/bin/sh\nexit 0\n' >"$repo/ok.sh"
  printf '#!/bin/sh\nexit 1\n' >"$repo/bad.sh"
  # A harness that rewrites the very file the artifact list hashes — the shape
  # that made the micro loop's digest drift between two identical runs.
  printf '#!/bin/sh\ncat "$0" >> terminus.json\nexit 0\n' >"$repo/bump.sh"
  printf '{}\n' >"$repo/terminus.json"
  # Receipts land under data/; leaving them untracked would make every case
  # after the first one read as a dirty tree and silently change the receipt
  # names the later cases assert on.
  printf 'data/\n' >"$repo/.gitignore"
  git -C "$repo" add -A
  git -C "$repo" -c user.email=t@t -c user.name=t commit -qm fixture
  sha12=$(git -C "$repo" rev-parse HEAD | cut -c1-12)
  digest_of() { grep -o '"proof_digest": "[0-9a-f]*"' "$1" | cut -d'"' -f4; }

  run_case() { # loop with-bad with-terminus
    (
      PROVE_HOME="$repo"
      prove_init "$1" "selftest fixture"
      prove_context doc doc.md "fixture -> reader"
      prove_harness ok ok.sh "fixture -> exit" -- sh ok.sh
      [ "$2" = 1 ] && prove_harness bad bad.sh "fixture -> exit" -- sh bad.sh
      [ "$3" = 1 ] && prove_artifact terminus terminus.json "fixture -> ledger"
      prove_emit
    ) >/dev/null 2>&1
  }

  # 1) positive control: clean traversal is green and writes a parseable receipt.
  run_case green 0 1; expect "green-run" 0 $?
  clean="$repo/data/proof-workflow/green-$sha12.json"
  [ -f "$clean" ] || { echo "SELFTEST case failed — green-run wrote no receipt" >&2; red=1; }
  grep -q '"status": "passed"' "$clean" 2>/dev/null || { echo "SELFTEST case failed — green receipt is not status=passed" >&2; red=1; }

  # 2) the instrument must go red when a traversed harness goes red.
  run_case red 1 1; expect "red-harness-step" 2 $?
  grep -q '"status": "failed"' "$repo/data/proof-workflow/red-$sha12.json" 2>/dev/null \
    || { echo "SELFTEST case failed — red run receipt is not status=failed" >&2; red=1; }

  # 3) receipts are frozen evidence: a second identical run must refuse, not
  #    silently rewrite the first one's verdict.
  run_case green 0 1; expect "receipt-collision-is-fatal-64" 64 $?

  # 4) an absent terminus is a named FAIL, never an implicit pass.
  run_case noterm 0 0
  rm -f "$repo/data/proof-workflow/noterm-$sha12"*.json
  ( PROVE_HOME="$repo"; prove_init noterm2 f
    prove_artifact gone missing.json "fixture -> nowhere"
    prove_emit ) >/dev/null 2>&1
  expect "absent-artifact-fails" 2 $?

  # 5) an absent context document is FATAL, not a skipped step.
  ( PROVE_HOME="$repo"; prove_init abs f; prove_context gone missing.md "x -> y" ) >/dev/null 2>&1
  expect "absent-context-is-fatal-64" 64 $?

  # 6) determinism under self-perturbation: a harness step that rewrites a
  #    tracked artifact must NOT move the digest, because tracked artifacts are
  #    judged at HEAD. Without this control the instrument can drift on its own,
  #    which is worth exactly nothing as hardening — and it did: two identical
  #    micro-loop runs produced two different digests before this was fixed.
  det_run() {
    (
      PROVE_HOME="$repo"
      prove_init "$1" "determinism fixture"
      prove_context doc doc.md "fixture -> reader"
      prove_harness bump bump.sh "fixture -> harness rewrites the tracked terminus" -- sh bump.sh
      prove_artifact terminus terminus.json "fixture -> ledger"
      prove_emit
    ) >/dev/null 2>&1
  }
  det_run det; expect "self-perturbing-run" 0 $?
  det1="$repo/data/proof-workflow/det-$sha12.json"
  # The second run starts on the tree the first one perturbed, hence -dirty.
  det_run det; expect "self-perturbing-rerun" 0 $?
  det2="$repo/data/proof-workflow/det-$sha12-dirty.json"
  if [ "$(digest_of "$det1")" != "$(digest_of "$det2" 2>/dev/null)" ]; then
    echo "SELFTEST case failed — digest drifted between two identical runs (a harness step is moving its own evidence)" >&2; red=1
  fi
  grep -q '"state":"present-at-head"' "$det1" 2>/dev/null \
    || { echo "SELFTEST case failed — tracked artifact was not judged at HEAD" >&2; red=1; }

  # 7) a tracked terminus deleted from the worktree must fail, never be covered
  #    for by its HEAD bytes. Deliberately NOT det_run: bump.sh recreates the
  #    file it appends to, which would repair the deletion before it is judged.
  mv "$repo/terminus.json" "$base/terminus.away"
  (
    PROVE_HOME="$repo"
    prove_init gone "deleted-terminus fixture"
    prove_artifact terminus terminus.json "fixture -> ledger"
    prove_emit
  ) >/dev/null 2>&1
  expect "tracked-terminus-deleted-locally" 2 $?
  mv "$base/terminus.away" "$repo/terminus.json"

  # 8) the optional kind: present is hashed and absent is recorded, and the two
  #    must not produce the same digest — an optional asset whose state cannot
  #    be read off the receipt is not covered, it is merely mentioned.
  printf 'idx\n' >"$repo/hostasset.bin"
  opt_run() {
    (
      PROVE_HOME="$repo"
      prove_init "$1" "optional fixture"
      prove_context doc doc.md "fixture -> reader"
      prove_optional asset hostasset.bin "host -> tolerated asset"
      prove_emit
    ) >/dev/null 2>&1
  }
  opt_run optpresent; expect "optional-present-is-green" 0 $?
  present_receipt="$repo/data/proof-workflow/optpresent-$sha12-dirty.json"
  grep -q '"state":"present-optional"' "$present_receipt" 2>/dev/null \
    || { echo "SELFTEST case failed — present optional asset not recorded as present-optional" >&2; red=1; }
  mv "$repo/hostasset.bin" "$base/hostasset.away"
  opt_run optabsent; expect "optional-absent-is-not-a-failure" 0 $?
  absent_receipt="$repo/data/proof-workflow/optabsent-$sha12-dirty.json"
  grep -q '"state":"absent-optional"' "$absent_receipt" 2>/dev/null \
    || { echo "SELFTEST case failed — absent optional asset not recorded as absent-optional" >&2; red=1; }
  if [ "$(digest_of "$present_receipt")" = "$(digest_of "$absent_receipt" 2>/dev/null)" ]; then
    echo "SELFTEST case failed — present and absent optional produced the same digest" >&2; red=1
  fi
  mv "$base/hostasset.away" "$repo/hostasset.bin"

  # 9) molecular hardening: one changed byte on the traversed path must move
  #    the digest, and the dirty tree must be visible in the receipt name.
  printf 'doc drifted\n' >"$repo/doc.md"
  run_case green 0 1; expect "dirty-rerun" 0 $?
  drifted="$repo/data/proof-workflow/green-$sha12-dirty.json"
  [ -f "$drifted" ] || { echo "SELFTEST case failed — dirty run did not land a -dirty receipt" >&2; red=1; }
  if [ "$(digest_of "$clean")" = "$(digest_of "$drifted" 2>/dev/null)" ]; then
    echo "SELFTEST case failed — planted byte did not move proof_digest" >&2; red=1
  fi
  grep -q '"worktree_dirty": true' "$drifted" 2>/dev/null \
    || { echo "SELFTEST case failed — dirty run does not record worktree_dirty" >&2; red=1; }

  echo "SELFTEST $([ "$red" = 0 ] && echo GREEN || echo RED)"
  return "$red"
}

case "$0" in
  */lib/prove.sh)
    case "${1:-}" in
      --selftest) _prove_selftest; exit $? ;;
      *) echo "usage: sh proof_workflow/lib/prove.sh --selftest  (otherwise this file is sourced)" >&2; exit 64 ;;
    esac
    ;;
esac
