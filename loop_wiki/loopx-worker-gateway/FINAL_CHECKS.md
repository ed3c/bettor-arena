# Pre-PR checks

```sh
sh loop_wiki/loopx-worker-gateway/tests/run-all.sh
python3 scripts/arena_modules.py catalog >/dev/null
```

After branch publication, inspect the exact current head. A generated-contract sync commit changes the subject and invalidates older green checks. Open or update the PR only against the latest exact head, and keep merge Human-only.
