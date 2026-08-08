# loopctl — container image for the stateless MCP server.
#
#   docker build -f loopctl/Dockerfile -t loopctl .
#   sh loopctl/docker-run.sh preflight      # answer the auth question first
#   sh loopctl/docker-run.sh serve v1.0     # then serve, pinned
#
# What this image is for: running loopctl for EXTERNAL callers, isolated from the
# tree anyone is working in. The repo is mounted, never copied — an image that
# baked the repo in would serve whatever it was built from while claiming to
# serve the ref it was told to.
#
# The deterministic base is installed and BUILD-CHECKED here, because a missing
# git/python3/bun turns into a loop's exit 64 much later, wearing a different
# error's clothes.
#
# The two drivers are NOT build-checked, on purpose, and the difference matters:
#   * Their install channel is passed as a build arg. The host runs macOS
#     standalone builds (~/.local/share/claude, ~/.codex/packages/standalone),
#     which cannot run here — Linux builds have to come from somewhere else, and
#     this file does not pretend to know which channel is right for your account.
#     A wrong channel shows up as "absent" in container_preflight.sh with a named
#     fix, rather than as an opaque build failure.
#   * Authentication cannot be tested at build time at all. A driver that is
#     present but has no session fails later looking like a model refusal.
#     container_preflight.sh spends one real turn per driver to tell those apart,
#     and it is the arbiter, not this file.
#
# node is here because both CLIs ship through npm channels and because the
# factory's quality lane invokes ./node_modules/.bin/* directly.

FROM node:22-bookworm-slim

# ripgrep is in the read-only subagents' allowlist; curl and ca-certificates are
# needed to fetch bun. Nothing else: every extra package is another thing that
# can differ between this image and the host the proofs were stamped on.
# unzip is not optional: bun's installer needs it and says so — `error: unzip is
# required to install bun` is how this image failed to build the first time.
RUN apt-get update && apt-get install -y --no-install-recommends \
        git python3 python3-pip ca-certificates curl unzip ripgrep poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# ruff drives the Python lane of the fast-quality gate. Absent, that gate FATALs
# 64 by design rather than skipping, so it belongs in the base.
RUN pip3 install --no-cache-dir --break-system-packages ruff

ENV BUN_INSTALL=/usr/local
# Not piped into bash. In `curl … | bash` the shell reports only the LAST stage,
# so a failed download hands bash an empty script and the layer succeeds having
# installed nothing — the same swallowed-exit-code shape this repo refuses
# everywhere else. Fetched, then run, each checked.
RUN curl -fsSL https://bun.sh/install -o /tmp/bun-install.sh \
    && bash /tmp/bun-install.sh \
    && rm /tmp/bun-install.sh

ARG CLAUDE_PKG=@anthropic-ai/claude-code
ARG CODEX_PKG=@openai/codex
# Failure here is a WARNING, not a build failure: a container that serves only
# the read-only roles is a legitimate deployment, and refusing to build would
# force a wrong channel to be guessed at build time instead of measured at run
# time. What is absent is named, and preflight reports it again per role.
RUN npm install -g "$CLAUDE_PKG" || echo "WARN: could not install $CLAUDE_PKG — the writing role will report absent" >&2
RUN npm install -g "$CODEX_PKG"  || echo "WARN: could not install $CODEX_PKG — the read-only role will report absent" >&2

# The deterministic base IS build-checked. Shipping an image whose base is broken
# would move the failure to a caller's first request.
RUN set -eu; \
    for tool in git python3 bun node ruff; do \
      command -v "$tool" >/dev/null || { echo "FATAL: $tool missing from the image" >&2; exit 1; }; \
    done; \
    echo "base ok: $(git --version), $(python3 -V), bun $(bun --version), node $(node --version)"

# The mounted repo is owned by the host user, and git refuses a repository whose
# owner differs from the caller. docker-run.sh runs as the host uid so nothing
# root-owned lands in the host's .git; this declaration covers the case where it
# does not.
RUN git config --system --add safe.directory /repo \
 && git config --system --add safe.directory '*'

WORKDIR /repo

# Clear the entrypoint INHERITED from node:22, which ships docker-entrypoint.sh.
# Nothing here wrote it and `docker run … <cmd>` never showed it, because that
# script execs a non-node command straight through. It only surfaced when
# something else drove the container: OpenShell injects its own supervisor as the
# workload process, that inherited entrypoint got in front of it, and the sandbox
# died as "ContainerRestarting" with nothing naming the cause. An inherited
# coupling stays invisible until a second driver appears — which is the whole
# reason to run the image under one.
ENTRYPOINT []

# No CMD that serves by default: an image whose default action is to start
# answering external calls is one `docker run` away from serving unpinned.
CMD ["sh", "loopctl/container_preflight.sh"]
