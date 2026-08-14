# Verification contract

Run from the repository root:

```sh
sh loop_wiki/loopx-worker-gateway/tests/run-all.sh
python3 scripts/arena_modules.py catalog >/dev/null
```

Success means only:

- four protocol Schemas are structurally present;
- exactly six static host adapters obey the authority and visibility ceilings;
- the fixture gateway binds an exact Git commit/tree, uses typed argv and `shell=False`, records process/filesystem artifacts, enforces bounded controls and verifies cleanup;
- planted controls turn red.

It does not mean:

- any real host binary is installed, authenticated or healthy;
- any host's model or Harness is superior;
- hidden calls were observed;
- physical network/filesystem isolation exists;
- Gate PASS, LoopX completion, Human Admit, merge or release promotion occurred.
