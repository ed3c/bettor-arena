# AGENTS.md — technical-equivalence research small loop

Canonical purpose: turn one technical viewpoint into evidence-graded implementation
equivalents without treating names, README claims, or producer receipts as behavior.

- Fixed prompt owner: `profile/technical-equivalence.md`.
- Packet/schema owner: `schemas/` and `modules/exchange-formats.md`.
- Runtime owner: `equivalence.py`; provider UI details stay in registered adapters.
- Judgment owner: deterministic grounding → fresh-zero-context semantic judge → Human admit.
- Proof owner: `proof_workflow/prove_equivalence.sh`; independent behavior control:
  `proof_workflow/control_equivalence_entry.sh`. The control must not call itself
  through `loopctl equivalence test`.
- `run` may generate a sync bundle; it must never write the target checkout.
- Per-run evidence lives under `_runs/` and is outside canonical digests.
