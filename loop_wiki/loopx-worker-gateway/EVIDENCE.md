# Evidence levels

```text
CONTRACT_ONLY  static schema/adapter bytes validate
FIXTURE_ONLY   synthetic Worker run proves gateway controls
LOCAL_OFFLINE  real host binary executes without network/credentials
LIVE           exact host/provider/session subject produces a redacted receipt
```

Only the first two levels are intended for this terminal leaf. `LOCAL_OFFLINE` and `LIVE` are later canary work and cannot be inferred from static manifests, source visibility or fixture results.
