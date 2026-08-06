#!/usr/bin/env python3
"""Explicit audit: pull each delivery line's live four-layer state from Forgejo.

This is the half the T0 gate deliberately does not do. `check_delivery_receipt`
proves a receipt exists and is shaped right, with zero network, at commit time.
This asks the forge what is actually true right now — PRD, open slices, PRs,
milestone progress — and therefore must never be wired into a hook: a commit
that needs the network to succeed fails for reasons that have nothing to do with
the commit.

Credentials come from the git credential helper in memory and are never printed
or written (the repo's credential-hygiene gate enforces the file half).

Usage:
  python3 scripts/delivery_status.py                 # every registered line
  python3 scripts/delivery_status.py --line ID       # one line
  python3 scripts/delivery_status.py --selftest      # render/parse controls, no network

Exit codes: 0 rendered · 2 a line's forge state could not be read · 64 usage,
unknown line, or absent credential.
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
        print(
            f"FATAL: no credential for {host} — the audit needs one; the gate does not",
            file=sys.stderr,
        )
        raise SystemExit(64)
    return fields["username"], fields["password"]


def api(api_base: str, path: str, auth: tuple[str, str]):
    request = urllib.request.Request(f"{api_base}{path}")
    token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
    request.add_header("Authorization", f"Basic {token}")
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode() or "null")


def render(
    line: dict, issues: list[dict], pulls: list[dict], milestone: dict | None
) -> str:
    """Format one line's four layers. Pure — the selftest drives it with fixtures."""
    slices = [i for i in issues if not i.get("pull_request")]
    open_slices = [i for i in slices if i["state"] == "open"]
    open_pulls = [p for p in pulls if p["state"] == "open"]
    if milestone:
        done = milestone["closed_issues"]
        total = done + milestone["open_issues"]
        pct = f"{100 * done // total}%" if total else "n/a"
        layer4 = f"{milestone['title']}: {done}/{total} ({pct})"
    else:
        layer4 = "NO MILESTONE — layer 4 absent, progress has no horizontal view"
    lines = [
        f"line: {line['line']}  repo: {line.get('forgejo_repo', '?')}",
        f"  1 PRD      {line.get('prd_issue', 'MISSING — no spec root registered')}",
        f"  2 slices   {len(open_slices)} open of {len(slices)}"
        + (
            f" → {', '.join('#' + str(i['number']) for i in open_slices[:8])}"
            if open_slices
            else ""
        ),
        f"  3 PRs      {len(open_pulls)} open of {len(pulls)}"
        + (
            f" → {', '.join('#' + str(p['number']) for p in open_pulls[:8])}"
            if open_pulls
            else ""
        ),
        f"  4 progress {layer4}",
        f"  plan       {line.get('plan_doc', 'MISSING — no as-run ledger registered')}",
    ]
    return "\n".join(lines)


def audit(root: Path, only: str | None) -> int:
    document = json.loads((root / REGISTRY_REL).read_text(encoding="utf-8"))
    forge = document.get("forge", {})
    api_base = forge.get("api_base")
    if not api_base:
        print("FATAL: registry declares no forge.api_base", file=sys.stderr)
        return 64
    host = api_base.split("//", 1)[-1].split("/", 1)[0]
    auth = credential(host)

    lines = [ln for ln in document["lines"] if only is None or ln.get("line") == only]
    if only and not lines:
        print(f"FATAL unknown-line: {only}", file=sys.stderr)
        return 64

    failed = False
    for line in lines:
        repo = line.get("forgejo_repo")
        try:
            issues = api(api_base, f"/repos/{repo}/issues?state=all&limit=100", auth)
            pulls = api(api_base, f"/repos/{repo}/pulls?state=all&limit=50", auth)
            milestone_url = line.get("milestone_url", "")
            milestone = None
            if milestone_url:
                mid = milestone_url.rstrip("/").rsplit("/", 1)[-1]
                milestone = api(api_base, f"/repos/{repo}/milestones/{mid}", auth)
        except (urllib.error.URLError, urllib.error.HTTPError) as err:
            print(
                f"FAIL {line.get('line')}: forge state unreadable: {err}",
                file=sys.stderr,
            )
            failed = True
            continue
        print(render(line, issues or [], pulls or [], milestone))
        print()
    return 2 if failed else 0


# ---------------------------------------------------------------- selftest


def _selftest() -> int:
    """No network: the renderer is the part that can silently lie."""
    line = {
        "line": "demo",
        "forgejo_repo": "neon/demo",
        "prd_issue": "http://x/issues/2",
        "milestone_url": "http://x/milestone/1",
        "plan_doc": "docs/plans/demo/as-run.md",
    }
    issues = [
        {"number": 2, "state": "open"},
        {"number": 3, "state": "closed"},
        {"number": 4, "state": "open", "pull_request": {}},
    ]
    pulls = [{"number": 1, "state": "closed"}, {"number": 5, "state": "open"}]
    milestone = {"title": "demo", "open_issues": 1, "closed_issues": 3}

    cases: list[tuple[str, bool]] = []
    out = render(line, issues, pulls, milestone)
    cases.append(("pull-requests-are-not-counted-as-slices", "1 open of 2" in out))
    cases.append(("open-slice-numbers-named", "#2" in out))
    cases.append(("pr-layer-counts-separately", "1 open of 2" in out.split("3 PRs")[1]))
    cases.append(("milestone-percentage", "3/4 (75%)" in out))

    bare = render({"line": "bare"}, [], [], None)
    cases.append(("absent-prd-is-named-not-blank", "MISSING" in bare))
    cases.append(
        (
            "absent-milestone-is-named-not-100pct",
            "NO MILESTONE" in bare and "100%" not in bare,
        )
    )
    cases.append(("absent-plan-is-named", "no as-run ledger" in bare))

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
        print("delivery_status: not inside a git work tree", file=sys.stderr)
        return 64
    if not argv:
        return audit(root, None)
    if len(argv) == 2 and argv[0] == "--line":
        return audit(root, argv[1])
    print(__doc__.strip(), file=sys.stderr)
    return 64


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
