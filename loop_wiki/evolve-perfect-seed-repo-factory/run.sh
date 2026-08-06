#!/bin/sh
set -eu

ROOT=$(cd "$(dirname "$0")" && pwd -P)
if [ "$#" -ne 2 ]; then
  echo "usage: run.sh <packet> <absolute-output>" >&2
  exit 64
fi

PACKET=$(cd "$(dirname "$1")" && pwd -P)/$(basename "$1")
OUTPUT=$2
cd "$ROOT"
exec bun run src/cli.ts build --packet "$PACKET" --output "$OUTPUT" </dev/null
