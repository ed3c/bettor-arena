#!/usr/bin/env python3
"""Deterministic OpenWiki passes, reimplemented for a host-agent (no-Node) port.

OpenWiki's official system prompts make promises the AGENT does not keep -- the
CLI does, in `src/agent/okf-middleware.ts`:

    beforeAgent : migrateWikiToOkf          -> `migrate` here
    afterAgent  : validateWikiMermaid       -> `finalize` step 1
                  synchronizeWikiIndexes    -> `finalize` step 2
                  validateWikiInternalLinks -> `finalize` step 3

Without these, prompt lines like "Directory index.md files are generated
deterministically after the run", "OpenWiki repairs front matter deterministically
after every run", and "if you find a text fence preceded by an HTML comment
starting with 'openwiki: mermaid parse failed', repair the syntax" are dead
letters. This module is the port of that code-owned layer; stdlib only, so it
runs wherever python3 does.

Fidelity notes -- read these before assuming byte-equality with upstream:
  * Mermaid uses the HEURISTIC path only. Upstream prefers the real `mermaid`
    parser when the optional peer dep is installed and falls back to the same
    three conservative heuristics otherwise. No Node here means heuristic always,
    which upstream documents as valid (it under-reports, never over-reports).
  * Index link ordering uses byte sort, not JS `localeCompare`. Identical for
    ASCII filenames; can differ for non-ASCII ones.
  * Heading slugs use Python `\\w`, the closest stdlib analogue of upstream's
    `\\p{L}\\p{N}`.
  * PRESERVED_EXTENSION_FIELDS is DELIBERATELY WIDER than upstream. Upstream
    preserves only `openwiki_translation_pending` across a front-matter rebuild,
    which would silently drop this port's RepoDoc routing fields and break KB
    ingest for exactly the pages that were already malformed. See
    kb-ingest/port/repodoc-extension.md.

Usage:
    openwiki_post.py migrate  <wiki_root> [--protect REL_PATH ...]
    openwiki_post.py finalize <wiki_root> [--target REPO] [--command init|update]
                                          [--model ID] [--status STATUS]
                                          [--protect REL_PATH ...]
    openwiki_post.py --selftest

`--protect` names a wiki-root-relative page that some other tool generates and
may assert byte-equality over. Protected pages are indexed and linked normally
but never rewritten by these passes.

`wiki_root` is the generated `openwiki/` directory itself.
Exit codes: 0 ok · 1 failure · 2 bad usage
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

# Reserved/control files that never carry concept front matter, diagrams, or
# concept links. Mirrors the EXCLUDED_FILES set repeated in index-sync.ts,
# mermaid/wiki.ts, and wiki-link-validator.ts.
EXCLUDED_FILES = {"index.md", "log.md", "_plan.md", "INSTRUCTIONS.md"}
INDEX_FILE = "index.md"

# Fallbacks stamped onto a page whose front matter has to be rebuilt.
DERIVED_TYPE = "Reference"
GENERATED_FIELD = "openwiki_generated"

# Fields carried across a front-matter rebuild. See the fidelity note above:
# upstream keeps only the first entry.
PRESERVED_EXTENSION_FIELDS = (
    "openwiki_translation_pending",
    "node_kind",
    "ingest_lane",
    "repo",
    "repo_url",
    "commit",
    "covers",
    "libraries",
    "generated_by",
    "generated_at",
    "source",
)

FRONTMATTER_LABELS = {"files": "Files", "directories": "Directories"}

# Wiki-root-relative paths this run must never rewrite, set from --protect.
#
# Upstream has no equivalent because upstream owns every page it touches. A real
# target can hold a page that some other tool generates and then asserts is
# byte-equal to that generator's output -- agent-skills-repo does exactly this
# with `render_lifecycle_openwiki.py --stdout`. Repairing such a page's front
# matter is a silent breakage: the page still looks fine, and a completely
# separate gate goes red. Protected pages are still indexed and still read for
# link targets; they are only never written.
PROTECTED: set[str] = set()


def protected(path: Path, root: Path) -> bool:
    return path.relative_to(root).as_posix() in PROTECTED


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
STAMP_RE = re.compile(r"^\s*<!--\s*openwiki:\s*broken internal link\b.*?-->\s*$")
EXTERNAL_RE = re.compile(r"^(?:[a-z][a-z\d+.-]*:|//)", re.IGNORECASE)
FENCE_RE = re.compile(r"^(\s*)(`{3,})\s*(\S*)\s*$")


# --------------------------------------------------------------------------
# front matter
# --------------------------------------------------------------------------


def split_frontmatter(content: str) -> tuple[list[str] | None, str]:
    """Split a leading `---` block into (block_lines, body).

    Returns (None, content) when the document has no front-matter block.
    """
    lines = content.split("\n")
    if not lines or lines[0].rstrip("\r") != "---":
        return None, content
    for idx in range(1, len(lines)):
        if lines[idx].rstrip("\r") == "---":
            return lines[1:idx], "\n".join(lines[idx + 1 :])
    return None, content


def read_field(block: list[str], key: str) -> str | None:
    """Read a top-level scalar field's value, or None when absent/non-scalar.

    Line-based on purpose: this port has no YAML dependency, and the only
    decision that destroys data (rebuild or not) hinges solely on `type`, which
    upstream also reduces to "is there a non-empty string here". Anything this
    parser cannot read is reported absent, which routes to the safe path for
    `type` (rebuild a page that really was malformed) and to "omit" for the
    optional display fields an index renders.
    """
    pattern = re.compile(rf"^{re.escape(key)}\s*:\s*(.*)$")
    for line in block:
        match = pattern.match(line)
        if not match:
            continue
        value = match.group(1).strip()
        if not value or value.startswith(("[", "{", "|", ">", "&", "*", "#")):
            return None
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        return value or None
    return None


def field_lines(block: list[str], key: str) -> list[str]:
    """Return the raw lines owning a top-level key, including indented children.

    Raw lines rather than a parsed value, so block lists (`covers:` followed by
    `  - a`) and nested maps survive a rebuild with their formatting intact.
    """
    pattern = re.compile(rf"^{re.escape(key)}\s*:")
    out: list[str] = []
    capturing = False
    for line in block:
        if pattern.match(line):
            capturing = True
            out.append(line)
            continue
        if capturing:
            if (
                line.strip()
                and not line[0].isspace()
                and not line.lstrip().startswith("-")
            ):
                capturing = False
                continue
            if not line.strip():
                capturing = False
                continue
            out.append(line)
    return out


def has_usable_type(content: str) -> bool:
    """True when the page already declares a non-empty OKF `type`."""
    block, _ = split_frontmatter(content)
    return block is not None and bool(read_field(block, "type"))


def title_from_filename(path: str) -> str:
    base = re.sub(r"\.md$", "", path.rsplit("/", 1)[-1], flags=re.IGNORECASE)
    spaced = re.sub(r"[-_]+", " ", base).strip()
    return spaced[:1].upper() + spaced[1:] if spaced else base


def normalize_concept_content(content: str, rel_path: str) -> tuple[bool, str]:
    """Guarantee valid OKF front matter without destroying good data.

    Port of okf/frontmatter.ts normalizeConceptContent: a page that already has
    a usable `type` is returned untouched, however junky its optional fields.
    Otherwise the block is rebuilt from the body and flagged for agent review.
    """
    if has_usable_type(content):
        return False, content

    block, body = split_frontmatter(content)
    heading = next(
        (
            m.group(1).strip()
            for m in (re.match(r"^#\s+(.+?)\s*$", line) for line in body.split("\n"))
            if m
        ),
        None,
    )
    rebuilt = [
        "---",
        f"type: {json.dumps(DERIVED_TYPE)}",
        f"title: {json.dumps(heading or title_from_filename(rel_path))}",
        f"{GENERATED_FIELD}: true",
    ]
    for key in PRESERVED_EXTENSION_FIELDS:
        if block:
            rebuilt.extend(field_lines(block, key))
    rebuilt.append("---")
    return True, "\n".join(rebuilt) + "\n\n" + body.lstrip()


# --------------------------------------------------------------------------
# mermaid
# --------------------------------------------------------------------------


class Fence:
    """One ```mermaid fence located in a Markdown document."""

    def __init__(self, open_line: int, indent: str, marker: str):
        self.open_line, self.indent, self.marker = open_line, indent, marker
        self.close_line = -1
        self.body_lines: list[str] = []

    @property
    def body(self) -> str:
        return "\n".join(self.body_lines)


def extract_mermaid_fences(markdown: str) -> list[Fence]:
    """Extract every ```mermaid fence, ignoring ones nested in a longer fence."""
    fences: list[Fence] = []
    open_fence: Fence | None = None
    generic_marker: str | None = None

    for idx, line in enumerate(markdown.split("\n")):
        match = FENCE_RE.match(line)
        if open_fence is not None:
            if (
                match
                and len(match.group(2)) >= len(open_fence.marker)
                and not match.group(3)
            ):
                open_fence.close_line = idx
                fences.append(open_fence)
                open_fence = None
            else:
                open_fence.body_lines.append(line)
            continue
        if generic_marker is not None:
            if (
                match
                and len(match.group(2)) >= len(generic_marker)
                and not match.group(3)
            ):
                generic_marker = None
            continue
        if match and match.group(3).lower() == "mermaid":
            open_fence = Fence(idx, match.group(1), match.group(2))
        elif match and match.group(3):
            generic_marker = match.group(2)
    return fences


def heuristic_error(body: str) -> str | None:
    """Conservative syntax check used when the real mermaid parser is absent.

    Only flags near-certain breakages, so a valid diagram is never degraded.
    Port of mermaid/validate.ts heuristicError.
    """
    first = (body.strip().split() or [""])[0].lower()
    is_flowchart = first in {"flowchart", "graph"}

    if is_flowchart and (
        re.search(r"(?:^|\n|\s)end\s*[\[({]", body)
        or re.search(r"-->\s*end\s*(?:$|\n|;)", body, re.MULTILINE)
    ):
        return (
            "Heuristic: `end` is a reserved word and cannot be a flowchart node id; "
            "rename the node."
        )
    if re.search(r"[\[({][^)\]}]*;[^)\]}]*[)\]}]", body):
        return "Heuristic: a semicolon inside a label breaks rendering; rephrase the label."
    if re.search(r"[\[({][^)\]}]*[<>][^)\]}]*[)\]}]", body):
        return (
            "Heuristic: an unescaped angle bracket inside a label breaks rendering; "
            "rephrase the label."
        )
    return None


def degrade_invalid_mermaid(markdown: str) -> tuple[str, int]:
    """Convert unparseable mermaid fences to text fences, stamping the reason."""
    failures = [
        (f, err)
        for f in extract_mermaid_fences(markdown)
        if (err := heuristic_error(f.body)) is not None
    ]
    if not failures:
        return markdown, 0

    lines = markdown.split("\n")
    for fence, error in reversed(failures):
        comment = (
            f"{fence.indent}<!-- openwiki: mermaid parse failed and this diagram "
            f"was converted to a text fence so it does not break rendering. Fix the "
            f"diagram source and restore the mermaid fence. Parser error: "
            f"{error.replace('--', '-')[:400]} -->"
        )
        lines[fence.open_line : fence.close_line + 1] = [
            comment,
            f"{fence.indent}{fence.marker}text",
            *fence.body_lines,
            f"{fence.indent}{fence.marker}",
        ]
    return "\n".join(lines), len(failures)


# --------------------------------------------------------------------------
# internal links
# --------------------------------------------------------------------------


def slugify_heading(text: str) -> str:
    """GitHub-style anchor slug: lowercased, punctuation dropped, spaces hyphenated."""
    return re.sub(r"\s+", "-", re.sub(r"[^\w\s-]", "", text.strip().lower()))


def heading_anchors(content: str) -> set[str]:
    """Anchor slugs a document exposes, with GitHub's -1/-2 duplicate suffixes."""
    counts: dict[str, int] = {}
    anchors: set[str] = set()
    for line in content.split("\n"):
        match = HEADING_RE.match(line)
        if not match:
            continue
        base = slugify_heading(match.group(2))
        if not base:
            continue
        seen = counts.get(base, 0)
        counts[base] = seen + 1
        anchors.add(base if seen == 0 else f"{base}-{seen}")
    return anchors


def strip_link_stamps(content: str) -> str:
    """Drop prior broken-link stamps so a fixed link leaves no residue."""
    return "\n".join(line for line in content.split("\n") if not STAMP_RE.match(line))


def parse_destination(href: str) -> tuple[str, str | None]:
    """Split a link destination into (path, anchor), dropping any link title."""
    without_title = re.sub(r"""\s+(["']).*\1\s*$""", "", href).strip()
    path, sep, anchor = without_title.partition("#")
    return path, (anchor if sep else None)


def validate_links(
    wiki_root: Path, source: Path, content: str
) -> list[tuple[int, str, str]]:
    """Return (line, href, reason) for every broken relative link in one page."""
    anchors = heading_anchors(content)
    issues: list[tuple[int, str, str]] = []

    for lineno, line in enumerate(content.split("\n"), start=1):
        for match in LINK_RE.finditer(line):
            if match.start() > 0 and line[match.start() - 1] == "!":
                continue
            href = match.group(2).strip()
            if not href or EXTERNAL_RE.match(href):
                continue
            link_path, anchor = parse_destination(href)

            if not link_path:
                if anchor and urllib.parse.unquote(anchor) not in anchors:
                    issues.append(
                        (
                            lineno,
                            href,
                            f'heading anchor "{anchor}" does not exist in {source.name}',
                        )
                    )
                continue

            is_dir = link_path.endswith("/")
            base = wiki_root if link_path.startswith("/") else source.parent
            target = Path(os.path.normpath(base / link_path.lstrip("/")))
            if not str(target).startswith(str(wiki_root)):
                issues.append(
                    (lineno, href, f'link "{link_path}" is outside the wiki root')
                )
                continue
            if target.is_dir() if is_dir else target.is_file():
                if anchor and not is_dir:
                    target_anchors = heading_anchors(target.read_text(encoding="utf-8"))
                    if urllib.parse.unquote(anchor) not in target_anchors:
                        issues.append(
                            (
                                lineno,
                                href,
                                f'heading anchor "{anchor}" does not exist in "{link_path}"',
                            )
                        )
                continue
            kind = "directory" if is_dir else "file"
            issues.append((lineno, href, f'{kind} "{link_path}" does not exist'))
    return issues


def stamp_links(content: str, issues: list[tuple[int, str, str]]) -> str:
    """Insert a stamp above each failing link line, bottom-up."""
    if not issues:
        return content
    lines = content.split("\n")
    by_line: dict[int, list[str]] = {}
    for lineno, href, message in issues:
        by_line.setdefault(lineno, []).append(
            f"<!-- openwiki: broken internal link [{href}] {message}. "
            f"Fix the href or restore the target, then delete this comment. -->"
        )
    for lineno in sorted(by_line, reverse=True):
        lines[lineno - 1 : lineno - 1] = by_line[lineno]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# index synchronization
# --------------------------------------------------------------------------


def escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def render_links(
    heading: str, links: list[tuple[str, str, str | None]], with_description: bool
) -> str:
    """Render one sorted index section; empty string when there is nothing to list."""
    if not links:
        return ""
    items = []
    for href, label, description in sorted(links):
        item = f"- [{escape_label(label)}]({href})"
        items.append(
            f"{item} - {description}" if with_description and description else item
        )
    return f"# {heading}\n\n" + "\n".join(items)


def render_index(
    files: list[tuple[str, str, str | None]],
    directories: list[tuple[str, str, str | None]],
    is_root: bool,
) -> str:
    sections = "\n\n".join(
        filter(
            None,
            [
                render_links(FRONTMATTER_LABELS["files"], files, True),
                render_links(FRONTMATTER_LABELS["directories"], directories, False),
            ],
        )
    )
    version = '---\nokf_version: "0.1"\n---\n\n' if is_root else ""
    fallback = "# " + FRONTMATTER_LABELS["files"]
    return f"{version}{sections or fallback}\n"


# --------------------------------------------------------------------------
# passes
# --------------------------------------------------------------------------


def concept_pages(directory: Path) -> list[Path]:
    """Immediate concept pages of a directory, sorted, excluding reserved files."""
    return sorted(
        p
        for p in directory.iterdir()
        if p.is_file()
        and p.suffix.lower() == ".md"
        and not p.name.startswith(".")
        and p.name not in EXCLUDED_FILES
    )


def walk_directories(root: Path) -> list[Path]:
    """Every visible wiki directory, root included."""
    found = [root]
    for path in sorted(root.rglob("*")):
        if path.is_dir() and not any(
            part.startswith(".") for part in path.relative_to(root).parts
        ):
            found.append(path)
    return found


def normalize_file(path: Path, root: Path) -> str:
    """Normalize one concept page in place; return its (possibly new) content."""
    original = path.read_text(encoding="utf-8")
    changed, content = normalize_concept_content(original, str(path.relative_to(root)))
    if not changed:
        return content
    if protected(path, root):
        print(
            f"  [okf] SKIPPED (protected, generated elsewhere): {path.relative_to(root)}"
        )
        return original
    path.write_text(content, encoding="utf-8")
    return content


def pass_migrate(root: Path) -> int:
    """beforeAgent: bring every existing page to conformant OKF front matter."""
    repaired = 0
    for directory in walk_directories(root):
        for page in concept_pages(directory):
            before = page.read_text(encoding="utf-8")
            if normalize_file(page, root) != before:
                repaired += 1
                print(f"  [okf] repaired front matter: {page.relative_to(root)}")
    return repaired


def pass_mermaid(root: Path) -> int:
    degraded = 0
    for directory in walk_directories(root):
        for page in concept_pages(directory):
            original = page.read_text(encoding="utf-8")
            content, count = degrade_invalid_mermaid(original)
            if count and not protected(page, root):
                page.write_text(content, encoding="utf-8")
                degraded += count
                print(
                    f"  [mermaid] degraded {count} fence(s): {page.relative_to(root)}"
                )
    return degraded


def pass_indexes(root: Path) -> int:
    written = 0
    for directory in walk_directories(root):
        files: list[tuple[str, str, str | None]] = []
        for page in concept_pages(directory):
            content = normalize_file(page, root)
            block, _ = split_frontmatter(content)
            files.append(
                (
                    urllib.parse.quote(page.name, safe=""),
                    (read_field(block, "title") if block else None) or page.stem,
                    read_field(block, "description") if block else None,
                )
            )
        directories = [
            (urllib.parse.quote(child.name, safe="") + "/", child.name, None)
            for child in sorted(directory.iterdir())
            if child.is_dir() and not child.name.startswith(".")
        ]

        index_path = directory / INDEX_FILE
        content = render_index(files, directories, directory == root)
        existing = (
            index_path.read_text(encoding="utf-8") if index_path.is_file() else None
        )
        if existing != content:
            index_path.write_text(content, encoding="utf-8")
            written += 1
            print(f"  [index] wrote {index_path.relative_to(root)}")
    return written


def pass_links(root: Path) -> int:
    found = 0
    for directory in walk_directories(root):
        for page in concept_pages(directory):
            original = page.read_text(encoding="utf-8")
            cleaned = strip_link_stamps(original)
            issues = validate_links(root, page, cleaned)
            stamped = stamp_links(cleaned, issues)
            if stamped != original and not protected(page, root):
                page.write_text(stamped, encoding="utf-8")
            if issues:
                found += len(issues)
                print(f"  [links] {len(issues)} broken: {page.relative_to(root)}")
    return found


def write_last_update(
    root: Path, target: Path | None, command: str, model: str, status: str
) -> None:
    """Record run metadata the update prompt reads back as `gitHead`."""
    metadata = {
        "updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "command": command,
        "model": model,
        "status": status,
    }
    if target is not None:
        head = subprocess.run(
            ["git", "-C", str(target), "rev-parse", "HEAD"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        ).stdout.strip()
        if head:
            metadata["gitHead"] = head
    (root / ".last-update.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

BACKLOG_HEADING = re.compile(r"^(##[ \t]+Backlog)([^\n]*)$", re.M)


def pass_backlog_heading(root: Path) -> int:
    """Normalize quickstart's Backlog heading to exactly `## Backlog`.

    The official prompt asks for "a concise Backlog section in quickstart" and
    fixes no heading form, so runs vary: one wrote `## Backlog`, another wrote
    `## Backlog - known gaps, with anchors`. Anything downstream that matches the
    heading then works on one wiki and silently no-ops on the other. Any title
    text is preserved as the section's first line rather than discarded.

    Returns 1 when a heading was rewritten, 0 when already canonical or absent.
    Opt-in via --normalize-backlog: repo-wiki-converge v1 is the control for a
    running measurement, and changing shared code under it would contaminate the
    baseline it provides.
    """
    page = root / "quickstart.md"
    if not page.is_file():
        return 0
    before = page.read_text(encoding="utf-8")
    match = BACKLOG_HEADING.search(before)
    if not match or not match.group(2).strip():
        return 0
    suffix = match.group(2).strip().lstrip("-—–:").strip()
    after = (
        before[: match.start()]
        + "## Backlog"
        + (f"\n\n{suffix}" if suffix else "")
        + before[match.end() :]
    )
    # Asserted, never announced. The bug this pass exists to prevent was a
    # success message printed by a removal that had silently matched nothing.
    canonical = BACKLOG_HEADING.search(after)
    if not canonical or canonical.group(2).strip():
        print(
            f"[FAIL] backlog heading not canonical after rewrite: {page}",
            file=sys.stderr,
        )
        return 0
    page.write_text(after, encoding="utf-8")
    print(f"[backlog] heading normalized, title text kept: {suffix!r}")
    return 1


def option(argv: list[str], name: str, default: str | None = None) -> str | None:
    return (
        argv[argv.index(name) + 1]
        if name in argv and argv.index(name) + 1 < len(argv)
        else default
    )


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help"} or len(argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    command, root = argv[0], Path(argv[1]).expanduser().resolve()
    if not root.is_dir():
        print(f"[FAIL] wiki root not found: {root}", file=sys.stderr)
        return 1

    PROTECTED.update(
        argv[i + 1]
        for i, a in enumerate(argv)
        if a == "--protect" and i + 1 < len(argv)
    )
    if PROTECTED:
        print(f"[protect] never rewritten: {sorted(PROTECTED)}")

    if command == "migrate":
        print(f"[migrate] {root}")
        print(f"[report] front matter repaired: {pass_migrate(root)}")
        return 0

    if command != "finalize":
        print(
            f"[FAIL] unknown command {command!r} (expected migrate|finalize)",
            file=sys.stderr,
        )
        return 2

    target = option(argv, "--target")
    print(f"[finalize] {root}")
    degraded = pass_mermaid(root)
    indexes = pass_indexes(root)
    broken = pass_links(root)
    write_last_update(
        root,
        Path(target).expanduser().resolve() if target else None,
        option(argv, "--command", "init"),
        option(argv, "--model", "host-agent"),
        option(argv, "--status", "success"),
    )
    backlog = pass_backlog_heading(root) if "--normalize-backlog" in argv else 0
    print(
        f"[report] mermaid degraded={degraded}  indexes written={indexes}  broken links={broken}"
        f"  backlog heading normalized={backlog}"
    )
    print(
        "         broken links and degraded diagrams are stamped in place, not fatal;"
        " the next update run repairs them from the inline comments."
    )
    return 0


def _selftest() -> None:
    import tempfile

    # front matter: a usable `type` is never touched, junk optional fields and all
    good = '---\ntype: Playbook\ntitle: ""\n---\n\n# X\n'
    assert normalize_concept_content(good, "a.md") == (False, good)

    # rebuild derives the title from the first H1 and preserves RepoDoc routing
    changed, out = normalize_concept_content(
        "---\ntitle: old\ncovers:\n  - retry-backoff\n  - budgets\nrepo: o/n\n---\n\n# Real Title\nbody\n",
        "arch/overview.md",
    )
    assert changed and 'type: "Reference"' in out and 'title: "Real Title"' in out
    assert "openwiki_generated: true" in out
    assert "  - retry-backoff" in out and "repo: o/n" in out, out
    # ...and a page with no front matter at all falls back to the filename
    _, out = normalize_concept_content("no front matter\n", "data_flow-api.md")
    assert 'title: "Data flow api"' in out, out

    # mermaid: valid diagrams survive byte-for-byte; broken ones degrade with a stamp
    ok_doc = "```mermaid\nsequenceDiagram\n  A->>B: hi\n```\n"
    assert degrade_invalid_mermaid(ok_doc) == (ok_doc, 0)
    bad_doc = "```mermaid\nflowchart TD\n  end[Done]\n```\n"
    degraded, count = degrade_invalid_mermaid(bad_doc)
    assert (
        count == 1
        and "```text" in degraded
        and "openwiki: mermaid parse failed" in degraded
    )
    assert "flowchart TD" in degraded, "degrading must preserve the diagram source"
    # a mermaid example nested in a longer fence is not a real diagram
    assert (
        extract_mermaid_fences("````markdown\n```mermaid\nbroken(\n```\n````\n") == []
    )

    # heading anchors follow GitHub's duplicate-suffix rule
    assert heading_anchors("# A B\n## A B\n") == {"a-b", "a-b-1"}

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "openwiki"
        (root / "arch").mkdir(parents=True)
        (root / "quickstart.md").write_text(
            "---\ntype: Playbook\ntitle: Quickstart\ndescription: Entry point.\n---\n\n"
            "# Quickstart\n\n[arch](arch/overview.md) [gone](arch/missing.md) "
            "[anchor](arch/overview.md#nope) [ext](https://example.com)\n",
            encoding="utf-8",
        )
        (root / "arch/overview.md").write_text(
            "---\ntype: Architecture\ntitle: Overview\n---\n\n# Overview\n",
            encoding="utf-8",
        )

        assert pass_links(root) == 2, "one missing file + one missing anchor"
        body = (root / "quickstart.md").read_text(encoding="utf-8")
        assert body.count("broken internal link") == 2 and "https://example.com" in body
        # re-running is idempotent: stamps are stripped before revalidation
        assert pass_links(root) == 2
        assert (root / "quickstart.md").read_text(encoding="utf-8") == body

        pass_indexes(root)
        index = (root / "index.md").read_text(encoding="utf-8")
        assert index.startswith('---\nokf_version: "0.1"\n---'), index
        assert "- [Quickstart](quickstart.md) - Entry point." in index
        assert "# Directories\n\n- [arch](arch/)" in index
        assert (
            not (root / "arch/index.md").read_text(encoding="utf-8").startswith("---")
        )

        write_last_update(root, None, "init", "m", "success")
        assert json.loads((root / ".last-update.json").read_text())["command"] == "init"

        # A protected page keeps byte-equality with whatever generates it, even
        # though it has no front matter and would otherwise be repaired...
        generated = "# Generated\n\nno front matter, byte-equality asserted elsewhere\n"
        (root / "generated.md").write_text(generated, encoding="utf-8")
        PROTECTED.add("generated.md")
        pass_migrate(root)
        assert (root / "generated.md").read_text(encoding="utf-8") == generated
        # ...but it is still indexed, under its filename-derived label.
        pass_indexes(root)
        assert "](generated.md)" in (root / "index.md").read_text(encoding="utf-8")
        PROTECTED.discard("generated.md")

        # backlog heading: a decorated heading is normalized and its title kept...
        quick = root / "quickstart.md"
        original = quick.read_text(encoding="utf-8")
        quick.write_text(
            original + "\n## Backlog — known gaps, with anchors\n\n1. thing\n",
            encoding="utf-8",
        )
        assert pass_backlog_heading(root) == 1
        fixed = quick.read_text(encoding="utf-8")
        assert "\n## Backlog\n" in fixed, fixed
        assert "known gaps, with anchors" in fixed, (
            "title text must survive, not be discarded"
        )
        assert "1. thing" in fixed
        # ...and re-running is a no-op, so it cannot claim work it did not do
        assert pass_backlog_heading(root) == 0
        assert quick.read_text(encoding="utf-8") == fixed
        # an already-canonical heading is left alone
        quick.write_text(original + "\n## Backlog\n\n1. thing\n", encoding="utf-8")
        assert pass_backlog_heading(root) == 0
        # and a page with no Backlog section at all is untouched
        quick.write_text(original, encoding="utf-8")
        assert pass_backlog_heading(root) == 0
        assert quick.read_text(encoding="utf-8") == original

    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--selftest"]:
        _selftest()
    else:
        sys.exit(main(sys.argv[1:]))
