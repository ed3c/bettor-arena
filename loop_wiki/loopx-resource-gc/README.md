# LoopX Resource GC v1

A single retention and garbage-collection contract so long-running AFK operation
cannot exhaust disk, ports, processes or index stores — while blocked evidence
and audit history stay recoverable. Stage 6 of the terminal queue, on the Ledger
(#63), the Runtime Fabric (#66) and the Worker Fleet (#94). Answers #97.

## Public port

```sh
python3 loop_wiki/loopx-resource-gc/scripts/resourcegc.py \
  <check|selftest|plan|run|verify-receipt>
```

Exit `0` ok, `2` a checked invariant disagreed, `64` unusable input,
**`70` resource exhausted**.

That fourth code is the point of a separate exit: a full disk is not a task that
failed and not a gate that disagreed. Someone reading "GC failed" goes to debug
the GC; someone reading "the disk filled" goes to find space.

## The idea this module rests on

**"Rebuildable" is a claim about the future. The only honest check is to rebuild
it now, next to the original, and compare bytes.**

```text
PROVEN       rebuilt, and byte-identical to what is on disk
DIVERGENT    rebuilt, and different
UNPROVABLE   could not rebuild at all
```

Only `PROVEN` admits deletion.

`DIVERGENT` is the one that gets skipped, and the reasoning that skips it is
entirely reasonable: the rebuild command exists, it runs, it exits zero, it
produces an index — so the projection *is* rebuildable and deleting it costs
nothing. What comes back is not what was there, and whatever the difference
encoded is gone.

The physical control measures that cost rather than arguing it: it deletes the
divergent projection, rebuilds, and shows the original does not come back.

## Selection is subtractive

Everything starts protected and earns its way into the deletable set by passing
each gate in turn; every gate that stops a resource records why. The reverse
arrangement — start deletable, remove what matches a protection rule — selects
whatever nobody wrote a rule for, and the rule nobody wrote is always the one for
the thing nobody thought about.

Never selectable, whatever a plan says or a human admits:

```text
IMMUTABLE_EVIDENCE   ledger segments, Human decisions, release receipts, WAL
blocked evidence     a blocked conflict must stay recoverable
leased or dirty      someone is using it, or the work exists nowhere else
```

A human admitting a ledger segment is in the positive fixtures on purpose: the
plan keeps it anyway, because deleting one destroys the record of *why*
everything else was allowed.

## Also enforced

- a resource with **no last-used time is protected, not expired** — an unknown
  age is not an old age, and a GC that expires on missing data deletes most
  confidently where it knows least;
- a closed resource-class vocabulary: an unknown class is refused rather than
  defaulted, because the default anyone would pick is the permissive one;
- `authorized_by` must be `HUMAN` — an agent or provider cannot admit a
  destructive class;
- path traversal in a resource path;
- residue verification across **four kinds** — path, process, port, mount —
  because they fail independently: a path can be gone while the process holding
  it is not;
- a removal with no tombstone: the resource is gone and so is the record that it
  existed;
- `CLEAN` is asserted after looking. `shutil.rmtree(..., ignore_errors=True)`
  returns nothing and raises nothing, so a cleanup that prints PASS after calling
  it is printing a hope.

## Evidence

```sh
sh loop_wiki/loopx-resource-gc/tests/run-all.sh
```

Three schemas under a digest manifest, nine manifest mutations, eleven positive
properties, thirteen planted controls, and a physical control group.

Every run builds a **real tree**, because the rebuild proofs compare bytes on
disk — a fixture-only suite would be testing the plan's arithmetic and not the
property the plan rests on.

The physical group prints its digests, so a reader can see `PROVEN` really is
byte equality:

```json
"vector-stale":    {"original": "sha256:f681c607…", "rebuilt": "sha256:f681c607…", "state": "PROVEN"}
"graph-divergent": {"original": "sha256:d65cbe36…", "rebuilt": "sha256:47269621…", "state": "DIVERGENT"}
```

**Verified by deliberately breaking it.** Reducing `PROVEN` to a zero exit code:

```
resource-gc control RED: graph-divergent proved PROVEN, expected DIVERGENT
resource-gc control RED: the GC deleted the DIVERGENT projection
exit=2
```

## Boundaries

- The default is a dry run. `--apply` plus a per-resource `--admit` are both
  required, and neither can reach a protected class.
- Every receipt carries `authority: OBSERVATION_ONLY` and
  `canonical_writer: LOOPX_LEDGER_REDUCER`.
- No canonical state write, gate verdict, merge, promotion, permission widening
  or production policy change occurs in this leaf.
