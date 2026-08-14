# Worker Gateway tests

`run-all.sh` validates the four typed contracts, the exact six-host registry, the executable fixture gateway, cleanup and planted negative controls.

The positive fixture uses a temporary Git repository and a synthetic Python Worker. It proves the gateway mechanism only. It does **not** prove that Codex CLI, Claude Code, Grok Build, OpenCode, Pi or Ante is installed, authenticated, healthy, capable or equivalent.

Mutation/control coverage includes adapter digest drift, host/subject mismatch, absolute/traversal paths, secret-shaped environment names, false authority fields, unavailable physical attestations, gray-box overclaim, write escape, output limit, timeout, cancellation, false success, receipt replay, duplicate event sequence and private-reasoning persistence.
