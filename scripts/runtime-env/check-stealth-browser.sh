#!/bin/sh
set -eu

ROOT=${STEALTH_BROWSER_ROOT:?STEALTH_BROWSER_ROOT is required}
case "$ROOT" in
  /*) ;;
  *) echo "stealth-browser control FATAL: root must be absolute" >&2; exit 64 ;;
esac

TOP=$(git -C "$ROOT" rev-parse --show-toplevel 2>/dev/null) || {
  echo "stealth-browser control FATAL: root is not a Git checkout" >&2
  exit 64
}
[ "$TOP" = "$ROOT" ] || {
  echo "stealth-browser control FATAL: root is not the checkout top level" >&2
  exit 64
}

for required in \
  package.json package-lock.json src/cli.ts src/index.ts \
  tests/cli.test.ts tests/dr-cdp-mode.test.ts \
  tests/dr-html-to-markdown.test.ts tests/dr-report-html-extract.test.ts
do
  [ -e "$ROOT/$required" ] || {
    echo "stealth-browser control RED: required module absent: $required" >&2
    exit 2
  }
done

if [ -n "$(git -C "$ROOT" status --porcelain=v1)" ]; then
  echo "stealth-browser control RED: checkout is dirty and not admitted" >&2
  exit 2
fi

cd "$ROOT" || exit 64
exec ./node_modules/.bin/vitest run \
  tests/cli.test.ts \
  tests/dr-cdp-mode.test.ts \
  tests/dr-html-to-markdown.test.ts \
  tests/dr-report-html-extract.test.ts
