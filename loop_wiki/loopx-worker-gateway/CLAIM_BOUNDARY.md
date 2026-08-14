# Observation versus claim

```text
process exit 0                 observable fact
changed path list              observable fact
cleanup result                 observable fact
OBSERVED_SUCCESS               gateway classification
Gate PASS                      external verifier decision
LoopX completion               reducer transition
production readiness           Human/release decision
```

The gateway may produce only the first four rows. It cannot infer or write the final three.
