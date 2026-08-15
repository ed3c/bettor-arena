#!/bin/sh
# verify_modular_contracts.sh — run the Modular contracts workflow's evidence
# locally, so a private repository does not have to spend an Actions job-minute
# to learn whether the tree is coherent.
#
# This is the `local_verification` argv named by .github-delivery/ci-policy.json.
# It mirrors .github/workflows/modular-contracts.yml step for step, minus the
# two steps that are only meaningful on a runner: the artifact upload, and the
# origin probe, which asks GitHub about an exact pushed commit that does not
# exist yet when this runs.
#
# The render step writes to a scratch directory and compares, exactly as the
# workflow does — it never rewrites the checked-in projections, because a
# verifier that fixes what it measures cannot fail.
#
# Exit: 0 coherent · 2 a check disagreed · 64 usage or missing tool.

set -eu

ROOT=$(cd "$(dirname "$0")/../.." && pwd -P)
OUT=${VERIFY_MODULAR_OUT:-${TMPDIR:-/tmp}/bettor-verify-modular}
FACTORY="$ROOT/loop_wiki/evolve-perfect-seed-repo-factory"

fatal() { echo "verify-modular FATAL: $1" >&2; exit 64; }
red() { echo "VERIFY-MODULAR-RED $1" >&2; RED=1; }

command -v python3 >/dev/null 2>&1 || fatal "python3 not on PATH"
command -v bun >/dev/null 2>&1 || fatal "bun not on PATH (install from https://bun.sh)"

cd "$ROOT"

# check_project_bootstrap's selftest refuses to run against a dirty checkout,
# and on a runner the tree is always clean. Refusing here with 64 keeps that
# distinct from a check that ran and disagreed: an unmeasurable tree is not a
# coherent one, and reporting it as either PASS or FAIL would be a claim this
# script cannot support.
if [ -n "$(git -C "$ROOT" status --porcelain)" ]; then
  fatal "working tree is dirty; commit or stash first (the bootstrap selftest requires a clean source checkout)"
fi

RED=0
rm -rf "$OUT"
mkdir -p "$OUT"

# --- the workflow's compile lane -------------------------------------------
python3 -m py_compile \
  scripts/arena_modules.py \
  scripts/arena_ownership.py \
  scripts/arena_lock.py \
  scripts/arena_proof.py \
  scripts/arena_context.py \
  scripts/arena_project.py \
  scripts/gates/check_agent_docs.py \
  scripts/gates/check_readme_coverage.py \
  scripts/gates/check_module_catalog.py \
  scripts/gates/check_mcp_policy.py \
  loopctl/mcp_tools.py \
  loopctl/mcp_runtime.py \
  loopctl/mcp_server.py || red "python entrypoints do not compile"

bun build \
  loopctl/mcp_runtime.ts loopctl/mcp_tools.ts scripts/gates/check_mcp_policy.ts \
  scripts/project_types.ts scripts/project_resolver.ts scripts/project_transaction.ts \
  scripts/arena_project.ts scripts/gates/check_project_bootstrap.ts \
  scripts/environment_types.ts scripts/arena_origins.ts \
  scripts/arena_origin_checkout_probe.ts scripts/arena_browser.ts \
  scripts/gates/check_environment_contracts.ts \
  --target=bun --outdir="$OUT/bun-build" >/dev/null || red "bun entrypoints do not build"

# --- can these gates disagree at all? --------------------------------------
bun test loopctl/mcp_core.test.ts >/dev/null 2>&1 || red "mcp_core tests"
for s in loopctl/mcp_tools.ts loopctl/mcp_runtime.ts scripts/gates/check_mcp_policy.ts \
         scripts/gates/check_project_bootstrap.ts scripts/gates/check_environment_contracts.ts; do
  bun "$s" --selftest >/dev/null 2>&1 || red "selftest $s"
done
for s in scripts/gates/check_agent_docs.py scripts/gates/check_readme_coverage.py \
         scripts/arena_lock.py scripts/arena_proof.py scripts/arena_context.py; do
  python3 "$s" --selftest >/dev/null 2>&1 || red "selftest $s"
done

# --- current-tree contracts -------------------------------------------------
python3 scripts/gates/check_agent_docs.py >/dev/null || red "check_agent_docs"
python3 scripts/gates/check_readme_coverage.py >/dev/null || red "check_readme_coverage"
bun scripts/gates/check_mcp_policy.ts >/dev/null || red "check_mcp_policy"
bun scripts/gates/check_project_bootstrap.ts >/dev/null || red "check_project_bootstrap"
bun scripts/gates/check_environment_contracts.ts >/dev/null || red "check_environment_contracts"
sh tests/test_ctg_mcp_carrier.sh >/dev/null 2>&1 || red "stateless MCP consumer canary"

# --- render one coherent expected release, then compare --------------------
# arena_context and arena_proof read the composition lock from the tree, so the
# workflow swaps in the freshly resolved one and restores it. Same dance here,
# with the restore on a trap so an interrupted run cannot leave it swapped.
cp .arena/locks/bettor-arena.lock.json "$OUT/original-lock.json"
trap 'cp "$OUT/original-lock.json" .arena/locks/bettor-arena.lock.json 2>/dev/null || true' EXIT INT TERM

python3 scripts/arena_lock.py resolve \
  --requirements .arena/compositions/bettor-arena.requirements.json \
  --output "$OUT/bettor-arena.lock.json" >/dev/null
cp "$OUT/bettor-arena.lock.json" .arena/locks/bettor-arena.lock.json
python3 scripts/arena_context.py lock --output "$OUT/contexts.lock.json" >/dev/null
python3 scripts/arena_context.py parity --output "$OUT/driver-parity.json" >/dev/null
python3 scripts/arena_proof.py subjects --output "$OUT/subjects.lock.json" >/dev/null
python3 scripts/arena_proof.py release \
  --subjects "$OUT/subjects.lock.json" \
  --output "$OUT/release-receipt.json" >/dev/null
bun loopctl/mcp_tools.ts loopctl/contract.json \
  --policy .arena/mcp-policy.json > "$OUT/mcp-exposure.json"
bun scripts/arena_origins.ts status --output "$OUT/origin-status.json" >/dev/null
bun scripts/arena_browser.ts status --output "$OUT/browser-status.json" >/dev/null

cp "$OUT/original-lock.json" .arena/locks/bettor-arena.lock.json
trap - EXIT INT TERM

compare() {
  python3 - "$1" "$2" <<'PY' || red "checked-in $1 differs from the rendered one"
import json, sys
a, b = sys.argv[1:3]
sys.exit(0 if json.load(open(a)) == json.load(open(b)) else 1)
PY
}
compare .arena/locks/bettor-arena.lock.json "$OUT/bettor-arena.lock.json"
compare .arena/contexts.lock.json "$OUT/contexts.lock.json"
compare data/context-capsules/driver-parity.json "$OUT/driver-parity.json"
compare data/module-proof/subjects.lock.json "$OUT/subjects.lock.json"
compare data/module-proof/release-receipt.json "$OUT/release-receipt.json"
compare data/mcp/exposure.json "$OUT/mcp-exposure.json"
compare data/origins/status.json "$OUT/origin-status.json"
compare data/browser/status.json "$OUT/browser-status.json"

[ "$RED" -eq 0 ] || { echo "verify-modular FAIL" >&2; exit 2; }
echo "PASS modular contracts verified locally (8 projections, gates and selftests)"
