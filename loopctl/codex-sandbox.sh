#!/bin/sh
# codex-sandbox.sh — run codex as a WRITING role inside an OpenShell sandbox.
#
#   sh loopctl/codex-sandbox.sh --dry-run "<prompt>"
#   sh loopctl/codex-sandbox.sh "refactor X and leave the tests passing"
#   sh loopctl/codex-sandbox.sh --selftest
#
# The ordinary ChatGPT auth.json path parses JWTs before making a request, so an
# OpenShell placeholder cannot go there. The stronger route is a custom Codex
# model provider: env_key and ChatGPT-Account-ID are opaque placeholders in the
# HTTPS request, then the OpenShell proxy substitutes them. The sandbox never
# receives, reconstructs, mounts, or uploads auth.json.
#
# Exit: 0 the turn ran · 2 the turn failed · 64 FATAL (no runtime, no session)
set -u

usage() {
  cat >&2 <<'USAGE'
usage: sh loopctl/codex-sandbox.sh [--dry-run] [--keep] [--out DIR] <prompt>
       sh loopctl/codex-sandbox.sh --selftest

  --dry-run   print the plan and run every precondition, create nothing
  --keep      leave the sandbox running after the turn (for inspection)
  --out DIR   where changed files land (default: data/codex-sandbox/<utc>)
USAGE
  exit 64
}

DRY=0
KEEP=0
OUT=""
PROMPT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1 ;;
    --keep) KEEP=1 ;;
    --out) shift; [ $# -gt 0 ] || usage; OUT=$1 ;;
    --selftest) SELFTEST=1 ;;
    -h|--help) usage ;;
    -*) echo "unknown flag: $1" >&2; usage ;;
    *) [ -z "$PROMPT" ] || usage; PROMPT=$1 ;;
  esac
  shift
done

ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "FATAL: not inside a git work tree — the upload is scoped to the repo root" >&2; exit 64; }
POLICY="$ROOT/.runtime-env/policies/codex-openshell-chatgpt-placeholder.json"
RENDERER="$ROOT/loopctl/codex-openshell-config.py"

if [ "${SELFTEST:-0}" = 1 ]; then
  python3 "$RENDERER" --policy "$POLICY" --selftest || exit $?
  echo "SELFTEST GREEN"
  exit 0
fi

[ -n "$PROMPT" ] || usage
command -v openshell >/dev/null 2>&1 || {
  echo "FATAL: openshell is not on PATH" >&2; exit 64; }
PROVIDER=${OPENSHELL_CODEX_PROVIDER:-codex-runtime-env}
MODEL=${CODEX_SANDBOX_MODEL:-gpt-5.6-sol}
case "$MODEL" in
  ''|*[!A-Za-z0-9._:/-]*)
    echo "FATAL: CODEX_SANDBOX_MODEL contains unsupported characters" >&2
    exit 64 ;;
esac
CONFIG=$(python3 "$RENDERER" --policy "$POLICY") || exit $?
[ -n "$CONFIG" ] || { echo "FATAL: rendered Codex provider config is empty" >&2; exit 64; }
CONFIG_B64=$(printf '%s' "$CONFIG" | base64 | tr -d '\n')

PROVIDERS=$(openshell provider list 2>&1); PROVIDERS_RC=$?
if [ "$PROVIDERS_RC" -ne 0 ]; then
  echo "FATAL: could not query OpenShell providers (exit $PROVIDERS_RC); this is not a missing provider" >&2
  printf '%s\n' "$PROVIDERS" | head -1 >&2
  exit 64
fi
printf '%s\n' "$PROVIDERS" | awk -v wanted="$PROVIDER" '
  $1 == wanted && $2 == "codex" { found = 1 }
  END { exit(found ? 0 : 1) }
' || {
  echo "FATAL: OpenShell answered, but codex provider '$PROVIDER' is absent" >&2
  echo "       bootstrap it from a trusted runtime-env checkout" >&2
  exit 64
}

# OrbStack redirects the docker CLI through a context, so a dead
# /var/run/docker.sock refuses while `docker ps` works. Announced, not silent.
if [ -z "${DOCKER_HOST:-}" ] && [ -S "$HOME/.orbstack/run/docker.sock" ]; then
  DOCKER_HOST="unix://$HOME/.orbstack/run/docker.sock"
  export DOCKER_HOST
  echo "DOCKER_HOST -> orbstack socket"
fi

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
NAME=${CODEX_SANDBOX_NAME:-codex-write-$STAMP}
[ -n "$OUT" ] || OUT="$ROOT/data/codex-sandbox/$STAMP"
WORK="/sandbox/$(basename "$ROOT")"

# The shared skills, at a NAMED commit — resolved BEFORE the dry-run returns,
# because it is a precondition that can refuse, and a dry-run that stops short of
# a refusal is not a dry-run. Without it the turn runs with none at all
# (/sandbox/.codex/skills does not exist) and, worse, nothing records that, so
# "which skills was this turn running with" has no answer at all.
#
# Opt-in: it refuses a dirty canonical, and a caller who has not yet decided what
# to do about that should not be blocked from taking an ordinary turn.
SKILLS_ARGS=""
SKILLS_LINE="skills-bundle: not carried (SANDBOX_SKILLS=1 to include them)"
if [ "${SANDBOX_SKILLS:-0}" = 1 ]; then
  SKILLS_DIR="$OUT/skills-bundle"
  if SKILLS_LINE=$(sh "$ROOT/loopctl/skills-bundle.sh" "$SKILLS_DIR" 2>&1); then
    SKILLS_ARGS="--upload $SKILLS_DIR/skills:/sandbox/.codex/skills"
  else
    printf '%s\n' "$SKILLS_LINE" >&2
    echo "FATAL: skills were asked for and could not be named — taking the turn anyway would put an unnameable version behind a receipt that claims to be reproducible" >&2
    exit 64
  fi
fi

if [ "$DRY" -eq 1 ]; then
  cat <<EOF
dry-run — every precondition ran, nothing was created
  provider  $PROVIDER (type=codex; sandbox receives placeholders only)
  model     $MODEL
  sandbox   $NAME  policy=loopctl/sandbox-policy.yaml  image=loopctl/Dockerfile
  upload    $ROOT -> $WORK   (no .git travels; codex runs with --skip-git-repo-check)
  skills    $SKILLS_LINE
  turn      codex exec -s danger-full-access
  changes   -> $OUT
EOF
  exit 0
fi

openshell sandbox delete "$NAME" >/dev/null 2>&1

# -s danger-full-access, and the name overstates it here. Codex confines its own
# shell commands with bubblewrap, which cannot create a user namespace inside
# this container — the turn fails with a bwrap namespace error and writes
# nothing. Turning that inner layer off does not widen the boundary: the outer
# sandbox still holds Landlock, seccomp, and deny-by-default egress bound to this
# binary. It is the same argument OpenShell's own docker driver makes when it
# drops AppArmor — redundant relative to the controls already in place, and in
# conflict with them.
INNER='
set -u
mkdir -p "$HOME/.codex"
printf "%s" "$CODEX_CONFIG_B64" | base64 -d >"$HOME/.codex/config.toml"
chmod 600 "$HOME/.codex/config.toml"
cd '"$WORK"' || exit 64

# A hashed manifest either side of the turn, not a timestamp sweep. `find -newer`
# cannot see a DELETION, and a packet that silently drops removals is worse than
# one that admits it: whoever applies it re-creates the file the agent decided to
# remove. 504 tracked files makes hashing twice free, so there is no reason to
# take the lossy reading.
manifest() { find . -type f -not -path "./.git/*" -not -name codex-changes.tar -exec sha256sum {} + 2>/dev/null | sort; }
manifest >/tmp/before.txt

codex exec --strict-config --skip-git-repo-check -s danger-full-access \
  -c approval_policy=never -c "model=\"$CODEX_SANDBOX_MODEL\"" "$CODEX_PROMPT"
rc=$?

manifest >/tmp/after.txt
# Only-in-after by whole line = created or edited. Only-in-before by PATH =
# deleted; comparing paths rather than lines here, or every edit would also
# read as a deletion.
comm -13 /tmp/before.txt /tmp/after.txt | sed "s/^[0-9a-f]*  //" >/tmp/changed.txt
sed "s/^[0-9a-f]*  //" /tmp/before.txt | sort >/tmp/bp.txt
sed "s/^[0-9a-f]*  //" /tmp/after.txt  | sort >/tmp/ap.txt
comm -23 /tmp/bp.txt /tmp/ap.txt >/tmp/_codex_deleted.txt

echo "changed files: $(wc -l </tmp/changed.txt)"
echo "deleted files: $(wc -l </tmp/_codex_deleted.txt)"
if [ -s /tmp/changed.txt ] || [ -s /tmp/_codex_deleted.txt ]; then
  cp /tmp/_codex_deleted.txt ./_codex_deleted.txt
  tar cf /sandbox/codex-changes.tar -T /tmp/changed.txt ./_codex_deleted.txt
  rm -f ./_codex_deleted.txt
fi
exit $rc
'

printf '%s\n' "$SKILLS_LINE"
openshell sandbox create --name "$NAME" --no-tty \
  --policy "$ROOT/loopctl/sandbox-policy.yaml" \
  --provider "$PROVIDER" \
  --env "CODEX_CONFIG_B64=$CONFIG_B64" \
  --env "CODEX_SANDBOX_MODEL=$MODEL" \
  --env "CODEX_PROMPT=$PROMPT" \
  $SKILLS_ARGS \
  --from "$ROOT/loopctl/Dockerfile" --upload "$ROOT" \
  -- sh -c "$INNER"
TURN_RC=$?

mkdir -p "$OUT"
if openshell sandbox download "$NAME" /sandbox/codex-changes.tar "$OUT" >/dev/null 2>&1 &&
   [ -f "$OUT/codex-changes.tar" ]; then
  ( cd "$OUT" && tar xf codex-changes.tar && rm -f codex-changes.tar )
  echo "changes -> $OUT"
  find "$OUT" -type f -not -name _codex_deleted.txt | sed 's|^|  +|'
  # Deletions travel as a LIST, not as absences: a tar cannot carry a file that
  # is not there, so applying this packet without reading it would restore
  # whatever the turn removed.
  if [ -s "$OUT/_codex_deleted.txt" ]; then
    echo "deleted by the turn (not applied automatically — remove these yourself):"
    sed 's|^|  -|' "$OUT/_codex_deleted.txt"
  fi
else
  echo "no changed files came back (the turn wrote nothing, or it never got that far)"
fi

[ "$KEEP" -eq 1 ] || openshell sandbox delete "$NAME" >/dev/null 2>&1
[ "$TURN_RC" -eq 0 ] || { echo "the codex turn exited $TURN_RC" >&2; exit 2; }
exit 0
