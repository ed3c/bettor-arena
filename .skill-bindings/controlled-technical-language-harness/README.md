# Controlled Technical Language Harness — Bettor binding

This directory owns the Bettor-specific binding for the shared
`controlled-technical-language-harness`. It does not copy the portable Skill.

## Authority and ownership

| Subject | Owner |
|---|---|
| Portable procedure, profile, evaluators, and offline A/B | Exact `ed3c/skills-shared` bundle in `binding.json` |
| Candidate, rollback, privacy policy, and fixture terminology | This directory |
| Deterministic admission verdict | `scripts/gates/check_controlled_language_binding.py` |
| Exact-head hosted execution | `.github/workflows/controlled-language-binding.yml` |
| Production TN/TV, confidential external processing, safety meaning, compliance, merge, release, rollback | Human Admit |

The source PDF is `SOURCE_PROPOSAL`. It motivates a layered pipeline, project
TN/TV injection, deterministic revalidation, and Human review. It is not an
official standard pack, approved vocabulary, certification, or runtime receipt.

## Immutable selection

```text
candidate commit       b3d47948feb6e2d44d84261354117aecfaa4f5dc
candidate tree         8b7a44fb080d290135223e372d77825589fdfe3a
candidate Skill tree   2c4582c1c0d1db27c318fbd2a1ed3957f4d2cb46
candidate evals blob   4a8f35732a283550bdce6730504f5b9974513c9e
A/B authority scorer   d742f62fb489c954636e2a41e45f2ce383774814

rollback commit        47cbb259c0157535d6f40b703b487e225a1a9de1
rollback tree          8d9a3a0b5f18eb95a3ec8e6ac74edfbe46a6f197
rollback Skill tree    95f32efc63e718cfc5b7663333cee1a35ed18b5a
rollback evals blob    c7e07c9f980f1d9b3b5ce9d42a1f01ee1d2f866f
```

The candidate contains the authority-bound A/B composition. The rollback is the
pre-composition integrated A/B bundle. The `SKILL.md` blob can remain identical
while evaluators and evidence change; rollback identity therefore binds the full
Skill tree and eval closure, not only the entrypoint.

## Directory → state-machine map

```text
.skill-bindings/controlled-technical-language-harness/
├── README.md              owner and state/data-flow map
├── binding.json           immutable selection and evidence ceilings
├── privacy-policy.json    classification → execution-lane law
└── fixtures/
    ├── termbase.json      non-production TN/TV test data
    └── cases.json         planted mutation inventory

scripts/gates/check_controlled_language_binding.py
scripts/gates/controlled_language_binding/
    SELECTED → BOUND → POLICY_CHECKED → MUTATION_SENSITIVE → CANDIDATE

tests/test_controlled_language_binding.py
    positive + mutation + exit-seam controls

.github/workflows/controlled-language-binding.yml
    PR_HEAD → EXACT_CHECKOUT → OFFLINE_GATE → HOSTED_RECEIPT

data/receipts/controlled-language/README.md
    evidence route and missing-lane declarations
```

## Data flow

```text
skills-shared immutable bundle
        │
        ▼
binding.json
        ├── exact privacy-policy digest
        ├── exact fixture-termbase digest
        └── exact control-case digest
                │
                ▼
zero-network checker
        ├── positive binding
        ├── 23 planted mutations
        ├── unit/exit controls
        └── stable 0 / 2 / 64 / 70 exits
                │
                ▼
exact-head GitHub Actions
                │
                ▼
CTL 07B resolver projection + physical Codex/Claude matrix
```

## Evidence boundary

```text
immutable consumer binding        IMPLEMENTED
privacy-routing contract          IMPLEMENTED
fixture termbase                  IMPLEMENTED
offline mutation controls         IMPLEMENTED
shared resolver projection        NOT_IMPLEMENTED
Codex projection                  NOT_IMPLEMENTED
Claude projection                 NOT_IMPLEMENTED
projection digest parity          NOT_EXERCISED
Codex physical carrier            NOT_EXERCISED
Claude physical carrier           NOT_EXERCISED
real model/manual                 NOT_EXERCISED
production termbase               ABSENT
external confidential processing NOT_EXERCISED
official compliance               NOT_CLAIMED
mem0 / CONTEXT writeback          NOT_IMPLEMENTED
```

## Commands

```bash
python3 scripts/gates/check_controlled_language_binding.py --root . --json
python3 scripts/gates/check_controlled_language_binding.py --root . --selftest --json
python3 -m unittest -v tests/test_controlled_language_binding.py
```

A green result proves only this immutable offline binding. It does not prove a
host loaded the Skill, a model preserved meaning, a confidential document was
processed lawfully, or Human admitted promotion.
