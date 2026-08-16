# ADE Git Town Stack Plan

## Current stack

```text
main @ d233da14ceb5ffcddc330169ab146c31d56e6191
└── agent/ade-provider-routing-v1
    └── agent/ade-tech-lead-adoption-v1
```

The child is a true dependency: it consumes the Blindspot Hybrid provider binding introduced by the foundation branch. It is not an arbitrary linear stack.

## Publication

- foundation PR base: `main`;
- Tech Lead adoption PR base: `agent/ade-provider-routing-v1`;
- both start as draft;
- no automatic merge;
- semantic conflicts, merge, release, permissions, and Forgejo remote configuration are Human-owned.

## Future parallel work

After the shared compiler is admitted, a plan may create path-disjoint siblings for provider adapters, runtime receipts, UI, and eval fixtures. Any shared registry/index update belongs to an explicit convergence task after required sibling subjects are admitted.

## Blindspots still requiring runtime receipts

- actual Git Town branch/worktree synchronization;
- grepai/SCIP/Tree-sitter/Serena provider identities, health, freshness, and bounded output;
- SQLite/LanceDB live projection rebuild;
- multi-Agent allocation, cancellation, retry, and budget enforcement;
- private Forgejo remote connectivity and non-public history proof;
- CI completion and Human Admit.
