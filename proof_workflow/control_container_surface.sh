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
