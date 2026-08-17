# Claude Code live lane (issue #91)

The successor lane the frozen leaf's `END.md` points at: the leaf above this
directory closed at `FIXTURE_ONLY`, and live host execution belongs to its own
work. `docs/git/pdf-terminal-sequence.json` assigns
`loop_wiki/loopx-worker-gateway/live` to stage-19 / issue #91, which is also the
only location where the frozen gateway can resolve an `adapter_entry` — that
field is a module-relative path with no `..`, so a successor carrier has to live
under the module root.

Queue state is `BLOCKED_BY_PREDECESSOR` at order 19. These are bytes, not queue
acceptance, and nothing here promotes any host in the frozen `LIVE_MATRIX.md`.

## What is new here

```text
adapters/claude-code.json   IMPLEMENTED descriptor; the frozen adapters/ stays NOT_EXERCISED
adapters/fixture-host.json  stub descriptor for the dry-run lane
carrier.py                  adapter entry: launches one host turn, emits the event stream
run_live_lane.py            request builder, gateway driver, post-run verification
payload/                    the exact bytes the lane carries into the turn
selftest_plants.py          a deliberately misbehaving carrier, selftest only
```

Nothing in the frozen leaf is edited. The frozen `contracts/*.schema.json` are
referenced, not copied: `run_live_lane.py` loads each schema through
`contracts/manifest.json` and refuses it if its SHA-256 has drifted from the pin.

## Running it

```sh
python3 loop_wiki/loopx-worker-gateway/live/run_live_lane.py --selftest
python3 loop_wiki/loopx-worker-gateway/live/run_live_lane.py --dry-run
python3 loop_wiki/loopx-worker-gateway/live/run_live_lane.py --live
```

`--selftest` runs one stub baseline, four planted controls that must each go RED
(wrong subject, dirty worktree, missing receipt field, fabricated event digest)
and a preflight of the live subject that stops short of the launch.

`--dry-run` runs the whole chain — lease a detached worktree of the exact
subject, invoke the carrier, collect events, write and validate the receipt,
clean up — with the stub carrier. `--live` is the same chain with `claude`.

`jsonschema` is required; without it the runner exits `64` rather than skipping
the schema binding.

## Why a dry-run receipt cannot be mistaken for a live one

```text
receipt.adapter.host_id           fixture-host, never claude-code
receipt.adapter.binary_identity   "python3 fixture-adapter", stamped by the frozen gateway
receipt.adapter.descriptor_digest the stub descriptor's digest
gateway invocation                requires the explicit --allow-fixture-adapter flag
published contracts               reject a fixture-host request/descriptor outright
lane.json.mode                    DRY_RUN_STUB_CARRIER
```

The last row is the weak one and is not relied on: the first five are structural.
The runner asserts the published-contract rejection instead of skipping it, so
"the stub is out of contract" is a checked property rather than a comment.

## The carried payload

`payload/live-turn-prompt.txt` is one line and is passed as `argv`. Its digest is
bound into `task.prompt_ref` and re-checked by the carrier before launch; the
worktree is searched first and the source checkout second, so an uncommitted
prompt still has to match the digest the gateway already bound.

`skill` names `payload/SKILL.md` because the request contract requires a Skill;
`capabilities.loaded_skill_digest` stays `false`. `context.entry_files` names
`AGENTS.md` and `CLAUDE.md`, which the host may auto-load from the worktree, and
`context.digest` covers exactly those bytes. Neither field claims the host read
anything — at `PROCESS_ONLY` that is not observable.

## Known ceilings

```text
mode=READ_ONLY with an empty writable set   any path the host touches turns the run RED
carrier timeout 300s, gateway timeout 330s  the gateway kill is the process-group backstop
env reaches the host by allowlist only      HOME/LOGNAME/TMPDIR/USER; agent-session names are dropped twice
argv is the admitted recipe verbatim        a bad flag surfaces as exit != 0 plus carrier-stderr.bin
receipts/live/turn-1 is single-shot         a second --live refuses rather than overwriting evidence
```
