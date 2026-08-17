# Provider activation receipts

Each JSON file is the durable output of the typed provider activation
controller for the exact candidate commit named by its filename. The receipt
binds both provider manifests, both live canaries, the rollback subject, policy
ceilings, authority limits, and cleanup result.

A receipt is not a release promotion, queue transition, gate waiver, or proof
that a provider result is source truth. Provider availability after the exact
activation subject must be re-observed rather than inferred from an older file.
