# Target contract — Code Truth Graph runtime

## Task

Own the generic CTG mechanism behind two explicit ingress classes: portable `ctg run` consumes one
admitted `ctg-input@1.0.0` bundle; trusted-local `ctg build-local` reads a subject-owned manifest without
moving raw evidence across the subject boundary.

## Success

- Closed packet/result schemas reject unknown and duplicate keys.
- Snapshot/profile/evidence digests and subject identity are verified before use.
- Tool execution is selected only through a pinned profile.
- STATIC/SANDBOX/PROD state, process exit, and invariant outcome remain distinct.
- Required stage failure still leaves a diagnostic route-result when the output carrier is usable.
- Good, hollow, portability, Java AST, trusted-local and MCP inline carrier tests pass.
- The clean HEAD traversal proof and behavioral control receipt share one independently rebuilt proof digest;
  verifier, relocation, trusted-local and MCP carrier each catch a byte-guarded planted defect.
- Frozen legacy GraphRAG CSV is byte-equal when old and new engines read the same subject-owned corpus.
- Trusted-local host paths never become MCP tools or portable delivery artifacts.
- The final edge is `human_review`, never automatic invariant admission.
- Live PROD/device and Human-admit states remain explicit `NOT_EXERCISED` until external evidence exists.

## Stop-loss

After three materially different failures, record the attempts in `PLAN.md`, question the abstraction,
and choose a smaller route or surface the blocker.
