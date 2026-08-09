# Routes — Code Truth Graph runtime

| node | actor | input | validator | pass | failure |
| --- | --- | --- | --- | --- | --- |
| C0 CONTRACT | mechanical | packet JSON | closed/duplicate-safe parser | C1 | exit 64 |
| C1 IDENTITY | mechanical | snapshot/profile/evidence | containment + SHA + subject match | C2 | result + exit 2 |
| C2 EXTRACT | pinned tool profile | immutable snapshot | extractor diagnostics | C3 | result + exit 2/64 |
| C3 GRAPH | mechanical | typed records | graph structural verifier | C4 | result + exit 2 |
| C4 SETTLE | mechanical | graph + typed evidence | invariant state machine | C5 | result + exit 2 |
| C5 EXPORT | mechanical | validated graph | artifact digest verifier | H1 | result + exit 2 |
| H1 REVIEW | human | route-result + domain projection | external admission | admit/reject | named return edge |

Trusted-local parity takes a separate ingress edge, `L0 MANIFEST → C2 EXTRACT`, and rejoins the same
generic graph/evidence/settlement/export mechanism. `L0` may resolve subject-owned host paths, so it is
CLI-only and its outputs remain inside the subject boundary; MCP starts only at `C0` with a bounded bundle.

`STATIC`, `SANDBOX`, and `PROD` are lanes, not progressively stronger aliases for the same observation.
Domain-specific payloads remain versioned profile/evidence artifacts outside the common envelope.
