# Architecture

The arena owns the host-neutral profile and compiler. Antigravity is a read-only
historical baseline plus the allowlisted Gemini `--dr-once` carrier. Skill-bettor
owns the apply authority and generated mirror. This separation keeps browser
selectors/login state out of the semantic contract and prevents arena `run` from
cross-repo mutation.

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
