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
        iproute2 \
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

# Point /usr/local/bin/codex at the NATIVE binary instead of npm's node shim.
#
# Not tidiness — the sandbox policy binds network endpoints to a binary PATH, and
# npm installs `codex` as a .js launcher that spawns a vendored executable from
# deep inside node_modules. The process that actually opens the connection is
# therefore neither `/usr/local/bin/codex` nor anything the policy can name, so a
# subscription turn died on `HTTP CONNECT failed with status 403` from the proxy
# while the policy plainly listed codex. claude works because npm ships it as
# `claude.exe`, an ELF at the linked path: same shape, and that difference is the
# whole bug.
#
# The path is discovered, never written down: it carries the platform triple and
# the platform package's version, both of which move. Absent is FATAL here rather
# than a warning, unlike the install above — an image that silently kept the shim
# would look identical and fail only inside a sandbox, hours later, as a 403.
RUN set -eu; \
    if [ -x /usr/local/bin/codex ]; then \
      real=$(find /usr/local/lib/node_modules/@openai/codex/node_modules \
               -type f -perm -u+x -name codex 2>/dev/null | head -1); \
      [ -n "$real" ] || { echo "FATAL: codex is installed but its native binary was not found under node_modules; the policy's binary identity would never match" >&2; exit 1; }; \
      ln -sf "$real" /usr/local/bin/codex; \
      file_out=$(head -c 4 /usr/local/bin/codex | od -An -c | tr -d ' \n'); \
      case "$file_out" in *177ELF*) : ;; *) echo "FATAL: /usr/local/bin/codex is still not an ELF after relinking (got $file_out)" >&2; exit 1 ;; esac; \
      codex --version; \
    fi

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

# A sandbox runtime requires this user by name. Its supervisor refuses outright:
#   "sandbox user 'sandbox' not found in image; all sandbox images must include
#    a 'sandbox' user and group"
# That line was in the failing container's own logs from the first attempt. It
# was found only after TWO rounds of differential guessing against a known-good
# image — inherited ENTRYPOINT, then the default CMD — each of which was a real
# difference and neither of which was the cause. The runtime replaces the
# entrypoint with its own supervisor anyway, so neither guess could have mattered.
# Read the failing thing's output before comparing it to a working one.
# Home is /sandbox rather than the distro's default per-user home (spelled out
# would trip the root-coupling gate, which cannot tell a container path from a
# machine's), and the shell is bash — matched to the
# known-good community image rather than invented. /sandbox is the runtime's
# MANAGED workspace: it creates and owns it, and its default policy admits it.
# With home elsewhere the upload died on "Permission denied" for a 0644 file
# readable by everyone, which is the tell that the refusal came from POLICY and
# not from unix permissions — an OPA-governed sandbox denies paths it was not
# told about, so the fix is to use the workspace it governs, not to widen modes.
RUN groupadd --system sandbox \
 && useradd --system --home-dir /sandbox --create-home --shell /bin/bash --gid sandbox sandbox

# The rest of the sandbox contract, taken from the runtime's own reference rather
# than discovered one retry at a time (docs/reference/sandbox-compute-drivers.mdx
# §Sandbox User Identity, architecture/compute-runtimes.md §Images):
#   * the driver reads the image's OCI USER as a per-field identity fallback;
#   * an absolute WorkingDir becomes the agent workspace, must already exist in
#     the image, and the resolved UID/GID must be able to traverse every parent
#     and write and enter it — the runtime does NOT chown it;
#   * proxy mode needs network-namespace isolation, hence iproute2 above
#     ("trusted ip helper not found; checked /usr/sbin/ip").
# Reading the spec once beat three more rounds of retry-as-probe.
RUN mkdir -p /repo && chown sandbox:sandbox /repo
USER sandbox

# /sandbox, not /repo. An absolute WorkingDir becomes the agent workspace, while
# uploads land in HOME — so naming /repo here split the two: the upload arrived
# at ~/bettor-arena and the command ran in an empty /repo, reported only as
# "cannot open loopctl/container_preflight.sh". Two path guesses later, looking
# at the sandbox instead of guessing showed it in one run. /sandbox is home,
# workspace and the policy-admitted path at once.
#
# The bind-mount path is unaffected: container-run.sh passes -w /repo explicitly
# alongside its mount, which overrides this.
WORKDIR /sandbox

# Cleared because node:22 ships docker-entrypoint.sh and nothing here wants it —
# hygiene, not a fix. A sandbox runtime overrides the entrypoint regardless.
ENTRYPOINT []

# A long-lived shell that depends on nothing: under `docker run` the repo is
# mounted, but a sandbox runtime uploads it into an already-running container, so
# a default command referencing the repo would exit instantly against an empty
# /repo. Also the second guess that was not the cause — kept because it is right,
# not because it fixed anything.
#
# Nothing served by default: bash serves nothing, so no `run` of this image can
# start answering external calls by accident.
CMD ["/bin/bash"]
