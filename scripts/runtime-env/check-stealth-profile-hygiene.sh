#!/bin/sh
set -eu

REPO=${STEALTH_BROWSER_ROOT:?STEALTH_BROWSER_ROOT is required}
PROFILE_ROOT=${STEALTH_PROFILE_ROOT:?STEALTH_PROFILE_ROOT is required}

case "$REPO" in /*) ;; *) echo "stealth profile hygiene FATAL: repo root must be absolute" >&2; exit 64;; esac
case "$PROFILE_ROOT" in /*) ;; *) echo "stealth profile hygiene FATAL: profile root must be absolute" >&2; exit 64;; esac
REPO=$(cd "$REPO" 2>/dev/null && pwd -P) || {
  echo "stealth profile hygiene FATAL: repo root is not a directory" >&2
  exit 64
}
PROFILE_ROOT=$(cd "$PROFILE_ROOT" 2>/dev/null && pwd -P) || {
  echo "stealth profile hygiene RED: profile root is not a directory" >&2
  exit 2
}

TOP=$(git -C "$REPO" rev-parse --show-toplevel 2>/dev/null) || {
  echo "stealth profile hygiene FATAL: STEALTH_BROWSER_ROOT is not a Git checkout" >&2
  exit 64
}
[ "$TOP" = "$REPO" ] || {
  echo "stealth profile hygiene FATAL: STEALTH_BROWSER_ROOT is not its checkout top level" >&2
  exit 64
}

case "$PROFILE_ROOT/" in
  "$REPO/"*) echo "stealth profile hygiene RED: profile root must be outside the repository" >&2; exit 2;;
esac

if [ -n "$(git -C "$REPO" ls-files -- 'profiles/**' 'profiles/*' 2>/dev/null)" ]; then
  echo "stealth profile hygiene RED: credential profile path is tracked by Git" >&2
  exit 2
fi
if [ -d "$REPO/profiles" ] && find "$REPO/profiles" \( -type f -o -type l \) -print -quit | grep -q .; then
  echo "stealth profile hygiene RED: repo-local credential profile exists" >&2
  exit 2
fi

[ -d "$PROFILE_ROOT" ] && [ ! -L "$PROFILE_ROOT" ] || {
  echo "stealth profile hygiene RED: host profile root must be a real directory" >&2
  exit 2
}
CURRENT_UID=$(id -u)
root_uid=$(stat -f '%u' "$PROFILE_ROOT")
root_mode=$(stat -f '%Lp' "$PROFILE_ROOT")
[ "$root_uid" = "$CURRENT_UID" ] && [ "$root_mode" = 700 ] || {
  echo "stealth profile hygiene RED: host profile root must be user-owned mode 0700" >&2
  exit 2
}

if find "$PROFILE_ROOT" -type l -print -quit | grep -q .; then
  echo "stealth profile hygiene RED: symlink found below host profile root" >&2
  exit 2
fi

find "$PROFILE_ROOT" -type d -print | while IFS= read -r path; do
  [ "$(stat -f '%u' "$path")" = "$CURRENT_UID" ] && [ "$(stat -f '%Lp' "$path")" = 700 ] || {
    echo "stealth profile hygiene RED: profile directory must be user-owned mode 0700" >&2
    exit 2
  }
done

find "$PROFILE_ROOT" -type f -print | while IFS= read -r path; do
  case "${path##*/}" in state.json|locked-fingerprint.json) ;; *)
    echo "stealth profile hygiene RED: undeclared file below profile root" >&2
    exit 2;;
  esac
  [ "$(stat -f '%u' "$path")" = "$CURRENT_UID" ] && [ "$(stat -f '%Lp' "$path")" = 600 ] || {
    echo "stealth profile hygiene RED: profile file must be user-owned mode 0600" >&2
    exit 2
  }
done

echo "PASS: stealth browser profiles are host-only; values not read"
