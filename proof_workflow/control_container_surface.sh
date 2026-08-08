#!/bin/sh
# control_container_surface.sh — the CONTROL GROUP for the container layer.
#
#   sh loopctl/loopctl.sh container test
#
# The container is the second driver (README §1 law 9): it is what makes an
# inherited coupling visible. So the properties worth holding down here are the
# ones that were only ever found by running the image under something other than
# `docker run`, plus the ones a wrapper silently gets wrong.
#
# Split into two tiers on purpose:
#   WRAPPER   always run. Socket selection, runtime detection, refusal of an
#             unpinned serve. Cheap, and every one of these failed for real once.
#   IMAGE     only when the image exists. Building it here would put minutes into
#             a control that is meant to be run often; an absent image is reported
#             as NOT EXERCISED, never scored as a pass.
#
# The planted defect that matters most: a FAKE driver on PATH that exits non-zero.
# preflight must call it "present but NOT authenticated" — if it says
# "authenticated", the check is asking `--version` in disguise and the whole
# auth story is decoration.
#
# Exit: 0 every property held · 2 one did not · 64 FATAL
set -u

CAPTURE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$CAPTURE_HOME/lib/capture.sh"
capture_init container-surface
ROOT=$CAPTURE_ROOT
IMAGE=${LOOPCTL_IMAGE:-loopctl}
BASE=$(mktemp -d "${TMPDIR:-/tmp}/control-container.XXXXXX")

RED=0
expect() { # name got want
  if [ "$2" = "$3" ]; then echo "  [ok]   $1 — $2"; else echo "  [RED]  $1 — got $2, want $3" >&2; RED=1; fi
}

# --- tier 1: the wrapper -----------------------------------------------------
capture wrapper-syntax -- sh -n "$ROOT/loopctl/container-run.sh"
expect "wrapper-parses" $? 0

# An unpinned serve must be refused, not defaulted. The default is the dangerous
# one: customer traffic would ride whatever HEAD is being edited into.
capture serve-without-ref -- sh "$ROOT/loopctl/container-run.sh" serve
expect "serve-without-ref-refused" $? 64

# Neither runtime present must be FATAL and say so, rather than falling through
# to a command that does not exist.
#
# PATH=/usr/bin:/bin, not PATH=/nonexistent: with an empty PATH `env` cannot find
# `sh` either, so the wrapper never runs and the probe returns 127 having proved
# nothing. It went RED rather than passing — a check that did not run must not
# read as a check that passed — but the fix belonged to the probe. Both runtimes
# live outside these two directories (/usr/local/bin, ~/.local/bin) while the
# coreutils the wrapper needs live inside them.
capture no-runtime -- env PATH=/usr/bin:/bin LOOPCTL_RUNTIME= sh "$ROOT/loopctl/container-run.sh" preflight
NO_RT=$?
expect "no-runtime-is-fatal" "$NO_RT" 64

# The socket announcement is the fix for a failure that reads as "the tool is
# broken" — a dead /var/run/docker.sock refuses while `docker ps` works, because
# OrbStack redirects the CLI through a docker CONTEXT and nothing else sees it.
if [ -S "$HOME/.orbstack/run/docker.sock" ]; then
  capture socket-announcement -- sh -c "sh '$ROOT/loopctl/container-run.sh' serve 2>&1 | head -3"
  SOCK_OUT="$RUNDIR/streams/$CAPTURE_SEQ-socket-announcement.out"
  grep -q 'DOCKER_HOST -> orbstack socket' "$SOCK_OUT" && ANNOUNCED=yes || ANNOUNCED=no
  expect "orbstack-socket-selected-and-announced" "$ANNOUNCED" yes
else
  echo "  [note] no orbstack socket on this host — the socket-selection path is NOT exercised"
fi

# --- tier 2: preflight's own discrimination ----------------------------------
# The negative control for law 11. A driver that exists and cannot answer must
# NOT be reported as authenticated; if it is, the check has degraded into asking
# whether the binary exists.
mkdir -p "$BASE/fakebin"
printf '#!/bin/sh\nexit 1\n' >"$BASE/fakebin/claude"
printf '#!/bin/sh\nexit 1\n' >"$BASE/fakebin/codex"
chmod +x "$BASE/fakebin/claude" "$BASE/fakebin/codex"
capture preflight-with-dead-drivers -- env PATH="$BASE/fakebin:$PATH" sh "$ROOT/loopctl/container_preflight.sh"
PF_RC=$?
PF_ERR="$RUNDIR/streams/$CAPTURE_SEQ-preflight-with-dead-drivers.err"
grep -q 'present but NOT authenticated' "$PF_ERR" && SPLIT=yes || SPLIT=no
expect "dead-driver-is-not-called-authenticated" "$SPLIT" yes
expect "dead-driver-fails-the-preflight" "$PF_RC" 2

# --- tier 3: the image, only if it is here -----------------------------------
if command -v docker >/dev/null 2>&1 && docker image inspect "$IMAGE" >/dev/null 2>&1; then
  # The defect that cost the most to find: node:22 ships ENTRYPOINT
  # docker-entrypoint.sh, `docker run` never shows it, and OpenShell's supervisor
  # died as ContainerRestarting with nothing naming the cause.
  capture image-entrypoint -- docker image inspect "$IMAGE" --format '{{.Config.Entrypoint}}'
  EP=$(tr -d ' \n' <"$RUNDIR/streams/$CAPTURE_SEQ-image-entrypoint.out")
  case "$EP" in
    ""|"[]") expect "inherited-entrypoint-is-cleared" cleared cleared ;;
    *) echo "  [RED]  inherited-entrypoint-is-cleared — image carries ENTRYPOINT $EP; a supervisor-driven runtime will restart-loop with no named cause" >&2; RED=1 ;;
  esac

  # Host green is not container green: every tool the loops FATAL without has to
  # be in the image, and poppler was missing until a run inside said so.
  capture image-base -- docker run --rm --entrypoint sh "$IMAGE" -c \
    'for t in git python3 bun node ruff pdftotext; do command -v $t >/dev/null || { echo "MISSING $t"; exit 1; }; done; echo base-complete'
  BASE_RC=$?
  expect "image-carries-every-tool-the-loops-need" "$BASE_RC" 0
  [ "$BASE_RC" -eq 0 ] || cat "$RUNDIR/streams/$CAPTURE_SEQ-image-base.out" >&2

  # The policy binds each network endpoint to a binary PATH, and nothing checked
  # that the image agrees with those paths. It is a silent coupling in the worst
  # direction: npm's prefix moving, or a base-image change, denies the traffic
  # and the failure surfaces as "claude cannot reach the API" — a symptom that
  # points at the agent, the network and the token before it points at a string
  # in a YAML file two directories away.
  #
  # Read out of the policy rather than listed here. A second list is what makes
  # a control fail on its own staleness instead of on the thing it measures.
  # Space-separated, not newline: the list is interpolated into a `for` inside a
  # `sh -c` string, and a newline ENDS the list there — the first version ran the
  # first path as the loop body and EXECUTED the remaining paths as commands.
  POLICY_BINS=$(python3 - "$ROOT/loopctl/sandbox-policy.yaml" <<'PY'
import re, sys
src = open(sys.argv[1], encoding="utf-8").read()
print(" ".join(sorted({m.group(1) for m in re.finditer(r"^\s*-\s*path:\s*(\S+)", src, re.M)})))
PY
)
  if [ -z "$POLICY_BINS" ]; then
    echo "  [RED]  policy-bound-binaries-derived — extracted no path from sandbox-policy.yaml; an empty list would make the next check pass by measuring nothing" >&2
    RED=1
  else
    capture policy-binaries-in-image -- docker run --rm --entrypoint sh "$IMAGE" -c \
      "for b in $POLICY_BINS; do [ -x \"\$b\" ] || { echo \"MISSING \$b\"; exit 1; }; done; echo all-bound-binaries-present"
    BIN_RC=$?
    expect "policy-bound-binaries-exist-in-the-image" "$BIN_RC" 0
    [ "$BIN_RC" -eq 0 ] || cat "$RUNDIR/streams/$CAPTURE_SEQ-policy-binaries-in-image.out" >&2

    # Existing is not enough — the bound path must BE the process that opens the
    # connection. npm ships codex as a .js launcher that spawns a vendored
    # executable from inside node_modules, so the policy named a path no running
    # process ever had and a subscription turn died on `HTTP CONNECT failed with
    # status 403` while the policy plainly listed codex. claude was fine only
    # because npm ships it as an ELF at the linked path.
    #
    # Every bound binary is checked, not just codex: any of them could acquire a
    # wrapper on an upgrade, and the failure would again surface as a proxy
    # refusal pointing at the network rather than at the image.
    capture policy-binaries-are-not-shims -- docker run --rm --entrypoint sh "$IMAGE" -c \
      "for b in $POLICY_BINS; do \
         head -c 2 \"\$b\" | grep -q '#!' && { echo \"SHIM \$b — a script here means the requesting process is the interpreter, which the policy cannot name\"; exit 1; }; \
       done; echo no-shims-among-bound-binaries"
    SHIM_RC=$?
    expect "policy-bound-binaries-are-real-executables" "$SHIM_RC" 0
    [ "$SHIM_RC" -eq 0 ] || cat "$RUNDIR/streams/$CAPTURE_SEQ-policy-binaries-are-not-shims.out" >&2
  fi

  # The subscription credential reaches the sandbox as a PLACEHOLDER, never as a
  # value (sandbox-policy.yaml, anthropic.binaries). The whole model dies if the
  # client inspects the token's shape and refuses it before the proxy ever gets
  # to substitute — so that is the property, stated as the thing that would kill
  # it rather than as "auth works".
  #
  # Judged on the LOGIN REFUSAL, not on the connect error. The first version
  # waited for `Unable to connect`, which arrives only after the client has
  # exhausted its retries — timeout 60 killed it at exit 124 with partial output
  # and the case scored RED for being slow. The refusal, when it comes, is
  # immediate; absence of it inside the window is the signal, and it costs
  # seconds instead of minutes.
  #
  # --network none on purpose: with egress the two arms would both end in a
  # network verdict and stop being distinguishable.
  REFUSAL='not logged in|please run /login|invalid api key|invalid.*token|malformed'

  # Negative arm FIRST, because it is what makes the other one mean anything. No
  # credential at all must produce the refusal; if it does not, the signature has
  # moved and the positive arm below is passing on a string that never appears.
  capture no-token-is-refused-locally -- docker run --rm --network none \
    --entrypoint sh "$IMAGE" -c 'timeout 45 claude -p hi 2>&1'
  NT_OUT="$RUNDIR/streams/$CAPTURE_SEQ-no-token-is-refused-locally.out"
  if grep -qiE "$REFUSAL" "$NT_OUT"; then
    expect "no-token-is-refused-before-any-request" refused refused
    ARMED=yes
  else
    echo "  [RED]  no-token-is-refused-before-any-request — the refusal signature did not appear, so the placeholder arm cannot tell 'accepted' from 'never refuses anything'" >&2
    head -c 400 "$NT_OUT" >&2
    RED=1
    ARMED=no
  fi

  if [ "$ARMED" = yes ]; then
    capture placeholder-token-not-refused -- docker run --rm --network none \
      -e CLAUDE_CODE_OAUTH_TOKEN='openshell:resolve:env:v1_CLAUDE_CODE_OAUTH_TOKEN' \
      --entrypoint sh "$IMAGE" -c 'timeout 45 claude -p hi 2>&1'
    PH_OUT="$RUNDIR/streams/$CAPTURE_SEQ-placeholder-token-not-refused.out"
    if grep -qiE "$REFUSAL" "$PH_OUT"; then
      echo "  [RED]  placeholder-token-is-not-refused-locally — the client rejected the placeholder before any request; the provider-placeholder credential model is dead as written and the sandbox needs a real token in it, which is the thing this design exists to avoid" >&2
      head -c 400 "$PH_OUT" >&2
      RED=1
    else
      expect "placeholder-token-is-not-refused-locally" accepted accepted
    fi
  fi

  # This pair only proves the client accepts the SHAPE. Whether the proxy really
  # substitutes it is a gateway property and is exercised where the gateway is —
  # `policy test`, gated on the provider existing. Named here so the boundary
  # between the two controls is readable from either side.
  echo "  [note] the proxy rewrite itself is exercised by 'policy test' (credential-turn), not here"
else
  echo "  [note] image '$IMAGE' is not built here — the ENTRYPOINT and base-tool checks are NOT exercised"
  echo "         build it with: sh loopctl/container-run.sh build"
fi

echo "control[container-surface] trace=proof_workflow/data/$RUN_ID"
if [ "$RED" -eq 0 ]; then
  echo "PASS: the container layer selected a live socket, refused an unpinned serve, and told present apart from authenticated"
  exit 0
fi
echo "FAIL: the container layer lost a property that was paid for by a real failure" >&2
exit 2
