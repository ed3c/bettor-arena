#!/usr/bin/env python3
"""Validate the ordered PDF terminal Git Town completion queue.

This gate is offline. It validates repository bytes only and never calls GitHub,
Git Town, an Agent, a provider, a model, a runtime, or a network service.

Exit codes:
  0  checked sequence PASS
  2  checked invariant FAIL
 64  invalid invocation or unreadable input
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

OK = 0
CHECK_FAILED = 2
FATAL = 64

SEQUENCE = Path("docs/git/pdf-terminal-sequence.json")
SCHEMA = Path("docs/git/pdf-terminal-sequence.schema.json")
DOC = Path("docs/git/PDF_TERMINAL_SEQUENCE.md")
README = Path("README.md")
AGENTS = Path("AGENTS.md")
STACK = Path("docs/traceability/STACK_PR_INDEX.md")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
STAGE_ID = re.compile(r"^stage-([0-9]{2})-[a-z0-9-]+$")

# COMPLETE is what a stage becomes when it lands. Without it the queue could
# only say "not started" or "blocked", so advancing by one stage meant editing
# the gate's assertion rather than the data -- and a snapshot that costs a gate
# change to update is a snapshot that stops being updated.
QUEUE_STATES = {
    "COMPLETE",
    "ACTIVE",
    "BLOCKED_BY_PREDECESSOR",
    "FINAL_CONVERGENCE",
}


class SequenceError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SequenceError(message)


def read_json(root: Path, path: Path) -> Any:
    try:
        return json.loads((root / path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SequenceError(f"ABSENT: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise SequenceError(f"UNREADABLE_JSON: {path}: {exc}") from exc


def read_text(root: Path, path: Path) -> str:
    try:
        return (root / path).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SequenceError(f"ABSENT: {path}") from exc
    except OSError as exc:
        raise SequenceError(f"UNREADABLE_TEXT: {path}: {exc}") from exc


def safe_repo_path(value: Any, label: str) -> None:
    require(isinstance(value, str) and value, f"{label}: non-empty string required")
    path = Path(value)
    require(not path.is_absolute(), f"{label}: absolute path forbidden")
    require(".." not in path.parts, f"{label}: traversal forbidden")


def require_markers(text: str, label: str, markers: list[str]) -> None:
    for marker in markers:
        require(marker in text, f"{label}: missing marker: {marker}")


def validate_shape(value: Any) -> dict[str, Any]:
    require(isinstance(value, dict), "sequence must be an object")
    require(
        value.get("schema") == "bettor-arena/pdf-terminal-sequence/v1",
        "sequence schema drift",
    )

    repository = value.get("repository")
    require(isinstance(repository, dict), "repository missing")
    require(
        repository.get("full_name") == "ed3c/bettor-arena", "repository identity drift"
    )
    require(repository.get("repository_id") == 1330387399, "repository id drift")
    require(repository.get("default_branch") == "main", "default branch drift")
    require(
        bool(SHA40.fullmatch(str(repository.get("base_sha", "")))),
        "repository base_sha must be a 40-character SHA",
    )

    source = value.get("source")
    require(isinstance(source, dict), "source missing")
    require(source.get("title") == "LLM 泛化：模型權重與 Harness", "source title drift")
    require(source.get("pages") == 41, "source page count drift")
    require(source.get("kind") == "ATTACHED_PDF_SOURCE_PROPOSAL", "source kind drift")
    require(
        source.get("authority") == "SOURCE_PROPOSAL_ONLY", "source authority overreach"
    )
    require(
        source.get("repository_copy") == "ABSENT", "repository PDF copy state drift"
    )

    skill = value.get("shared_skill")
    require(isinstance(skill, dict), "shared_skill missing")
    require(
        skill.get("repository") == "ed3c/skills-shared", "shared Skill repository drift"
    )
    require(
        skill.get("commit") == "c5750720d960a228a0d9419f28125c09d064e3e1",
        "shared Skill commit drift",
    )
    require(
        skill.get("blob") == "eb2d915bca3e8a3938625f7d33a10fae95a15769",
        "shared Skill blob drift",
    )
    require(
        skill.get("path") == "skills/git-town-stacked-pr-worker/SKILL.md",
        "shared Skill path drift",
    )
    require(
        skill.get("selection_state") == "NOT_SELECTED",
        "Git Town shared Skill selection overclaimed",
    )

    policy = value.get("queue_policy")
    require(isinstance(policy, dict), "queue_policy missing")
    require(
        policy.get("ordering") == "STRICT_GLOBAL_COMPLETION", "queue ordering drift"
    )
    require(policy.get("active_limit") == 1, "active_limit must remain one")
    require(
        policy.get("later_completion") == "REQUIRES_PREDECESSOR_OR_HUMAN_WAIVER",
        "later-completion policy drift",
    )
    require(
        policy.get("branch_topology") == "DEPENDENCY_DRIVEN_NOT_ONE_DEEP_CHAIN",
        "branch topology policy drift",
    )
    require(
        policy.get("future_branch_creation") == "BLOCKED_UNTIL_QUEUE_ITEM_ACTIVE",
        "future branch policy drift",
    )

    current = value.get("current")
    require(isinstance(current, dict), "current queue state missing")
    require(current.get("program_issue") == 61, "program issue drift")
    require(current.get("index_issue") == 102, "index issue drift")
    # `active_order` and `active_issue` were pinned here too, to the same literal
    # head. They are checked against the items in validate_items instead, where
    # the queue itself says which stage is active -- a summary field agreeing
    # with a constant proves nothing about the list it summarises.
    order = current.get("active_order")
    require(
        isinstance(order, int) and not isinstance(order, bool) and 0 <= order <= 25,
        "active order must be an order in this queue",
    )
    issue = current.get("active_issue")
    require(
        isinstance(issue, int) and not isinstance(issue, bool) and issue > 0,
        "active issue must be a positive issue number",
    )
    require(current.get("convergence_issue") == 68, "convergence issue drift")
    return value


def validate_foundation(value: dict[str, Any]) -> None:
    subjects = value.get("foundation_subjects")
    require(
        isinstance(subjects, list) and len(subjects) == 5,
        "foundation_subjects must contain five current-main mechanisms",
    )
    expected = {
        (62, 74, "loopx-kernel"),
        (63, 75, "loopx-ledger"),
        (64, 76, "loopx-worker-gateway"),
        (42, 78, "loopx-decision-memory"),
        (69, 79, "code-truth-graph-v2"),
    }
    observed: set[tuple[int, int, str]] = set()
    for index, subject in enumerate(subjects):
        require(isinstance(subject, dict), f"foundation[{index}] must be object")
        key = (subject.get("issue"), subject.get("pr"), subject.get("module"))
        require(key not in observed, f"duplicate foundation subject: {key}")
        observed.add(key)  # type: ignore[arg-type]
        require(
            subject.get("state") == "MERGED_TO_MAIN", f"foundation {key}: state drift"
        )
        require(
            subject.get("validation_item") == "stage-01-main-validation",
            f"foundation {key}: validation owner drift",
        )
    require(observed == expected, f"foundation subjects drift: {sorted(observed)}")


def validate_items(value: dict[str, Any]) -> list[dict[str, Any]]:
    items = value.get("items")
    require(
        isinstance(items, list) and len(items) == 26,
        "items must contain orders 0 through 25",
    )
    orders = [item.get("order") for item in items if isinstance(item, dict)]
    require(
        orders == list(range(26)), f"orders must be contiguous and sorted: {orders}"
    )

    ids: set[str] = set()
    issues: set[int] = set()
    by_id: dict[str, dict[str, Any]] = {}
    active: list[dict[str, Any]] = []

    for index, item in enumerate(items):
        require(isinstance(item, dict), f"items[{index}] must be object")
        order = item.get("order")
        item_id = item.get("id")
        require(isinstance(item_id, str), f"items[{index}].id missing")
        match = STAGE_ID.fullmatch(item_id)
        require(bool(match), f"items[{index}].id invalid: {item_id!r}")
        require(int(match.group(1)) == order, f"{item_id}: stage prefix/order mismatch")
        require(item_id not in ids, f"duplicate item id: {item_id}")
        ids.add(item_id)
        by_id[item_id] = item

        issue_list = item.get("issues")
        require(
            isinstance(issue_list, list) and issue_list, f"{item_id}: issues missing"
        )
        for issue in issue_list:
            require(isinstance(issue, int) and issue > 0, f"{item_id}: invalid issue")
            require(
                issue not in issues,
                f"issue appears in more than one queue item: {issue}",
            )
            issues.add(issue)

        prs = item.get("prs")
        require(isinstance(prs, list), f"{item_id}: prs must be list")
        require(len(prs) == len(set(prs)), f"{item_id}: duplicate PR")

        safe_repo_path(item.get("expected_branch"), f"{item_id}.expected_branch")
        relation = item.get("stack_relation")
        require(
            relation in {"ROOT", "TRUE_CHILD", "ROOT_AFTER_PREDECESSOR", "CONVERGENCE"},
            f"{item_id}: invalid relation",
        )

        prerequisites = item.get("prerequisite_items")
        require(
            isinstance(prerequisites, list), f"{item_id}: prerequisites must be list"
        )
        require(
            len(prerequisites) == len(set(prerequisites)),
            f"{item_id}: duplicate prerequisite",
        )

        owner_paths = item.get("owner_paths")
        require(
            isinstance(owner_paths, list) and owner_paths,
            f"{item_id}: owner_paths missing",
        )
        for path_index, path in enumerate(owner_paths):
            safe_repo_path(path, f"{item_id}.owner_paths[{path_index}]")

        acceptance = item.get("acceptance")
        require(
            isinstance(acceptance, list) and len(acceptance) >= 2,
            f"{item_id}: acceptance missing",
        )
        require(
            isinstance(item.get("evidence_boundary"), str)
            and item["evidence_boundary"],
            f"{item_id}: evidence boundary missing",
        )
        require(
            isinstance(item.get("human_boundary"), str) and item["human_boundary"],
            f"{item_id}: Human boundary missing",
        )

        state = item.get("queue_state")
        require(
            state in QUEUE_STATES,
            f"{item_id}: invalid queue state",
        )
        if state == "ACTIVE":
            active.append(item)

    require(len(active) == 1, f"exactly one ACTIVE item required, found {len(active)}")

    # The head is derived, not pinned. Naming the ACTIVE item by order and issue
    # made finishing a stage a gate edit, and a rule that has to be rewritten
    # every time the thing it describes changes is a rule that will eventually
    # be left alone while the data goes stale instead.
    completed = [item for item in items[:-1] if item["queue_state"] == "COMPLETE"]
    first_open = next(
        (item for item in items if item["queue_state"] != "COMPLETE"), None
    )
    require(first_open is not None, "every item is COMPLETE but nothing converged")
    require(
        active[0]["order"] == first_open["order"],
        f"ACTIVE is order {active[0]['order']} but the lowest item that is not "
        f"COMPLETE is order {first_open['order']}; the queue is either working out "
        "of order or has stopped recording what finished",
    )

    # COMPLETE forms a prefix. Without this, a stage finished ahead of its
    # predecessor leaves a hole, and the hole is invisible: every individual
    # item still reads correctly and only the sequence is wrong.
    completed_orders = sorted(item["order"] for item in completed)
    if completed_orders and completed_orders != list(range(len(completed_orders))):
        missing = sorted(set(range(max(completed_orders) + 1)) - set(completed_orders))
        require(
            False,
            f"COMPLETE items are not a prefix; orders {missing} are unfinished but "
            f"later orders are COMPLETE. STRICT_GLOBAL_COMPLETION means a stage "
            "finished ahead of its predecessor needs the Human waiver the policy "
            "names, recorded as such rather than left as a gap",
        )

    # The summary agrees with the list it summarises. Checking `current` against
    # a constant, as this gate did, cannot catch the case the whole issue was
    # about: the items advancing while the summary stays where it was.
    current = value.get("current", {})
    require(
        current.get("active_order") == active[0]["order"],
        f"current.active_order is {current.get('active_order')} but the ACTIVE item "
        f"is order {active[0]['order']}; the summary and the queue disagree",
    )
    require(
        current.get("active_issue") in active[0]["issues"],
        f"current.active_issue is {current.get('active_issue')} but the ACTIVE item "
        f"carries issues {active[0]['issues']}",
    )

    for item in items:
        order = item["order"]
        item_id = item["id"]
        prerequisites = item["prerequisite_items"]
        if item["stack_relation"] == "TRUE_CHILD":
            require(prerequisites, f"{item_id}: TRUE_CHILD requires a predecessor")
        for prerequisite in prerequisites:
            require(
                prerequisite in by_id, f"{item_id}: unknown prerequisite {prerequisite}"
            )
            require(
                by_id[prerequisite]["order"] < order,
                f"{item_id}: prerequisite is not earlier: {prerequisite}",
            )
        if 0 < order < 25 and order > active[0]["order"]:
            require(
                item["queue_state"] == "BLOCKED_BY_PREDECESSOR",
                f"{item_id}: item after the ACTIVE head is {item['queue_state']}, "
                "not BLOCKED_BY_PREDECESSOR; work started or finished past the head "
                "without the queue advancing to it",
            )

    final = items[-1]
    require(final["id"] == "stage-25-final-convergence", "final item id drift")
    require(final["issues"] == [68], "final convergence must be issue 68")
    require(
        final["stack_relation"] == "CONVERGENCE", "final relation must be CONVERGENCE"
    )
    require(final["queue_state"] == "FINAL_CONVERGENCE", "final queue state drift")
    require(
        set(final["prerequisite_items"]) == {item["id"] for item in items[:-1]},
        "final convergence must depend on every prior item",
    )

    return items


def validate_convergence(value: dict[str, Any]) -> None:
    convergence = value.get("convergence")
    require(isinstance(convergence, dict), "convergence missing")
    require(convergence.get("issue") == 68, "convergence issue drift")
    require(convergence.get("order") == 25, "convergence order drift")
    require(
        convergence.get("branch") == "integration/loopx-harness-convergence-v1",
        "convergence branch drift",
    )
    paths = convergence.get("shared_artifacts")
    require(isinstance(paths, list) and paths, "convergence shared_artifacts missing")
    for index, path in enumerate(paths):
        safe_repo_path(path, f"convergence.shared_artifacts[{index}]")
    required = {
        ".arena/compositions/bettor-arena.requirements.json",
        ".arena/locks/bettor-arena.lock.json",
        ".arena/contexts.lock.json",
        "data/module-proof/release-receipt.json",
        "README.md",
        "AGENTS.md",
    }
    require(
        required <= set(paths),
        f"convergence shared artifacts missing: {sorted(required - set(paths))}",
    )


def validate_human_boundary(value: dict[str, Any]) -> None:
    operations = value.get("human_owned_operations")
    require(
        isinstance(operations, list) and len(operations) >= 6,
        "human_owned_operations missing",
    )
    joined = "\n".join(str(item).lower() for item in operations)
    for marker in (
        "semantic conflict",
        "publication",
        "merge",
        "promotion",
        "rollback",
    ):
        require(marker in joined, f"Human-owned operation missing: {marker}")


def validate_docs(root: Path, items: list[dict[str, Any]]) -> None:
    doc = read_text(root, DOC)
    readme = read_text(root, README)
    agents = read_text(root, AGENTS)
    stack = read_text(root, STACK)

    require_markers(
        doc,
        str(DOC),
        [
            "Ordered PDF terminal Git Town Stack",
            "Only one queue item may be `ACTIVE`",
            "## Ordered terminal queue",
            "## Directory → State Machine responsibility",
            "## End-to-end ordered data flow",
            "#82",
            "#68",
        ],
    )
    for item in items:
        for issue in item["issues"]:
            require(f"#{issue}" in doc, f"{DOC}: missing issue #{issue}")

    require_markers(
        readme,
        "README.md",
        [
            "Ordered PDF terminal Stack",
            str(DOC),
            str(SEQUENCE),
            "current active item: #82",
            "final convergence: #68",
        ],
    )
    require_markers(
        agents,
        "AGENTS.md",
        [
            "Ordered PDF terminal Stack protocol",
            str(DOC),
            str(SEQUENCE),
            "Only one queue item may be ACTIVE",
            "Do not create a future terminal branch",
        ],
    )
    require_markers(
        stack,
        str(STACK),
        [
            "Ordered PDF terminal completion queue",
            str(DOC),
            "#82",
            "#102",
            "#68",
        ],
    )


def validate_repository(root: Path) -> dict[str, Any]:
    sequence = validate_shape(read_json(root, SEQUENCE))
    schema = read_json(root, SCHEMA)
    require(isinstance(schema, dict), "sequence schema must be object")
    require(
        schema.get("$id")
        == "https://github.com/ed3c/bettor-arena/docs/git/pdf-terminal-sequence.schema.json",
        "sequence schema $id drift",
    )
    validate_foundation(sequence)
    items = validate_items(sequence)
    validate_convergence(sequence)
    validate_human_boundary(sequence)
    validate_docs(root, items)
    return {
        "status": "PASS",
        "items": len(items),
        "active_order": sequence["current"]["active_order"],
        "active_issue": sequence["current"]["active_issue"],
        "convergence_issue": sequence["current"]["convergence_issue"],
    }


def expect_failure(name: str, action: Callable[[], None], expected: str) -> str:
    try:
        action()
    except SequenceError as exc:
        require(expected in str(exc), f"{name}: wrong failure: {exc}")
        return name
    raise SequenceError(f"{name}: mutation unexpectedly passed")


def run_selftest(root: Path) -> dict[str, Any]:
    original = validate_shape(read_json(root, SEQUENCE))
    outcomes: list[str] = []

    def mutate_items(
        name: str, mutator: Callable[[dict[str, Any]], None], expected: str
    ) -> None:
        candidate = copy.deepcopy(original)
        mutator(candidate)
        outcomes.append(
            expect_failure(name, lambda: validate_items(candidate), expected)
        )

    mutate_items(
        "missing-item", lambda value: value["items"].pop(), "orders 0 through 25"
    )
    mutate_items(
        "duplicate-order",
        lambda value: value["items"][1].update(order=0),
        "contiguous and sorted",
    )

    # These mutations locate their targets by queue state rather than by index.
    # An earlier version used literal positions, and the first time the queue
    # advanced, `items[6]` was already the ACTIVE item -- so the two-active
    # mutation changed nothing and the control passed while testing nothing.
    # That is the same position-pinning the derived-head rule replaced, left in
    # the controls for the rule, which is exactly where it is hardest to notice.
    def head(value: dict[str, Any]) -> dict[str, Any]:
        return next(i for i in value["items"] if i["queue_state"] == "ACTIVE")

    def blocked(value: dict[str, Any], offset: int = 0) -> dict[str, Any]:
        return [
            i for i in value["items"] if i["queue_state"] == "BLOCKED_BY_PREDECESSOR"
        ][offset]

    def completed(value: dict[str, Any], offset: int = -1) -> dict[str, Any]:
        return [i for i in value["items"] if i["queue_state"] == "COMPLETE"][offset]

    def point_current_at(value: dict[str, Any], item: dict[str, Any]) -> None:
        value["current"].update(
            active_order=item["order"], active_issue=item["issues"][0]
        )

    mutate_items(
        "two-active",
        lambda value: blocked(value).update(queue_state="ACTIVE"),
        "exactly one ACTIVE",
    )
    mutate_items(
        "work-started-past-the-head",
        lambda value: blocked(value, 1).update(queue_state="FINAL_CONVERGENCE"),
        "not BLOCKED_BY_PREDECESSOR",
    )
    mutate_items(
        "head-skipped-an-unfinished-stage",
        # ACTIVE moves one past the head while the head itself stays unfinished.
        # `current` moves with it, so the summary agrees and only the derived
        # head rule can catch this -- which is the rule under test.
        # offset 1 because the first statement just made the old head the
        # lowest BLOCKED item; offset 0 would set it straight back to ACTIVE
        # and the mutation would cancel itself out.
        lambda value: (
            head(value).update(queue_state="BLOCKED_BY_PREDECESSOR"),
            blocked(value, 1).update(queue_state="ACTIVE"),
            point_current_at(value, head(value)),
        ),
        "lowest item that is not COMPLETE",
    )
    mutate_items(
        "summary-left-behind-when-the-queue-advanced",
        # The exact failure #111 reported: items move, `current` does not.
        lambda value: value["current"].update(active_order=0, active_issue=82),
        "the summary and the queue disagree",
    )
    mutate_items(
        "completed-stage-left-unmarked",
        # A landed stage nobody marked. The head then sits past it, which is the
        # right diagnosis: the queue has stopped recording what finished.
        lambda value: completed(value).update(queue_state="BLOCKED_BY_PREDECESSOR"),
        "lowest item that is not COMPLETE",
    )
    mutate_items(
        "hole-in-the-completed-prefix",
        # Shaped to pass the derived-head rule so the prefix rule is the only
        # thing that can catch it: ACTIVE moves back into the hole, so the head
        # is correct and only the sequence is wrong.
        lambda value: (
            head(value).update(queue_state="BLOCKED_BY_PREDECESSOR"),
            completed(value, 0).update(queue_state="ACTIVE"),
            point_current_at(value, head(value)),
        ),
        "COMPLETE items are not a prefix",
    )
    mutate_items(
        "unknown-prerequisite",
        lambda value: value["items"][2]["prerequisite_items"].append(
            "stage-99-missing"
        ),
        "unknown prerequisite",
    )
    mutate_items(
        "future-prerequisite",
        lambda value: value["items"][2]["prerequisite_items"].append(
            "stage-03-observability"
        ),
        "not earlier",
    )
    mutate_items(
        "true-child-without-parent",
        lambda value: value["items"][1].update(prerequisite_items=[]),
        "TRUE_CHILD requires",
    )
    mutate_items(
        "duplicate-issue",
        lambda value: value["items"][1].update(issues=[82]),
        "more than one queue item",
    )
    mutate_items(
        "path-traversal",
        lambda value: value["items"][0]["owner_paths"].append("../escape"),
        "traversal forbidden",
    )
    mutate_items(
        "wrong-final-issue",
        lambda value: value["items"][-1].update(issues=[999]),
        "issue 68",
    )
    mutate_items(
        "final-missing-prerequisite",
        lambda value: value["items"][-1]["prerequisite_items"].pop(),
        "depend on every prior item",
    )

    bad_skill = copy.deepcopy(original)
    bad_skill["shared_skill"]["commit"] = "0" * 40
    outcomes.append(
        expect_failure(
            "shared-skill-drift",
            lambda: validate_shape(bad_skill),
            "shared Skill commit drift",
        )
    )

    bad_source = copy.deepcopy(original)
    bad_source["source"]["authority"] = "REPOSITORY_TRUTH"
    outcomes.append(
        expect_failure(
            "source-authority-overreach",
            lambda: validate_shape(bad_source),
            "source authority overreach",
        )
    )

    # Six entries, none of them the required markers. A shorter list would trip
    # the length check first and this control would go red for the wrong reason
    # -- which is what expect_failure is here to catch, and did.
    bad_human = copy.deepcopy(original)
    bad_human["human_owned_operations"] = [
        "inspection only",
        "reading the queue",
        "asking a question",
        "taking notes",
        "watching a run",
        "reviewing a diff",
    ]
    outcomes.append(
        expect_failure(
            "human-boundary-loss",
            lambda: validate_human_boundary(bad_human),
            "Human-owned operation missing",
        )
    )

    # The length floor needs its own control, or removing it would be invisible.
    bad_human_short = copy.deepcopy(original)
    bad_human_short["human_owned_operations"] = ["inspection only"]
    outcomes.append(
        expect_failure(
            "human-boundary-truncated",
            lambda: validate_human_boundary(bad_human_short),
            "human_owned_operations missing",
        )
    )

    return {"status": "PASS", "mutations": outcomes}


def find_root(explicit: str | None) -> Path:
    root = Path(explicit).resolve() if explicit else Path(__file__).resolve().parents[2]
    require((root / "AGENTS.md").is_file(), f"repository root not found: {root}")
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        root = find_root(args.root)
        result = run_selftest(root) if args.selftest else validate_repository(root)
    except SequenceError as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        else:
            print(f"pdf-terminal-sequence FAIL: {exc}", file=sys.stderr)
        return CHECK_FAILED
    except (OSError, RuntimeError) as exc:
        payload = {"status": "FATAL", "error": str(exc)}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        else:
            print(f"pdf-terminal-sequence FATAL: {exc}", file=sys.stderr)
        return FATAL

    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    elif args.selftest:
        print(
            f"pdf-terminal-sequence selftest PASS: {len(result['mutations'])} mutations"
        )
    else:
        print(
            "pdf-terminal-sequence PASS: "
            f"{result['items']} items, active=#{result['active_issue']} order={result['active_order']}, "
            f"convergence=#{result['convergence_issue']}"
        )
    return OK


if __name__ == "__main__":
    raise SystemExit(main())
