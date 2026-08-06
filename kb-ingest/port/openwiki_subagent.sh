#!/usr/bin/env bash
# openwiki_subagent.sh <critic|finder|verifier> <TARGET> [PAYLOAD_FILE]
#
# TARGET is always the repository being documented; each role derives its own
# sandbox from it. Payload (skeleton scope / question set / verification batch)
# comes from PAYLOAD_FILE or stdin.
#
# Runs one of OpenWiki's three official review subagents as an isolated child
# process on Claude Code or Codex CLI. NO API KEY: inference is the host CLI's
# own subscription session.
#
# Why subprocesses instead of an in-session subagent: each subagent's READ
# BOUNDARY is load-bearing, and upstream can only assert it in prose (deepagents
# subagents share one virtual filesystem). Break the boundary and the gate is
# self-deception -- an answer_verifier that peeks at source is answering FROM
# source, not testing whether the wiki can answer. Here the boundary is the
# directory the child can see:
#
#   critic    throwaway git worktree at TARGET HEAD + the skeleton copied in.
#             Read-only reviewer; any write it attempts dies with the worktree.
#   finder    same worktree with openwiki/ DELETED. It cannot read the wiki
#             because the wiki is not there. (Deleting inside a throwaway
#             worktree never touches the real target.)
#   verifier  cwd = a scratch copy of the wiki only. No repository source
#             exists in it, so it can only answer from the wiki.
#
# Env:
#   OPENWIKI_HOST   claude | codex   (default: codex when present -- its -C plus
#                                     -s read-only make the boundary a sandbox,
#                                     not an instruction)
#   OPENWIKI_MODEL  model override passed to the host CLI
#
# Writes the child's final message to <TARGET>/.openwiki-review/<role>-latest.txt
# and echoes that path. It lives OUTSIDE openwiki/ on purpose: anything inside
# the wiki tree becomes a section directory to the index generator.
#
# Exit: 0 ok · 1 run failed · 2 bad usage
set -uo pipefail

ROLE="${1:?critic|finder|verifier}"
TARGET="${2:?target repo (verifier: wiki snapshot dir)}"
PAYLOAD="${3:-}"
HERE="$(cd "$(dirname "$0")" && pwd)"
PROMPTS="$HERE/../openwiki/subagents"

case "$ROLE" in
  critic)   SYS="$PROMPTS/skeleton-critic.md" ;;
  finder)   SYS="$PROMPTS/question-finder.md" ;;
  verifier) SYS="$PROMPTS/answer-verifier.md" ;;
  *) echo "FATAL: role must be critic|finder|verifier" >&2; exit 2 ;;
esac
[ -f "$SYS" ] || { echo "FATAL: missing prompt asset $SYS — run kb-ingest/port/sync_prompts.py" >&2; exit 1; }

HOST="${OPENWIKI_HOST:-}"
if [ -z "$HOST" ]; then
  if command -v codex >/dev/null 2>&1; then HOST=codex
  elif command -v claude >/dev/null 2>&1; then HOST=claude
  else echo "FATAL: neither codex nor claude found on PATH" >&2; exit 1; fi
fi

# Extract only the official systemPrompt section; the provenance header and the
# dispatch description are not part of the child's system prompt.
SYSTEM_PROMPT="$(awk '/^## systemPrompt$/{f=1;next} /^<!-- OPENWIKI-OFFICIAL:END/{f=0} f' "$SYS")"
[ -n "$SYSTEM_PROMPT" ] || { echo "FATAL: could not extract systemPrompt from $SYS" >&2; exit 1; }

# WT_REPO is set only on the worktree path, so cleanup never fires for a sandbox
# that was a plain copy (there is nothing registered with git to unregister).
WORKTREE=""; WT_REPO=""
cleanup() {
  [ -n "$WORKTREE" ] && [ -n "$WT_REPO" ] && \
    git -C "$WT_REPO" worktree remove --force "$WORKTREE" >/dev/null 2>&1
  return 0
}
trap cleanup EXIT

if [ "$ROLE" = "verifier" ]; then
  # Snapshot the wiki into a scratch directory so the child sees the wiki and
  # nothing else. Copying here rather than asking the caller to prepare a
  # directory keeps the boundary a property of the runner, not of discipline.
  REPO="$(cd "$TARGET" && pwd)"
  [ -d "$REPO/openwiki" ] || { echo "FATAL: no wiki at $REPO/openwiki" >&2; exit 1; }
  SNAPSHOT="$(mktemp -d "${TMPDIR:-/tmp}/openwiki-verifier-XXXXXX")"
  # The wiki keeps its openwiki/ prefix inside the sandbox. The official verifier
  # prompt says "Search only files under /openwiki", so flattening the pages to the
  # sandbox root makes the child look for a directory that is not there and report
  # every question FAIL for the wrong reason. Path SHAPE is part of the contract,
  # not just path CONTENT.
  mkdir -p "$SNAPSHOT/openwiki"
  cp -R "$REPO/openwiki/." "$SNAPSHOT/openwiki/"
  # Control files are not wiki pages. _skeleton.md/_plan.md state what was
  # INTENDED, which is exactly the thing a verifier must not be able to mistake
  # for what the wiki actually says.
  rm -r "$SNAPSHOT/openwiki/_skeleton.md" "$SNAPSHOT/openwiki/_plan.md" 2>/dev/null || true
  SANDBOX="$SNAPSHOT"
  OUTDIR="$REPO/.openwiki-review"
else
  REPO="$(cd "$TARGET" && pwd)"
  OUTDIR="$REPO/.openwiki-review"
  # A worktree is only the right sandbox when TARGET is the root of its OWN
  # repository. A vendored subdirectory sits inside some enclosing repo, and
  # `git worktree add` there would check out THAT repo -- handing the child the
  # whole parent tree instead of the target, which is both a boundary leak and
  # the wrong content. Fall back to a copy when the toplevel is not the target.
  TOPLEVEL="$(git -C "$REPO" rev-parse --show-toplevel 2>/dev/null || true)"
  if [ "$TOPLEVEL" = "$REPO" ]; then
    WORKTREE="$(mktemp -d "${TMPDIR:-/tmp}/openwiki-$ROLE-XXXXXX")"
    rmdir "$WORKTREE"
    git -C "$REPO" worktree add --detach "$WORKTREE" HEAD >/dev/null 2>&1 || {
      echo "FATAL: git worktree add failed for $REPO" >&2; WORKTREE=""; exit 1; }
    SANDBOX="$WORKTREE"; WT_REPO="$REPO"
  else
    [ -n "$TOPLEVEL" ] && echo "[$ROLE] note: $REPO is not its own repository (enclosing: $TOPLEVEL);" \
      "using a copied sandbox, and target git history is NOT available to this child" >&2
    SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/openwiki-$ROLE-XXXXXX")"
    cp -R "$REPO/." "$SANDBOX/"
    rm -rf "$SANDBOX/.git"
  fi

  if [ "$ROLE" = "finder" ]; then
    # The physical boundary: the generated wiki must not exist in this checkout.
    # Untracked output is already absent from a HEAD worktree; a committed
    # openwiki/ is removed here, inside the disposable copy only.
    rm -rf "$SANDBOX/openwiki"
  else
    SKEL="$REPO/openwiki/_skeleton.md"
    [ -f "$SKEL" ] || { echo "FATAL: no skeleton at $SKEL — the init run must write it first" >&2; exit 1; }
    mkdir -p "$SANDBOX/openwiki"
    cp "$SKEL" "$SANDBOX/openwiki/_skeleton.md"
  fi
fi

mkdir -p "$OUTDIR"
# OPENWIKI_LABEL keeps a wave of concurrent runs from overwriting each other. The
# official verifier procedure launches every batch of a wave together, so without
# a per-batch label the last writer would silently win and the other batches'
# verdicts would vanish.
OUT="$OUTDIR/$ROLE${OPENWIKI_LABEL:+-$OPENWIKI_LABEL}-latest.txt"

# The invocation payload (skeleton scope / question set / batch to verify) comes
# from a file when given, otherwise from stdin. Never block on an idle terminal.
if [ -n "$PAYLOAD" ]; then
  [ -f "$PAYLOAD" ] || { echo "FATAL: payload file not found: $PAYLOAD" >&2; exit 2; }
  USER_PROMPT="$(cat "$PAYLOAD")"
elif [ ! -t 0 ]; then
  USER_PROMPT="$(cat)"
else
  USER_PROMPT=""
fi
[ -n "$USER_PROMPT" ] || { echo "FATAL: no invocation payload (pass a file, or pipe it in)" >&2; exit 2; }

# Shape assertions. The read boundary is only half the contract: each official
# prompt also assumes where things ARE. A sandbox with the right content at the
# wrong path makes a child report a uniform failure for a reason that has nothing
# to do with the wiki's quality.
case "$ROLE" in
  verifier)
    [ -n "$(find "$SANDBOX/openwiki" -name '*.md' -print -quit 2>/dev/null)" ] || {
      echo "FATAL: verifier sandbox has no openwiki/*.md — the official prompt only searches /openwiki" >&2
      exit 1; }
    [ -d "$SANDBOX/scripts" ] && { echo "FATAL: verifier sandbox leaks repository source" >&2; exit 1; }
    ;;
  finder)
    [ -d "$SANDBOX/openwiki" ] && { echo "FATAL: finder sandbox leaks the generated wiki" >&2; exit 1; }
    ;;
  critic)
    [ -f "$SANDBOX/openwiki/_skeleton.md" ] || {
      echo "FATAL: critic sandbox has no openwiki/_skeleton.md to review" >&2; exit 1; }
    ;;
esac

echo "[$ROLE] host=$HOST sandbox=$SANDBOX"

# Proves the read boundary before spending a turn on it: lists what the child
# will actually be able to see, then exits without invoking the host.
if [ -n "${OPENWIKI_DRY_RUN:-}" ]; then
  echo "[dry-run] system prompt: $(printf '%s' "$SYSTEM_PROMPT" | wc -l | tr -d ' ') lines"
  echo "[dry-run] payload: $(printf '%s' "$USER_PROMPT" | wc -c | tr -d ' ') bytes"
  echo "[dry-run] sandbox top level:"
  ls -A "$SANDBOX" | sed 's/^/           /'
  exit 0
fi

if [ "$HOST" = "codex" ]; then
  # codex exec has no system-prompt flag, so the official system prompt is
  # prepended to the turn. -s read-only is a real sandbox, not an instruction.
  # codex streams its whole reasoning trace to stderr (hundreds of KB); park it in
  # a log next to the review instead of drowning the caller. The trace is still
  # there to diagnose a failed run.
  printf '%s\n\n---\n\n%s\n' "$SYSTEM_PROMPT" "$USER_PROMPT" | \
    codex exec -C "$SANDBOX" -s read-only --skip-git-repo-check --ephemeral \
      ${OPENWIKI_MODEL:+-m "$OPENWIKI_MODEL"} -o "$OUT" - >/dev/null 2>"$OUTDIR/$ROLE${OPENWIKI_LABEL:+-$OPENWIKI_LABEL}-trace.log"
  STATUS=$?
  [ "$STATUS" -eq 0 ] || tail -20 "$OUTDIR/$ROLE${OPENWIKI_LABEL:+-$OPENWIKI_LABEL}-trace.log" >&2
else
  # An array, not a bare word split: the Bash(...) specifiers contain `*` and
  # would otherwise be glob-expanded against the cwd.
  if [ "$ROLE" = "verifier" ]; then
    TOOLS=(Read Grep Glob)
  else
    TOOLS=(Read Grep Glob 'Bash(git log:*)' 'Bash(git show:*)' 'Bash(git diff:*)'
           'Bash(rg:*)' 'Bash(ls:*)')
  fi
  ( cd "$SANDBOX" && claude -p --system-prompt "$SYSTEM_PROMPT" \
      --allowedTools "${TOOLS[@]}" --add-dir "$SANDBOX" --no-session-persistence \
      ${OPENWIKI_MODEL:+--model "$OPENWIKI_MODEL"} "$USER_PROMPT" ) > "$OUT"
  STATUS=$?
fi

if [ "$STATUS" -ne 0 ] || [ ! -s "$OUT" ]; then
  echo "FATAL: $ROLE run failed (status=$STATUS, output $( [ -s "$OUT" ] && echo non-empty || echo empty ))" >&2
  echo "       An empty review is NOT a pass — do not treat it as one." >&2
  exit 1
fi

echo "$OUT"
