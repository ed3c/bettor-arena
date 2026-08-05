#!/bin/sh
# driver_smoke — one real round-trip per CLI driver lane (claude, codex).
#
# Proves the S11 driver-alignment contract physically: the claude lane is a
# fresh `claude -p` call, the codex lane is a direct `codex exec` call (never
# the Claude host plugin), and a missing tool is FATAL 64 naming itself —
# absence must never read as green. A real run writes a receipt (exit codes +
# truncated output summaries, no absolute paths) to
# data/receipts/driver-smoke.json.
#
# Exit codes: 0 both lanes round-tripped · 2 a lane ran but failed ·
# 64 tool absent (named) · 1 selftest red.
# Env: CLAUDE_BIN / CODEX_BIN override the binaries (selftest seam).
set -u

ROOT=$(cd "$(dirname "$0")/../.." && pwd)
CLAUDE_BIN=${CLAUDE_BIN:-claude}
CODEX_BIN=${CODEX_BIN:-codex}

fatal() { echo "driver_smoke FATAL: $1" >&2; exit 64; }

selftest() {
  red=0
  # negative control 1: absent claude must be FATAL 64 naming claude
  err=$(CLAUDE_BIN=/nonexistent/claude CODEX_BIN=/bin/sh sh "$0" 2>&1 >/dev/null)
  code=$?
  if [ "$code" -ne 64 ] || ! echo "$err" | grep -q "claude"; then
    echo "SELFTEST case failed — absent-claude: exit $code (want 64 naming claude): $err" >&2
    red=1
  fi
  # negative control 2: absent codex must be FATAL 64 naming codex
  err=$(CLAUDE_BIN=/bin/sh CODEX_BIN=/nonexistent/codex sh "$0" 2>&1 >/dev/null)
  code=$?
  if [ "$code" -ne 64 ] || ! echo "$err" | grep -q "codex"; then
    echo "SELFTEST case failed — absent-codex: exit $code (want 64 naming codex): $err" >&2
    red=1
  fi
  [ "$red" -eq 0 ] && echo "SELFTEST GREEN" || echo "SELFTEST RED"
  return "$red"
}

[ "${1:-}" = "--selftest" ] && { selftest; exit $?; }

# doctor: absence is FATAL 64 and names the missing tool — before any model call
command -v "$CLAUDE_BIN" >/dev/null 2>&1 \
  || fatal "claude CLI absent ($CLAUDE_BIN) — claude lane cannot run"
command -v "$CODEX_BIN" >/dev/null 2>&1 \
  || fatal "codex CLI absent ($CODEX_BIN) — codex lane cannot run (no plugin fallback)"

# claude lane: fresh non-interactive call, model round-trip
claude_out=$("$CLAUDE_BIN" -p "reply exactly OK" --max-turns 1 2>&1)
claude_exit=$?

# codex lane: direct codex exec, last message captured via -o (never the
# Claude host plugin codex-companion path)
tmp_last=$(mktemp)
trap 'rm -f "$tmp_last"' EXIT
"$CODEX_BIN" exec "reply exactly OK" -o "$tmp_last" >/dev/null 2>&1
codex_exit=$?
codex_last=$(cat "$tmp_last" 2>/dev/null || echo "")

receipt="$ROOT/data/receipts/driver-smoke.json"
mkdir -p "$ROOT/data/receipts"
CLAUDE_EXIT="$claude_exit" CLAUDE_OUT="$claude_out" \
CODEX_EXIT="$codex_exit" CODEX_LAST="$codex_last" RECEIPT="$receipt" \
python3 -c '
import json, os
from datetime import datetime, timezone
payload = {
    "schema": "bettor-arena-driver-smoke@1.0.0",
    "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "prompt": "reply exactly OK",
    "lanes": {
        "claude": {"argv_shape": "claude -p <prompt> --max-turns 1",
                   "exit": int(os.environ["CLAUDE_EXIT"]),
                   "output_head": os.environ["CLAUDE_OUT"][:200]},
        "codex": {"argv_shape": "codex exec <prompt> -o <last-message-file>",
                  "exit": int(os.environ["CODEX_EXIT"]),
                  "last_message_head": os.environ["CODEX_LAST"][:200]},
    },
}
text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
assert "/Users/" not in text and "/home/" not in text, "receipt must not carry absolute home paths"
with open(os.environ["RECEIPT"], "w", encoding="utf-8") as fh:
    fh.write(text)
' || fatal "receipt write failed"

# assert before announcing: the receipt must exist and carry both lane exits
grep -q '"claude"' "$receipt" && grep -q '"codex"' "$receipt" \
  || fatal "receipt missing a lane record: $receipt"

echo "claude lane exit=$claude_exit output: $(echo "$claude_out" | head -c 120)"
echo "codex lane exit=$codex_exit last-message: $(echo "$codex_last" | head -c 120)"
if [ "$claude_exit" -ne 0 ] || [ "$codex_exit" -ne 0 ]; then
  echo "driver_smoke FAIL: a lane ran but did not round-trip (see receipt)" >&2
  exit 2
fi
echo "driver_smoke PASS: both lanes round-tripped, receipt written"
exit 0
