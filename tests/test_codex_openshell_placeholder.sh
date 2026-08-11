#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
POLICY="${ROOT}/.runtime-env/policies/codex-openshell-chatgpt-placeholder.json"
RENDERER="${ROOT}/loopctl/codex-openshell-config.py"

python3 "${RENDERER}" --policy "${POLICY}" --selftest >/dev/null
config="$(python3 "${RENDERER}" --policy "${POLICY}")"

grep -Fxq 'model_provider = "openshell_chatgpt"' <<<"${config}"
grep -Fxq 'base_url = "https://chatgpt.com/backend-api/codex"' <<<"${config}"
grep -Fxq 'env_key = "CODEX_AUTH_ACCESS_TOKEN"' <<<"${config}"
grep -Fxq 'requires_openai_auth = false' <<<"${config}"
grep -Fxq 'supports_websockets = false' <<<"${config}"
grep -Fxq '"ChatGPT-Account-ID" = "CODEX_AUTH_ACCOUNT_ID"' <<<"${config}"
! grep -Fq 'auth.json' <<<"${config}"

for carrier in loopctl/codex-sandbox.sh loopctl/automode-bench.sh; do
  grep -Fq 'codex-openshell-config.py' "${ROOT}/${carrier}"
  grep -Fq -- '--provider' "${ROOT}/${carrier}"
  ! grep -Fq 'CODEX_AUTH_JSON' "${ROOT}/${carrier}"
  ! grep -Fq 'printenv CODEX_AUTH' "${ROOT}/${carrier}"
done

echo 'PASS: Codex OpenShell carriers use opaque HTTP placeholders, never sandbox auth.json'
