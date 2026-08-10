#!/bin/sh
# control_sandbox_policy.sh — the CONTROL GROUP for the sandbox policy.
#
#   sh loopctl/loopctl.sh policy test
#
# A policy that has only ever been seen ACCEPTING is not known to deny anything.
# Every check here is a denial driven for real from inside a sandbox, because the
# properties that matter are negative ones: what an external caller cannot reach.
#
# The one worth the most: naming host.docker.internal for the MCP port must NOT
# open the host. Endpoints are per host AND port, but that is a claim about the
# runtime's matcher, and a claim about someone else's matcher is exactly the kind
# that is true until it is not. So :3000 is dialled every run.
#
# Denials are read as HTTP status where possible. A refused connection (exit 56,
# no status) and a proxy 403 are NOT the same evidence: 403 proves the traffic
# reached the proxy and was JUDGED, while a connection failure alone could just
# as well mean the network was down — which would make an unenforced policy look
# enforced.
#
# Exit: 0 every denial held · 2 something reachable that must not be · 64 FATAL
set -u

CAPTURE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$CAPTURE_HOME/lib/capture.sh"
capture_init sandbox-policy
ROOT=$CAPTURE_ROOT
POLICY="$ROOT/loopctl/sandbox-policy.yaml"
[ -f "$POLICY" ] || { echo "control FATAL: no policy at $POLICY" >&2; exit 64; }

command -v openshell >/dev/null 2>&1 || {
  echo "control FATAL: openshell is not on PATH — the policy cannot be exercised, and reading it is not the same as enforcing it" >&2
  exit 64; }
# The orbstack socket selection used to live here and now lives in capture.sh,
# because a fourth caller forgot it and got "Connection refused" on a working
# machine. One entry point, not four copies.

RED=0
expect() { # name got want
  if [ "$2" = "$3" ]; then echo "  [ok]   $1 — $2"; else echo "  [RED]  $1 — got $2, want $3" >&2; RED=1; fi
}

# One sandbox, several probes: each create costs an image build and an upload, so
# the probes are batched and their answers parsed apart afterwards.
# One clean `name=NNN` line per probe. The first version interleaved the status
# and the exit code on one line and the reader glued them into "000000", which
# then fell through to the unknown branch and reported a DENIED destination as
# reachable — a false alarm on a security check is as corrosive as a missed one.
PROBE='
probe() { code=$(curl -s -m 8 -o /dev/null -w "%{http_code}" "$2" 2>/dev/null); echo "$1=${code:-000}"; }
probe unlisted_host https://example.com/
probe forgejo http://host.docker.internal:3000/
probe gateway https://host.docker.internal:8080/
'
capture policy-probes -- sh -c "openshell sandbox create --name policy-probe --no-tty --no-keep \
  --policy '$POLICY' --from '$ROOT/loopctl/Dockerfile' --upload '$ROOT' -- sh -c '$PROBE'"
PROBE_OUT="$RUNDIR/streams/$CAPTURE_SEQ-policy-probes.out"

read_probe() { sed -nE "s/^$1=([0-9]{3}).*/\1/p" "$PROBE_OUT" | head -1; }

UNLISTED=$(read_probe unlisted_host)
FORGEJO=$(read_probe forgejo)
GATEWAY=$(read_probe gateway)

if [ -z "$UNLISTED$FORGEJO$GATEWAY" ]; then
  echo "  [RED]  probes produced no readings — the sandbox never ran, so nothing was tested" >&2
  tail -6 "$PROBE_OUT" >&2
  RED=1
else
  # 000 means the connection never completed; anything 2xx/3xx means it did.
  # Both 000 and 403 are acceptable denials; only a success is a failure here.
  for pair in "unlisted-host:$UNLISTED" "forgejo-3000:$FORGEJO" "gateway-8080:$GATEWAY"; do
    name=${pair%%:*}
    code=${pair#*:}
    case "$code" in
      000|4*|5*) expect "$name-denied" denied denied ;;
      "") echo "  [note] $name produced no reading this run — NOT exercised" ;;
      *) echo "  [RED]  $name-denied — reachable with HTTP $code; an external caller can touch this machine" >&2; RED=1 ;;
    esac
  done
  # Judged, not merely unreachable. If NOTHING came back as a proxy status the
  # policy might not be in the path at all, and every denial above would be the
  # network's doing rather than the policy's.
  case "$FORGEJO$GATEWAY" in
    *4*|*5*) expect "denial-is-a-proxy-verdict" judged judged ;;
    *) echo "  [note] every local denial was a dropped connection (000), so this run did not prove the proxy is in the path — only that nothing answered" ;;
  esac
fi

# --- the credential half: the token must WORK without ever being in here -----
# Everything above is a denial. This is the one positive property, and it is the
# one the whole writing role rests on: the subscription credential is handed to
# the gateway as a provider, the sandbox receives only
# `openshell:resolve:env:v<n>_CLAUDE_CODE_OAUTH_TOKEN`, and the proxy substitutes
# the real value on the way out. Two things have to hold at once, and either one
# alone is worthless — a working turn with the token sitting in the environment
# is just a secret in a box, and a placeholder that cannot buy a turn is a
# broken sandbox.
#
# Gated on the provider existing rather than skipped silently: a control may not
# mint a subscription token, so its absence is NOT EXERCISED, never a pass.
PROVIDER=${POLICY_CLAUDE_PROVIDER:-claude-code}
# Same three-outcome split as automode-bench.sh, and for the same reason: a
# gateway that cannot be reached used to read as a provider that is not there,
# so the control reported NOT EXERCISED for the one condition it can actually
# distinguish — "nobody minted a token" — while the truth was "nobody could ask".
# Those send the reader to different places.
POLICY_PROVIDERS=$(openshell provider list 2>&1); POLICY_PROVIDERS_RC=$?
if [ "$POLICY_PROVIDERS_RC" -ne 0 ]; then
  echo "  [note] could not ask the gateway which providers exist (exit $POLICY_PROVIDERS_RC) — the credential turn is NOT EXERCISED, and this is NOT the same as the provider being absent:"
  printf '%s\n' "$POLICY_PROVIDERS" | head -1 | sed 's/^/         /'
elif printf '%s\n' "$POLICY_PROVIDERS" | grep -q "^$PROVIDER "; then
  capture credential-turn -- sh -c "openshell sandbox create --name policy-credential --no-tty --no-keep \
    --policy '$POLICY' --provider '$PROVIDER' --from '$ROOT/loopctl/Dockerfile' --upload '$ROOT' \
    -- sh -c 'echo \"ENV=\${CLAUDE_CODE_OAUTH_TOKEN:-<unset>}\"; claude -p \"reply with exactly: ok\"; echo \"TURN_RC=\$?\"'"
  CRED_OUT="$RUNDIR/streams/$CAPTURE_SEQ-credential-turn.out"

  SEEN=$(sed -nE 's/^ENV=(.*)$/\1/p' "$CRED_OUT" | head -1)
  case "$SEEN" in
    openshell:resolve:env:*) expect "sandbox-holds-a-placeholder-not-the-token" placeholder placeholder ;;
    "") echo "  [note] the credential sandbox printed no ENV line — NOT exercised, so neither half below is proven" ;;
    "<unset>") echo "  [RED]  sandbox-holds-a-placeholder-not-the-token — the provider injected nothing; the turn below cannot mean anything" >&2; RED=1 ;;
    *) echo "  [RED]  sandbox-holds-a-placeholder-not-the-token — the environment carries a literal value, so the secret IS in the sandbox and every process there can read it" >&2; RED=1 ;;
  esac

  TURN_RC=$(sed -nE 's/^TURN_RC=([0-9]+)$/\1/p' "$CRED_OUT" | head -1)
  case "$TURN_RC" in
    0) expect "placeholder-buys-a-real-turn" 0 0 ;;
    "") echo "  [note] the credential sandbox printed no TURN_RC — the proxy rewrite is NOT exercised this run" ;;
    *) echo "  [RED]  placeholder-buys-a-real-turn — got $TURN_RC; the proxy did not substitute the placeholder, so the writing role cannot run without putting the token in the sandbox" >&2; RED=1 ;;
  esac
else
  echo "  [note] no provider '$PROVIDER' on this gateway — the proxy rewrite is NOT exercised, not passed."
  echo "         create it with: openshell provider create --name $PROVIDER --type generic --credential CLAUDE_CODE_OAUTH_TOKEN"
fi

# --- the other writing role, which pays a different price -------------------
# codex cannot use the placeholder above — it parses its credential as a JWT
# before any request — so its session enters the sandbox as a real value and the
# policy is the only thing bounding what can spend it. Two policy properties ride
# on this and nothing else covers them: that chatgpt.com is admitted at all (the
# subscription backend is NOT api.openai.com), and that codex's binary identity
# still matches after an image rebuild.
#
# Opt-in, like CONTROL_OPENWIKI_FULL: it costs an image build, an upload and a
# real model turn, which is minutes and tokens on every `policy test`. Default is
# NOT EXERCISED with the command named — a silent skip would read as covered.
if [ "${CONTROL_CODEX_TURN:-0}" = 1 ]; then
  if [ -f "${CODEX_AUTH_FILE:-$HOME/.codex/auth.json}" ]; then
    capture codex-write-turn -- sh "$ROOT/loopctl/codex-sandbox.sh" \
      "create a file named CONTROL_CODEX_TURN.txt whose only content is the word ok, then stop"
    CODEX_RC=$?
    CODEX_OUT="$RUNDIR/streams/$CAPTURE_SEQ-codex-write-turn.out"
    expect "codex-write-turn-completes" "$CODEX_RC" 0
    grep -q "^changed files: [1-9]" "$CODEX_OUT" && WROTE=yes || WROTE=no
    expect "codex-turn-actually-wrote-a-file" "$WROTE" yes
  else
    echo "  [note] no codex session on this host — the codex write turn is NOT EXERCISED, not passed"
  fi
else
  echo "  [note] the codex write turn is NOT EXERCISED (costs a build + a real turn); run with CONTROL_CODEX_TURN=1 to include it"
fi

echo "control[sandbox-policy] trace=proof_workflow/data/$RUN_ID"
if [ "$RED" -eq 0 ]; then
  echo "PASS: the policy denied every unnamed destination, including this machine's own services,"
  echo "      and the credential half held — placeholder in the sandbox, real turn out of it"
  exit 0
fi
echo "FAIL: the policy let something through that an external caller must not reach" >&2
exit 2
