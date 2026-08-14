#!/usr/bin/env python3
"""Positive properties plus one planted control per named failure in #96.

Every run starts a real subprocess, because three of the controls are about what
a server *process* does -- crash, hang, answer for the wrong tree -- and none of
them can be demonstrated by a function that returns a dict.
"""

from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from lsp_common import ContractError
from lsp_fallback import CEILING, validate_fallback_admission
from lsp_pool import compatible, evict, select
from lsp_pipeline import run_query
from lsp_query import to_code_truth_graph

NAMES = (
    "server",
    "server-multi-root",
    "workspaces",
    "slots",
    "limits",
    "request",
    "fallback-admission",
)


def load_inputs(root: Path) -> dict[str, Any]:
    good = root / "tests/fixtures/good"
    return {
        name: json.loads((good / f"{name}.json").read_text(encoding="utf-8"))
        for name in NAMES
    }


def server_argv(module_root: Path) -> list[str]:
    return [sys.executable, str(module_root / "tests/fake_server.py")]


def build_workspace_tree(root: Path) -> Path:
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "src/app.py").write_text("x = 1\n# TODO: finish\n", encoding="utf-8")
    (root / "src/clean.py").write_text("y = 2\n", encoding="utf-8")
    (root / "src/broken.py").write_text("def f(\n", encoding="utf-8")
    return root


def run_selftest(module_root: Path) -> tuple[int, int]:
    base = load_inputs(module_root)
    argv = server_argv(module_root)
    positives = 0
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="loopx-lsp-selftest-") as tmp:
        root = build_workspace_tree(Path(tmp) / "alpha")
        request, slots, limits = base["request"], base["slots"], base["limits"]

        # --- positives ------------------------------------------------------
        normal = run_query(copy.deepcopy(request), slots, limits, argv, root)
        if normal["result"]["state"] != "FINDINGS" or not normal["result"]["findings"]:
            raise ContractError(f"a TODO was not reported: {normal['result']}")
        if normal["pool_decision"]["decision"] != "REUSE":
            raise ContractError("a compatible warm slot was not reused")
        positives += 1

        clean = copy.deepcopy(request)
        clean["path"] = "src/clean.py"
        clean_result = run_query(clean, slots, limits, argv, root)["result"]
        if clean_result["state"] != "CLEAN" or clean_result["findings"]:
            raise ContractError(f"a clean file was not CLEAN: {clean_result}")
        positives += 1

        # Provenance is on every result, and names the tree that was asked about.
        provenance = normal["result"]["provenance"]
        for field in ("workspace_id", "commit", "tree", "root"):
            if provenance[field] != request["workspace"][field]:
                raise ContractError(f"provenance.{field} does not match the request")
        if provenance["index_freshness"] != "CURRENT":
            raise ContractError("a current index reported itself stale")
        positives += 1

        # The Code Truth Graph gets provenance, never bare diagnostics.
        admitted = to_code_truth_graph(normal["result"])
        if not admitted["admitted"] or "provenance" not in admitted:
            raise ContractError("the graph was handed diagnostics without provenance")
        if admitted["authority"] != "EVIDENCE_INPUT_NOT_GATE_VERDICT":
            raise ContractError("LSP output was handed over as a gate verdict")
        positives += 1

        # And a non-evidence state is not admitted at all.
        crashed = run_query(
            copy.deepcopy(request), slots, limits, argv, root, behaviour="crash"
        )
        if crashed["result"]["state"] != "SERVER_FAILED":
            raise ContractError(
                f"a crashed server produced {crashed['result']['state']}"
            )
        if to_code_truth_graph(crashed["result"])["admitted"]:
            raise ContractError(
                "a crashed server's silence was admitted to the graph; it produces an "
                "empty findings list and so does a clean file"
            )
        positives += 1

        # A hang is unavailable, not clean. Short timeout so the suite stays fast.
        hung = run_query(
            copy.deepcopy(request),
            slots,
            limits,
            argv,
            root,
            behaviour="hang",
            timeout_s=1.0,
        )
        if hung["result"]["state"] != "SERVER_FAILED":
            raise ContractError(f"a hung server produced {hung['result']['state']}")
        positives += 1

        # empty-on-fail: exits zero, indexed nothing. UNKNOWN, not CLEAN.
        empty = run_query(
            copy.deepcopy(request), slots, limits, argv, root, behaviour="empty-on-fail"
        )
        if empty["result"]["state"] != "UNKNOWN":
            raise ContractError(
                f"a server that exited zero having indexed nothing produced "
                f"{empty['result']['state']}; an unindexed file reported as clean is a "
                "file nobody opened"
            )
        positives += 1

        # Unsupported language is UNKNOWN, and the discarded findings are named.
        rust = copy.deepcopy(request)
        rust["language"] = "rust"
        rust_result = run_query(rust, slots, limits, argv, root)["result"]
        if rust_result["state"] != "UNKNOWN" or rust_result["findings"]:
            raise ContractError(f"an unsupported language produced {rust_result}")
        if "discarded" not in rust_result["reason"]:
            raise ContractError(
                "findings from a server that could not look were dropped silently; a "
                "reader cannot then tell 0 findings from findings we threw away"
            )
        positives += 1

        # The fallback answers syntax and refuses project-wide questions.
        broken = copy.deepcopy(request)
        broken["path"] = "src/broken.py"
        fallen = run_query(
            broken,
            slots,
            limits,
            argv,
            root,
            behaviour="crash",
            fallback_admission=base["fallback-admission"],
        )["result"]
        if fallen["state"] != "FINDINGS":
            raise ContractError(f"the fallback missed a syntax error: {fallen}")
        refs = copy.deepcopy(request)
        refs["kind"] = "REFERENCES"
        refs_result = run_query(
            refs,
            slots,
            limits,
            argv,
            root,
            behaviour="crash",
            fallback_admission=base["fallback-admission"],
        )["result"]
        if refs_result["state"] != "UNKNOWN" or refs_result["findings"]:
            raise ContractError(
                "a project-wide question was answered by a single-file fallback; an "
                "empty reference list reads as 'this symbol is unused'"
            )
        positives += 1

        # Determinism.
        again = run_query(copy.deepcopy(request), slots, limits, argv, root)
        if again["query_digest"] != normal["query_digest"]:
            raise ContractError("two identical queries produced different decisions")
        positives += 1

        # --- controls -------------------------------------------------------
        def expect_refusal(name: str, needle: str, call) -> None:
            try:
                call()
            except ContractError as exc:
                if needle not in str(exc):
                    failures.append(
                        f"{name} refused for the wrong reason: expected {needle!r}, "
                        f"got {exc}"
                    )
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{name} raised {type(exc).__name__}: {exc}")
            else:
                failures.append(f"{name} was accepted")

        expect_refusal(
            "result-crosses-worktree",
            "as authoritative as a correct one",
            lambda: run_query(
                copy.deepcopy(request),
                slots,
                limits,
                argv,
                root,
                behaviour="wrong-tree",
                other_workspace_id="ws-beta",
            ),
        )

        moved = copy.deepcopy(request)
        moved["workspace"]["commit"] = "9f" * 20
        decision = select(slots, moved["server"], moved["workspace"], limits)
        if decision["decision"] == "REUSE":
            failures.append(
                "a slot whose workspace commit moved was reused; the index describes "
                "bytes that are no longer there"
            )
        elif not any(
            "no longer there" in reason
            for entry in decision["reasons"]
            if isinstance(entry, dict)
            for reason in entry.get("reasons", [])
        ):
            failures.append("the stale-slot refusal did not name why the slot is stale")

        # A second workspace on a single-root server is not shareable.
        other = copy.deepcopy(request)
        other["workspace"] = base["workspaces"][1]
        reasons = compatible(slots[0], other["server"], other["workspace"])
        if not any("not multi-root" in reason for reason in reasons):
            failures.append(
                "a single-root server was offered to a second workspace; one index "
                "answering for two trees returns symbols from whichever it loaded"
            )

        # A multi-root server may share, but not across repositories.
        cross = copy.deepcopy(base["workspaces"][1])
        cross["repository"] = "ed3c/another-repo"
        multi_slot = {**slots[0], "server": base["server-multi-root"]}
        reasons = compatible(multi_slot, base["server-multi-root"], cross)
        if not any("resolves a name to whichever" in reason for reason in reasons):
            failures.append("a multi-root server was allowed to cross repositories")

        # Eviction cannot kill an active request.
        busy = [{**slots[0], "active_requests": 1}]
        expect_refusal(
            "eviction-kills-an-active-request",
            "kills a query someone is waiting on",
            lambda: evict(busy, busy[0]["slot_id"]),
        )

        # A full pool of busy slots queues rather than evicting.
        tight = {"max_slots": 1, "max_memory_mb": 512, "slot_memory_mb": 512}
        queued = select(busy, base["server-multi-root"], base["workspaces"][1], tight)
        if queued["decision"] != "QUEUE":
            failures.append(
                f"a full pool of busy slots decided {queued['decision']}; evicting "
                "turns a capacity problem into a wrong answer"
            )

        # And a full pool with an idle slot evicts deterministically.
        idle = [
            {**slots[0], "slot_id": "slot-old", "indexed_at": "2026-08-15T09:00:00Z"},
            {**slots[0], "slot_id": "slot-new", "indexed_at": "2026-08-15T09:30:00Z"},
        ]
        room = select(
            idle,
            base["server-multi-root"],
            base["workspaces"][1],
            {"max_slots": 2, "max_memory_mb": 1024, "slot_memory_mb": 512},
        )
        if room["decision"] != "EVICT_THEN_CREATE" or room["slot_id"] != "slot-old":
            failures.append(
                f"eviction chose {room.get('slot_id')}; a pool that evicts by dict "
                "order evicts differently on every run"
            )

        # A queued query is NOT_EXERCISED, never CLEAN.
        starved = run_query(
            copy.deepcopy(base["request"]) | {"workspace": base["workspaces"][1]},
            busy,
            tight,
            argv,
            root,
        )
        if starved["result"]["state"] != "NOT_EXERCISED":
            failures.append(
                f"a queued query reported {starved['result']['state']}; being queued "
                "is not the same as finding nothing"
            )

        # A fallback that runs without admission.
        expect_refusal(
            "fallback-without-admission",
            "was not admitted",
            lambda: validate_fallback_admission(
                {**base["fallback-admission"], "admitted": False}
            ),
        )
        expect_refusal(
            "fallback-admitted-without-its-ceiling",
            "admitting a shape",
            lambda: validate_fallback_admission(
                {**base["fallback-admission"], "ceiling_acknowledged": ["DIAGNOSTICS"]}
            ),
        )

        # The ceiling itself must refuse project-wide kinds.
        for kind in ("REFERENCES", "DEFINITION"):
            if not CEILING[kind].startswith("REFUSED"):
                failures.append(f"the fallback claims it can answer {kind}")

    if failures:
        raise ContractError(
            "planted controls did not behave:\n  " + "\n  ".join(failures)
        )
    return positives, 12
