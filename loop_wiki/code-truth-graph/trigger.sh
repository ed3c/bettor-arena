#!/bin/sh
set -u

HERE=$(cd "$(dirname "$0")" && pwd -P) || exit 64
if [ "$#" -ne 2 ]; then
  echo "usage: trigger.sh <packet> <absolute-fresh-output>" >&2
  exit 64
fi

exec sh "$HERE/run.sh" --packet "$1" --output "$2" </dev/null
