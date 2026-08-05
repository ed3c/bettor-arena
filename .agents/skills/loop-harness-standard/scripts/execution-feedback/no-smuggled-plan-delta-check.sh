#!/usr/bin/env bash
# no-smuggled-plan-delta-check.sh <rerun-prompt.md> <judge-verdict.md> <assertions.md>
# B-2（05-integration-and-judge-findings.md）：重跑 prompt 只許逐字引 verdict 的「改執行方式」行；
# 引到任何「plan-delta 候選」行或計劃斷言(assertions.md)文字 = FAIL（隱形 plan-delta 機械擋層，
# 非只自律）。配 plan-dir-diff-check.sh 兜底「不改計劃檔卻隱式改前提」的殘留風險。
#
# ponytail: 樸素子字串比對（cut -c1-N 取字首當 needle），非語義比對——
# 上限：長句改寫/同義替換可能漏抓。升級路徑：dogfood 後若噪音高，
# 改結構化 verdict schema（B-1 統一表已有 id 欄，可用 id 而非文字比對）。
set -euo pipefail
prompt="${1:?usage: no-smuggled-plan-delta-check.sh <prompt> <verdict> <assertions>}"
verdict="${2:?}"
assertions="${3:?}"
[ -f "$prompt" ] && [ -f "$verdict" ] && [ -f "$assertions" ] || {
  echo "FAIL: missing input file(s)" >&2; exit 64;
}

fail=0

# 白名單違反 1：verdict 裡標「plan-delta 候選」的行，字首片段不許出現在重跑 prompt
while IFS= read -r line; do
  [ -z "$line" ] && continue
  # ②b 設計分首燒(slice02)抓到：needle 含「plan-delta 候選：」自證標籤，剝標籤搬實質即逃逸(P1)。
  # 修：先剝標籤(全/半形冒號皆剝)，needle=實質內容，帶不帶標籤的 smuggle 都抓。
  needle=$(printf '%s' "$line" | sed -E 's/^[[:space:]]*-?[[:space:]]*//; s/plan-delta[[:space:]]*候選[：:][[:space:]]*//' | cut -c1-40)
  [ -z "$needle" ] && continue
  if grep -qF "$needle" "$prompt" 2>/dev/null; then
    echo "FAIL: rerun prompt quotes a plan-delta candidate line: $line" >&2
    fail=1
  fi
done < <(grep -F 'plan-delta 候選' "$verdict" || true)

# 白名單違反 2：assertions.md 的「斷言」欄文字不許出現在重跑 prompt（引到計劃前提）
while IFS='|' read -r _blank _id assertion _rest; do
  assertion=$(printf '%s' "${assertion:-}" | xargs 2>/dev/null || true)
  case "$assertion" in
    ""|斷言|---*) continue ;;
  esac
  needle=$(printf '%s' "$assertion" | cut -c1-20)
  [ -z "$needle" ] && continue
  if grep -qF "$needle" "$prompt" 2>/dev/null; then
    echo "FAIL: rerun prompt echoes plan assertion text: $assertion" >&2
    fail=1
  fi
done < <(grep '^|' "$assertions" || true)

if [ "$fail" -ne 0 ]; then exit 1; fi
echo "PASS: rerun prompt carries no smuggled plan-delta / assertion text"
