#!/usr/bin/env bash
# held-reference-check.sh <judge-verdict.md>
# hollow h2 擋層（02 §1.4）：判官勾稽表每個 HELD 行必附軌跡引用（variant-*/iter* token），
# 沒引用 = 心證放水 = FAIL。查證動作非印象打分。
set -euo pipefail
f="${1:?usage: held-reference-check.sh <judge-verdict.md>}"

# 只查勾稽表的表格行（'|' 開頭），不誤抓散文提及「HELD」的句子
bad=$(grep -n '^|.*HELD' "$f" | grep -viE 'variant-[A-Za-z0-9_./-]*iter[0-9A-Za-z_.-]*' || true)
if [ -n "$bad" ]; then
  echo "FAIL: HELD verdict line(s) without variant-*/iter* trajectory reference:" >&2
  echo "$bad" >&2
  exit 1
fi
echo "PASS: all HELD verdicts cite a trajectory (variant-*/iter*)"
