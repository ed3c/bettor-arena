# State ledger — Code Truth Graph runtime

STATUS: candidate

## Iteration trajectory

| iter | result | evidence |
| ---: | :---: | --- |
| 0 | RED | public `loopctl ctg run` was an unknown loop (exit 64) |
| 1 | GREEN | closed input/result schemas; good 0, stale 2, malformed/unsafe 64 |
| 2 | RED | legacy settlement made non-critical synthetic evidence unreachable as `DEMO_ONLY` |
| 3 | GREEN | deterministic model/settlement/GraphRAG/HTML and pinned Java AST run through the public CLI |
| 4 | RED | failed evidence produced exit 2 but no route-result |
| 5 | GREEN | failed required measurement materializes a diagnostic route-result; good/hollow verifier added |

Rows are append-only. A later correction adds a row; it does not rewrite why an earlier belief existed.

## Human gates

- Domain adapter and redaction policy admission belongs to ix.
- Legacy parity and cutover require cross-repository Human admission.
- Release/baseline admission remains blocked until the operational ledger exists.
