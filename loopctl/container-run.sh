#!/bin/sh
# container-run.sh — run loopctl in a container, on whichever runtime is here.
#
#   sh loopctl/container-run.sh build
#   sh loopctl/container-run.sh preflight            # answer the auth question
#   sh loopctl/container-run.sh serve <commit|tag>   # stateless MCP, pinned
#   sh loopctl/container-run.sh shell
#
# Two runtimes, one image. Apple's `container` and Docker both consume OCI images
# and both accept the flags this needs — verified against container's own command
# reference rather than assumed: -e/--env, -i/--interactive, -u/--user, -w
# /--workdir, --rm, -v/--volume, and `build -f … -t … <context>`. So the Dockerfile
# is shared and only the invocation is abstracted. LOOPCTL_RUNTIME overrides the
# choice; otherwise `container` wins when present, because on Apple silicon it is
# the lighter path.
#
# NOT verified by running: `container` is not installed on the machine this was
# written on. The runtime that was chosen is announced on every invocation, and
# container_preflight.sh is what proves the choice actually works — a wrapper
# claiming portability it has not exercised is the kind of green this repo spends
# its time removing.
#
# Every mount decision below is one that fails quietly if left to memory:
#
# --user $(id -u):$(id -g)
#   `git worktree add` writes into the mounted repo's .git. As root that leaves
#   root-owned files in YOUR tree, and the next host-side git command fails with
#   a permission error nowhere near the cause.
#
# HOME=/repo/.container-home
#   With --user there is no home for that uid in the image, and both CLIs write
#   session state under $HOME. Pointing it at a gitignored path inside the mount
#   gives them a writable home that leaks into neither the image nor the host's ~.
#
# the auth mounts
#   The host's CLI binaries are macOS builds and cannot run in a Linux container,
#   but the SESSIONS are just files. Mounted read-write on purpose: a read-only
#   mount breaks token refresh, and a driver whose refresh fails reports itself
#   unauthenticated mid-request instead of at preflight.
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd -P)
IMAGE=${LOOPCTL_IMAGE:-loopctl}
CMD=${1:-preflight}

# OrbStack serves its daemon on its own socket and switches the docker CLI to it
# through a docker CONTEXT, which is a CLI-level concept. Anything that talks to
# the daemon directly — openshell's builder, for one — goes to
# /var/run/docker.sock, and on a Mac that has ever run Docker Desktop that path
# still exists as a dead socket. The failure is "Connection refused" while
# `docker ps` works two lines earlier, which reads like the tool is broken rather
# than like it is holding the wrong end. Exporting DOCKER_HOST puts everything on
# the same live socket.
if [ -z "${DOCKER_HOST:-}" ] && [ -S "$HOME/.orbstack/run/docker.sock" ]; then
  DOCKER_HOST="unix://$HOME/.orbstack/run/docker.sock"
  export DOCKER_HOST
  echo "container-run: DOCKER_HOST -> orbstack socket (a dead /var/run/docker.sock is refused, not absent)" >&2
fi

RUNTIME=${LOOPCTL_RUNTIME:-}
if [ -z "$RUNTIME" ]; then
  if command -v container >/dev/null 2>&1; then RUNTIME=container
  elif command -v docker >/dev/null 2>&1; then RUNTIME=docker
  else
    echo "container-run FATAL: neither \`container\` nor \`docker\` is on PATH — there is no runtime to build or serve on" >&2
    exit 64
  fi
fi
echo "container-run: runtime=$RUNTIME image=$IMAGE" >&2

# Each session path is mounted only if it exists, and its absence is announced:
# a container missing one of these produces a driver that is present but cannot
# answer, which fails later looking like a model refusal rather than like a
# missing session.
AUTH_MOUNTS=""
for pair in "$HOME/.claude:/repo/.container-home/.claude" \
            "$HOME/.claude.json:/repo/.container-home/.claude.json" \
            "$HOME/.codex:/repo/.container-home/.codex"; do
  src=${pair%%:*}
  dst=${pair#*:}
  if [ -e "$src" ]; then
    AUTH_MOUNTS="$AUTH_MOUNTS -v $src:$dst"
  else
    echo "container-run: note — $src is absent on this host; the driver using it will report absent" >&2
  fi
done

mkdir -p "$ROOT/.container-home"

run() {
  # shellcheck disable=SC2086 # AUTH_MOUNTS is a deliberate argument list
  "$RUNTIME" run --rm -i \
    --user "$(id -u):$(id -g)" \
    -e HOME=/repo/.container-home \
    -v "$ROOT:/repo" \
    $AUTH_MOUNTS \
    -w /repo "$IMAGE" "$@"
}

case "$CMD" in
  build)
    exec "$RUNTIME" build -f "$ROOT/loopctl/Dockerfile" -t "$IMAGE" "$ROOT" ;;
  preflight)
    run sh loopctl/container_preflight.sh ;;
  serve)
    REF=${2:-}
    # No default ref. A server with no pin serves HEAD, which is right on a dev
    # box and wrong for a service: customer traffic would ride whatever is being
    # edited. Refused rather than defaulted, because the default is the dangerous
    # one.
    [ -n "$REF" ] || { echo "container-run FATAL: serve needs a ref — pin a tag, or external calls follow HEAD" >&2; exit 64; }
    run sh loopctl/loopctl.sh mcp serve --ref "$REF" ;;
  shell)
    run bash ;;
  *)
    echo "usage: container-run.sh <build|preflight|serve <commit|tag>|shell>" >&2
    exit 64 ;;
esac
