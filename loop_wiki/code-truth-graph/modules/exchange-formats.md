# Exchange formats

- `ctg-input@1.0.0`: semantic envelope. Delivery output path is not part of its digest.
- `ctg-subject-snapshot@1.0.0`: content-addressed file closure; no live checkout path.
- `ctg-domain-profile@1.0.0`: pinned tool profile plus domain invariant declarations.
- Typed evidence descriptors: identity and digest only; raw PROD/session content stays at the ix boundary.
- `ctg-route-result@1.0.0`: actual runner, digests, three stage states, durable artifact refs, outcome and Human edge.

All JSON parsing rejects duplicate keys. Common envelopes are closed; domain growth uses a separately versioned artifact,
not unknown fields in the common packet.
