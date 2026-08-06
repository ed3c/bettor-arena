#!/bin/sh
# Seam: commit-msg.staged / post-commit.staged CLI exit codes + real git
# commit behavior, in an isolated fixture where the staged hooks are ACTIVATED
# (activation in this repo itself is a separate human admit).
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
fail() { echo "FAIL: $1" >&2; exit 1; }

V="$ROOT/.githooks/lib/validate_molecular_message.ts"
[ -f "$V" ] || fail "validator missing: $V"
[ -f "$ROOT/.githooks/commit-msg.staged" ] || fail "commit-msg.staged missing"
[ -f "$ROOT/.githooks/post-commit.staged" ] || fail "post-commit.staged missing"

# Staged names must NOT be active in this repo (activation = separate human admit).
[ ! -e "$ROOT/.githooks/commit-msg" ] || fail "commit-msg unexpectedly active in repo"
[ ! -e "$ROOT/.githooks/post-commit" ] || fail "post-commit unexpectedly active in repo"

# Charter: single file, node: builtins only, no sibling-checkout reads.
if grep -E '^import .* from "(\.|/)' "$V" | grep -v '"node:' >/dev/null; then
  fail "validator imports outside node: builtins"
fi

# 0) Validator selftest — proves every green in it was seen red.
bun run "$V" --selftest >/dev/null || fail "validator selftest RED"

# 1) Fixture repo with hooks activated.
R="$TMP/repo"
mkdir -p "$R/.githooks/lib" "$R/scripts/gates"
cp "$V" "$R/.githooks/lib/"
cp "$ROOT/.githooks/commit-msg.staged" "$R/.githooks/commit-msg"
cp "$ROOT/.githooks/post-commit.staged" "$R/.githooks/post-commit"
chmod +x "$R/.githooks/commit-msg" "$R/.githooks/post-commit"
git -C "$R" init -q -b main
git -C "$R" config core.hooksPath .githooks
git -C "$R" config user.email test@test
git -C "$R" config user.name test

# 1a) Ordinary message on ordinary file → commit succeeds.
echo hi > "$R/plain.txt"
git -C "$R" add plain.txt
git -C "$R" commit -q -m "good: ordinary message on ordinary file" \
  || fail "ordinary commit rejected"
[ "$(git -C "$R" rev-list --count HEAD)" = "1" ] || fail "ordinary commit not created"

# 1b) post-commit receipt exists, is record-only, names the sha.
SHA=$(git -C "$R" rev-parse HEAD)
RCPT="$R/data/receipts/post-commit-$SHA.json"
[ -f "$RCPT" ] || fail "post-commit stage-request receipt missing: $RCPT"
grep -q "$SHA" "$RCPT" || fail "receipt does not name the commit sha"
grep -q '"stage-request"' "$RCPT" || fail "receipt is not a stage-request record"

# 2) Hollow molecular message → commit must fail AND commit must not exist.
echo x > "$R/plain2.txt"
git -C "$R" add plain2.txt
printf 'bad hollow molecular\n\nIntent-Slice: ISSUE-10\nRoute: somewhere\n' > "$TMP/hollow.msg"
if git -C "$R" commit -q -F "$TMP/hollow.msg" 2>/dev/null; then
  fail "hollow molecular commit was accepted"
fi
[ "$(git -C "$R" rev-list --count HEAD)" = "1" ] || fail "hollow molecular commit exists"

# 3) Protected gate surface + ordinary message → must fail.
echo '# gate' > "$R/scripts/gates/g.py"
git -C "$R" add scripts/gates/g.py
if git -C "$R" commit -q -m "bad: ordinary message touching gate surface" 2>/dev/null; then
  fail "protected-surface commit with ordinary message was accepted"
fi
[ "$(git -C "$R" rev-list --count HEAD)" = "1" ] || fail "protected-surface bad commit exists"

# 4) Full molecular message on protected surface → must pass.
cat > "$TMP/good.msg" <<'EOF'
good: molecular message touching gate surface

Intent-Slice: ISSUE-14
Route: docs/routes.md#gate
Plan-Package: docs/plan-package.yaml
Small-Loop: loop_wiki/some-loop/
Final-Repo: repo/
Exchange-Format: docs/exchange-format.md
Exchange-Packet: docs/packet.yaml
Fixed-Prompt-Context: docs/prompt.md
Iteration-Auto-Context: docs/iteration.md
Emergent-Prompt-Context: docs/emergent.md
Dataflow:
docs/plan-package.yaml
  -> repo/
EOF
git -C "$R" commit -q -F "$TMP/good.msg" || fail "good molecular commit rejected"
[ "$(git -C "$R" rev-list --count HEAD)" = "2" ] || fail "good molecular commit not created"

# 5) bun-absent negative control: FATAL 64, diagnostic names bun.
printf 'any message\n' > "$TMP/any.msg"
set +e
ERR=$(env PATH=/usr/bin:/bin sh "$R/.githooks/commit-msg" "$TMP/any.msg" 2>&1)
RC=$?
set -e
[ "$RC" -eq 64 ] || fail "bun-absent hook exited $RC, want 64"
echo "$ERR" | grep -qi "bun" || fail "bun-absent diagnostic does not name bun"

# Receipt: this run's evidence, written only after every assertion above held.
# Lands in $TMP — the tracked 2026-08-05 receipt is historical evidence and is
# never overwritten by reruns (rewriting evidence is forging evidence).
mkdir -p "$TMP/receipts"
cat > "$TMP/receipts/molecular-gate-smoke.json" <<EOF
{
  "kind": "molecular-gate-smoke",
  "utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "checks": [
    "validator-selftest-green",
    "staged-names-inactive-in-repo",
    "node-builtin-imports-only",
    "ordinary-commit-passes",
    "post-commit-stage-request-receipt",
    "hollow-molecular-commit-rejected-and-absent",
    "protected-surface-ordinary-message-rejected",
    "full-molecular-commit-passes",
    "bun-absent-exit-64-names-bun"
  ],
  "result": "PASS"
}
EOF
echo "PASS: molecular gate contract holds"
