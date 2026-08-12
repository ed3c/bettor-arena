#!/bin/sh
# Seam: fast_quality.sh CLI exit codes + pre-commit real git commit behavior,
# in an isolated fixture repo (the hook was activated in this repo by the
# admitted #14 stage 1; this file judges the same hook source).
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
H="$ROOT/.githooks/pre-commit"
FACTORY="$ROOT/loop_wiki/evolve-perfect-seed-repo-factory"
[ -f "$G" ] || fail "gate missing: $G"
# #14 stage 1 (human admit) activated the hook; it must be live and executable.
[ -x "$H" ] || fail "pre-commit missing or not executable: $H"

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

# 2a) Bun-style explicit .ts imports are part of the checked repo surface.
#     The staged-file tsc mirror must accept the same import form while still
#     running with --noEmit; otherwise any root entrypoint importing its typed
#     closure is uncommittable even when the closure is valid.
printf 'export const value: number = 1;\n' > "$W/imported.ts"
printf 'import { value } from "./imported.ts";\nexport const imported: number = value;\n' > "$W/good_import.ts"
set +e
OUT=$(sh "$G" "$W/good_import.ts" 2>&1)
RC=$?
set -e
[ "$RC" -eq 0 ] || fail "explicit .ts import exited $RC, want 0 — $OUT"

# 2aa) The real environment-contract entrypoint imports the browser/origin
#      validators. Keep that production closure under the staged-file gate so
#      fixture-only greens cannot hide strict errors in repo code.
set +e
OUT=$(sh "$G" "$ROOT/scripts/gates/check_environment_contracts.ts" 2>&1)
RC=$?
set -e
[ "$RC" -eq 0 ] || fail "environment-contract TS closure exited $RC, want 0 — $OUT"

# 2b) TS strictness parity probe: optional-param `.length` must red here exactly
#     as the factory's strict tsconfig reds it (two mounts, one judgment). The
#     probe is prettier-clean so the red can only come from ts-typecheck.
printf 'export function f(s?: string): number {\n  return s.length;\n}\n' > "$W/optional.ts"
set +e
OUT=$(sh "$G" "$W/optional.ts" 2>&1)
RC=$?
set -e
[ "$RC" -eq 2 ] || fail "optional-param strictness probe exited $RC, want 2 (pre-commit tsc diverges from factory strict tsconfig)"
echo "$OUT" | grep -q '"id":"ts-typecheck","status":"failed"' \
  || fail "strictness probe did not red at ts-typecheck — $OUT"

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

# 7b) No-network-fallback control: uvx IS on PATH but ruff is not — the gate
#     must still FATAL 64 naming ruff, never shell out to a fetching fallback
#     (a green judged by a network-fetched tool is not the pinned toolchain).
STUBBIN="$TMP/stubbin"
mkdir -p "$STUBBIN"
printf '#!/bin/sh\nexit 0\n' > "$STUBBIN/uvx"
chmod +x "$STUBBIN/uvx"
set +e
ERR=$(env PATH="$STUBBIN:/usr/bin:/bin" sh "$G" "$W/good.py" 2>&1)
RC=$?
set -e
[ "$RC" -eq 64 ] || fail "uvx-present/ruff-absent exited $RC, want 64 (gate still has a uvx fallback)"
echo "$ERR" | grep -qi 'ruff' || fail "uvx-present/ruff-absent diagnostic does not name ruff"

# 8) check_root_coupling --staged is exercised by its own selftest (staged
#    positive + worktree-only negative controls live there).
python3 "$ROOT/scripts/gates/check_root_coupling.py" --selftest >/dev/null \
  || fail "check_root_coupling selftest RED"

# ---------------------------------------------------------- hook in fixture
R="$TMP/repo"
MARKERS="$TMP/modular-gate-markers"
mkdir -p "$R/.githooks" "$R/scripts/gates" "$MARKERS"
cp "$H" "$R/.githooks/pre-commit"
cp "$G" "$R/scripts/gates/fast_quality.sh"
cp "$ROOT/scripts/gates/check_root_coupling.py" "$R/scripts/gates/"
cp "$ROOT/scripts/gates/_gate_common.py" "$R/scripts/gates/"
chmod +x "$R/.githooks/pre-commit"
# Structure gates (placement/skill-pointers) verify THIS repo's structure and
# carry their own selftests; the fixture only needs to prove the hook CALLS
# them. Marker-writing stubs make that wiring observable, not silently skipped.
for stub in check_placement check_skill_pointers check_credential_hygiene check_runtime_env_binding check_delivery_receipt; do
  printf '#!/usr/bin/env python3\n# fixture stub: real gate has its own selftest; this proves hook wiring.\nimport pathlib\npathlib.Path(__file__).with_name("%s.called").touch()\n' "$stub" \
    > "$R/scripts/gates/$stub.py"
done
# Modular gates execute from the staged checkout, which is deleted when the
# hook exits. Their stubs therefore write observable markers to a fixture-owned
# directory inherited through the environment instead of their own directory.
for stub in check_agent_docs check_module_catalog check_mcp_policy; do
  printf '#!/usr/bin/env python3\nimport os, pathlib\npathlib.Path(os.environ["FAST_QUALITY_TEST_MARKERS"], "%s.called").touch()\n' "$stub" \
    > "$R/scripts/gates/$stub.py"
done
for stub in arena_proof arena_context; do
  printf '#!/usr/bin/env python3\nimport os, pathlib\npathlib.Path(os.environ["FAST_QUALITY_TEST_MARKERS"], "%s.called").touch()\n' "$stub" \
    > "$R/scripts/$stub.py"
done
for stub in check_project_bootstrap check_environment_contracts; do
  printf 'await Bun.write(`${process.env.FAST_QUALITY_TEST_MARKERS}/%s.called`, "");\n' "$stub" \
    > "$R/scripts/gates/$stub.ts"
done
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
export FAST_QUALITY_TEST_MARKERS="$MARKERS"

# 9) Clean staged tree (all three lanes) → commit passes, wall time < 5s.
printf 'export const ok: number = 1;\n' > "$R/a.ts"
printf 'X = 1\n' > "$R/a.py"
printf '#!/bin/sh\necho ok\n' > "$R/a.sh"
git -C "$R" add a.ts a.py a.sh
T0=$(python3 -c 'import time; print(time.time())')
git -C "$R" commit -q -m "clean commit" || fail "clean commit rejected by hook"
T1=$(python3 -c 'import time; print(time.time())')
[ "$(git -C "$R" rev-list --count HEAD)" = "2" ] || fail "clean commit not created"
# Wiring proof: the hook must have invoked every repo-level gate stub.
[ -f "$R/scripts/gates/check_placement.called" ] || fail "hook did not call check_placement"
[ -f "$R/scripts/gates/check_skill_pointers.called" ] || fail "hook did not call check_skill_pointers"
[ -f "$R/scripts/gates/check_credential_hygiene.called" ] || fail "hook did not call check_credential_hygiene"
[ -f "$R/scripts/gates/check_runtime_env_binding.called" ] || fail "hook did not call check_runtime_env_binding"
[ -f "$R/scripts/gates/check_delivery_receipt.called" ] || fail "hook did not call check_delivery_receipt"
for marker in check_agent_docs check_module_catalog check_mcp_policy arena_proof arena_context check_project_bootstrap check_environment_contracts; do
  [ -f "$MARKERS/$marker.called" ] || fail "hook did not call $marker"
done
ELAPSED=$(python3 -c "print($T1 - $T0)")
python3 -c "import sys; sys.exit(0 if $ELAPSED < 5.0 else 1)" \
  || fail "hook wall time ${ELAPSED}s breaches the <5s budget"

# 10) Staged TS type error → commit blocked, no new commit.
printf 'const broken: number = "nope";\nexport default broken;\n' > "$R/b.ts"
git -C "$R" add b.ts
git -C "$R" commit -q -m "bad ts" 2>/dev/null && fail "type-error commit was accepted"
[ "$(git -C "$R" rev-list --count HEAD)" = "2" ] || fail "type-error commit exists"
git -C "$R" reset -q b.ts && rm "$R/b.ts"

# 10b) Index/worktree divergence: staged blob is broken, worktree copy is clean
#      → the hook must judge the staged blob and still block the commit.
printf 'const broken: number = "nope";\nexport default broken;\n' > "$R/e.ts"
git -C "$R" add e.ts
printf 'export const fine: number = 1;\n' > "$R/e.ts"
git -C "$R" commit -q -m "bad staged blob" 2>/dev/null \
  && fail "staged-bad/worktree-clean commit was accepted (gate judged the worktree, not the index)"
[ "$(git -C "$R" rev-list --count HEAD)" = "2" ] || fail "staged-bad commit exists"
git -C "$R" reset -q e.ts && rm "$R/e.ts"

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
git -C "$R" reset -q d.ts && rm "$R/d.ts"

# 15b) Watchdog kill radius: the budget kill must take out the gate's WHOLE
#      process tree, not just the direct child. A stub gate spawns a tagged
#      grandchild then blocks; after the budget FATAL, pgrep must find no
#      tagged survivor. Deterministic on purpose: budget=1s while the stub
#      spawns in milliseconds — a budget of 0 could kill before anything
#      spawned, making the no-orphan assertion trivially (vacuously) green.
TAG="fq-orphan-probe-$$"
# One EXIT trap owns orphan cleanup from here on: every exit path — fail(),
# a set -e death, or normal completion — sweeps tagged survivors off the host.
# (Replaces three per-assertion pkill copies that missed the instrument edge.)
trap 'pkill -f "$TAG" 2>/dev/null || true; rm -rf "$TMP"' EXIT
# The grandchild's fds are detached so a surviving orphan cannot also hang the
# $(…) capture below by holding the pipe open — the pgrep is the one detector.
printf '#!/bin/sh\n# orphan-probe stub; the real gate is restored right after this case\nsh -c "while :; do sleep 5; done # %s" </dev/null >/dev/null 2>&1 &\ntouch grandchild.spawned\nwait\n' "$TAG" \
  > "$R/scripts/gates/fast_quality.sh"
git -C "$R" add scripts/gates/fast_quality.sh
printf 'export const orphan: number = 3;\n' > "$R/f.ts"
git -C "$R" add f.ts
set +e
ERR=$(env FAST_QUALITY_BUDGET=1 git -C "$R" commit -q -m "orphan probe" 2>&1)
RC=$?
set -e
[ "$RC" -ne 0 ] || fail "orphan-probe commit was accepted"
echo "$ERR" | grep -q 'budget' || fail "orphan-probe budget FATAL missing: $ERR"
# Instrument first, reading second: prove the grandchild really spawned…
[ -f "$R/grandchild.spawned" ] || fail "orphan-probe instrument broken: stub never spawned its grandchild"
# …then assert the budget kill reached it.
if pgrep -f "$TAG" >/dev/null 2>&1; then
  fail "watchdog left an orphaned grandchild running past the budget kill"
fi
rm -f "$R/grandchild.spawned"
cp "$G" "$R/scripts/gates/fast_quality.sh"   # restore closure
git -C "$R" add scripts/gates/fast_quality.sh
git -C "$R" reset -q f.ts && rm "$R/f.ts"

echo "PASS: fast quality gate contract holds"
