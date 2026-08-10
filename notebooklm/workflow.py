#!/usr/bin/env python3
"""notebooklm/workflow.py — the NotebookLM harvest loop's one entry point.

    workflow.py run (--target NAME | --notebook-title TITLE)
                    [--source-title T] [--out DIR] [--follow] [--dry-run]
    workflow.py --selftest

Reached through `sh loopctl/loopctl.sh notebooklm run ...`; the flags a caller
may say are declared in loopctl/contract.json, not here.

Two ways in, exactly one of which must be chosen. `--target` names an entry in
notebooklm/registry.json — this repo's interaction data for notebooklm-py, where
a harvest's shape is reviewable in a diff instead of living in a shell history.
`--notebook-title` is the ad-hoc form. Accepting both would silently pick a
winner; accepting neither would reach the account with no subject.

The registry's `id` is a PIN and never a shortcut: the title is still resolved
against the live account, and a disagreement is exit 2. A stale pin that quietly
won would harvest a different notebook under the right name.

What it does, in two hops:

  hop 1  resolve a notebook BY TITLE to its full UUID, pick one AI-related
         Google Doc or Google Sheet source out of it, and pull that source's
         indexed fulltext.
  hop 2  (`--follow`, opt-in) take a docs.google.com/document URL found INSIDE
         that fulltext and really access the document behind it. The source
         notebook is never written to: the second hop happens in a disposable
         scratch notebook that is deleted again on every exit path, including
         failure. Reading a notebook must not be able to change it.

Three things here are measurements, not preferences:

  * `--json` is only pure when the id is a FULL UUID. Given a partial id the CLI
    prints a human `Matched: <id> (<title>)` line to stdout BEFORE the JSON, and
    json.loads then dies on a document that is really there. So every id is
    resolved to its full UUID first, and the purity is still asserted afterwards
    — a fix that is only ever seen agreeing is not known to be able to disagree.

  * present is not authenticated. An absent `notebooklm` binary is FATAL 64; a
    present binary whose cookies no longer authenticate is exit 2. Collapsing
    them sends the repair at the wrong layer. `auth check --json` alone is a
    false-positive trap (it only proves the cookie file parses), so this drives
    `--test` and requires `checks.token_fetch` to be true as well as status ok.

  * an empty extraction equals anything it is compared against. Every derived
    set is asserted non-empty before it decides anything, and an empty one gets
    its own named state rather than falling through as "nothing to do".

Exit: 0 ok · 2 a named business absence or a red check · 64 FATAL (absent tool,
absent output directory, usage). Never re-mapped; the codes are what loopctl
passes through.

Cheap verification surface: `python3 notebooklm/workflow.py --selftest` — hermetic,
zero network, a fake CLI on PATH, and every named absence driven at least once
including the two above.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "bettor-arena-notebooklm-module@1.0.0"
BIN = "notebooklm"
REGISTRY = Path(__file__).resolve().parent / "registry.json"
DRIVE_FETCH = Path(__file__).resolve().parent / "drive_fetch.py"

# ASCII-boundary lookarounds, not \b: Python's \b is Unicode-aware, so \bAI\b
# does NOT match "AI高價值內容知識變現" — the very titles this loop exists to
# find. The first version silently classified every Chinese title as unrelated
# and picked nothing, which reads exactly like an empty notebook.
AI_TITLE = re.compile(
    r"(?<![A-Za-z])(?:AI|LLM|GPT|RAG|ML)(?![A-Za-z])"
    r"|(?i:agent|model|prompt|solopreneur|open ?source)"
    r"|人工智慧|大模型|機器學習|智能",
)
# The id is captured, not just matched: hop 2 goes by Drive FILE ID over the
# signed-in session, because the URL form is fetched anonymously and every one of
# these documents answers 401 to that.
DOC_URL = re.compile(r"https://docs\.google\.com/document/d/([A-Za-z0-9_-]{20,})")
HARVESTABLE = ("google_docs", "google_spreadsheet")


class Fatal(Exception):
    """Absence of a tool or a place to write: exit 64, never exit 2."""


class Red(Exception):
    """A named business absence or a failed check: exit 2, never exit 0."""


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------ the CLI


def _run(argv: list[str]) -> tuple[int, str, str]:
    if shutil.which(argv[0]) is None:
        raise Fatal(
            f"{argv[0]} is not on PATH — install notebooklm-py "
            "(pip install 'notebooklm-py[browser]'). An absent tool is not a "
            "notebook that came back empty."
        )
    proc = subprocess.run(argv, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def _json_out(argv: list[str], what: str) -> dict:
    """Run a --json command and refuse anything that is not pure JSON.

    The impurity is real and is what this guard is for: a partial id makes the
    CLI prepend `Matched: <id> (<title>)`. Parsing "leniently" (find the first
    brace) would hide a caller that is passing partial ids around, and partial
    ids are also ambiguous by construction.
    """
    rc, out, err = _run(argv)
    if rc != 0:
        raise Red(f"{what}: {BIN} exited {rc} — {(err or out).strip()[:400]}")
    head = out.lstrip()
    if not head.startswith(("{", "[")):
        raise Red(
            f"{what}: stdout is not pure JSON — it starts with "
            f"{head.splitlines()[0][:80]!r}. The CLI prepends a human `Matched:` "
            "line when it is handed a PARTIAL id; pass the full UUID."
        )
    try:
        return json.loads(head)
    except json.JSONDecodeError as exc:
        raise Red(f"{what}: stdout did not parse as JSON — {exc}") from exc


# ------------------------------------------------------------------- stages


def stage_auth() -> dict:
    data = _json_out([BIN, "auth", "check", "--test", "--json"], "auth check")
    checks = data.get("checks") or {}
    if data.get("status") != "ok" or checks.get("token_fetch") is not True:
        raise Red(
            "not-authenticated: the binary is present but its cookies do not "
            f"authenticate (status={data.get('status')!r}, "
            f"token_fetch={checks.get('token_fetch')!r}). Run `notebooklm auth "
            "refresh`, or `notebooklm login` if that is too stale. This is NOT "
            "the same absence as a missing binary and is not repaired the same way."
        )
    return {"status": "ok", "token_fetch": True}


def load_registry(path: Path = REGISTRY) -> dict:
    if not path.is_file():
        raise Fatal(
            f"no registry at {path} — `--target` names an entry in it, and "
            "guessing a notebook is exactly what naming a target avoids"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_target(name: str, registry: dict) -> dict:
    targets = registry.get("targets") or []
    if not targets:
        raise Red("registry-empty: notebooklm/registry.json declares no targets")
    hits = [t for t in targets if t.get("name") == name]
    if not hits:
        raise Red(
            f"target-not-found: no target named {name!r} in the registry. "
            "Declared: " + ", ".join(sorted(repr(t.get("name")) for t in targets))
        )
    return hits[0]


def pinned_id(title: str, registry: dict) -> str | None:
    for nb in registry.get("notebooks") or []:
        if nb.get("title") == title:
            return nb.get("id")
    return None


def stage_notebook(title: str, pin: str | None = None) -> dict:
    data = _json_out([BIN, "list", "--json"], "notebook list")
    books = data.get("notebooks") or []
    if not books:
        raise Red("no-notebooks: `notebooklm list` returned an empty set")
    hits = [b for b in books if b.get("title") == title]
    if not hits:
        raise Red(
            f"notebook-not-found: no notebook is titled {title!r}. Present: "
            + ", ".join(sorted(repr(b.get("title")) for b in books))
        )
    if len(hits) > 1:
        raise Red(
            f"notebook-ambiguous: {len(hits)} notebooks are titled {title!r}; "
            "a title is not an id, so this loop refuses to pick one for you"
        )
    live = hits[0]["id"]
    if pin is not None and pin != live:
        raise Red(
            f"registry-pin-stale: notebooklm/registry.json pins {title!r} to "
            f"{pin} but the account resolves it to {live}. A pin that quietly "
            "lost would harvest a different notebook under the right name; "
            "update the registry once you know which one you meant."
        )
    return {"id": live, "title": title, "pin_checked": pin is not None}


def stage_pick(notebook_id: str, source_title: str | None) -> dict:
    data = _json_out(
        [BIN, "source", "list", "-n", notebook_id, "--json"], "source list"
    )
    sources = data.get("sources") or []
    if not sources:
        raise Red("no-sources: the notebook resolved but carries no sources")
    ready = [
        s
        for s in sources
        if s.get("type") in HARVESTABLE and s.get("status") == "ready"
    ]
    if not ready:
        raise Red(
            "no-harvestable-source: the notebook has no READY Google Doc or "
            "Google Sheet. Types present: "
            + ", ".join(sorted({str(s.get("type")) for s in sources}))
        )
    if source_title is not None:
        named = [s for s in ready if s.get("title") == source_title]
        if not named:
            raise Red(
                f"source-title-not-found: no ready Doc/Sheet titled "
                f"{source_title!r} among "
                + ", ".join(sorted(repr(s.get("title")) for s in ready))
            )
        pick, why = named[0], "named by --source-title"
    else:
        related = [s for s in ready if AI_TITLE.search(s.get("title") or "")]
        if not related:
            raise Red(
                "no-ai-related-source: every ready Doc/Sheet title failed the "
                "AI-relevance match, so nothing was picked. Titles: "
                + ", ".join(sorted(repr(s.get("title")) for s in ready))
            )
        # A spreadsheet first, deliberately: only a sheet plausibly carries the
        # links hop 2 follows, so the default pick is the one that can make the
        # second hop possible rather than the one that sorts first.
        related.sort(key=lambda s: (s.get("type") != "google_spreadsheet", s["title"]))
        pick, why = related[0], "AI-related, spreadsheet-first, then by title"
    return {
        "id": pick["id"],
        "title": pick["title"],
        "type": pick["type"],
        "why": why,
        "candidates": [
            {"id": s["id"], "title": s["title"], "type": s["type"]} for s in ready
        ],
    }


def stage_fulltext(notebook_id: str, source_id: str, out: Path) -> dict:
    data = _json_out(
        [BIN, "source", "fulltext", source_id, "-n", notebook_id, "--json"],
        "source fulltext",
    )
    content = data.get("content") or ""
    if not content.strip():
        raise Red(
            f"empty-fulltext: source {source_id} is READY but its indexed text "
            "is empty. An empty extraction compares equal to anything, so it "
            "gets its own exit rather than flowing on as 'no links found'."
        )
    target = out / "hop1.txt"
    target.write_text(content, encoding="utf-8")
    return {
        "path": target.name,
        "chars": len(content),
        "sha256": _sha256(content),
        "title": data.get("title"),
        "kind": data.get("kind"),
    }


def stage_extract(out: Path) -> dict:
    content = (out / "hop1.txt").read_text(encoding="utf-8")
    ids = sorted({m.group(1) for m in DOC_URL.finditer(content)})
    return {
        "doc_ids": ids,
        "doc_urls": [f"https://docs.google.com/document/d/{i}" for i in ids],
        "count": len(ids),
    }


def cli_interpreter() -> str:
    """The interpreter that can import notebooklm, read off the CLI's shebang.

    The CLI is normally installed into an isolated environment (pipx / uv tool),
    so the python running THIS file cannot import the library. The interpreter
    that can is the one the CLI's own launcher names, and reading it from there
    keeps the absolute path out of a tracked file — the repo refuses those, and
    a hard-coded one would be wrong on the next machine anyway.
    """
    cli = shutil.which(BIN)
    if cli is None:
        raise Fatal(f"{BIN} is not on PATH — install notebooklm-py")
    try:
        first = Path(cli).read_text(encoding="utf-8", errors="replace").splitlines()[0]
    except (OSError, IndexError) as exc:
        raise Fatal(f"cannot read the shebang of {cli}: {exc}") from exc
    if not first.startswith("#!"):
        raise Fatal(
            f"{cli} is not a script with a shebang, so the interpreter that has "
            "the notebooklm library cannot be derived from it. Hop 2 needs the "
            "library because the CLI has no authenticated Drive path."
        )
    parts = first[2:].strip().split()
    interp = parts[1] if parts and parts[0].endswith("/env") else parts[0]
    resolved = shutil.which(interp) or interp
    if not Path(resolved).exists():
        raise Fatal(f"the interpreter named by {cli} does not exist: {resolved}")
    return resolved


def stage_follow(url: str, file_id: str, out: Path, timeout: int) -> dict:
    """Really open the linked Google Doc, in a notebook that is thrown away.

    By Drive file id over the SIGNED-IN session, not by URL. Measured: every
    document linked from the harvested sheet answers 401 to an anonymous fetch
    (a nonexistent id answers 404, which is how "gated" was told apart from "not
    there"), and the CLI's URL ingestion is anonymous — it returned
    FAILED_PRECONDITION for all of them. There is no CLI flag for the Drive
    path, so this goes through notebooklm/drive_fetch.py under the CLI's own
    interpreter.

    Adding a source is a write, and the only notebook this loop is allowed to
    write to is one it just created. The delete runs from `finally` so a failed
    add, a timeout, or a KeyboardInterrupt still takes the scratch notebook with
    it — a harvest that leaves debris in the account is not read-only in any
    sense the user would recognise.
    """
    created = _json_out(
        [BIN, "create", f"notebooklm-workflow-scratch-{_utc()}", "--json"],
        "scratch notebook create",
    )
    scratch = (created.get("notebook") or {}).get("id")
    if not scratch:
        raise Red("scratch-create-failed: `create --json` carried no notebook.id")
    try:
        # Selftest seam, deliberately NOT on the loopctl surface: a surface that
        # covers most of a target teaches callers to reach past it for the rest.
        override = os.environ.get("NOTEBOOKLM_DRIVE_FETCH")
        argv = (
            shlex.split(override) if override else [cli_interpreter(), str(DRIVE_FETCH)]
        )
        rc, stdout, stderr = _run(
            [*argv, scratch, file_id, f"followed-{file_id[:8]}", str(timeout)]
        )
        if rc == 3:
            raise Red(
                "follow-library-absent: the notebooklm LIBRARY is not importable "
                "under the CLI's own interpreter, so the authenticated Drive path "
                f"is unavailable. {(stderr or '').strip()[:300]}"
            )
        if rc == 4:
            # Do NOT lead with "not shared". Measured 2026-08-08 against Drive as
            # a second arrival: all eleven documents linked from the harvested
            # sheet are owned by this very account, and an anonymous fetch still
            # 401s on them. The gate is authentication, not sharing — so naming
            # sharing first sent a reader to ask a colleague for permission on a
            # file they already own. This message is the SIGNED-IN path failing,
            # which is a different and narrower set of causes.
            raise Red(
                "follow-not-accessible: Drive refused the document on the "
                "AUTHENTICATED path. Discriminate before repairing — `curl` the "
                "URL: 404 means the id itself is wrong (go back and check what "
                "produced hop1), while 401 only means sign-in is required and "
                "says NOTHING about sharing. Real causes here are a session that "
                "no longer has access, a file this account genuinely cannot "
                "reach, or a file that is not a native Google Doc. "
                f"{(stderr or '').strip()[:300]}"
            )
        if rc != 0:
            raise Red(
                f"follow-failed: drive_fetch exited {rc} — {(stderr or stdout).strip()[:300]}"
            )
        head = stdout.lstrip()
        if not head.startswith("{"):
            raise Red(
                "follow-impure-json: drive_fetch printed something before its "
                f"JSON — {head.splitlines()[0][:80]!r}"
            )
        data = json.loads(head)
        content = data.get("content") or ""
        if not content.strip():
            raise Red(f"follow-empty: {url} was reachable but indexed to no text")
        target = out / "hop2.txt"
        target.write_text(content, encoding="utf-8")
        return {
            "state": "accessed",
            "via": "drive-file-id-over-signed-in-session",
            "url": url,
            "file_id": file_id,
            "title": data.get("title"),
            "path": target.name,
            "chars": len(content),
            "sha256": _sha256(content),
            "scratch_notebook": scratch,
        }
    finally:
        _run([BIN, "delete", "-n", scratch, "--yes"])


# ---------------------------------------------------------------------- run


def run(args: argparse.Namespace) -> int:
    root = Path(__file__).resolve().parent.parent
    registry_path = Path(args.registry) if args.registry else REGISTRY
    registry: dict = {}
    target: dict = {}
    if args.target is not None:
        registry = load_registry(registry_path)
        target = resolve_target(args.target, registry)
        args.notebook_title = target["notebook_title"]
        if args.source_title is None:
            args.source_title = target.get("source_title")
        if target.get("follow"):
            args.follow = True
        print(f"  [target  ] {args.target} -> {args.notebook_title!r} (registry)")
    elif registry_path.is_file():
        # Ad-hoc titles still get the pin check when the registry knows the
        # notebook. Skipping it for --notebook-title would leave the cheaper
        # path as the unchecked one, which is backwards.
        registry = json.loads(registry_path.read_text(encoding="utf-8"))

    out = Path(args.out) if args.out else root / "data" / "notebooklm" / _utc()
    try:
        out.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise Fatal(f"cannot create the output directory {out}: {exc}") from exc

    plan = [
        f"{BIN} auth check --test --json",
        f"{BIN} list --json",
        f"{BIN} source list -n <notebook-uuid> --json",
        f"{BIN} source fulltext <source-uuid> -n <notebook-uuid> --json",
    ]
    if args.follow:
        plan += [
            f"{BIN} create notebooklm-workflow-scratch-<utc> --json",
            "<cli-interpreter> notebooklm/drive_fetch.py <scratch-uuid> <doc-file-id> <title>",
            "    (sources.add_drive over the signed-in session — the CLI's URL",
            "     ingestion is anonymous and every one of these docs answers 401)",
            f"{BIN} delete -n <scratch-uuid> --yes  (always, from finally)",
        ]
    for line in plan:
        print(f"  [plan    ] {line}")

    result: dict = {
        "schema_version": SCHEMA,
        "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "notebook_title": args.notebook_title,
        "target": args.target,
        "follow_requested": bool(args.follow),
        "dry_run": bool(args.dry_run),
        "out_dir": str(out),
    }

    result["auth"] = stage_auth()
    print("  [auth    ] authenticated (token_fetch true, not just a parseable file)")

    nb = stage_notebook(args.notebook_title, pinned_id(args.notebook_title, registry))
    result["notebook"] = nb
    print(
        f"  [notebook] {nb['title']} -> {nb['id']}"
        + (" (registry pin agrees)" if nb["pin_checked"] else " (no registry pin)")
    )

    pick = stage_pick(nb["id"], args.source_title)
    result["source"] = pick
    print(
        f"  [source  ] {pick['type']} {pick['title']!r} -> {pick['id']} "
        f"({pick['why']}; {len(pick['candidates'])} candidate(s))"
    )

    if args.dry_run:
        # Every call point above really executed; the ones below are the writes.
        # A dry run that skipped the reads too would prove only that argparse works.
        result["stopped_at"] = "dry-run-before-fetch"
        _emit(out, result)
        print(
            "  [dry-run ] stopped before any fetch or write; the plan above is complete"
        )
        return 0

    hop1 = stage_fulltext(nb["id"], pick["id"], out)
    result["hop1"] = hop1
    print(
        f"  [hop1    ] {hop1['chars']} chars -> {hop1['path']} sha={hop1['sha256'][:12]}"
    )

    found = stage_extract(out)
    result["extracted"] = found
    print(f"  [extract ] {found['count']} docs.google document URL(s) inside hop1")

    if not args.follow:
        result["hop2"] = {
            "state": "not-requested",
            "why": "--follow is opt-in: hop 2 creates and deletes a scratch notebook",
        }
        _emit(out, result)
        return _verdict(result)

    if not found["doc_urls"]:
        result["hop2"] = {
            "state": "no-doc-urls",
            "why": "--follow was asked for and the fulltext carries no document link",
        }
        _emit(out, result)
        raise Red(
            "no-doc-urls: --follow was requested but hop1 carries no "
            "docs.google.com/document link, so there is nothing to follow. An "
            "empty set is not a successful second hop."
        )

    # Try the links in order and stop at the first one that opens. A single
    # attempt would turn "this particular link is dead" into "the second hop does
    # not work", and those are different facts; every refusal is kept so the
    # receipt says which documents were tried and why each was refused.
    attempts: list[dict] = []
    for file_id, url in zip(found["doc_ids"], found["doc_urls"]):
        print(f"  [hop2    ] following {url}")
        try:
            result["hop2"] = stage_follow(url, file_id, out, args.timeout)
            break
        except Red as exc:
            attempts.append({"url": url, "why": str(exc)})
            print(f"  [hop2    ] refused — {str(exc)[:120]}")
    else:
        result["hop2"] = {
            "state": "none-accessible",
            "attempted": attempts,
            "why": f"all {len(attempts)} linked document(s) were refused",
        }
        _emit(out, result)
        raise Red(
            f"follow-none-accessible: every one of the {len(attempts)} linked "
            "documents was refused. See hop2.attempted in the receipt for each "
            "reason — they are not all the same repair."
        )
    result["hop2"]["earlier_refusals"] = attempts
    hop2 = result["hop2"]
    print(
        f"  [hop2    ] {hop2['chars']} chars -> {hop2['path']} sha={hop2['sha256'][:12]}"
    )
    _emit(out, result)
    return _verdict(result)


def _emit(out: Path, result: dict) -> None:
    target = out / "module.json"
    target.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    # Assert before announcing: the receipt has to exist and parse, or the line
    # below is a claim about a file nobody wrote.
    json.loads(target.read_text(encoding="utf-8"))
    print(f"  [receipt ] {target}")


def _verdict(result: dict) -> int:
    print(
        f"PASS: {result['notebook_title']} -> {result['source']['title']!r} -> "
        f"{result['extracted']['count']} doc link(s), hop2={result['hop2']['state']}"
    )
    return 0


# ------------------------------------------------------------------ selftest

# Stands in for notebooklm/drive_fetch.py under the CLI's own interpreter, which
# the selftest cannot have: the real one imports a library installed in a
# separate environment. Its EXIT CODES are the contract being exercised — 3 the
# library is absent, 4 Drive refused the file — because those are what the caller
# turns into two different named states with two different repairs.
DRIVE_STUB = r"""#!/usr/bin/env python3
import json, os, sys

mode = os.environ["NOTEBOOKLM_STUB"]
notebook, file_id, title = sys.argv[1], sys.argv[2], sys.argv[3]

if mode == "no-library":
    print("no module named notebooklm", file=sys.stderr)
    raise SystemExit(3)
if mode == "doc-not-shared":
    print("PermissionError: not shared", file=sys.stderr)
    raise SystemExit(4)
if mode == "first-doc-dead" and file_id.startswith("D"):
    print("PermissionError: not shared", file=sys.stderr)
    raise SystemExit(4)
if mode == "follow-impure":
    print("Matched: something")
print(json.dumps({"source_id": "s-follow", "title": "the linked doc",
                  "content": "the linked document's own text\n"}))
"""

STUB = r'''#!/usr/bin/env python3
"""Fake notebooklm. Behaviour is chosen by NOTEBOOKLM_STUB, one case per named absence."""
import json, os, sys

mode = os.environ["NOTEBOOKLM_STUB"]
a = sys.argv[1:]


def out(obj):
    print(json.dumps(obj))
    raise SystemExit(0)


if a[:2] == ["auth", "check"]:
    ok = mode != "stale-cookies"
    out({"status": "ok", "checks": {"token_fetch": ok}})
if a[:1] == ["list"]:
    if mode == "wrong-title":
        out({"notebooks": [{"id": "n-1", "title": "somewhere else"}]})
    out({"notebooks": [{"id": "11111111-1111-1111-1111-111111111111",
                        "title": "AI 知識變現"}]})
if a[:2] == ["source", "list"]:
    if mode == "no-ai-source":
        out({"sources": [{"id": "s-1", "title": "grocery list",
                          "type": "google_docs", "status": "ready"}]})
    out({"sources": [
        {"id": "22222222-2222-2222-2222-222222222222",
         "title": "AI高價值內容知識變現潛力排行榜",
         "type": "google_spreadsheet", "status": "ready"},
        {"id": "33333333-3333-3333-3333-333333333333",
         "title": "grocery list", "type": "google_docs", "status": "ready"},
    ]})
if a[:2] == ["source", "fulltext"]:
    # Two links, so "the first one is dead" can be told apart from "hop 2 is broken".
    body = ("row\nhttps://docs.google.com/document/d/" + "D" * 30 + "/edit\n"
            "row\nhttps://docs.google.com/document/d/" + "E" * 30 + "/edit\n")
    if mode == "no-links":
        body = "a sheet with no document links at all\n"
    if mode == "impure-json":
        # The real defect: a human line printed before the JSON.
        print("Matched: 2222222 (AI...)")
        body = "x"
    out({"content": body, "title": "t", "kind": "google_spreadsheet"})
if a[:1] == ["create"]:
    out({"notebook": {"id": "scratch-99999999"}})
if a[:1] == ["delete"]:
    # Recorded so the selftest can prove the scratch notebook is always removed.
    with open(os.environ["NOTEBOOKLM_STUB_LOG"], "a", encoding="utf-8") as fh:
        fh.write("deleted " + a[2] + "\n")
    out({"ok": True})
print("stub: unhandled " + " ".join(a), file=sys.stderr)
raise SystemExit(70)
'''


def _selftest() -> int:
    red = 0

    def case(name: str, got, want) -> None:
        nonlocal red
        if got != want:
            print(
                f"SELFTEST case failed — {name}: got {got!r}, want {want!r}",
                file=sys.stderr,
            )
            red = 1

    me = str(Path(__file__).resolve())
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        stub_dir = base / "bin"
        stub_dir.mkdir()
        stub = stub_dir / BIN
        stub.write_text(STUB, encoding="utf-8")
        stub.chmod(0o755)
        log = base / "delete.log"
        drive_stub = base / "drive_stub.py"
        drive_stub.write_text(DRIVE_STUB, encoding="utf-8")
        fetch_cmd = f"{shlex.quote(sys.executable)} {shlex.quote(str(drive_stub))}"

        def drive_argv(mode: str, argv: list[str]) -> tuple[int, str]:
            env = dict(
                os.environ,
                NOTEBOOKLM_STUB=mode,
                NOTEBOOKLM_STUB_LOG=str(log),
                NOTEBOOKLM_DRIVE_FETCH=fetch_cmd,
            )
            env["PATH"] = f"{stub_dir}:{env['PATH']}"
            proc = subprocess.run(
                [sys.executable, me, "run", *argv],
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            return proc.returncode, proc.stdout + proc.stderr

        def drive(mode: str, *flags: str, on_path: bool = True) -> tuple[int, str]:
            env = dict(
                os.environ,
                NOTEBOOKLM_STUB=mode,
                NOTEBOOKLM_STUB_LOG=str(log),
                NOTEBOOKLM_DRIVE_FETCH=fetch_cmd,
            )
            env["PATH"] = f"{stub_dir}:{env['PATH']}" if on_path else "/nonexistent"
            outdir = base / f"out-{mode}-{len(flags)}-{int(on_path)}"
            proc = subprocess.run(
                [
                    sys.executable,
                    me,
                    "run",
                    "--notebook-title",
                    "AI 知識變現",
                    "--out",
                    str(outdir),
                    "--registry",
                    str(base / "empty-registry.json"),
                    *flags,
                ],
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            return proc.returncode, proc.stdout + proc.stderr

        # An empty-but-present registry for the ad-hoc cases: pointing them at
        # the REAL registry would make every one of them depend on this repo's
        # current notebook pins, so a pin edit would break unrelated cases.
        (base / "empty-registry.json").write_text(
            '{"targets": [], "notebooks": []}', encoding="utf-8"
        )
        reg = base / "registry.json"
        reg.write_text(
            json.dumps(
                {
                    "targets": [
                        {
                            "name": "t1",
                            "notebook_title": "AI 知識變現",
                            "source_title": None,
                            "follow": True,
                        }
                    ],
                    "notebooks": [
                        {
                            "title": "AI 知識變現",
                            "id": "11111111-1111-1111-1111-111111111111",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        stale = base / "stale.json"
        stale.write_text(
            json.dumps(
                {
                    "targets": [
                        {
                            "name": "t1",
                            "notebook_title": "AI 知識變現",
                            "source_title": None,
                            "follow": False,
                        }
                    ],
                    "notebooks": [
                        {
                            "title": "AI 知識變現",
                            "id": "deadbeef-0000-0000-0000-000000000000",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        # Positive control first. A checker that can only fail proves nothing,
        # and every red case below is only meaningful against a green one.
        rc, _ = drive("happy", "--follow")
        case("happy-path-is-green", rc, 0)
        receipt = json.loads(
            (base / "out-happy-1-1" / "module.json").read_text(encoding="utf-8")
        )
        case("receipt-carries-schema", receipt["schema_version"], SCHEMA)
        case("receipt-carries-the-followed-doc", receipt["hop2"]["state"], "accessed")
        case("hop2-really-read-the-linked-doc", receipt["hop2"]["chars"] > 0, True)
        case("extraction-is-non-empty", receipt["extracted"]["count"], 2)
        case(
            "hop2-went-by-drive-file-id",
            receipt["hop2"]["via"],
            "drive-file-id-over-signed-in-session",
        )
        case(
            "scratch-notebook-was-deleted",
            "deleted scratch-99999999" in log.read_text(encoding="utf-8"),
            True,
        )

        # A dead first link must not be reported as a broken second hop: the run
        # moves on to the next document and records why the first was refused.
        rc, _ = drive("first-doc-dead", "--follow")
        case("dead-first-link-falls-through", rc, 0)
        fell = json.loads(
            (base / "out-first-doc-dead-1-1" / "module.json").read_text(
                encoding="utf-8"
            )
        )
        case("second-link-was-the-one-opened", fell["hop2"]["state"], "accessed")
        case("the-refusal-was-kept", len(fell["hop2"]["earlier_refusals"]), 1)

        # Every link refused is its own state, and it is a red — an empty result
        # is not a successful second hop.
        rc, txt = drive("doc-not-shared", "--follow")
        case("all-links-refused-is-2", rc, 2)
        case("all-refused-is-named", "follow-none-accessible" in txt, True)

        # The library being absent is repaired by installing, not by re-sharing a
        # document, so it may not wear the same name as a refusal.
        rc, txt = drive("no-library", "--follow")
        case("absent-library-is-2", rc, 2)
        case("absent-library-is-named", "follow-library-absent" in txt, True)

        # The same purity rule applies to the drive helper's own stdout.
        rc, txt = drive("follow-impure", "--follow")
        case("impure-drive-output-is-refused", rc, 2)
        case("impure-drive-output-is-named", "follow-impure-json" in txt, True)

        # Absent tool and present-but-unauthenticated must not wear each other's
        # exit code: one is repaired by installing, the other by refreshing.
        rc, txt = drive("happy", on_path=False)
        case("absent-binary-is-fatal-64", rc, 64)
        case("absent-binary-says-so", "not on PATH" in txt, True)
        rc, txt = drive("stale-cookies")
        case("present-but-unauthenticated-is-2", rc, 2)
        case("unauthenticated-is-named", "not-authenticated" in txt, True)

        # The measured interface defect: a `Matched:` line before the JSON must
        # be refused, never leniently parsed past.
        rc, txt = drive("impure-json")
        case("impure-json-is-refused", rc, 2)
        case("impure-json-names-the-cause", "PARTIAL id" in txt, True)

        # Named business absences, each with its own exit rather than a silent pass.
        rc, txt = drive("wrong-title")
        case("notebook-not-found-is-2", rc, 2)
        case("notebook-not-found-is-named", "notebook-not-found" in txt, True)
        rc, txt = drive("no-ai-source")
        case("no-ai-related-source-is-2", rc, 2)
        case("no-ai-source-is-named", "no-ai-related-source" in txt, True)

        # An empty link set with --follow is a red, not "nothing to do".
        rc, txt = drive("no-links", "--follow")
        case("empty-extraction-with-follow-is-2", rc, 2)
        case("empty-extraction-is-named", "no-doc-urls" in txt, True)
        # ...and without --follow the same tree is green: the emptiness only
        # decides something where it was actually asked to.
        rc, _ = drive("no-links")
        case("empty-extraction-without-follow-is-green", rc, 0)

        # A document the signed-in path cannot reach fails as its own state, and
        # STILL takes the scratch notebook with it.
        log.write_text("", encoding="utf-8")
        rc, txt = drive("doc-not-shared", "--follow")
        case("unreachable-doc-is-2", rc, 2)
        case(
            "scratch-deleted-even-on-failure",
            "deleted scratch-99999999" in log.read_text(encoding="utf-8"),
            True,
        )

        # The registry: a named target must resolve, carry its own --follow, and
        # a pin that no longer matches the account must lose loudly.
        rc, txt = drive_argv(
            "happy",
            [
                "--target",
                "t1",
                "--registry",
                str(reg),
                "--out",
                str(base / "out-target"),
            ],
        )
        case("named-target-resolves", rc, 0)
        tgt = json.loads(
            (base / "out-target" / "module.json").read_text(encoding="utf-8")
        )
        case("target-turned-on-follow", tgt["hop2"]["state"], "accessed")
        case("target-is-recorded", tgt["target"], "t1")
        case("pin-was-checked", tgt["notebook"]["pin_checked"], True)

        rc, txt = drive_argv(
            "happy",
            [
                "--target",
                "nope",
                "--registry",
                str(reg),
                "--out",
                str(base / "out-notarget"),
            ],
        )
        case("unknown-target-is-2", rc, 2)
        case("unknown-target-is-named", "target-not-found" in txt, True)

        rc, txt = drive_argv(
            "happy",
            [
                "--target",
                "t1",
                "--registry",
                str(stale),
                "--out",
                str(base / "out-stale"),
            ],
        )
        case("stale-pin-is-2", rc, 2)
        case("stale-pin-is-named", "registry-pin-stale" in txt, True)

        rc, txt = drive_argv("happy", ["--out", str(base / "out-neither")])
        case("neither-target-nor-title-is-64", rc, 64)
        rc, txt = drive_argv(
            "happy",
            [
                "--target",
                "t1",
                "--notebook-title",
                "x",
                "--out",
                str(base / "out-both"),
            ],
        )
        case("both-target-and-title-is-64", rc, 64)

        # Chinese titles must survive the relevance match — Python's \b would
        # have dropped every one of them.
        case(
            "chinese-ai-title-matches",
            bool(AI_TITLE.search("AI高價值內容知識變現潛力排行榜")),
            True,
        )
        case("unrelated-title-does-not", bool(AI_TITLE.search("grocery list")), False)

        # Dry run exercises every read and writes no fetch.
        rc, txt = drive("happy", "--dry-run", "--follow")
        case("dry-run-is-green", rc, 0)
        case("dry-run-plans-the-write-calls", "drive_fetch.py" in txt, True)
        case(
            "dry-run-fetched-nothing",
            (base / "out-happy-2-1" / "hop1.txt").exists(),
            False,
        )

    print("SELFTEST " + ("GREEN" if not red else "RED"))
    return red


# ---------------------------------------------------------------------- cli


def main(argv: list[str]) -> int:
    if argv[:1] == ["--selftest"]:
        return _selftest()
    parser = argparse.ArgumentParser(add_help=False)
    sub = parser.add_subparsers(dest="cmd")
    run_p = sub.add_parser("run", add_help=False)
    run_p.add_argument("--target", default=None)
    run_p.add_argument("--notebook-title", default=None)
    run_p.add_argument("--source-title", default=None)
    run_p.add_argument("--registry", default=None)
    run_p.add_argument("--out", default=None)
    run_p.add_argument("--follow", action="store_true")
    run_p.add_argument("--dry-run", action="store_true")
    run_p.add_argument("--timeout", type=int, default=600)
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        print(__doc__.strip(), file=sys.stderr)
        return 64
    if args.cmd != "run":
        print(__doc__.strip(), file=sys.stderr)
        return 64
    if (args.target is None) == (args.notebook_title is None):
        print(
            "notebooklm FATAL: give exactly one of --target (a registry entry) or "
            "--notebook-title (ad hoc). Both would silently pick a winner; neither "
            "would reach the account with no subject.",
            file=sys.stderr,
        )
        return 64
    try:
        return run(args)
    except Fatal as exc:
        print(f"notebooklm FATAL: {exc}", file=sys.stderr)
        return 64
    except Red as exc:
        print(f"notebooklm RED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
