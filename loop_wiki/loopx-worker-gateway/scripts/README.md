# Worker Gateway runner

`gateway.py` is trusted host code. It accepts one exact adapter manifest and one exact Worker request, then:

```text
validate → lease detached worktree → execute argv → capture artifacts
→ enforce timeout/cancel/output/path controls → cleanup → receipt
```

The runner uses `shell=False` and a new process group. It copies only non-secret environment names explicitly allowlisted by the request; secret-shaped names must be represented as broker references and are not resolved by this leaf.

The local gateway only attests exact worktree identity, process-group control, changed-path observation and cleanup. It does not claim physical network/filesystem isolation. Requests that require such attestations fail closed until an admitted runtime-fabric adapter is available.
