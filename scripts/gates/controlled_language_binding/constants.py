from __future__ import annotations

import re
from pathlib import Path

BASE = Path(".skill-bindings/controlled-technical-language-harness")
FILES = {
    "binding": BASE / "binding.json",
    "privacy": BASE / "privacy-policy.json",
    "termbase": BASE / "fixtures/termbase.json",
    "cases": BASE / "fixtures/cases.json",
}

CANDIDATE = {
    "authority_composition": {
        "reference_blob": "d3939b692f0393f8347b56f33ac3521e1968027e",
        "scorer_blob": "d742f62fb489c954636e2a41e45f2ce383774814",
        "selftest_blob": "448ad77ff6d6e6c401517b94ca8cb9cbc6304321",
        "state": "VERIFIED_OFFLINE_MECHANISM_ONLY",
    },
    "commit": "b3d47948feb6e2d44d84261354117aecfaa4f5dc",
    "entrypoint": "skills/controlled-technical-language-harness/SKILL.md",
    "entrypoint_blob": "5c1932161e9d4164b013f0e2b1f7dc7830021c5d",
    "evals_blob": "4a8f35732a283550bdce6730504f5b9974513c9e",
    "repository_state": "MERGED",
    "skill_path": "skills/controlled-technical-language-harness",
    "skill_tree": "2c4582c1c0d1db27c318fbd2a1ed3957f4d2cb46",
    "tree": "8b7a44fb080d290135223e372d77825589fdfe3a",
}

ROLLBACK = {
    "authority_composition": {
        "reference_blob": None,
        "scorer_blob": None,
        "selftest_blob": None,
        "state": "ABSENT",
    },
    "commit": "47cbb259c0157535d6f40b703b487e225a1a9de1",
    "entrypoint": "skills/controlled-technical-language-harness/SKILL.md",
    "entrypoint_blob": "5c1932161e9d4164b013f0e2b1f7dc7830021c5d",
    "evals_blob": "c7e07c9f980f1d9b3b5ce9d42a1f01ee1d2f866f",
    "repository_state": "MERGED",
    "skill_path": "skills/controlled-technical-language-harness",
    "skill_tree": "95f32efc63e718cfc5b7663333cee1a35ed18b5a",
    "tree": "8d9a3a0b5f18eb95a3ec8e6ac74edfbe46a6f197",
}

SOURCE_PROPOSAL = {
    "artifact_digest": (
        "sha256:d919a887f9bc8acda76ad6350276059e4c4f71a739f048a47626c686d7175578"
    ),
    "authority": "NON_NORMATIVE",
    "classification": "SOURCE_PROPOSAL",
    "drive_file_id": "1vqFNBQmCwh9xgziZxlO0oYk6fZQg9rQ_",
    "file_name": "STE100 檢查與改寫 LLM 應用.pdf",
}

PROFILE = {
    "approved_vocabulary_state": "ABSENT",
    "compliance_claim_policy": "HUMAN_ADMIT_REQUIRED",
    "edition": "0.1-proposal-derived",
    "fixture_termbase_state": "FIXTURE_ONLY",
    "official_compliance_claim": "FORBIDDEN",
    "official_standard_pack_reference": None,
    "official_standard_pack_state": "ABSENT",
    "pack_blob": "a3cc85d63c6ebec867bd27f01ba7d94deb399644",
    "pack_id": "ste-proposal-derived",
    "production_termbase_state": "ABSENT",
    "ruleset_digest": (
        "sha256:69aecdf43eacd3b4429d63d4ebff42e4cf3be445313717b3ab98bbe964cba0ef"
    ),
    "technical_name_human_admit": True,
    "technical_verb_human_admit": True,
}

EVIDENCE_STATES = [
    "PASS",
    "FAIL",
    "ABSENT",
    "NOT_IMPLEMENTED",
    "NOT_EXERCISED",
    "SKIPPED_BY_POLICY",
]

HUMAN_OWNED = [
    "PRODUCTION_TERM_ADMISSION",
    "CONFIDENTIAL_EXTERNAL_PROCESSING",
    "SAFETY_SEMANTIC_ACCEPTANCE",
    "OFFICIAL_COMPLIANCE_REPRESENTATION",
    "HOST_TRUST",
    "RESOLVER_PROMOTION",
    "MERGE",
    "RELEASE",
    "ROLLBACK",
]

FORBIDDEN_REASONING_KEYS = {
    "chain_of_thought",
    "hidden_reasoning",
    "private_reasoning",
    "reasoning_trace",
    "scratchpad",
}
SECRET_PATTERN = re.compile(
    r"(gh[pousr]_[A-Za-z0-9]{12,}|sk-[A-Za-z0-9_-]{12,}|"
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)"
)
MACHINE_PATH_PATTERN = re.compile(r"(?:^|[\s'\"])(?:/Users/|/home/|[A-Za-z]:[\\/])")
