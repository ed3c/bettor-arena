# Architecture

The arena owns the host-neutral profile and compiler. Antigravity is a read-only
historical baseline plus the pinned Gemini provider implementation. Skill-bettor
owns the apply authority and generated mirror. This separation keeps browser
selectors/login state out of the semantic contract and prevents arena `run` from
cross-repo mutation.

The live carrier never executes from the sibling checkout directly. After its
HEAD, required-file digests, package lock and installed dependency versions are
verified, the runner copies those exact modules into a per-attempt execution
mirror. The registry names the `state.js` write-path exports that may be changed;
each is redirected into the run directory. The policy digest, transformed file
digests and dependency link are retained in adapter-receipt v1.1. Missing or
ambiguous exports fail before the mirror is created, and unlisted exports keep
their pinned bytes.

Primary and gap queries share one bettor-owned JSONL runner and one CDP
connection. The runner is copied into the same mirror and its digest is part of
the execution-policy identity; it calls the pinned `ui.js` provider entry and
returns one response per prompt, so invocation receipts remain distinct. This
avoids reconnecting to a Chrome debug endpoint that can stop answering HTTP
after a completed Deep Research page disconnects.

Long Gemini runs resume only at digest-bound invocation boundaries. A prior
successful primary/gap result is reusable only when the request, source,
dependency, execution-policy, prompt, and output identities still match its
immutable receipt.
Failed edges always rerun, every attempt gets a new receipt, and a run directory
fails closed after three receipts.

Hard drift (schema, digest, owner, required clause, dangling pointer) blocks on
one observation. Soft provider jitter is measured only by live canaries: three
initial runs, then against the median of the last five admitted runs; two
consecutive deviations or one >20% degradation requests revalidation.

Gemini research may only create `candidate` records. A separate operator must
read the pinned checkout, execute a real probe and, when any rebuild trigger is
true, build and measure an alternative. The enriched research result is keyed
by its own digest and enters `candidate_ready`; only a result containing at
least one `technical_equivalent` gets a fresh-zero-context judge packet.

Local receipt hashes detect accidental mutation and bind stages; they are not
cryptographic proof against an actor that can rewrite both artifact and digest.
Authority therefore comes from actor separation (researcher / fresh judge /
external Human admit) and target-side revalidation. A hostile local writer is
outside this receipt threat model and must be contained by the host sandbox.

The traversal proof and behavior control are separate programs. The proof hashes
the canonical path and runs deterministic seams; the control checks committed
HEAD in a disposable worktree, derives the complete loop inventory from Git,
ablates core inputs, and plants defects in digest, judge-authority, and committed-
source guards. Both may be green while live carrier, fresh judge, or Human admit
remain explicitly NOT_EXERCISED.
