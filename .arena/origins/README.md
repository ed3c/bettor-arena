# Logical release origins

[`release.json`](release.json) defines GitHub and Forgejo as origins of one logical release rather than interchangeable mutable branches.

Accepted equivalence must be explicit, such as:

- exact commit;
- same Git tree;
- same release manifest and selected closure.

A missing or unreachable origin remains distinct from a mismatch. Mutable `main` is never a release identity.

Commands:

```sh
bun scripts/arena_origins.ts status
bun scripts/arena_origin_checkout_probe.ts --help
```

Current generated status is [`../../data/origins/status.json`](../../data/origins/status.json).
