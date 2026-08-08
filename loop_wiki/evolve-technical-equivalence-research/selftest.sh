#!/bin/sh
set -u
HERE=$(cd "$(dirname "$0")" && pwd -P)
exec python3 "$HERE/selftest.py"
