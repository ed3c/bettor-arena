#!/bin/sh
# Seam: the /delivery forwarder's promises must resolve to things that exist.
#
# Why this test exists: the first version of that command file promised a live
# progress table pulled from the forge, and no code computed one. A forwarder is
# supposed to carry zero logic — but "zero logic" must not mean "unchecked
# prose". Every script path and skill it names is asserted here, so the file
# cannot promise a capability that was never built (issue #28's root cause).
#
# Controls: a mutated copy naming a script that does not exist must fail; the
# real file must pass. Both run below, so this green was seen red first.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
CMD="$ROOT/.claude/commands/delivery.md"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
fail() { echo "FAIL: $1" >&2; exit 1; }

[ -f "$CMD" ] || fail "forwarder missing: $CMD"

# --- the file's own shape ---------------------------------------------------
head -1 "$CMD" | grep -q '^---$' || fail "no frontmatter fence on line 1"
grep -q '^description:' "$CMD" || fail "frontmatter lacks description"
grep -q '\$ARGUMENTS' "$CMD" || fail "forwarder never passes \$ARGUMENTS through"
grep -q 'forgejo-delivery-loop' "$CMD" || fail "forwarder does not name the skill it forwards to"
grep -q '\.claude/skills/forgejo-delivery-loop/SKILL.md' "$CMD" \
  || fail "forwarder does not point at the canonical skill"
if grep -q 'python3 scripts/' "$CMD"; then
  fail "forwarder duplicates workflow commands instead of remaining a thin alias"
fi

# --- every promise must resolve --------------------------------------------
# Extract `scripts/...py` mentions and require each to exist and be runnable.
check_paths() {
  target=$1
  missing=""
  for path in $(grep -oE 'scripts/[A-Za-z0-9_/]+\.py' "$target" | sort -u); do
    [ -f "$ROOT/$path" ] || missing="$missing $path"
  done
  [ -z "$missing" ] || { echo "$missing"; return 1; }
  return 0
}
check_paths "$CMD" >/dev/null || fail "forwarder names script(s) that do not exist:$(check_paths "$CMD" || true)"

# The skill it forwards to must be reachable from the host entry it claims.
[ -e "$ROOT/.claude/skills/forgejo-delivery-loop/SKILL.md" ] \
  || fail "host skill entry does not resolve to a SKILL.md"

# Each named script must answer --selftest 0 (the forwarder promises working tools).
for path in $(grep -oE 'scripts/[A-Za-z0-9_/]+\.py' "$CMD" | sort -u); do
  python3 "$ROOT/$path" --selftest >/dev/null 2>&1 \
    || fail "$path --selftest is not green; the forwarder promises a tool that cannot prove itself"
done

# --- negative control: a promise with no implementation must be caught ------
cp "$CMD" "$TMP/mutated.md"
printf '\n- **fake**: `python3 scripts/delivery_nonexistent.py`（此工具不存在，測試用）\n' >> "$TMP/mutated.md"
if check_paths "$TMP/mutated.md" >/dev/null 2>&1; then
  fail "negative control: an unimplemented promise passed the check"
fi

echo "PASS: every /delivery promise resolves to a tool that exists and self-tests"
