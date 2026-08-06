#!/bin/bash
# open_decision_cockpit.sh — /html-for-decisions 復用入口(唯一復用命令)。
# [med4 修] 把 serve/reset/open 的入口提升到 skill scripts,接「決策包目錄」參數,不再綁死單一沙盒。
# 腳本串聯:reset-pending(dj.py,清舊決策防 stale)→ decision_server.py --pack <pack>(server 已參數化)→ 印 URL。
# 用法: open_decision_cockpit.sh <pack-dir> [port]    ·    open_decision_cockpit.sh --selftest
set -uo pipefail
ROOT="$(git rev-parse --show-toplevel)"
ENGINE="$ROOT/loop_wiki/dx-adversarial-fix"      # 參考引擎:server + dj.py(pack 只需 shell/data)
SERVER="$ENGINE/decision_server.py"; DJPY="$ENGINE/dj.py"

do_selftest() {
  local pack="$ENGINE"
  [ -f "$pack/decision-shell.html" ] && [ -f "$pack/decision-data.json" ] || { echo "SELFTEST RED: pack 缺 shell/data"; return 1; }
  python3 -m py_compile "$SERVER" || { echo "SELFTEST RED: server 語法"; return 1; }
  [ -f "$DJPY" ] || { echo "SELFTEST RED: 缺 dj.py"; return 1; }
  local tmp; tmp="$(mktemp -d)"
  cp "$pack/decision-data.json" "$tmp/"
  python3 "$DJPY" reset-pending "$tmp" >/dev/null
  local st; st="$(python3 "$DJPY" get status "$tmp/decision.json")"
  rm -rf "$tmp"
  [ "$st" = "pending" ] || { echo "SELFTEST RED: reset-pending 未產 pending(得 '$st')"; return 1; }
  # server --pack 參數化:讀碼確認不再寫死 __file__ 目錄
  grep -q -- "--pack" "$SERVER" || { echo "SELFTEST RED: server 未參數化 --pack"; return 1; }
  echo "SELFTEST GREEN(pack 完整 · server --pack 參數化 · reset-pending→pending · dj.py 在)"
}

if [ "${1:-}" = "--selftest" ]; then do_selftest; exit $?; fi
PACK="${1:?用法: open_decision_cockpit.sh <pack-dir> [port]}"; PORT="${2:-8770}"
PACK="$(cd "$PACK" && pwd)"
[ -f "$PACK/decision-shell.html" ] && [ -f "$PACK/decision-data.json" ] || { echo "✗ pack 缺 decision-shell.html/decision-data.json: $PACK" >&2; exit 64; }
python3 "$DJPY" reset-pending "$PACK"                      # 重開重置 pending,不派舊決策(high2)
echo "▶ 決策 cockpit:pack=$PACK port=$PORT → http://127.0.0.1:$PORT"
echo "  (提交前 server 端會重跑 narration_gate;gate FAIL 拒收=物理閘 high1)"
exec python3 "$SERVER" --pack "$PACK" "$PORT"
