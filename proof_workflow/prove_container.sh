#!/bin/sh
# prove_container.sh — physical traversal proof of the container layer.
#
# Entry point: `loopctl container build` -> the OCI image -> `container preflight`
# inside it. This is the layer external callers reach the loops through, and it
# was the only mechanism here with a control group and no receipt — so nothing
# recorded WHICH bytes of it a green control had been measured against.
#
#   DETERMINISTIC harness — the Dockerfile, the runtime-agnostic wrapper, the
#     in-container preflight, and the control that holds their properties down.
#     None is fired here: building an image costs minutes, and firing the wrapper
#     would start a container. `container test` is where they run.
#   PROBABILISTIC read documents — none of its own. The container carries the
#     other loops' context lanes rather than adding one, and saying so is the
#     point: a proof that silently has no context steps looks the same as one
#     whose context was forgotten.
#
# Terminal artifact: the image is NOT one. It is rebuildable from the Dockerfile
# and lives in a runtime's store, not in this tree — hashing an image id would
# record which machine last built it. What the image must satisfy is asserted by
# `container test` against the real thing instead.
#
# Usage: sh proof_workflow/prove_container.sh
# Exit:  0 pass · 2 a step went red · 64 FATAL.
set -u

PROVE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$PROVE_HOME/lib/prove.sh"

prove_init container "loopctl container build -> OCI image -> container preflight (inside)"

# --- the layer's own files ---------------------------------------------------
prove_harness dockerfile loopctl/Dockerfile \
  "base image -> deterministic base (build-checked) + the sandbox runtime's contract: sandbox user/group, iproute2 for proxy-mode isolation, OCI USER as identity fallback, workspace == home == policy-admitted path"
prove_harness wrapper loopctl/container-run.sh \
  "caller -> live-socket selection (a dead /var/run/docker.sock is refused, not absent) -> host uid -> session mounts -> no default ref for serve"
prove_harness preflight loopctl/container_preflight.sh \
  "inside the container -> deterministic base, worktree isolation, and ONE REAL TURN per driver to tell present from authenticated"
# .gitignore decides what `--upload` carries into a sandbox — OpenShell filters by
# it unless told otherwise — and equally what a commit carries. Nothing hashed it
# until an audit asked which of this layer's files were actually measured: editing
# it moved no digest and the lineage hook stayed silent about a change to the rule
# that governs which bytes ever reach a sandbox.
prove_harness upload-boundary .gitignore \
  "the ignore rules -> what \`openshell sandbox create --upload\` sends and what a commit carries; per-run evidence (data/codex-sandbox/, proof_workflow/data/) is excluded here so an agent's draft never lands on main by default"
# The shared skills entering a sandbox under a name. Before it, a sandbox turn
# ran with zero skills and nothing recorded that — "which skills version was this"
# had no answer at all. Its refusal is the mechanism: the canonical is read live
# by five projects through symlinks, so an uncommitted edit there is in force
# everywhere while being in no commit, and carrying that in would put an
# unnameable version behind a receipt claiming reproducibility. It fired on the
# real canonical the first time it was pointed at it.
prove_harness skills-bundle loopctl/skills-bundle.sh \
  "shared-skills canonical -> a bundle named by commit -> <sandbox>/.claude|.codex/skills; a dirty canonical is refused, and the explicit override stamps -dirty so the id can never read as a named commit" \
  -- sh loopctl/skills-bundle.sh --selftest
prove_harness codex-writing-role loopctl/codex-sandbox.sh \
  "host ChatGPT session -> --env -> ~/.codex/auth.json inside an OpenShell sandbox -> one write turn -> changed files back out; its selftest gives each way of having no usable session its own exit" \
  -- sh loopctl/codex-sandbox.sh --selftest

# The paired auto-permission experiment. It has no control group of its own, and
# that is the proportionate call rather than an omission: the script IS a
# control — two sandboxes differing in one variable — and what could silently
# invert its verdict is the grader and the report, both of which carry selftests
# that run here. A second control spending real model turns to check an
# experiment that spends real model turns would buy nothing.
prove_harness automode-bench loopctl/automode-bench.sh \
  "one task x two sandboxes differing only in the guard -> per-run result json; a run is graded before it is counted, so an arm cannot win by failing cheaply" \
  -- sh loopctl/automode-bench.sh --selftest
prove_harness automode-report loopctl/automode_report.py \
  "per-run usage -> per-field medians and a delta; refuses to print a comparison when only one arm answered, and names 'neither answered' differently from 'one answered'" \
  -- python3 loopctl/automode_report.py --selftest

prove_note control-owned-by-harness proof_workflow/control_container_surface.sh \
  "declared here, hashed by the harness proof. Ownership rule: every file under proof_workflow/ belongs to prove_harness.sh, because those files ARE the instrument. Hashing a control in two proofs records one claim twice and makes a single edit look like two moved digests"

# --- what this layer deliberately does not carry -----------------------------
prove_note no-context-lane - \
  "this layer reads no prompt of its own: it carries the other loops' context lanes rather than adding one. Recorded so that 'no context steps' reads as a decision instead of as an omission"
prove_note image-not-an-artifact - \
  "the built image is not hashed: it is rebuildable from the Dockerfile above and lives in a runtime's store, so its id would record which machine last built it rather than what the layer is. Its required shape is asserted by 'container test' against the real image"

# --- the assertion that keeps the two isolation models honest ----------------
# Upload-based sandboxes carry no .git, and every loopctl command resolves its
# root through git. This asserts the dependency exists rather than leaving it as
# prose: if the CLI ever stopped needing a work tree, the division of labour in
# proof_workflow/README.md would be stale and nothing would say so.
prove_harness git-anchored-by-construction - \
  "loopctl resolves the repo root through git, which is why an upload-based sandbox (no .git) cannot host the proofs — asserted, not assumed" \
  -- sh -c 'grep -q "rev-parse --show-toplevel" loopctl/loopctl.sh'

prove_emit
