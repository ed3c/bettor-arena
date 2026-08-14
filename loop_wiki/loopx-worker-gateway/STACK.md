# Molecular Stack relation

```text
feat/loopx-contract-v1 (#74)
├── feat/loopx-ledger-v1 (#75)
└── feat/loopx-worker-gateway-v1 (this terminal leaf)
```

The ledger and Worker Gateway are siblings: both consume the unmerged LoopX contract bytes, but neither consumes the other's implementation. A later strategy/HITL or convergence leaf may depend on their admitted interfaces.

GitHub base/head metadata is publication truth. Local Git Town metadata, if any, must not override the exact relationship above.
