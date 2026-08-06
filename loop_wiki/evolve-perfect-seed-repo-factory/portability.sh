#!/bin/sh
# portability.sh — prove this factory is a relocatable asset, not a tree that only works here.
#
# Deliberately NOT part of verify.sh: verify.sh is the per-iteration T0 hot path and this pays
# for a clean `bun install`. verify.sh only asserts that this file exists, so it cannot quietly
# disappear; running it is an explicit human/CI act.
#
# What "relocatable" is allowed to mean here: what HEAD carries, extracted anywhere, installed
# from its own lockfile, passes its own T0. It says nothing about an uncommitted working tree --
# hence the dirty-tree refusal below.
#
# Usage: sh portability.sh
# exit 0  = portable, receipt written
# exit 2  = a stage produced the wrong verdict (including a negative control that failed to fail)
# exit 64 = usage/precondition problem (not in a repo, dirty subtree, missing tooling)

set -eu

ROOT=$(cd "$(dirname "$0")" && pwd -P)
RECEIPT="$ROOT/_engine-run/portability-receipt.json"

die64() { echo "portability: $*" >&2; exit 64; }
die2() { echo "portability: $*" >&2; exit 2; }

command -v git >/dev/null 2>&1 || die64 "git not found"
command -v bun >/dev/null 2>&1 || die64 "bun not found"
command -v tar >/dev/null 2>&1 || die64 "tar not found"

git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1 || die64 "not inside a Git repository: $ROOT"

# Path of this loop relative to whatever repository root it currently sits under. Resolved, not
# hardcoded -- the point of the exercise is that this file makes no assumption about its depth.
PREFIX=$(git -C "$ROOT" rev-parse --show-prefix)
PREFIX=${PREFIX%/}
[ -n "$PREFIX" ] || die64 "this loop is the repository root; nothing to extract as a subtree"

# `git archive` run from a subdirectory silently applies that subdirectory as an implicit
# pathspec on top of the tree-ish, so `HEAD:<prefix>` from inside the loop yields an empty
# archive rather than an error. Drive it from the top level instead.
TOPLEVEL=$(git -C "$ROOT" rev-parse --show-toplevel)

# `git archive HEAD:` reads HEAD, not the working tree. A dirty subtree would make a green run a
# statement about a commit nobody is looking at. Refuse instead of silently proving the wrong tree.
DIRTY=$(git -C "$ROOT" status --porcelain -- "$ROOT")
[ -z "$DIRTY" ] || {
  echo "portability: subtree is dirty; commit first or the proof measures HEAD, not your tree" >&2
  printf '%s\n' "$DIRTY" >&2
  exit 64
}

TMP=$(mktemp -d "${TMPDIR:-/tmp}/perfect-seed-portability.XXXXXX")
trap 'rm -rf "$TMP"' EXIT
DEST="$TMP/factory"
mkdir -p "$DEST"

# Not piped: `set -e` in POSIX sh ignores the exit status of everything but the last stage, so a
# failing `git archive` would hand tar an empty stream and read as success.
git -C "$TOPLEVEL" archive "HEAD:$PREFIX" >"$TMP/subtree.tar" || die2 "git archive failed for HEAD:$PREFIX"
tar -xf "$TMP/subtree.tar" -C "$DEST" || die2 "tar extraction failed"
[ -f "$DEST/verify.sh" ] || die2 "extracted tree has no verify.sh; HEAD does not carry this loop"

run_verify() {
  ( cd "$DEST" && sh ./verify.sh >"$TMP/$1.out" 2>&1 ) && echo 0 || echo $?
}

# --- Negative control 1: the archive must NOT ship its dependencies -------------------------
# Non-tautological: if HEAD ever started carrying node_modules, or if verify.sh stopped needing a
# real install, this would go green and the "clean install buys the green" claim would be hollow.
[ -d "$DEST/node_modules" ] && die2 "HEAD carries node_modules; the install step proves nothing"
PRE_INSTALL_RC=$(run_verify pre-install)
[ "$PRE_INSTALL_RC" -ne 0 ] || die2 "verify.sh passed before bun install; the green is not bought by the archive"

# --- Positive control: clean install, own T0 ------------------------------------------------
( cd "$DEST" && bun install --frozen-lockfile >"$TMP/install.out" 2>&1 ) || {
  echo "portability: bun install --frozen-lockfile failed" >&2
  cat "$TMP/install.out" >&2
  exit 2
}
INSTALLED_RC=$(run_verify installed)
[ "$INSTALLED_RC" -eq 0 ] || {
  echo "portability: verify.sh failed in the extracted tree (exit $INSTALLED_RC)" >&2
  cat "$TMP/installed.out" >&2
  exit 2
}

# --- Negative control 2: the instrument must be able to go red ------------------------------
# A green verifier is only evidence if it is demonstrably capable of failing. Remove one file
# verify.sh:7 declares required and require its own contract exit code back.
rm "$DEST/tsconfig.json"
MUTILATED_RC=$(run_verify mutilated)
[ "$MUTILATED_RC" -eq 2 ] || die2 "removing a required contract file did not produce exit 2 (got $MUTILATED_RC)"

# No control for "resolves node_modules upward to a host project": run_fast_quality.ts invokes
# ./node_modules/.bin/{prettier,eslint,tsc} by explicit relative path with cwd=ROOT, so there is
# no upward resolution to exercise. Asserting it does not happen would be a tautology, not a
# mitigation. If those stages ever move to bare command names, add the control then.

mkdir -p "$(dirname "$RECEIPT")"
cat >"$RECEIPT" <<EOF
{
  "schema_version": "perfect-seed-portability-receipt@1.0.0",
  "status": "passed",
  "measured_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "source_commit": "$(git -C "$ROOT" rev-parse HEAD)",
  "source_prefix": "$PREFIX",
  "mechanism": "git archive HEAD:<prefix> | tar -x; bun install --frozen-lockfile; sh verify.sh",
  "stages": [
    { "id": "archive-ships-no-node-modules", "kind": "negative-control", "expected": "absent", "observed": "absent" },
    { "id": "verify-before-install", "kind": "negative-control", "expected_nonzero": true, "exit_code": $PRE_INSTALL_RC },
    { "id": "verify-after-clean-install", "kind": "positive-control", "expected": 0, "exit_code": $INSTALLED_RC },
    { "id": "verify-without-required-tsconfig", "kind": "negative-control", "expected": 2, "exit_code": $MUTILATED_RC }
  ],
  "claim_boundary": "relocatability-of-HEAD-only-not-of-the-working-tree",
  "human_gate": "not_required"
}
EOF

echo "PASS: portable — pre-install=$PRE_INSTALL_RC installed=$INSTALLED_RC mutilated=$MUTILATED_RC receipt=$RECEIPT"
