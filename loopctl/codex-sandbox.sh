#!/bin/sh
# codex-sandbox.sh — run codex as a WRITING role inside an OpenShell sandbox.
#
#   sh loopctl/codex-sandbox.sh --dry-run "<prompt>"
#   sh loopctl/codex-sandbox.sh "refactor X and leave the tests passing"
#   sh loopctl/codex-sandbox.sh --selftest
#
# claude reaches the model through a provider and never holds its credential: the
# sandbox carries `openshell:resolve:env:v<n>_...` and the proxy substitutes on
# the way out. Codex CANNOT use that model, and the reason is measured rather
# than assumed — it parses its credential as a JWT before any request, so a
# placeholder dies locally with `invalid agent identity JWT format`.
#
# So this path is deliberately weaker and says so: the REAL ChatGPT session is
# handed in literally through `--env`, reconstructed as ~/.codex/auth.json inside
# the sandbox, and is therefore readable by everything running there. What keeps
# that bounded is the policy — deny-by-default egress, bound to codex's binary —
# and the fact that the sandbox is disposable. Do not run this against a sandbox
# you would not hand that session to.
#
# `--with-access-token` is NOT the way in. It wants codex's own agent-identity
# JWT, a different credential entirely; feeding it a ChatGPT access token fails
# with `agent identity JWT payload is not valid JSON`, which reads like a corrupt
# token and is not one.
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
AUTH_FILE=${CODEX_AUTH_FILE:-$HOME/.codex/auth.json}

# --- the one thing worth a selftest: reading a session and judging it ---------
# Every other step here costs a sandbox. This is the step that decides whether a
# turn is even possible, and it has three distinct refusals that must not blur
# into each other.
read_session() { # <auth.json path> -> compact json on stdout, or FATAL
  python3 - "$1" <<'PY'
import base64, json, sys, time

path = sys.argv[1]
try:
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
except FileNotFoundError:
    sys.exit("FATAL: no codex session at %s — run `codex login` on the host first" % path)
except json.JSONDecodeError as exc:
    sys.exit("FATAL: %s is not valid JSON (%s); a half-written session would fail inside the sandbox as an auth error" % (path, exc))

mode = d.get("auth_mode")
if mode != "chatgpt":
    sys.exit(
        "FATAL: auth_mode is %r, not 'chatgpt'. An API-key session should go through an "
        "OpenShell provider instead, where the key never enters the sandbox at all." % (mode,)
    )
token = (d.get("tokens") or {}).get("access_token") or ""
if not token:
    sys.exit("FATAL: the session carries no access_token")

# Decode, never verify — this is an expiry check, not authentication. An expired
# token fails inside the sandbox minutes later as an opaque auth error, which is
# the most expensive place to learn something knowable here for free.
try:
    payload = token.split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
except Exception as exc:
    sys.exit("FATAL: the access_token is not a decodable JWT (%s)" % exc)
exp = claims.get("exp")
if exp is None:
    sys.exit("FATAL: the access_token carries no exp claim, so its validity cannot be judged here")
left = exp - time.time()
if left <= 0:
    sys.exit("FATAL: the codex session expired %d hours ago — run any codex command on the host to refresh it" % (-left // 3600))
# The session lasts ~10 days and the host's codex renews it lazily, so the
# failure mode is not "it expires mid-turn" but "nobody ran codex on the host for
# a fortnight". Warning inside the last day turns that into something visible
# while it is still free to fix, instead of a FATAL on the morning it matters.
if left < 24 * 3600:
    print(
        "WARNING: %d hours of session left. Run any codex turn on the host to renew it "
        "(`codex exec -s read-only 'ok'`) before it becomes a FATAL here." % (left // 3600),
        file=sys.stderr,
    )
print("session ok: %d hours of validity left" % (left // 3600), file=sys.stderr)
print(json.dumps(d, separators=(",", ":")))
PY
}

if [ "${SELFTEST:-0}" = 1 ]; then
  RED=0
  T=$(mktemp -d "${TMPDIR:-/tmp}/codex-sandbox-selftest.XXXXXX")
  check() { # name expected-substring actual-rc actual-err
    if [ "$3" -ne 0 ] && printf '%s' "$4" | grep -q "$2"; then
      echo "  [ok]   $1"
    else
      echo "  [RED]  $1 — rc=$3 err=$(printf '%s' "$4" | head -1)" >&2; RED=1
    fi
  }
  E=$(read_session "$T/missing.json" 2>&1 >/dev/null); check "absent-session-is-fatal" "no codex session" $? "$E"
  printf 'not json' >"$T/bad.json"
  E=$(read_session "$T/bad.json" 2>&1 >/dev/null); check "unparseable-session-is-fatal" "not valid JSON" $? "$E"
  printf '{"auth_mode":"apikey"}' >"$T/apikey.json"
  E=$(read_session "$T/apikey.json" 2>&1 >/dev/null); check "api-key-session-is-refused-with-the-better-route" "provider" $? "$E"
  printf '{"auth_mode":"chatgpt","tokens":{"access_token":""}}' >"$T/empty.json"
  E=$(read_session "$T/empty.json" 2>&1 >/dev/null); check "empty-token-is-fatal" "no access_token" $? "$E"
  # An expired session must be caught HERE, not sixty seconds into a sandbox.
  python3 - "$T/expired.json" <<'PY'
import base64, json, sys, time
claims = base64.urlsafe_b64encode(json.dumps({"exp": int(time.time()) - 7200}).encode()).decode().rstrip("=")
json.dump({"auth_mode": "chatgpt", "tokens": {"access_token": "h.%s.s" % claims}}, open(sys.argv[1], "w"))
PY
  E=$(read_session "$T/expired.json" 2>&1 >/dev/null); check "expired-session-is-fatal" "expired" $? "$E"
  rm -rf "$T"
  [ "$RED" -eq 0 ] && { echo "SELFTEST GREEN"; exit 0; }
  echo "SELFTEST RED" >&2; exit 2
fi

[ -n "$PROMPT" ] || usage
command -v openshell >/dev/null 2>&1 || {
  echo "FATAL: openshell is not on PATH" >&2; exit 64; }

# OrbStack redirects the docker CLI through a context, so a dead
# /var/run/docker.sock refuses while `docker ps` works. Announced, not silent.
if [ -z "${DOCKER_HOST:-}" ] && [ -S "$HOME/.orbstack/run/docker.sock" ]; then
  DOCKER_HOST="unix://$HOME/.orbstack/run/docker.sock"
  export DOCKER_HOST
  echo "DOCKER_HOST -> orbstack socket"
fi

AUTH=$(read_session "$AUTH_FILE") || exit 64
[ -n "$AUTH" ] || { echo "FATAL: the session read back empty" >&2; exit 64; }

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
  session   $AUTH_FILE (auth_mode=chatgpt, unexpired, ${#AUTH} bytes)
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
printenv CODEX_AUTH_JSON >"$HOME/.codex/auth.json"
chmod 600 "$HOME/.codex/auth.json"
cd '"$WORK"' || exit 64

# A hashed manifest either side of the turn, not a timestamp sweep. `find -newer`
# cannot see a DELETION, and a packet that silently drops removals is worse than
# one that admits it: whoever applies it re-creates the file the agent decided to
# remove. 504 tracked files makes hashing twice free, so there is no reason to
# take the lossy reading.
manifest() { find . -type f -not -path "./.git/*" -not -name codex-changes.tar -exec sha256sum {} + 2>/dev/null | sort; }
manifest >/tmp/before.txt

codex exec --skip-git-repo-check -s danger-full-access "$CODEX_PROMPT"
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
  --env "CODEX_AUTH_JSON=$AUTH" \
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
