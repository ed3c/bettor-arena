#!/bin/sh
# Seam: bootstrap.sh CLI exit codes + resulting git config, on an isolated copy.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
fail() { echo "FAIL: $1" >&2; exit 1; }

cp -R "$ROOT/scripts" "$TMP/scripts"
[ -d "$ROOT/.githooks" ] && cp -R "$ROOT/.githooks" "$TMP/.githooks" || mkdir "$TMP/.githooks"
cp "$ROOT/bootstrap.sh" "$TMP/bootstrap.sh" 2>/dev/null || fail "bootstrap.sh does not exist yet"
git -C "$TMP" init -q -b main

sh "$TMP/bootstrap.sh" || fail "first bootstrap run exited $?"
HP=$(git -C "$TMP" config core.hooksPath) || fail "hooksPath unset after bootstrap"
[ "$HP" = ".githooks" ] || fail "hooksPath is '$HP', want relative '.githooks'"

sh "$TMP/bootstrap.sh" || fail "bootstrap is not idempotent (second run exited $?)"
[ "$(git -C "$TMP" config core.hooksPath)" = ".githooks" ] || fail "hooksPath drifted on rerun"

# Missing-tool probe must be FATAL 64 with a diagnosable message, distinct from gate FAIL 2.
set +e
ERR=$(env PATH=/usr/bin:/bin sh "$TMP/bootstrap.sh" 2>&1)
RC=$?
set -e
[ "$RC" -eq 64 ] || fail "missing-bun run exited $RC, want 64"
echo "$ERR" | grep -qi "bun" || fail "missing-bun diagnostic does not name the tool"

echo "PASS: bootstrap contract holds"
