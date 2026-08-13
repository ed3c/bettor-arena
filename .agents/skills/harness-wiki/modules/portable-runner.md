# Host-owned portable Skill runner

## Decision

`SKILL.md` supplies reusable procedure and context. It does not execute a command, evaluate its own assertions, mark a Todo complete, promote a release, or issue Human Admit. Those powers remain in deterministic host code.

The public host-only port is:

```bash
sh loopctl/loopctl.sh skill-execution run \
  --request /trusted/request.json \
  --assertions /trusted/assertions.json \
  --repo /trusted/repository \
  --output /fresh/receipt-directory
```

## Execution chain

```text
exact request + assertion-set digest
→ exact Git repository / commit / tree
→ exact canonical Skill directory digest
→ detached disposable worktree
→ executable + argv (shell=false)
→ bounded process group / timeout / environment / output
→ OS and artifact observations
→ independent assertion evaluator
→ content-addressed artifacts
→ subject-bound receipt
→ mandatory worktree cleanup
```

The Worker may propose source changes and emit stdout/stderr. It cannot write an assertion verdict, modify LoopX state, waive a hard gate, promote a release, or sign Human Admit.

## Local-process adapter: what it proves

The current adapter can directly observe and attest:

- exact repository remote, commit and tree;
- exact Skill package digest;
- exact assertion-set digest;
- one executable plus an argv vector with `shell=False`;
- explicit environment names with secret-like names refused;
- a new process group, timeout and forced termination;
- stdout, stderr, changed paths and selected artifacts by SHA-256;
- post-run writable/read-only path boundaries;
- independent hard/advisory assertion outcomes;
- append-only output directory and worktree cleanup.

It does **not** claim physical network denial or OS-enforced filesystem isolation. Requests declaring `network=deny` or `network=allowlisted` return `SKIPPED_BY_POLICY` until a physical sandbox adapter can produce that evidence. Post-run diff checks detect a repository boundary violation; they do not prevent a malicious process from touching the host.

## Assertion support

Implemented assertion kinds:

- `subject_match`
- `exit_code`
- `stderr_pattern`
- `stdout_json_schema`
- `file_exists`
- `file_hash`
- `file_content`
- `git_diff_allowlist`
- `lsp_diagnostics` from a declared JSON artifact
- `test_report` from a declared JUnit XML artifact
- `artifact_digest`

An unknown assertion kind fails closed. A model-based reviewer belongs in an `advisory` assertion or a separately calibrated verifier; it cannot silently become a hard gate.

## Named exits

- `0`: execution occurred, cleanup passed and every hard assertion passed.
- `2`: checked execution/assertion failure or fail-closed policy skip.
- `64`: malformed usage/input, absent executable, unresolvable exact subject or output collision.

Portable execution PASS is not a live Codex CLI, Claude Code, Grok Build, OpenCode, Pi or Ante canary. Host/provider/model/sandbox evidence remains separately named.
