#!/bin/sh
# Seam: fast_quality.sh CLI exit codes + pre-commit.staged real git commit
# behavior, in an isolated fixture where the staged hook is ACTIVATED
# (activation in this repo itself is a separate human admit).
#
# Controls (every green here was first seen red while this file predated the
# implementation): three lanes each carry a negative control — TS type error,
# Python format violation, shell syntax error — plus a clean-tree positive
# control, a fail-fast not_run assertion, a ruff-absent FATAL 64, a hook
# self-integrity block, a budget-overrun FATAL, and a <5s wall-time bound.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
fail() { echo "FAIL: $1" >&2; exit 1; }

G="$ROOT/scripts/gates/fast_quality.sh"
H="$ROOT/.githooks/pre-commit.staged"
FACTORY="$ROOT/loop_wiki/evolve-perfect-seed-repo-factory"
[ -f "$G" ] || fail "gate missing: $G"
[ -f "$H" ] || fail "pre-commit.staged missing: $H"
# Staged name must NOT be active in this repo (activation = separate human admit).
[ ! -e "$ROOT/.githooks/pre-commit" ] || fail "pre-commit unexpectedly active in repo"

# Assembled so this tracked file never embeds a literal home-root prefix.
BADROOT=$(printf '/Use%s' 'rs/nobody/home')

# ---------------------------------------------------------------- gate CLI
W="$TMP/work"
mkdir -p "$W"
printf 'export const ok: number = 1;\n' > "$W/good.ts"
printf 'const broken: number = "not a number";\nexport default broken;\n' > "$W/bad_type.ts"
printf 'X = 1\n' > "$W/good.py"
printf 'x=1;y  =2\n' > "$W/bad_format.py"
printf '#!/bin/sh\necho ok\n' > "$W/good.sh"
printf '#!/bin/sh\nif [ 1 -eq 1 ]; then\n  echo missing-fi\n' > "$W/bad_syntax.sh"

# 1) Clean tree, all three lanes → green; receipt carries claim boundary + hashes.
set +e
OUT=$(sh "$G" "$W/good.ts" "$W/good.py" "$W/good.sh" 2>&1)
RC=$?
set -e
[ "$RC" -eq 0 ] || fail "clean run exited $RC, want 0 — $OUT"
echo "$OUT" | grep -q 'preflight-only-not-code-quality-axis' \
  || fail "receipt missing claim_boundary"
echo "$OUT" | grep -q '"gate_inputs"' || fail "receipt missing gate_inputs"
echo "$OUT" | grep -Eq '[0-9a-f]{64}' || fail "gate_inputs carries no sha256"

# 2) TS lane negative control: type error → red.
set +e
sh "$G" "$W/bad_type.ts" >/dev/null 2>&1
RC=$?
set -e
[ "$RC" -eq 2 ] || fail "TS type error exited $RC, want 2"

# 3) Python lane negative control: format violation → red; and with a TS file
#    also staged, fail-fast must mark the TS stages not_run.
set +e
OUT=$(sh "$G" "$W/bad_format.py" "$W/good.ts" 2>&1)
RC=$?
set -e
[ "$RC" -eq 2 ] || fail "py format violation exited $RC, want 2"
echo "$OUT" | grep -q '"not_run"' || fail "fail-fast left no not_run stage in receipt"

# 4) Shell lane negative control: syntax error → red.
set +e
sh "$G" "$W/bad_syntax.sh" >/dev/null 2>&1
RC=$?
set -e
[ "$RC" -eq 2 ] || fail "shell syntax error exited $RC, want 2"

# 5) stdin mode + --receipt path.
set +e
printf '%s\n' "$W/good.py" "$W/good.sh" | sh "$G" --receipt "$TMP/r.json" >/dev/null 2>&1
RC=$?
set -e
[ "$RC" -eq 0 ] || fail "stdin mode exited $RC, want 0"
[ -f "$TMP/r.json" ] || fail "--receipt wrote no file"
grep -q 'preflight-only-not-code-quality-axis' "$TMP/r.json" \
  || fail "--receipt file missing claim_boundary"

# 6) Missing input file → FATAL 64, names the file.
set +e
ERR=$(sh "$G" "$W/does_not_exist.py" 2>&1)
RC=$?
set -e
[ "$RC" -eq 64 ] || fail "missing file exited $RC, want 64"
echo "$ERR" | grep -q 'does_not_exist.py' || fail "missing-file FATAL does not name the file"

# 7) ruff-absent negative control: FATAL 64, diagnostic names ruff.
set +e
ERR=$(env PATH=/usr/bin:/bin sh "$G" "$W/good.py" 2>&1)
RC=$?
set -e
[ "$RC" -eq 64 ] || fail "ruff-absent exited $RC, want 64"
echo "$ERR" | grep -qi 'ruff' || fail "ruff-absent diagnostic does not name ruff"

# 8) check_root_coupling --staged is exercised by its own selftest (staged
#    positive + worktree-only negative controls live there).
python3 "$ROOT/scripts/gates/check_root_coupling.py" --selftest >/dev/null \
  || fail "check_root_coupling selftest RED"

# ---------------------------------------------------------- hook in fixture
R="$TMP/repo"
mkdir -p "$R/.githooks" "$R/scripts/gates"
cp "$H" "$R/.githooks/pre-commit"
cp "$G" "$R/scripts/gates/fast_quality.sh"
cp "$ROOT/scripts/gates/check_root_coupling.py" "$R/scripts/gates/"
chmod +x "$R/.githooks/pre-commit"
git -C "$R" init -q -b main
git -C "$R" config user.email test@test
git -C "$R" config user.name test
# Track the gate closure BEFORE activating hooks (mirrors the real repo, where
# .githooks/ and scripts/gates/ are tracked — untracked files are invisible to
# the self-integrity diff). The real repo's Python gates are not yet
# ruff-clean, so this baseline lands hook-free; every later commit is gated.
git -C "$R" add .githooks scripts
git -C "$R" commit -q -m "baseline: gate closure tracked"
git -C "$R" config core.hooksPath .githooks
export FAST_QUALITY_FACTORY="$FACTORY"

# 9) Clean staged tree (all three lanes) → commit passes, wall time < 5s.
printf 'export const ok: number = 1;\n' > "$R/a.ts"
printf 'X = 1\n' > "$R/a.py"
printf '#!/bin/sh\necho ok\n' > "$R/a.sh"
git -C "$R" add a.ts a.py a.sh
T0=$(python3 -c 'import time; print(time.time())')
git -C "$R" commit -q -m "clean commit" || fail "clean commit rejected by hook"
T1=$(python3 -c 'import time; print(time.time())')
[ "$(git -C "$R" rev-list --count HEAD)" = "2" ] || fail "clean commit not created"
ELAPSED=$(python3 -c "print($T1 - $T0)")
python3 -c "import sys; sys.exit(0 if $ELAPSED < 5.0 else 1)" \
  || fail "hook wall time ${ELAPSED}s breaches the <5s budget"

# 10) Staged TS type error → commit blocked, no new commit.
printf 'const broken: number = "nope";\nexport default broken;\n' > "$R/b.ts"
git -C "$R" add b.ts
git -C "$R" commit -q -m "bad ts" 2>/dev/null && fail "type-error commit was accepted"
[ "$(git -C "$R" rev-list --count HEAD)" = "2" ] || fail "type-error commit exists"
git -C "$R" reset -q b.ts && rm "$R/b.ts"

# 11) Staged py format violation → blocked.
printf 'x=1;y  =2\n' > "$R/b.py"
git -C "$R" add b.py
git -C "$R" commit -q -m "bad py" 2>/dev/null && fail "format-violation commit was accepted"
[ "$(git -C "$R" rev-list --count HEAD)" = "2" ] || fail "format-violation commit exists"
git -C "$R" reset -q b.py && rm "$R/b.py"

# 12) Staged shell syntax error → blocked.
printf '#!/bin/sh\nif true; then\n  echo missing-fi\n' > "$R/b.sh"
git -C "$R" add b.sh
git -C "$R" commit -q -m "bad sh" 2>/dev/null && fail "syntax-error commit was accepted"
[ "$(git -C "$R" rev-list --count HEAD)" = "2" ] || fail "syntax-error commit exists"
git -C "$R" reset -q b.sh && rm "$R/b.sh"

# 13) Hook wires check_root_coupling --staged: staged home-root path → blocked.
printf 'points at %s\n' "$BADROOT" > "$R/doc.md"
git -C "$R" add doc.md
git -C "$R" commit -q -m "coupled doc" 2>/dev/null && fail "root-coupled commit was accepted"
[ "$(git -C "$R" rev-list --count HEAD)" = "2" ] || fail "root-coupled commit exists"
git -C "$R" reset -q doc.md && rm "$R/doc.md"

# 14) Self-integrity radius: unstaged edit inside scripts/gates/ blocks even an
#     unrelated commit (the gate that would run is not the gate being committed).
printf '# drift\n' >> "$R/scripts/gates/fast_quality.sh"
printf 'Y = 2\n' > "$R/c.py"
git -C "$R" add c.py
git -C "$R" commit -q -m "unrelated" 2>/dev/null && fail "gate-drift commit was accepted"
[ "$(git -C "$R" rev-list --count HEAD)" = "2" ] || fail "gate-drift commit exists"
cp "$G" "$R/scripts/gates/fast_quality.sh"   # restore closure
git -C "$R" reset -q c.py && rm "$R/c.py"

# 15) Budget overrun → FATAL 64, commit blocked (TS lane takes >0s).
printf 'export const slow: number = 2;\n' > "$R/d.ts"
git -C "$R" add d.ts
set +e
ERR=$(env FAST_QUALITY_BUDGET=0 git -C "$R" commit -q -m "budget" 2>&1)
RC=$?
set -e
[ "$RC" -ne 0 ] || fail "budget-overrun commit was accepted"
echo "$ERR" | grep -q 'budget' || fail "budget FATAL diagnostic missing: $ERR"
[ "$(git -C "$R" rev-list --count HEAD)" = "2" ] || fail "budget-overrun commit exists"

echo "PASS: fast quality gate contract holds"
