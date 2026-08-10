#!/bin/sh
set -u

HERE=$(cd "$(dirname "$0")" && pwd -P) || exit 64
if [ "$#" -ne 2 ]; then
  echo "usage: local-trigger.sh <absolute-manifest> <absolute-fresh-output>" >&2
  exit 64
fi

PYTHONPATH="$HERE/src${PYTHONPATH:+:$PYTHONPATH}" \
  exec python3 -m code_truth_graph.local_cli \
    --manifest "$1" \
    --output "$2" </dev/null
