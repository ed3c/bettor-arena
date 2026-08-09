#!/bin/sh
set -u
HERE=$(cd "$(dirname "$0")" && pwd -P)
command -v python3 >/dev/null 2>&1 || {
  echo "SELFTEST FATAL: python3 absent" >&2
  exit 64
}
for required in \
  equivalence.py \
  drift.py \
  profile/technical-equivalence.md \
  adapter-registry.json \
  schemas
do
  [ -e "$HERE/$required" ] || {
    echo "SELFTEST RED: required mechanism input absent: $required" >&2
    exit 2
  }
done
exec python3 "$HERE/selftest.py"
