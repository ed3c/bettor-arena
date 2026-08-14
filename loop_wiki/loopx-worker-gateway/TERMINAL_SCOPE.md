# Terminal scope freeze

This leaf owns only:

```text
loop_wiki/loopx-worker-gateway/**
.arena/modules/loopx-worker-gateway/**
.github/workflows/loopx-worker-gateway.yml
```

It does not edit shared composition requirements, generated release locks, `loopctl`/MCP public surfaces, live credential/provider configuration, runtime-fabric, LoopX ledger state or final convergence indexes except through generated feature-branch projections.
