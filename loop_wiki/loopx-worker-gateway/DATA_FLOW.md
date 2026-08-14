# Worker Gateway data flow

```text
LoopX dispatch proposal
+ exact repository/task subject
+ immutable Skill and Context digests
+ adapter manifest digest
        ↓
request validation
        ↓
detached exact-subject worktree lease
        ↓
typed executable + argv launch (`shell=False`)
        ↓
process-group stdout/stderr/exit observation
+ changed-path/diff observation
        ↓
timeout / cancel / output / write-policy controls
        ↓
content-addressed artifacts
        ↓
worktree cleanup observation
        ↓
non-authoritative Worker receipt
        ↓
independent Gate evaluation (outside this module)
        ↓
LoopX reducer transition (outside this module)
```

The gateway never reads or persists private reasoning. Gray-box internal actions remain unknown unless the host emits a documented structured event that can be independently captured.
