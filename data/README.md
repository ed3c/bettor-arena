# Versioned evidence and generated snapshots

`data/` stores checked-in machine evidence. It is not an implementation source tree and must not contain secrets, browser profiles, cookies, OAuth material, `.env` values or unbounded prompt/stdout dumps.

This README is navigation only; it is not a receipt.

| Path | Content |
|---|---|
| [`module-proof/`](module-proof/) | Module closure subjects and aggregate release receipt |
| [`context-capsules/`](context-capsules/) | Claude/Codex driver parity and Context Capsule evidence |
| [`mcp/`](mcp/) | Generated MCP exposure snapshot |
| [`origins/`](origins/) | Logical release origin status |
| [`browser/`](browser/) | Browser Contract v2 status |
| [`proof-workflow/`](proof-workflow/) | Legacy/traversal receipts keyed by loop and repository subject |
| [`migration/`](migration/) | Migration manifests and append-only apply reports |
| [`receipts/`](receipts/) | Other admitted versioned receipts |

Rules:

1. Regenerate deterministic snapshots; do not hand-edit them.
2. A receipt records observed provenance and status; it does not prove an unexecuted external path.
3. Per-run private or volatile outputs remain ignored and are represented only by bounded hashes/counts where the contract allows.
4. `NOT_EXERCISED`, ABSENT and FAIL cannot be normalized to PASS.
