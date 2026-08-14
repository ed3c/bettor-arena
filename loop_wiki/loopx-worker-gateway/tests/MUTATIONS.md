# Planted controls

The executable selftest must reject or turn red for:

1. adapter manifest digest drift;
2. absolute working directory;
3. write-allowlist traversal;
4. secret-shaped environment name;
5. Worker-supplied Gate verdict;
6. adapter/host identity mismatch;
7. required network attestation unavailable;
8. LIVE request against a non-admitted adapter;
9. gray-box internal-event overclaim;
10. write outside the allowlist;
11. output-budget overflow;
12. timeout;
13. cancellation;
14. false observed success;
15. receipt replay against another task subject;
16. duplicate event sequence;
17. private-reasoning persistence.

A fixture PASS proves only these gateway controls. It does not establish any real host's installation, authentication, health, capability, parity, or production readiness.
