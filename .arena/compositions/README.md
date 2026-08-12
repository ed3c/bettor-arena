# Composition requirements

A composition requirements file declares the desired modules and components. It is a request, not a resolved release.

[`bettor-arena.requirements.json`](bettor-arena.requirements.json) is the owner composition. Resolution must:

- select a provider for every required capability;
- reject duplicate or incompatible providers;
- validate requested and required components;
- reject path ownership conflicts;
- compute the selected Skill/runtime closure;
- emit a deterministic lock under [`../locks/`](../locks/).

Resolve without mutation:

```sh
python3 scripts/arena_lock.py resolve \
  --requirements .arena/compositions/bettor-arena.requirements.json
```
