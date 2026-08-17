# claude-code-live-canary

The instruction payload this lane carries into one Claude Code host turn.

```text
carried to the host   the single line of payload/live-turn-prompt.txt, as argv
not carried           this file, any Skill directory, any context capsule
host-side context     whatever the host itself loads from the leased worktree
```

The request must name a Skill, so it names this document and digests these
exact bytes. That is an honest description of the carried payload, not a claim
that the host loaded a Skill: `capabilities.loaded_skill_digest` stays `false`
and the adapter trace ceiling stays `PROCESS_ONLY`.

The turn is read-only. The request runs in `READ_ONLY` mode with an empty
writable set, so any path the host changes inside the leased worktree turns the
run RED instead of being absorbed.
