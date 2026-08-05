#!/usr/bin/env bash
# approach-diversity-check.sh <APPROACH.md...>  (>=2 files)
# hollow h3 擋層（02 §1.4）：N 版必須跨 approach 或跨家族真多樣——
# 同 approach 同家族 = 假多樣（NV=2≈0 實測，00 §D 校正一），dispatch 前擋，不起跑。
set -euo pipefail
[ "$#" -ge 2 ] || { echo "usage: approach-diversity-check.sh <APPROACH.md...> (>=2 files)" >&2; exit 64; }

sigs=()
for f in "$@"; do
  a=$(grep -m1 -E '^approach:' "$f" 2>/dev/null | cut -d: -f2- | xargs || true)
  fam=$(grep -m1 -E '^family:' "$f" 2>/dev/null | cut -d: -f2- | xargs || true)
  if [ -z "$a" ] || [ -z "$fam" ]; then
    echo "FAIL: $f missing required 'approach:' / 'family:' field" >&2
    exit 1
  fi
  sigs+=("$a|$fam")
done

dupe=$(printf '%s\n' "${sigs[@]}" | sort | uniq -d)
if [ -n "$dupe" ]; then
  echo "FAIL: duplicate approach|family across variants (fake diversity):" >&2
  echo "$dupe" >&2
  exit 1
fi
echo "PASS: all variants pairwise distinct on approach|family"
