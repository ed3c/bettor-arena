# lifecycle-hardening

This module records the production lifecycle hardening requirements for
`autoresearch-composer`.

## Hard Requirements

- Stateful workflow: match / route / generate / validate / recover are separate nodes.
- Conditional edges are explicit and named.
- Missing information is surfaced as `INCOMPLETE`, not guessed.
- Missing Domain terms are tracked as `known`, `candidate`, or `unknown`.
- Candidate/unknown terms require judge-loop or human admission before promotion.
- 10-20 behavior cases are mandatory.
- A/B ablation is a hard gate before lifecycle promotion.
- Golden Dataset evals are mandatory for route, native-yield, compressed-context recovery, and local-first eval/guardrail/trace behavior.
- LLM-as-a-Judge is local deterministic heuristic by default; cloud/API execution is implemented only as an explicit opt-in and remains disabled by default.
- pytest markers `evals`, `llm_judge`, and `trace` are required so CI/CD can run local gates without secrets.
- Local-first trace sampling must validate state nodes, route, verdict, sample reason, and disabled cloud state.

## Production Evidence Owner

The production proof is owned by:

- `repo/agent-skills-repo/skills/autoresearch_composer/`
- `repo/agent-skills-repo/scripts/check_autoresearch_lifecycle.py`
- `repo/agent-skills-repo/scripts/eval_autoresearch_composer.py`
- `repo/agent-skills-repo/scripts/sample_autoresearch_traces.py`
- `repo/agent-skills-repo/data/autoresearch_golden/pr_golden_set.json`
- `repo/agent-skills-repo/data/autoresearch_traces/local_trace_samples.jsonl`
- `repo/agent-skills-repo/scripts/ablation_engine.py`
- `repo/agent-skills-repo/scripts/git_gate.py`
