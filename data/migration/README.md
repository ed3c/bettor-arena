# Migration evidence

This directory stores versioned migration manifests and apply receipts.

Migration is transactional:

```text
plan → verify preconditions → apply → verify target → append receipt
```

Rollback is allowed only against the exact apply receipt and only when target bytes have not changed since apply. Receipts store bounded hashes and provenance, not secret values or raw credential-bearing output.
