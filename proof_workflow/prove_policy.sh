#!/bin/sh
# prove_policy.sh — physical traversal proof of the external authorization surface.
#
# What an outside caller is allowed to reach is decided in two places, and the
# split is not tidy — it is forced. The sandbox policy governs the network; the
# checked-in MCP policy and server govern which tools exist to be called. They are proved together
# because a claim about authorization that covers only one of them is false by
# omission: the installed gateway cannot match per tool, so the explicit MCP
# allowlist and the server's default-deny behavior must agree with the sandbox
# network policy.
#
#   DETERMINISTIC harness — the policy document, the server that enforces what
#     the policy cannot express, the generated tool surface, the result shape,
#     and both controls that drive denials for real.
#   PROBABILISTIC read documents — none. Nothing here is read by a model; this
#     layer decides what a model-driven caller may do. Said out loud so that "no
#     context steps" reads as a property rather than as an omission.
#
# Terminal artifact: none in this tree. The layer's output is a refusal, and a
# refusal leaves no file — which is exactly why `policy test` and `mcp test`
# exist, and why this proof hashes them rather than pretending a receipt could
# stand in for driving the denial.
#
# Usage: sh proof_workflow/prove_policy.sh
# Exit:  0 pass · 2 a step went red · 64 FATAL.
set -u

PROVE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$PROVE_HOME/lib/prove.sh"

prove_init policy "sandbox-policy.yaml (network) + mcp-policy.json explicit allowlist + Bun default-deny runtime -> what an external caller may reach"

# --- the network half --------------------------------------------------------
prove_harness sandbox-policy loopctl/sandbox-policy.yaml \
  "deny-by-default network surface: model endpoints bound to the single binary allowed to use them; one MCP port named on the host alias and nothing else local"
prove_note policy-control-owned-by-harness proof_workflow/control_sandbox_policy.sh \
  "declared here, hashed by the harness proof. Ownership rule: every file under proof_workflow/ belongs to prove_harness.sh, because those files ARE the instrument. Hashing a control in two proofs records one claim twice and makes a single edit look like two moved digests — the same reason README.md is declared rather than hashed there"

# --- the tool half, which the installed gateway cannot express ---------------
prove_harness mcp-policy .arena/mcp-policy.json \
  "reviewed explicit tool allowlist -> the only command names the MCP surface may generate"
prove_harness mcp-server-compat loopctl/mcp_server.py \
  "stable Python compatibility entry -> the Bun MCP runtime"
prove_harness mcp-runtime loopctl/mcp_runtime.ts \
  "stdio + HTTP transports, per-call disposable worktree at the pinned ref, and an unknown-tool selftest that requires an externally-denied diagnostic" \
  -- bun loopctl/mcp_runtime.ts --selftest
prove_harness mcp-tools-compat loopctl/mcp_tools.py \
  "stable Python compatibility entry -> the Bun MCP tool generator"
prove_harness mcp-tools loopctl/mcp_tools.ts \
  "contract.json + explicit policy -> the MCP tool list, generated so the two surfaces cannot drift" \
  -- bun loopctl/mcp_tools.ts --selftest
prove_harness result-shape loopctl/result_json.py \
  "one machine-readable result per invocation: exit unchanged, artifacts scraped from the run's own announcement, truncation declared" \
  -- python3 loopctl/result_json.py --selftest
prove_note mcp-control-owned-by-harness proof_workflow/control_mcp_surface.sh \
  "declared here, hashed by the harness proof — same ownership rule as above"

# --- the assertion that keeps the two halves honest about each other ---------
# The policy carries a comment saying per-tool rules live in the server because
# the installed gateway rejects a `tool:` matcher. If someone later adds tool
# rules to the YAML believing they are enforced, this goes red rather than
# leaving two documents quietly disagreeing about who is in charge.
prove_harness authorization-split-is-real - \
  "the policy must NOT claim per-tool rules while the server owns them: a \`tool:\` matcher in the YAML would be silently unenforced on the running gateway" \
  -- sh -c '! grep -qE "^\s+tool:" loopctl/sandbox-policy.yaml'
# The subscription backend is NOT api.openai.com, and a policy that admits only
# the latter denies every codex turn while reading as though codex is allowed.
# Asserted statically here because the real turn that would catch it is opt-in
# (CONTROL_CODEX_TURN=1) and therefore absent from a default run — one arrival
# that always runs, one that proves it end to end, and neither is fooled by what
# fools the other.
prove_harness codex-subscription-backend-admitted - \
  "codex on a ChatGPT session dials chatgpt.com/backend-api/codex, so the policy must name that host AND bind it to codex's binary — an endpoint without the binding would let anything in the sandbox spend the session" \
  -- python3 -c 'import sys, yaml; p = yaml.safe_load(open("loopctl/sandbox-policy.yaml"))["network_policies"]; ok = any(any(e["host"] == "chatgpt.com" for e in v["endpoints"]) and any("codex" in b["path"] for b in v.get("binaries", [])) for v in p.values()); sys.exit(0 if ok else 2)'
prove_note no-context-lane - \
  "this layer reads no prompt: it decides what a model-driven caller may do rather than being read by one. Recorded so the absence is a property, not an omission"
prove_note refusal-leaves-no-artifact - \
  "no terminal artifact is hashed because the output of this layer is a REFUSAL, which writes nothing. The controls above are what turn that into evidence"

prove_emit
