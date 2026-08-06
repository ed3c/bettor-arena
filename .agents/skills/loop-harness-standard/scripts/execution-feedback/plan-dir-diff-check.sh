#!/usr/bin/env bash
# plan-dir-diff-check.sh <plan-dir>
# hollow h1 擋層（02 §1.4）：人 admit 前，計劃目錄必須零 git diff——
# 這是「迴圈不可自動改計劃」鐵律（02 §0.2 ①）的收尾機械兜底，非自律。
set -euo pipefail
d="${1:?usage: plan-dir-diff-check.sh <plan-dir>}"
[ -d "$d" ] || { echo "FAIL: plan dir not found: $d" >&2; exit 1; }

dirty=$(git -C "$d" status --porcelain -- . 2>/dev/null || true)
if [ -n "$dirty" ]; then
  echo "FAIL: plan directory has uncommitted changes before human admit:" >&2
  echo "$dirty" >&2
  exit 1
fi
echo "PASS: plan directory clean (no auto plan-edit)"
