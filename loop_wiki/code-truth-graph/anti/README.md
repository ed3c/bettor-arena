# Negative-control notes

Record named planted defects and why each must fail. Test artifacts themselves stay in disposable directories.

| control id | planted defect | must fail because |
| --- | --- | --- |
| `verifier-missing-human-gate` | removes `human_gate` from the verifier's closed result shape | a route result without the terminal authority edge is hollow |
| `relocation-root-coupling` | pins `run.sh` back to its original checkout | a relocated runtime must execute its own bytes, not resolve upward or sideways |
| `local-receipt-open-schema` | makes `claim_boundary` optional in the trusted-local receipt | a receipt without its non-egress boundary can be misread outside the subject |
| `mcp-local-artifact-list-leak` | restores the CLI artifact list beside bounded inline delivery | remote delivery must not expose carrier-local artifact references |

`control_ctg_entry.sh` installs each defect in a detached worktree, byte-checks the mutation, requires exit 2,
restores the file, and records the outcome in the CTG control receipt.
