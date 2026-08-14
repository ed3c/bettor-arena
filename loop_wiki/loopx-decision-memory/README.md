# LoopX Decision Memory Admission v1

This terminal leaf converts observable execution evidence into bounded memory proposals and Human-authorized candidate capsules. It never stores private chain-of-thought, never lets Mem0 or another retrieval provider become canonical truth, and never writes LoopX state directly.

## State Machine

```text
OBSERVATION / DEAD END / DECISION
→ PROPOSAL_VALIDATED
→ EVIDENCE_AND_SUBJECT_BOUND
→ PRIVACY / RETENTION / CONFLICT_CHECKED
→ HUMAN_ADMIT | REJECT | DEFER | CONFLICT
→ CANDIDATE_CAPSULE
→ future LoopX memory-ledger event
→ optional rebuildable provider projection
→ EXPIRE | SUPERSEDE | DELETE
```

## Authority law

```text
Worker may propose memory
Repository source/tests/ADR/receipts remain higher authority
Validator checks evidence, scope, privacy, retention and conflicts
Human admits or rejects
LoopX reducer persists a later memory event
Mem0/vector/graph stores are rebuildable projections only
```

## Public control port

```sh
python3 loop_wiki/loopx-decision-memory/scripts/memory.py check
python3 loop_wiki/loopx-decision-memory/scripts/memory.py selftest
python3 loop_wiki/loopx-decision-memory/scripts/memory.py compile \
  --proposal proposal.json \
  --decision human-decision.json \
  --output candidate-capsule.json
```

`compile` emits a candidate capsule. It does not append a durable event, write Mem0, mutate repository docs, mark a task complete, merge, promote or Human Admit.

## Allowed memory kinds

- verified dead end;
- codebase quirk;
- bounded hypothesis with a falsifier and expiry;
- decision with evidence and rejected alternatives represented externally;
- incident pointer;
- project preference.

## Forbidden content

- private chain-of-thought, Thought Stream or hidden reasoning;
- raw credentials, cookies, private keys or signed-in page bodies;
- model prose used as its own evidence;
- memory that overrides newer source, tests, ADR or runtime receipts;
- universal/high-confidence hypothesis without independent evidence;
- indefinite retention without a reviewed policy;
- direct provider write, Gate verdict, LoopX transition or Human authority.

## Evidence boundary

The contracts and fixture compiler can be `IMPLEMENTED`. Durable memory-ledger persistence, live Mem0 projection, conflict reconciliation against a current product repository, deletion residue proof and production retention remain `NOT_EXERCISED` until exact receipts exist.
