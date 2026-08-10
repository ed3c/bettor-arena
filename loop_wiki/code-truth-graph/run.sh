#!/bin/sh
set -u

HERE=$(cd "$(dirname "$0")" && pwd -P) || exit 64
PYTHONPATH="$HERE/src${PYTHONPATH:+:$PYTHONPATH}" \
  exec python3 -m code_truth_graph.cli "$@" </dev/null
