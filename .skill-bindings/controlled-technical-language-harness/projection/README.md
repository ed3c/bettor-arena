# Controlled-language projection — sealed disposable materializer (CTL 07B)

This directory owns the immutable projection mechanism for the shared
`controlled-technical-language-harness`. It does not commit a second copy of the
Skill, and it does not treat a machine-local symlink, a branch name, or a
package declaration as release authority.

## Authority and ownership

| Subject | Owner |
|---|---|
| Admitted consumer binding and immutable upstream selection | [`../binding.json`](../binding.json), blob `d4f4d360…` |
| Carrier layout, mode vocabulary, evidence ceiling | `contract.json` |
| Planted control inventory | `cases.json` |
| Deterministic materializer and parity verdict | `scripts/gates/check_controlled_language_projection.py` |
| Materializer internals | `scripts/gates/controlled_language_binding/projection.py` |
| Exact-head hosted execution | `../../../.github/workflows/controlled-language-binding.yml` |
| Private-upstream credentials, host trust, physical carrier runs, merge, release, rollback | Human Admit |

## Immutable selection

```text
consumer binding blob  d4f4d36095862c46b0d92057ee2e6d42dea14b2a
upstream commit        b3d47948feb6e2d44d84261354117aecfaa4f5dc
upstream tree          8b7a44fb080d290135223e372d77825589fdfe3a
upstream Skill tree    2c4582c1c0d1db27c318fbd2a1ed3957f4d2cb46
upstream SKILL.md blob 5c1932161e9d4164b013f0e2b1f7dc7830021c5d
upstream evals blob    4a8f35732a283550bdce6730504f5b9974513c9e
rollback commit        47cbb259c0157535d6f40b703b487e225a1a9de1
```

Source identity is commit plus repository tree plus Skill tree. A branch, a tag
without a digest, `main`, or `latest` is refused before any byte is copied. The
selected commit must also be the checked-out head of the source, otherwise the
clean-subtree observation would be about a different subject than the one being
projected.

## One body, two carriers

```text
<disposable target>/
├── .agents/skills/controlled-technical-language-harness/   materialized body
└── .claude/skills/controlled-technical-language-harness -> ../../.agents/skills/controlled-technical-language-harness
```

Claude never receives a second hand-maintained copy, only a repository-relative
pointer into the one Codex body. Divergence is therefore prevented by shape, not
by discipline: there is no second set of bytes that can drift. `CTL-PROJ-019`
still plants a hand-maintained copy to prove the gate refuses that shape.

## Directory → state-machine map

```text
.skill-bindings/controlled-technical-language-harness/projection/
├── README.md       owner and state/data-flow map
├── contract.json   carrier layout, selection, evidence ceiling, case seal
└── cases.json      planted control inventory (23)

scripts/gates/controlled_language_binding/projection.py
    BOUND → SOURCE_VERIFIED → TARGET_SEALED → MATERIALIZED
          → PARITY_CHECKED → REDACTED_RECEIPT
    any red edge → target purged back to the state it was found in

tests/test_controlled_language_projection.py
    positive + control + rollback + exit-seam controls
```

## Data flow

```text
admitted 07A binding blob        exact checked-out upstream source
        │                                     │
        └──────────────┬──────────────────────┘
                       ▼
              contract.json selection
                       │
                       ▼
           empty disposable target outside both checkouts
                       │
                       ▼
            one materialized body (git ls-tree parity)
                       ├── Codex carrier: the body
                       └── Claude carrier: relative pointer
                       │
                       ▼
           path-redacted receipt on stdout, no committed verdict
```

## Commands

```bash
python3 scripts/gates/check_controlled_language_projection.py --root . --json
python3 scripts/gates/check_controlled_language_projection.py --root . --selftest --json
python3 -m unittest -v tests/test_controlled_language_projection.py
```

Without `--source`/`--target` the positive lane materializes a synthetic Git
fixture inside a temporary directory and removes it again. The operator lane
`--source <upstream checkout> --target <empty disposable directory>` projects
the selected bundle and retains it; both arguments are required together.

## Evidence boundary

```text
sealed materializer mechanism     IMPLEMENTED
synthetic Git parity controls     IMPLEMENTED
rollback-safe disposable target   IMPLEMENTED
real upstream private checkout    NOT_EXERCISED
Codex cold start                  NOT_EXERCISED
Claude cold start                 NOT_EXERCISED
model or manual processing        NOT_EXERCISED
production termbase               ABSENT
official compliance               NOT_CLAIMED
merge / release / rollback        HUMAN_ADMIT_REQUIRED
```

A green materializer proves that the mechanism copies, seals, and refuses. It
does not prove that a host loaded the Skill, that the private upstream was ever
read on this machine, or that a model preserved meaning.

## Open reconciliation

[`../binding.json`](../binding.json) still records `generated_binding_state`,
`shared_requirements_update_state`, and `content_digest_parity_state` as
`NOT_IMPLEMENTED` / `NOT_EXERCISED`, and `scripts/gates/check_controlled_language_binding.py`
enforces exactly those values. Those fields describe the consumer's own
generated-binding and shared-requirements lanes, which this slice does not
implement; the disposable materializer here is a separate mechanism whose
physical carrier lanes stay `NOT_EXERCISED`. The wording of
`codex_projection_state` / `claude_projection_state` is nevertheless close
enough to this slice to be re-read by a later reviewer. Reconciling those two
documents is a later slice: it needs `binding.json`, the 07A validator, and the
07A mutation inventory to move together, and none of them are inside the CTL 07B
path allowance.
