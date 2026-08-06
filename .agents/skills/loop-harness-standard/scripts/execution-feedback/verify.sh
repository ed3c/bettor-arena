#!/usr/bin/env bash
# verify.sh — selftest for the 4 execution-feedback checkers (02 §1.4 good/hollow, anti-placebo).
# good=PASS 且 hollow=FAIL 才算 checker 活（evals-design-method.md positive-control 紀律）。
set -uo pipefail
cd "$(dirname "$0")"
fail=0

check() {
  local desc="$1"; shift
  local want="$1"; shift  # "pass" or "fail"
  if "$@" >/tmp/execution-feedback-verify.out 2>&1; then got=pass; else got=fail; fi
  if [ "$got" = "$want" ]; then
    echo "ok   - $desc"
  else
    echo "FAIL - $desc (want $want, got $got)"
    sed 's/^/       /' /tmp/execution-feedback-verify.out
    fail=1
  fi
}

check "held-reference-check good"    pass ./held-reference-check.sh fixtures/good/judge-verdict.md
check "held-reference-check hollow"  fail ./held-reference-check.sh fixtures/hollow/judge-verdict.md

check "approach-diversity-check good"   pass ./approach-diversity-check.sh fixtures/good/variant-A/APPROACH.md fixtures/good/variant-B/APPROACH.md
check "approach-diversity-check hollow" fail ./approach-diversity-check.sh fixtures/hollow/variant-A/APPROACH.md fixtures/hollow/variant-B/APPROACH.md

check "no-smuggled-plan-delta-check good"   pass ./no-smuggled-plan-delta-check.sh fixtures/good/rerun-prompt.md fixtures/good/judge-verdict.md fixtures/good/assertions.md
check "no-smuggled-plan-delta-check hollow" fail ./no-smuggled-plan-delta-check.sh fixtures/hollow/rerun-prompt.md fixtures/hollow/judge-verdict.md fixtures/hollow/assertions.md

# plan-dir-diff-check：git 狀態本身即檢查對象，用臨時 repo 造 good(clean)/hollow(dirty) 兩態，非靜態 fixture
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
git -C "$tmpdir" init -q
echo "plan text" > "$tmpdir/00-intent.md"
git -C "$tmpdir" add -A && git -C "$tmpdir" -c user.email=t@t -c user.name=t commit -q -m init
check "plan-dir-diff-check good (clean)" pass ./plan-dir-diff-check.sh "$tmpdir"
echo "loop 偷改了計劃前提" >> "$tmpdir/00-intent.md"
check "plan-dir-diff-check hollow (dirty)" fail ./plan-dir-diff-check.sh "$tmpdir"

if [ "$fail" -ne 0 ]; then
  echo "=== execution-feedback checkers: SELFTEST FAILED ==="
  exit 1
fi
echo "=== execution-feedback checkers: all good=PASS, hollow=FAIL ✓ ==="
