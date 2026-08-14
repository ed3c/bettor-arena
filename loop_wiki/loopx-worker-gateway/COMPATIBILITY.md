# Six-host compatibility contract

The common portable surface is intentionally small:

```text
SKILL.md package + host projection
exact subject + Context Capsule digest
typed executable + argv
observable process/filesystem artifacts
non-authoritative Worker receipt
```

Host-specific Skill discovery, configuration and structured-event details stay in the adapter manifest. They do not change the common request/event/receipt Schemas. A host that cannot satisfy the requested policy returns a checked refusal rather than silently degrading.
