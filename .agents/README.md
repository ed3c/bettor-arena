# `.agents/` — Skill requirements, bindings, and projections

Owner: the selected Skill closure used by bettor-arena.

```text
module requirements
→ shared Skill requirements
→ immutable source binding
→ module-set aggregation
→ local or bundled host projection
→ adapter/consumer receipt
```

Machine authorities:

- `shared-skills.requirements.json` — desired Skill names/interfaces.
- `bindings/*.json` — resolved immutable source/content identity.
- `module-set.json` — aggregate Skill/runtime/host integration subject.
- `skills/` — development projections and repo-owned Skills.

A symlink is a local development projection, not a release. Shared Skill bodies remain canonical in `skills-shared`; repo-owned differences live here or under `.skill-bindings/` as explicitly classified.
