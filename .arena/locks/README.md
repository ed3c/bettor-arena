# Composition locks

A lock is the deterministic result of resolving one composition requirements file against the current module catalog and ownership map.

[`bettor-arena.lock.json`](bettor-arena.lock.json) binds:

- selected modules and components;
- interface versions and manifest digests;
- capability providers;
- requirements digest;
- ownership-class and tracked-path ownership digests.

Do not hand-edit a lock. Regenerate it from the requirements and compare canonical JSON bytes in CI. A module implementation change may alter module proof subjects without altering the composition lock; a manifest, requirements or ownership change must alter the lock.
