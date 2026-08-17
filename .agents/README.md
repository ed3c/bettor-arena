# `.agents/` — Skill requirements, bindings, and projections

Owner: the selected Skill closure used by bettor-arena.

```text
authored immutable source pin
→ desired shared Skill requirements
→ canonical shared generator
→ generated immutable consumer binding
→ module-set aggregation
→ local or bundled host projection
→ adapter/consumer receipt
```

Machine authorities:

- `shared-skills.source.json` — authored immutable upstream repository, commit, tree, interface blobs, and canonical generator blob.
- `shared-skills.requirements.json` — desired shared and repo-owned Skill names plus host surfaces.
- `bindings/*.json` — generated immutable source/content identity; never edit these digests by hand.
- `module-set.json` — aggregate Skill/runtime/host integration subject.
- `skills/` — development projections and repo-owned Skills.

For shared Skill, module, binding, projection, or adapter changes, read [`../docs/architecture/DOMAIN_DECOUPLING.md`](../docs/architecture/DOMAIN_DECOUPLING.md). Resolve the exact shared subject before generating a projection. The existing `Sync feature modular contracts` workflow is the single generator owner: it checks out the source pin, runs the canonical shared `shared_skills.py sync`, validates the result, and then refreshes the dependent modular projections.

A local symlink can support development, but cannot satisfy immutable binding or release evidence. Shared Skill bodies remain canonical in `skills-shared`; repo-owned differences live here or under `.skill-bindings/` as explicitly classified.

Forbidden:

```text
mutable main/latest as source identity
hand-edited generated binding digests
consumer copies of canonical shared SKILL.md bodies
machine-local paths, credentials, or sessions in the pin
a provider/package-presence check promoted to execution evidence
```
