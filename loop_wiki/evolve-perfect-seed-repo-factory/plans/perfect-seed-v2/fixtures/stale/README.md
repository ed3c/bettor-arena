# Stale fixture contract

Start from passing candidate/profile attestations, then change HEAD/tree,
profile, oracle set, prompt hash, or Forgejo readback target.

Expected result: old attestations contribute no current pass; projection is
pending or `repair_required`, and promotion is false.
