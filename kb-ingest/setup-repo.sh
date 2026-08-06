#!/usr/bin/env bash
# setup-repo.sh <repo_name> <clone_url>
# Clone a repo (FULL history) into the skill-bettor mastery-workspace convention:
#   TARGET = <host_root>/repo/<repo_name>/<repo_name>   (basename = slug)
#   OUT    = <host_root>/repo/<repo_name>/              (repo_wiki/ · invariants/ · _judge/ land here)
# <host_root> = the checkout this module is installed in, derived via git at run time
# (override with SKILL_BETTOR_REPO_ROOT); never a hardcoded machine path.
# /repo/ is gitignored → durable on disk, never committed. NEVER clone to /tmp.
#   Run:  bash kb-ingest/setup-repo.sh repoprompt-ce https://github.com/repoprompt/repoprompt-ce.git
set -uo pipefail

NAME="${1:?repo_name (e.g. repoprompt-ce)}"; URL="${2:?clone url or local path}"
HOST_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null)" || true
[ -n "${SKILL_BETTOR_REPO_ROOT:-}" ] || [ -n "$HOST_ROOT" ] || \
  { echo "FATAL: module is not inside a git work tree — set SKILL_BETTOR_REPO_ROOT" >&2; exit 1; }
ROOT="${SKILL_BETTOR_REPO_ROOT:-"$HOST_ROOT/repo"}/$NAME"; TARGET="$ROOT/$NAME"

if [ -d "$TARGET/.git" ]; then
  echo "Clone already present → $TARGET (skipping clone)"
else
  mkdir -p "$ROOT"
  echo "Cloning FULL history (never --depth 1) → $TARGET ..."
  git clone "$URL" "$TARGET" || { echo "FATAL: clone failed" >&2; exit 1; }
fi

git -C "$TARGET" rev-parse --is-shallow-repository 2>/dev/null | grep -qx false || \
  echo "WARN: shallow clone — run 'git -C $TARGET fetch --unshallow' before extraction (rationale grounding needs history)" >&2

echo "OK — convention location set:"
echo "  TARGET (read-only) = $TARGET  (HEAD $(git -C "$TARGET" rev-parse --short HEAD 2>/dev/null), $(git -C "$TARGET" rev-list --count HEAD 2>/dev/null) commits)"
echo "  OUT (artifacts)    = $ROOT   (durable, gitignored, NOT /tmp)"
echo "  Next → tell Claude: run /repo-wiki-converge (L1) or L2 repo-agent-native on $TARGET"
