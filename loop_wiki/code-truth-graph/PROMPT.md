# Target contract — Code Truth Graph runtime

## Task

Consume one admitted `ctg-input@1.0.0` bundle and deterministically produce a validated graph,
settlement projection, portable exports, and `ctg-route-result@1.0.0`.

## Success

- Closed packet/result schemas reject unknown and duplicate keys.
- Snapshot/profile/evidence digests and subject identity are verified before use.
- Tool execution is selected only through a pinned profile.
- STATIC/SANDBOX/PROD state, process exit, and invariant outcome remain distinct.
- Required stage failure still leaves a diagnostic route-result when the output carrier is usable.
- Good, hollow, portability, Java AST, proof and behavioral control tests pass.
- The final edge is `human_review`, never automatic invariant admission.

## Stop-loss

After three materially different failures, record the attempts in `PLAN.md`, question the abstraction,
and choose a smaller route or surface the blocker.
