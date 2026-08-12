# `.agents/skills/`

Owner: bettor-arena's local Skill projection surface.

- Shared Skill names normally point to the canonical `skills-shared` checkout during local development or are materialized from an immutable requirements-filtered bundle during execution.
- Repo-owned Skills such as product/runbook mappings may live as real directories.
- `SKILL.md` is procedural. Domain examples belong under `modules/` and are loaded on demand.
- A repo-local copy of a shared name is shadowing unless explicitly classified.

This directory never stores credentials, browser profiles, provider sessions, or executable dependencies from another checkout.
