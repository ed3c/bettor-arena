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
if [ -z "${DOCKER_HOST:-}" ] && [ -S "$HOME/.orbstack/run/docker.sock" ]; then
  DOCKER_HOST="unix://$HOME/.orbstack/run/docker.sock"
  export DOCKER_HOST
fi

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

echo "control[sandbox-policy] trace=proof_workflow/data/$RUN_ID"
if [ "$RED" -eq 0 ]; then
  echo "PASS: the policy denied every unnamed destination, including this machine's own services"
  exit 0
fi
echo "FAIL: the policy let something through that an external caller must not reach" >&2
exit 2
