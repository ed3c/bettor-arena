#!/usr/bin/env python3
"""Refresh a line's delivery receipt from the forge, then prove the gate accepts it.

`/delivery sync <line>` used to be prose telling a human to hand-edit
delivery.json; a receipt maintained by memory drifts the same way the state it
records did. This rewrites the receipt's four-layer addresses from what the
forge says right now, stamps the commit it was synced at, and then runs the T0
gate — a sync that leaves the gate red is not a sync.

Writes only <materialized_path>/delivery.json. Refuses to invent a line, and
refuses to leave a receipt it cannot then verify.

Usage:
  python3 scripts/delivery_sync.py --line ID              # rewrite + verify
  python3 scripts/delivery_sync.py --line ID --dry-run    # print the diff only
  python3 scripts/delivery_sync.py --selftest             # merge logic, no network

Exit codes: 0 synced (gate green) · 2 gate red after sync · 64 usage/unknown line.
"""

from __future__ import annotations

import base64
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "gates"))
from _gate_common import repo_root  # noqa: E402

REGISTRY_REL = ".agents/skills/forgejo-delivery-loop/registry.json"


def credential(host: str) -> tuple[str, str]:
    result = subprocess.run(
        ["git", "credential", "fill"],
        input=f"protocol=http\nhost={host}\n\n",
        text=True,
        capture_output=True,
    )
    fields = dict(
        line.split("=", 1) for line in result.stdout.splitlines() if "=" in line
    )
    if not fields.get("username") or not fields.get("password"):
        print(f"FATAL: no credential for {host}", file=sys.stderr)
        raise SystemExit(64)
    return fields["username"], fields["password"]


def api(api_base: str, path: str, auth: tuple[str, str]):
    request = urllib.request.Request(f"{api_base}{path}")
    token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
    request.add_header("Authorization", f"Basic {token}")
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode() or "null")


def build_receipt(
    line: dict,
    issues: list[dict],
    pulls: list[dict],
    base_url: str,
    head: str,
    previous: dict | None,
) -> dict:
    """Merge live forge state into the receipt, preserving human-written fields.

    Open issues are what an unfinished line owes; closed ones live in git history
    and the plan ledger, so listing them here would make the receipt grow without
    telling anyone anything new.
    """
    repo = line["forgejo_repo"]
    open_issues = [
        f"{base_url}/{repo}/issues/{i['number']}"
        for i in issues
        if i["state"] == "open" and i.get("pull_request") is None
    ]
    open_pulls = [
        f"{base_url}/{repo}/pulls/{p['number']}" for p in pulls if p["state"] == "open"
    ]
    receipt = dict(previous or {})
    receipt.update(
        {
            "line": line["line"],
            "repo": repo,
            "issues": open_issues or [line.get("prd_issue", "")],
            "pr": open_pulls[0] if open_pulls else (previous or {}).get("pr", ""),
            "milestone_url": line.get("milestone_url", ""),
            "plan_doc": line.get("plan_doc", ""),
            "synced_at_commit": head,
        }
    )
    return receipt


def sync(root: Path, line_id: str, dry_run: bool) -> int:
    document = json.loads((root / REGISTRY_REL).read_text(encoding="utf-8"))
    line = next((ln for ln in document["lines"] if ln.get("line") == line_id), None)
    if line is None:
        print(
            f"FATAL unknown-line: {line_id} — register it before syncing",
            file=sys.stderr,
        )
        return 64
    materialized = line.get("materialized_path")
    if not materialized:
        print(
            f"FATAL not-materialized: {line_id} has no materialized_path to hold a receipt",
            file=sys.stderr,
        )
        return 64

    forge = document.get("forge", {})
    api_base = forge["api_base"]
    base_url = forge.get("base_url", api_base.rsplit("/api/", 1)[0])
    auth = credential(api_base.split("//", 1)[-1].split("/", 1)[0])
    repo = line["forgejo_repo"]
    try:
        issues = api(api_base, f"/repos/{repo}/issues?state=all&limit=100", auth) or []
        pulls = api(api_base, f"/repos/{repo}/pulls?state=all&limit=50", auth) or []
    except (urllib.error.URLError, urllib.error.HTTPError) as err:
        print(f"FATAL forge-unreadable: {err}", file=sys.stderr)
        return 64

    head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    target = root / materialized / "delivery.json"
    previous = (
        json.loads(target.read_text(encoding="utf-8")) if target.is_file() else None
    )
    receipt = build_receipt(line, issues, pulls, base_url, head, previous)
    text = json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"

    if dry_run:
        print(text)
        print("(dry-run: nothing written)")
        return 0

    target.write_text(text, encoding="utf-8")
    print(
        f"synced {target.relative_to(root)} → {len(receipt['issues'])} open issue(s), "
        f"pr={receipt['pr'] or 'none'}, at {head}"
    )
    # Assert before announcing: a sync whose receipt the gate rejects is not done.
    gate = subprocess.run(
        ["python3", str(root / "scripts/gates/check_delivery_receipt.py")],
        text=True,
        capture_output=True,
        cwd=str(root),
    )
    print(gate.stdout.strip())
    if gate.returncode != 0:
        print(gate.stderr.strip(), file=sys.stderr)
        print("FAIL: receipt written but the gate rejects it", file=sys.stderr)
        return 2
    return 0


def _selftest() -> int:
    line = {
        "line": "demo",
        "forgejo_repo": "neon/demo",
        "prd_issue": "http://x/neon/demo/issues/1",
        "milestone_url": "http://x/milestone/1",
        "plan_doc": "docs/p.md",
    }
    issues = [
        {"number": 1, "state": "open"},
        {"number": 2, "state": "closed"},
        {"number": 3, "state": "open", "pull_request": {}},
    ]
    pulls = [{"number": 9, "state": "open"}, {"number": 8, "state": "closed"}]
    previous = {
        "_note": "human-written",
        "pr": "http://x/old",
        "synced_at_commit": "old1234",
    }

    receipt = build_receipt(line, issues, pulls, "http://x", "abc1234", previous)
    cases = [
        (
            "only-open-issues-listed",
            receipt["issues"] == ["http://x/neon/demo/issues/1"],
        ),
        (
            "pull-requests-not-listed-as-issues",
            all("pulls" not in url for url in receipt["issues"]),
        ),
        ("open-pr-replaces-stale-one", receipt["pr"] == "http://x/neon/demo/pulls/9"),
        ("commit-stamp-refreshed", receipt["synced_at_commit"] == "abc1234"),
        ("human-written-fields-survive", receipt.get("_note") == "human-written"),
    ]
    empty = build_receipt(line, [], [], "http://x", "abc1234", None)
    cases.append(
        (
            "no-open-issues-falls-back-to-prd-not-empty",
            empty["issues"] == ["http://x/neon/demo/issues/1"],
        )
    )
    cases.append(("no-open-pr-leaves-pr-empty-not-fabricated", empty["pr"] == ""))

    red = [name for name, ok in cases if not ok]
    for name in red:
        print(f"SELFTEST case failed — {name}", file=sys.stderr)
    print("SELFTEST " + ("GREEN" if not red else "RED"))
    return 0 if not red else 1


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return _selftest()
    root = repo_root(Path(__file__).resolve().parent)
    if root is None:
        print("delivery_sync: not inside a git work tree", file=sys.stderr)
        return 64
    if len(argv) >= 2 and argv[0] == "--line":
        return sync(root, argv[1], dry_run="--dry-run" in argv[2:])
    print(__doc__.strip(), file=sys.stderr)
    return 64


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
