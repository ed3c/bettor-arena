#!/bin/sh
# Seam: bootstrap.sh CLI exit codes + resulting git config, on an isolated copy.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
fail() { echo "FAIL: $1" >&2; exit 1; }

cp -R "$ROOT/scripts" "$TMP/scripts"
# Unconditional: .githooks is tracked (S8); a fallback mkdir would mask its absence.
cp -R "$ROOT/.githooks" "$TMP/.githooks" || fail ".githooks missing in repo (S8 tracked hooks)"
cp "$ROOT/bootstrap.sh" "$TMP/bootstrap.sh" 2>/dev/null || fail "bootstrap.sh does not exist yet"
git -C "$TMP" init -q -b main

sh "$TMP/bootstrap.sh" || fail "first bootstrap run exited $?"
HP=$(git -C "$TMP" config core.hooksPath) || fail "hooksPath unset after bootstrap"
[ "$HP" = ".githooks" ] || fail "hooksPath is '$HP', want relative '.githooks'"

sh "$TMP/bootstrap.sh" || fail "bootstrap is not idempotent (second run exited $?)"
[ "$(git -C "$TMP" config core.hooksPath)" = ".githooks" ] || fail "hooksPath drifted on rerun"

# Wiki freshness WARN (never FATAL): absent fires / fresh silent / stale fires.
# Fixture commits disable hooksPath explicitly: this seam tests the doctor
# WARN, not the hooks — those have their own seam tests (fast_quality /
# molecular), and the fixture lacks the factory toolchain the TS lane needs.
fixture_commit() { git -C "$TMP" -c core.hooksPath= -c user.email=t@t -c user.name=t commit -qm "$1"; }
git -C "$TMP" add -A
fixture_commit base
ERR=$(sh "$TMP/bootstrap.sh" 2>&1) || fail "bootstrap failed inside wiki-warn block"
echo "$ERR" | grep -q "wiki absent" || fail "absent wiki did not WARN"
mkdir -p "$TMP/openwiki"
printf '{"gitHead": "%s"}\n' "$(git -C "$TMP" rev-parse HEAD)" > "$TMP/openwiki/.last-update.json"
ERR=$(sh "$TMP/bootstrap.sh" 2>&1) || fail "bootstrap failed with fresh wiki"
echo "$ERR" | grep -q "openwiki/ is stale" && fail "fresh wiki wrongly WARNed stale"
echo x > "$TMP/code.txt"
git -C "$TMP" add code.txt
fixture_commit change
ERR=$(sh "$TMP/bootstrap.sh" 2>&1) || fail "bootstrap failed with stale wiki"
echo "$ERR" | grep -q "openwiki/ is stale" || fail "stale wiki did not WARN"

# Missing-tool probe must be FATAL 64 with a diagnosable message, distinct from gate FAIL 2.
set +e
ERR=$(env PATH=/usr/bin:/bin sh "$TMP/bootstrap.sh" 2>&1)
RC=$?
set -e
[ "$RC" -eq 64 ] || fail "missing-bun run exited $RC, want 64"
echo "$ERR" | grep -qi "bun" || fail "missing-bun diagnostic does not name the tool"

# Missing-python3 probe: stub PATH dir holding only git/sh/bun must FATAL 64.
mkdir "$TMP/bin"
for t in git sh bun; do ln -s "$(command -v "$t")" "$TMP/bin/$t"; done
set +e
ERR=$(env PATH="$TMP/bin" sh "$TMP/bootstrap.sh" 2>&1)
RC=$?
set -e
[ "$RC" -eq 64 ] || fail "missing-python3 run exited $RC, want 64"
echo "$ERR" | grep -qi "python3" || fail "missing-python3 diagnostic does not name the tool"

# .githooks-absent probe: hooksPath pointing at nothing must FATAL 64, not OK.
rm -rf "$TMP/.githooks"
set +e
ERR=$(sh "$TMP/bootstrap.sh" 2>&1)
RC=$?
set -e
[ "$RC" -eq 64 ] || fail "hookless run exited $RC, want FATAL 64"
echo "$ERR" | grep -q "githooks" || fail "hookless diagnostic does not name .githooks"

echo "PASS: bootstrap contract holds"
