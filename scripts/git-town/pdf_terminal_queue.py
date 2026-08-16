#!/usr/bin/env python3
"""Fail-closed controller for advancing the ordered PDF terminal queue.

The controller is intentionally offline. It consumes a committed admission
receipt plus repository bytes, validates one immediate predecessor/successor
transition, and can render/apply the queue/document projection. It never calls
GitHub, a provider, Git Town, a model, or a network service.

Exit codes: 0 PASS, 2 deterministic refusal, 64 invocation/input error.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

OK = 0
REFUSED = 2
FATAL = 64
QUEUE = Path("docs/git/pdf-terminal-sequence.json")
DOC = Path("docs/git/PDF_TERMINAL_SEQUENCE.md")
README = Path("README.md")


class QueueError(ValueError):
    pass


def require(value: bool, message: str) -> None:
    if not value:
        raise QueueError(message)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise QueueError(f"ABSENT: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise QueueError(f"UNREADABLE_JSON: {path}: {exc}") from exc


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def queue_blob(path: Path = QUEUE) -> str:
    try:
        return git_blob_sha(path.read_bytes())
    except OSError as exc:
        raise QueueError(f"UNREADABLE_QUEUE: {exc}") from exc


def validate_activation(root: Path, receipt: dict[str, Any]) -> None:
    activation = receipt.get("activation_receipt")
    require(isinstance(activation, dict), "activation_receipt missing")
    rel = activation.get("path")
    require(isinstance(rel, str) and rel, "activation_receipt.path missing")
    path = root / rel
    data = path.read_bytes()
    expected_blob = activation.get("git_blob_sha")
    require(git_blob_sha(data) == expected_blob, "activation receipt blob drift")
    value = json.loads(data)
    require(value.get("schema") == "bettor-arena/provider-activation-receipt/v1", "activation schema drift")
    require(value.get("outcome") == "ADMITTED", "provider activation is not ADMITTED")
    authority = value.get("authority", {})
    require(authority.get("activated_provider") is True, "provider activation authority absent")
    require(value.get("cleanup", {}).get("status") == "PASS", "activation cleanup not PASS")
    policy = value.get("policy", {})
    for key in ("exact_subject", "source_readback", "cleanup"):
        require(policy.get(key) == "PASS", f"activation policy {key} not PASS")
    providers = value.get("providers")
    require(isinstance(providers, list) and {p.get("provider_id") for p in providers} == {"serena", "grepai"}, "activation provider set drift")
    for provider in providers:
        require(provider.get("state_after") == "ADMITTED", f"{provider.get('provider_id')}: not ADMITTED")
        canary_path = provider.get("canary_receipt_path")
        require(isinstance(canary_path, str) and canary_path, "canary receipt path missing")
        canary = load_json(root / canary_path)
        require(canary.get("status") == "PASS", f"{provider.get('provider_id')}: canary not PASS")
        require(canary.get("execution", {}).get("executed") is True, f"{provider.get('provider_id')}: canary not executed")
        require(canary.get("execution", {}).get("state") == "PASS", f"{provider.get('provider_id')}: execution not PASS")
        require(canary.get("cleanup", {}).get("status") == "PASS", f"{provider.get('provider_id')}: cleanup not PASS")
        require(canary.get("manifest", {}).get("identity_match") is True, f"{provider.get('provider_id')}: manifest identity mismatch")
        require(canary.get("manifest", {}).get("identity_state") == "PINNED", f"{provider.get('provider_id')}: manifest not PINNED")
        require(canary.get("source_readback", {}).get("token_observed") is True, f"{provider.get('provider_id')}: source readback absent")


def validate_transition(queue: dict[str, Any], receipt: dict[str, Any], *, check_blob: bool = True, root: Path = Path(".")) -> dict[str, Any]:
    require(receipt.get("schema") == "bettor-arena/pdf-terminal-advancement/v1", "advancement receipt schema drift")
    require(receipt.get("outcome") == "ADMITTED", "advancement receipt is not ADMITTED")
    require(receipt.get("repository") == "ed3c/bettor-arena", "repository drift")
    if check_blob:
        require(queue_blob(root / QUEUE) == receipt.get("queue_blob_before_git_sha"), "stale queue subject")
    items = queue.get("items")
    require(isinstance(items, list) and len(items) == 26, "queue item set drift")
    active = [item for item in items if item.get("queue_state") == "ACTIVE"]
    require(len(active) == 1, "exactly one ACTIVE predecessor required")
    predecessor = receipt.get("predecessor")
    successor = receipt.get("successor")
    require(isinstance(predecessor, dict) and isinstance(successor, dict), "predecessor/successor missing")
    current = active[0]
    require(current.get("id") == predecessor.get("id"), "wrong active predecessor id")
    require(current.get("order") == predecessor.get("order"), "wrong active predecessor order")
    require(predecessor.get("issue") in current.get("issues", []), "wrong active predecessor issue")
    order = current["order"]
    require(order < 24, "controller cannot advance final convergence")
    require(successor.get("order") == order + 1, "successor must be immediate next order")
    next_item = items[order + 1]
    require(next_item.get("id") == successor.get("id"), "wrong successor id")
    require(successor.get("issue") in next_item.get("issues", []), "wrong successor issue")
    require(next_item.get("queue_state") == "BLOCKED_BY_PREDECESSOR", "successor is not blocked")
    require(current.get("id") in next_item.get("prerequisite_items", []), "successor does not depend on predecessor")
    for item in items[:order]:
        require(item.get("queue_state") == "COMPLETE", f"earlier stage {item.get('order')} is not COMPLETE")
    for item in items[order + 1 : 25]:
        require(item.get("queue_state") == "BLOCKED_BY_PREDECESSOR", f"later stage {item.get('order')} already advanced")
    summary = queue.get("current", {})
    require(summary.get("active_order") == order, "current.active_order drift")
    require(summary.get("active_issue") == predecessor.get("issue"), "current.active_issue drift")
    remote = receipt.get("remote_delivery")
    require(isinstance(remote, dict), "remote_delivery missing")
    require(remote.get("pull_request") == 150, "unexpected completion PR")
    require(remote.get("head_sha") == "76eca27c8a4eda7623d498d8a9bdc3365b26e901", "completion PR head drift")
    require(remote.get("merge_commit_sha") == "3357dadcde509a7e92515be52d9b301e4ff130e0", "completion merge drift")
    validate_activation(root, receipt)
    return {
        "status": "PASS",
        "predecessor": current["id"],
        "predecessor_order": order,
        "successor": next_item["id"],
        "successor_order": order + 1,
    }


def render(queue: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    validate_transition(queue, receipt)
    value = copy.deepcopy(queue)
    predecessor = receipt["predecessor"]
    successor = receipt["successor"]
    prev = value["items"][predecessor["order"]]
    nxt = value["items"][successor["order"]]
    prev["queue_state"] = "COMPLETE"
    nxt["queue_state"] = "ACTIVE"
    value["current"]["active_order"] = successor["order"]
    value["current"]["active_issue"] = successor["issue"]
    value["observed_at"] = receipt["observed_at"]
    return value


def replace_once(text: str, old: str, new: str, label: str) -> str:
    require(text.count(old) == 1, f"{label}: expected exactly one marker")
    return text.replace(old, new, 1)


def update_docs(root: Path) -> None:
    doc_path = root / DOC
    doc = doc_path.read_text(encoding="utf-8")
    doc = replace_once(
        doc,
        "| 12 | #92 | `feat/loopx-code-intelligence-canaries-v1` | live Serena/GrepAI freshness and source-readback canaries | `ACTIVE` |",
        "| 12 | #92 | `feat/loopx-code-intelligence-canaries-v1` | live Serena/GrepAI freshness and source-readback canaries | `COMPLETE` |",
        "terminal row 12",
    )
    doc = replace_once(
        doc,
        "| 13 | #140 | `feat/92-context-funnel-retirement` | retire Code-Graph-RAG; converge Blindspots/source/SCIP/Tree-sitter replacement route | `BLOCKED_BY_PREDECESSOR` |",
        "| 13 | #140 | `feat/92-context-funnel-retirement` | retire Code-Graph-RAG; converge Blindspots/source/SCIP/Tree-sitter replacement route | `ACTIVE` |",
        "terminal row 13",
    )
    doc_path.write_text(doc, encoding="utf-8")

    readme_path = root / README
    readme = readme_path.read_text(encoding="utf-8")
    replacements = [
        ("current active item:    #92 (order 12)", "current active item: #140 (order 13)"),
        ("ordered acceptance through order 11                      COMPLETE", "ordered acceptance through order 12                      COMPLETE"),
        ("current order 12 Serena/GrepAI live canaries             NOT_EXERCISED", "order 12 Serena/GrepAI live canaries                     ADMITTED / COMPLETE"),
        ("Code-Graph-RAG active route / order-13 #140 retirement    RETIRED / BLOCKED_BY_PREDECESSOR", "Code-Graph-RAG active route / order-13 #140 retirement    RETIRED / ACTIVE"),
        ("ordered live-acceptance queue is stopped at #92", "ordered live-acceptance queue is now active at #140"),
        ("governance `IMPLEMENTED`; active #92", "governance `IMPLEMENTED`; active #140"),
        ("PR #124 merged; live provider #92 active", "PR #124 merged; live provider #92 complete; #140 active"),
    ]
    for old, new in replacements:
        readme = replace_once(readme, old, new, f"README marker {old!r}")
    readme_path.write_text(readme, encoding="utf-8")


def apply(root: Path, receipt_path: Path) -> dict[str, Any]:
    receipt = load_json(root / receipt_path)
    queue = load_json(root / QUEUE)
    value = render(queue, receipt)
    (root / QUEUE).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_docs(root)
    return validate_transition_after(value, receipt)


def validate_transition_after(queue: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    predecessor = receipt["predecessor"]
    successor = receipt["successor"]
    prev = queue["items"][predecessor["order"]]
    nxt = queue["items"][successor["order"]]
    require(prev["queue_state"] == "COMPLETE", "predecessor not COMPLETE after apply")
    require(nxt["queue_state"] == "ACTIVE", "successor not ACTIVE after apply")
    require(queue["current"]["active_order"] == successor["order"], "active order not advanced")
    require(queue["current"]["active_issue"] == successor["issue"], "active issue not advanced")
    require(sum(1 for item in queue["items"] if item["queue_state"] == "ACTIVE") == 1, "post-apply ACTIVE cardinality drift")
    return {"status": "PASS", "active_order": successor["order"], "active_issue": successor["issue"]}


def selftest(root: Path, receipt_path: Path) -> dict[str, Any]:
    receipt = load_json(root / receipt_path)
    queue = load_json(root / QUEUE)
    validate_transition(queue, receipt, root=root)
    controls: list[str] = []

    def must_fail(name: str, q: dict[str, Any], r: dict[str, Any]) -> None:
        try:
            validate_transition(q, r, check_blob=False, root=root)
        except QueueError:
            controls.append(name)
            return
        raise QueueError(f"{name}: planted mutation passed")

    r = copy.deepcopy(receipt); r["predecessor"]["issue"] = 999999; must_fail("wrong-predecessor", copy.deepcopy(queue), r)
    r = copy.deepcopy(receipt); r["successor"]["order"] += 1; must_fail("skipped-order", copy.deepcopy(queue), r)
    r = copy.deepcopy(receipt); r["outcome"] = "REJECTED"; must_fail("unadmitted-receipt", copy.deepcopy(queue), r)
    q = copy.deepcopy(queue); q["items"][13]["queue_state"] = "ACTIVE"; must_fail("two-active-items", q, copy.deepcopy(receipt))
    q = copy.deepcopy(queue); q["items"][12]["order"] = 24; must_fail("final-advance", q, copy.deepcopy(receipt))
    require(receipt.get("queue_blob_before_git_sha") == queue_blob(root / QUEUE), "stale queue control baseline")
    controls.append("stale-queue-digest")
    return {"status": "PASS", "controls": controls}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("plan", "apply", "selftest"))
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    root = Path(".")
    receipt_path = Path(args.receipt)
    try:
        if args.command == "plan":
            out = validate_transition(load_json(QUEUE), load_json(receipt_path), root=root)
        elif args.command == "apply":
            out = apply(root, receipt_path)
        else:
            out = selftest(root, receipt_path)
    except (QueueError, OSError, json.JSONDecodeError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return REFUSED
    print(json.dumps(out, sort_keys=True))
    return OK


if __name__ == "__main__":
    raise SystemExit(main())
