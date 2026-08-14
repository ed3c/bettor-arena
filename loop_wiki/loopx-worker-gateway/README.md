# LoopX Worker Gateway v1

This module defines one host-neutral execution boundary for Codex CLI, Claude
Code, Grok Build, OpenCode, Pi, and Ante.

It is deliberately **not** a model router, winner selector, state reducer,
sandbox attestation service, or release authority.

```text
LoopX command proposal
+ immutable repository/task/Skill/context subject
+ disposable workspace lease
+ typed policy
→ trusted host adapter
→ observable process/artifact events
→ subject-bound Worker receipt
→ independent Gates
→ LoopX reducer
```

## Authority law

```text
Strategy proposes
Worker executes
Gates observe
LoopX reducer commits
Human admits
```

A Worker receipt cannot set a Gate verdict, mutate the LoopX ledger, waive a
policy, sign a Human decision, promote a release, or claim hidden gray-box
events.

## Host classifications

| Host | Harness classification | Initial execution state |
|---|---|---|
| Codex CLI | `SOURCE_VISIBLE_HOST` | `NOT_EXERCISED` |
| Claude Code | `GRAY_BOX_HOST` | `NOT_EXERCISED` |
| Grok Build | `SOURCE_VISIBLE_HOST` | `NOT_EXERCISED` |
| OpenCode | `SOURCE_VISIBLE_HOST` | `NOT_EXERCISED` |
| Pi | `SOURCE_VISIBLE_HOST` | `NOT_EXERCISED` |
| Ante | `EXPERIMENTAL_GRAY_BOX_HOST` | `NOT_EXERCISED` |

Source visibility of a Harness does not make its provider/model white-box.
Documentation support does not constitute a live canary.

## Public port

```sh
python3 loop_wiki/loopx-worker-gateway/scripts/gateway.py validate \
  --registry loop_wiki/loopx-worker-gateway/contracts/host-registry.json \
  --request <request.json>

python3 loop_wiki/loopx-worker-gateway/scripts/gateway.py probe \
  --registry loop_wiki/loopx-worker-gateway/contracts/host-registry.json \
  --output <fresh-output-dir>

python3 loop_wiki/loopx-worker-gateway/scripts/gateway.py run \
  --registry <admitted-or-fixture-registry.json> \
  --request <request.json> \
  --output <fresh-output-dir>

python3 loop_wiki/loopx-worker-gateway/scripts/gateway.py selftest
```

Exit codes:

```text
0   checked request or execution passed
2   checked request/execution/policy failed
64  malformed invocation, missing input, tool failure, or receipt collision
```

The checked-in production registry is contract-only. `run` refuses its
`NOT_EXERCISED` entries. Tests use a separate `FIXTURE_ONLY` registry whose
adapter launches a deterministic Python fixture.

## Security boundary

The local process adapter can attest:

- exact argv construction with `shell=False`;
- disposable workspace creation;
- process-group start, timeout, cancel and kill;
- bounded stdout/stderr artifacts;
- exact request/host/Skill/context identity;
- cleanup and residue check.

It cannot attest kernel-enforced network or filesystem isolation. A request that
requires those properties is refused unless an admitted physical-sandbox adapter
supplies the corresponding attestation. Runtime Fabric issue #66 owns that work.

## Evidence

```sh
sh loop_wiki/loopx-worker-gateway/tests/run-all.sh
```

The suite includes one positive fixture, one hollow fixture, and independent
mutations for fake PASS, host/subject/Skill/context drift, raw shell, path
escape, secret-bearing environment input, Worker authority escalation,
gray-box internal-event fabrication, timeout, process-group cleanup, mutable
workspace reuse and unsupported host/flag behavior.

## Non-goals

- no live host authentication or paid model call;
- no cross-host quality ranking;
- no LangGraph strategy policy;
- no direct LoopX ledger write;
- no Gate verdict written by a Worker;
- no provider activation, composition selection, MCP exposure, merge, promotion,
  rollback, or Human Admit.
