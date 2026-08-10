#!/bin/sh
# skills-bundle.sh — materialise the shared skills at a NAMED commit, for a sandbox.
#
#   sh loopctl/skills-bundle.sh --dry-run
#   sh loopctl/skills-bundle.sh <outdir>     # extracts, prints the bundle line
#   sh loopctl/skills-bundle.sh --selftest
#
# A sandbox turn currently runs with ZERO shared skills: /sandbox/.claude/skills
# and /sandbox/.codex/skills do not exist, so the whole governance layer stops at
# the host boundary. Worse than the absence is that nothing records it — ask an
# agent turn "which version of the skills did you run with" and there is no
# answer, because there were none and nothing said so.
#
# THE REFUSAL IS THE POINT. ~/.agents/skills-shared is read live by five projects
# through symlinks, so an uncommitted edit there is already in force everywhere
# while being in no commit at all. Carrying that into a sandbox would put an
# unnameable version behind a turn whose receipt claims to be reproducible. So a
# dirty canonical is FATAL by default; SKILLS_BUNDLE_ALLOW_DIRTY=1 exists for the
# case where you know, and it stamps the id `-dirty` so it can never be read
# later as a named commit.
#
# Env: SKILLS_SHARED_ROOT   override the canonical checkout (default ~/.agents/skills-shared)
#      SKILLS_BUNDLE_ALLOW_DIRTY=1   carry uncommitted canonical, id marked dirty
#
# Exit: 0 bundle written · 2 canonical is dirty · 64 FATAL (no checkout, no git)
set -u

DRY=0
OUTDIR=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1 ;;
    --selftest) SELFTEST=1 ;;
    -h|--help) sed -n '2,10p' "$0" >&2; exit 64 ;;
    -*) echo "unknown flag: $1" >&2; exit 64 ;;
    *) OUTDIR=$1 ;;
  esac
  shift
done

SHARED=${SKILLS_SHARED_ROOT:-$HOME/.agents/skills-shared}

# The one piece worth a selftest: deciding whether a canonical may be bundled and
# under what id. Everything else is `git archive` and tar.
bundle_id() { # <root> -> "<sha12>[-dirty]" on stdout, or FATAL/refusal
  _root=$1
  git -C "$_root" rev-parse --show-toplevel >/dev/null 2>&1 || {
    echo "FATAL: $_root is not a git work tree — a bundle with no commit behind it cannot be named, and an unnameable bundle behind a turn is exactly what this refuses" >&2
    return 64; }
  _sha=$(git -C "$_root" rev-parse --short=12 HEAD 2>/dev/null) || return 64
  if [ -n "$(git -C "$_root" status --porcelain 2>/dev/null)" ]; then
    if [ "${SKILLS_BUNDLE_ALLOW_DIRTY:-0}" = 1 ]; then
      printf '%s-dirty\n' "$_sha"
      return 0
    fi
    echo "REFUSED: the shared-skills canonical is dirty, so this bundle would carry edits that are in no commit — and five projects are already reading them live." >&2
    git -C "$_root" status --porcelain 2>/dev/null | sed 's/^/    /' >&2
    echo "  commit them, or re-run with SKILLS_BUNDLE_ALLOW_DIRTY=1 (the id is then marked -dirty and never reads as a named commit)" >&2
    return 2
  fi
  printf '%s\n' "$_sha"
}

if [ "${SELFTEST:-0}" = 1 ]; then
  RED=0
  say() { if [ "$2" = "$3" ]; then echo "  [ok]   $1"; else echo "  [RED]  $1 — got $2, want $3" >&2; RED=1; fi; }
  T=$(mktemp -d "${TMPDIR:-/tmp}/skills-bundle-selftest.XXXXXX")

  # Not a git tree at all.
  mkdir -p "$T/notgit"
  bundle_id "$T/notgit" >/dev/null 2>&1
  say "non-git-canonical-is-fatal" $? 64

  mkdir -p "$T/repo/skills/demo"
  git -C "$T/repo" init -q
  git -C "$T/repo" config user.email t@local
  git -C "$T/repo" config user.name t
  echo "x" >"$T/repo/skills/demo/SKILL.md"
  git -C "$T/repo" add -A
  git -C "$T/repo" commit -qm init
  CLEAN_ID=$(bundle_id "$T/repo"); CLEAN_RC=$?
  say "clean-canonical-is-bundleable" "$CLEAN_RC" 0
  case "$CLEAN_ID" in *-dirty) say "clean-id-is-not-marked-dirty" marked plain ;; *) say "clean-id-is-not-marked-dirty" plain plain ;; esac

  # The refusal, which is the mechanism.
  echo "edited but never committed" >>"$T/repo/skills/demo/SKILL.md"
  bundle_id "$T/repo" >/dev/null 2>&1
  say "dirty-canonical-is-refused" $? 2

  # The escape hatch must never produce an id that reads like a named commit.
  DIRTY_ID=$(SKILLS_BUNDLE_ALLOW_DIRTY=1 bundle_id "$T/repo"); DIRTY_RC=$?
  say "allowed-dirty-still-succeeds" "$DIRTY_RC" 0
  case "$DIRTY_ID" in
    *-dirty) echo "  [ok]   allowed-dirty-id-cannot-pass-as-a-commit" ;;
    *) echo "  [RED]  allowed-dirty-id-cannot-pass-as-a-commit — got '$DIRTY_ID', which a later reader would take for a clean commit" >&2; RED=1 ;;
  esac

  rm -rf "$T"
  [ "$RED" -eq 0 ] && { echo "SELFTEST GREEN"; exit 0; }
  echo "SELFTEST RED" >&2; exit 2
fi

[ -d "$SHARED" ] || { echo "FATAL: no shared-skills checkout at $SHARED (set SKILLS_SHARED_ROOT)" >&2; exit 64; }
ID=$(bundle_id "$SHARED") || exit $?

if [ "$DRY" -eq 1 ]; then
  echo "dry-run — the canonical was read and judged, nothing was written"
  echo "  canonical  $SHARED"
  echo "  id         $ID"
  echo "  skills     $(git -C "$SHARED" ls-files 'skills/*' | wc -l | tr -d ' ') tracked file(s) under skills/"
  echo "  targets    <sandbox>/.claude/skills and <sandbox>/.codex/skills"
  exit 0
fi

[ -n "$OUTDIR" ] || { echo "FATAL: no output directory given" >&2; exit 64; }
mkdir -p "$OUTDIR"

# `git archive` of the COMMIT, not a copy of the working tree — so what lands in
# the sandbox is exactly what the id names. With ALLOW_DIRTY the working tree is
# what is in force, so that path copies instead, and the id already says -dirty.
case "$ID" in
  *-dirty)
    ( cd "$SHARED" && tar cf - skills ) | ( cd "$OUTDIR" && tar xf - )
    ;;
  *)
    git -C "$SHARED" archive --format=tar HEAD skills | ( cd "$OUTDIR" && tar xf - )
    ;;
esac

COUNT=$(find "$OUTDIR/skills" -type f 2>/dev/null | wc -l | tr -d ' ')
[ "$COUNT" -gt 0 ] || { echo "FATAL: the bundle came out empty — a sandbox given nothing looks identical to one given everything" >&2; exit 64; }
echo "skills-bundle id=$ID files=$COUNT dir=$OUTDIR/skills"
