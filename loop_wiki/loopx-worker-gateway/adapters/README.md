# Worker adapter contracts

```text
Codex CLI   SOURCE_VISIBLE_HOST
Claude Code GRAY_BOX
Grok Build  WHITE_BOX_REFERENCE
OpenCode    SOURCE_VISIBLE_HOST
Pi          WHITE_BOX_REFERENCE
Ante        EXPERIMENTAL_GRAY_BOX
```

These labels describe Harness observability ceilings, not model-weight visibility or runtime success. Every static adapter remains `NOT_EXERCISED`; no binary/version/session/provider is admitted by this directory.

Gray-box hosts may expose process/filesystem observations and documented structured output, but the gateway must not fabricate hidden tool calls or private reasoning. White-box reference hosts still execute inside a separately governed runtime and cannot write LoopX state or Gate verdicts.
