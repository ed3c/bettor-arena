# Security and privacy boundary

The terminal leaf enforces typed argv, exact-subject worktrees, process-group control, bounded output, changed-path allowlists, content digests and cleanup observation.

It does **not** yet attest:

- kernel/VM filesystem isolation;
- network denial or domain allowlists;
- secret-broker dereference;
- container/MicroVM escape resistance;
- model-provider data retention;
- live host authentication safety.

Those claims remain `NOT_EXERCISED` until runtime-fabric and live-canary receipts exist. No raw credential, cookie, browser profile, private key, hidden reasoning or unredacted signed-in content may enter Git or a Worker receipt.
