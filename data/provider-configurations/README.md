# Provider configuration receipts

Each JSON file binds the typed transition from the historical unpinned
candidate manifests to fixed Serena and GrepAI on-demand policies. It records
the current exact subject, the older live-evidence subject, the rollback
subject, and both before/after manifest digests.

`CONFIGURED` is not `ADMITTED`: a new live canary for the configured exact
subject and a separate activation-controller pass are still required.
