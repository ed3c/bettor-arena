#!/bin/sh
# docker-run.sh — run loopctl in the container with the mounts that make it work.
#
#   sh loopctl/docker-run.sh build
#   sh loopctl/docker-run.sh preflight            # answer the auth question
#   sh loopctl/docker-run.sh serve <commit|tag>   # stateless MCP, pinned
#   sh loopctl/docker-run.sh shell                # poke around
#
# Every decision below is one that fails quietly if left to the caller to
# remember, which is why it lives in a script instead of a README line.
#
# --user $(id -u):$(id -g)
#   `git worktree add` writes into the mounted repo's .git. As root that leaves
#   root-owned files in YOUR tree, and the next host-side git command fails with
#   a permission error nowhere near the cause. Running as the host uid keeps
#   every byte the container writes owned by you.
#
# HOME=/repo/.container-home
#   With --user there is no home directory for that uid in the image, and both
#   CLIs write session state under $HOME. Pointing HOME at a gitignored path
#   inside the mount gives them a writable home that does not leak into the image
#   and does not pollute the host's real ~/.
#
# the auth mounts
#   The host's binaries are macOS builds and cannot run here, but the SESSIONS
#   are just files. They are mounted read-write on purpose: a read-only mount
#   breaks token refresh, and a driver whose refresh fails reports itself as
#   unauthenticated later, which is the failure this whole preflight exists to
#   surface early rather than mid-request.
#
# what is NOT mounted
#   Nothing else from the host. The container sees this repo and these sessions.
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd -P)
IMAGE=${LOOPCTL_IMAGE:-loopctl}
CMD=${1:-preflight}

# Sessions live in a few separate places; each is mounted only if it exists, and
# the absence is announced rather than silently producing an unauthenticated
# container that fails later looking like a model refusal.
AUTH_MOUNTS=""
for pair in "$HOME/.claude:/repo/.container-home/.claude" \
            "$HOME/.claude.json:/repo/.container-home/.claude.json" \
            "$HOME/.codex:/repo/.container-home/.codex"; do
  src=${pair%%:*}
  dst=${pair#*:}
  if [ -e "$src" ]; then
    AUTH_MOUNTS="$AUTH_MOUNTS -v $src:$dst"
  else
    echo "docker-run: note — $src is absent on this host; the driver using it will report absent" >&2
  fi
done

mkdir -p "$ROOT/.container-home"

run() {
  # shellcheck disable=SC2086 # AUTH_MOUNTS is a deliberate argument list
  docker run --rm -i \
    --user "$(id -u):$(id -g)" \
    -e HOME=/repo/.container-home \
    -v "$ROOT:/repo" \
    $AUTH_MOUNTS \
    -w /repo "$IMAGE" "$@"
}

case "$CMD" in
  build)
    exec docker build -f "$ROOT/loopctl/Dockerfile" -t "$IMAGE" "$ROOT" ;;
  preflight)
    run sh loopctl/container_preflight.sh ;;
  serve)
    REF=${2:-}
    # A server with no pin serves HEAD, which is right on a dev box and wrong for
    # a service: customer traffic would ride whatever is being edited. Refused
    # here rather than defaulted, because the default is the dangerous one.
    [ -n "$REF" ] || { echo "docker-run FATAL: serve needs a ref — pin a tag, or external calls follow HEAD" >&2; exit 64; }
    run sh loopctl/loopctl.sh mcp serve --ref "$REF" ;;
  shell)
    run bash ;;
  *)
    echo "usage: docker-run.sh <build|preflight|serve <commit|tag>|shell>" >&2
    exit 64 ;;
esac
