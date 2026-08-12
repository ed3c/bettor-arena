# JSON Schemas

This directory defines the accepted shapes for module manifests, composition requirements/locks and proof/release receipts.

Schema validation proves shape, not behavior. Behavioral claims still require the module public port, independent control and mutation/hollow evidence.

Rules:

- version schema identifiers;
- reject unknown fields when the schema contract requires a closed shape;
- keep interface versions separate from implementation digests;
- do not weaken a schema to make stale data pass;
- migrate old receipts explicitly instead of silently reinterpreting them.
