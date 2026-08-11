#!/bin/sh
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
CHECK="$ROOT/scripts/runtime-env/check-stealth-profile-hygiene.sh"
TMP=$(mktemp -d "${TMPDIR:-/tmp}/stealth-profile-hygiene.XXXXXX")
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

REPO="$TMP/stealth-browser"
PROFILE_ROOT="$TMP/host-profiles"
mkdir -p "$REPO" "$PROFILE_ROOT/research"
git -C "$REPO" init -q
git -C "$REPO" config user.email fixture@example.invalid
git -C "$REPO" config user.name fixture
printf 'fixture\n' >"$REPO/README.md"
git -C "$REPO" add README.md
git -C "$REPO" commit -qm fixture
chmod 700 "$PROFILE_ROOT" "$PROFILE_ROOT/research"
: >"$PROFILE_ROOT/research/state.json"
chmod 600 "$PROFILE_ROOT/research/state.json"

STEALTH_BROWSER_ROOT="$REPO" STEALTH_PROFILE_ROOT="$PROFILE_ROOT" sh "$CHECK"

mkdir -p "$REPO/profiles/research"
: >"$REPO/profiles/research/state.json"
if STEALTH_BROWSER_ROOT="$REPO" STEALTH_PROFILE_ROOT="$PROFILE_ROOT" sh "$CHECK" >/dev/null 2>&1; then
  echo "FAIL: repo-local credential profile passed hygiene" >&2
  exit 1
fi
rm "$REPO/profiles/research/state.json"

chmod 644 "$PROFILE_ROOT/research/state.json"
if STEALTH_BROWSER_ROOT="$REPO" STEALTH_PROFILE_ROOT="$PROFILE_ROOT" sh "$CHECK" >/dev/null 2>&1; then
  echo "FAIL: world-readable credential profile passed hygiene" >&2
  exit 1
fi

echo "PASS: stealth profile hygiene has positive and planted-negative controls"
