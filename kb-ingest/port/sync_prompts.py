#!/usr/bin/env python3
"""Extract OpenWiki's official agent prompts verbatim into local markdown assets.

Why a script instead of hand-copied markdown: the claim this port rests on is
"the prompt text is byte-identical to langchain-ai/openwiki". Hand-copying ~1000
lines makes that claim unfalsifiable after the first typo. Re-running this
against a fresh openwiki checkout regenerates every asset, so `git diff` is the
proof, and upgrading to a newer openwiki is one command.

The extracted text is wrapped in OPENWIKI-OFFICIAL:BEGIN/END markers so the
comparators — `--check` here and the module gate's check_prompt_assets()
(../check_repo_wiki_converge.py) — can re-derive it and compare, and so
skill-bettor's own appendices can never leak into the verbatim region.

Usage:
    python3 kb-ingest/port/sync_prompts.py <openwiki_repo> [--check]

    --check  Regenerate in memory and fail (exit 1) if any file is stale,
             instead of writing. Use in CI / the migration gate.

Exit codes: 0 ok · 1 stale (--check) or extraction failure · 2 bad usage
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# This generator is non-official and lives beside the other skill-bettor additions;
# it writes into the sibling openwiki/ directory, which holds upstream bytes ONLY.
HERE = Path(__file__).resolve().parent.parent / "openwiki"

BEGIN = "<!-- OPENWIKI-OFFICIAL:BEGIN -->"
END = "<!-- OPENWIKI-OFFICIAL:END -->"

# Placeholder values chosen by this port. They mirror prompt.ts for a run with no
# --language and no .openwikiignore, which is the only configuration this port
# supports. Each is quoted from the formatter it comes from so a reviewer can
# diff them against src/agent/prompt.ts without reading TypeScript.
PLACEHOLDERS = {
    # formatLanguageInstructions(undefined) -> ""
    "{OUTPUT_LANGUAGE_INSTRUCTIONS}": "",
    # formatGitHistoryHint(inactive)
    "{GIT_HISTORY_HINT}": (
        "Read git history when it helps establish repository context or "
        "explain why code exists. "
    ),
    # formatDiscoveryInstruction(inactive)
    "{DISCOVERY_INSTRUCTION}": (
        "- Do not call glob with **/* from the root. Use targeted discovery by "
        "directory and extension. Prefer shell commands like rg --files with "
        "excludes for .git, node_modules, dist, build, cache directories, and "
        "existing generated wiki output."
    ),
    # formatOpenWikiIgnoreInstructions(inactive) -> "\n"
    "{OPENWIKIIGNORE_INSTRUCTIONS}": "\n",
}

# createLinkIntegrityInstructions(), appended by createSystemPrompt() to every
# non-chat system prompt.
LINK_INTEGRITY = """
Link integrity:
- Prefer relative Markdown links to existing wiki pages and stable heading anchors. Do not invent destinations that are not written in the same run.
- OpenWiki validates relative internal links and heading anchors after the run. Broken links are left in place and marked with an HTML comment starting with "openwiki: broken internal link", so the run completes and a later update can self-correct. If you find such a comment, repair the href or restore the target page using the reason in the comment, then delete the comment.
"""

# (output basename, source file, anchor text preceding the template literal,
#  append link-integrity?)
SYSTEM_PROMPTS = [
    ("init.system.md", "src/agent/prompts/code.ts", "  init: `", True),
    ("update.system.md", "src/agent/prompts/code.ts", "  update: `", True),
]
USER_PROMPTS = [
    ("user.init.md", "src/agent/prompts/code.ts", "  init: `", False),
    ("user.update.md", "src/agent/prompts/code.ts", "  update: `", False),
]
SUBAGENTS = [
    (
        "subagents/skeleton-critic.md",
        "src/agent/skeleton_critic.ts",
        "const SKELETON_CRITIC_DESCRIPTION =\n  \"",
        "const SKELETON_CRITIC_SYSTEM_PROMPT = `",
    ),
    (
        "subagents/question-finder.md",
        "src/agent/wiki_qa_subagents.ts",
        '    "Inspects repository source',
        None,  # located positionally below
    ),
]


def read_template_literal(text: str, start: int) -> str:
    """Return the template literal beginning at `start` (the char after a backtick).

    Handles backslash escapes so an escaped backtick inside the literal does not
    terminate it. Fails loud rather than returning a truncated prompt.
    """
    out: list[str] = []
    i = start
    while i < len(text):
        ch = text[i]
        if ch == "\\":
            nxt = text[i + 1] if i + 1 < len(text) else ""
            out.append({"`": "`", "\\": "\\", "$": "$", "n": "\n", "t": "\t"}.get(nxt, "\\" + nxt))
            i += 2
            continue
        if ch == "`":
            return "".join(out)
        out.append(ch)
        i += 1
    raise ValueError(f"unterminated template literal starting at offset {start}")


def literal_after(text: str, anchor: str, source: str) -> str:
    """Extract the template literal that follows `anchor` (which ends with a backtick)."""
    idx = text.find(anchor)
    if idx == -1:
        raise ValueError(f"anchor {anchor!r} not found in {source} — openwiki layout changed")
    return read_template_literal(text, idx + len(anchor))


def double_quoted_after(text: str, anchor: str, source: str) -> str:
    """Extract a plain double-quoted string literal that starts at `anchor`'s quote."""
    idx = text.find(anchor)
    if idx == -1:
        raise ValueError(f"anchor {anchor!r} not found in {source} — openwiki layout changed")
    start = text.index('"', idx + len(anchor) - 1) + 1
    out: list[str] = []
    i = start
    while i < len(text):
        ch = text[i]
        if ch == "\\":
            out.append({'"': '"', "\\": "\\", "n": "\n"}.get(text[i + 1], text[i + 1]))
            i += 2
            continue
        if ch == '"':
            return "".join(out)
        out.append(ch)
        i += 1
    raise ValueError("unterminated string literal")


def apply_placeholders(prompt: str) -> str:
    """Apply the same single-shot replacements createSystemPrompt() performs.

    str.replace in JS replaces only the FIRST occurrence for a string pattern.
    Python's str.replace replaces all, so each substitution is capped at 1 to
    stay faithful. {DISCOVERY_INSTRUCTION} and friends appear once per prompt in
    the current source; the cap makes a future duplicate fail visibly (an
    un-substituted placeholder is obvious) rather than silently diverge.
    """
    for key, value in PLACEHOLDERS.items():
        prompt = prompt.replace(key, value, 1)
    return prompt.strip()


def build(repo: Path) -> dict[str, str]:
    """Build every generated asset's full file content, keyed by relative path."""
    sha = git_sha(repo)
    code = (repo / "src/agent/prompts/code.ts").read_text(encoding="utf-8")
    critic_src = (repo / "src/agent/skeleton_critic.ts").read_text(encoding="utf-8")
    qa_src = (repo / "src/agent/wiki_qa_subagents.ts").read_text(encoding="utf-8")

    sys_start = code.index("export const CODE_SYSTEM_PROMPTS")
    user_start = code.index("export const CODE_USER_PROMPTS")
    sys_block, user_block = code[sys_start:user_start], code[user_start:]

    files: dict[str, str] = {}

    for name, key in (("init.system.md", "init"), ("update.system.md", "update")):
        body = apply_placeholders(literal_after(sys_block, f"  {key}: `", "code.ts"))
        body = f"{body}\n\n{LINK_INTEGRITY.strip()}"
        files[name] = wrap(
            body, sha, f"src/agent/prompts/code.ts CODE_SYSTEM_PROMPTS.{key}"
            " + createLinkIntegrityInstructions()")

    for name, key in (("user.init.md", "init"), ("user.update.md", "update")):
        files[name] = wrap(
            literal_after(user_block, f"  {key}: `", "code.ts").strip(),
            sha, f"src/agent/prompts/code.ts CODE_USER_PROMPTS.{key}")

    files["subagents/skeleton-critic.md"] = subagent(
        sha, "src/agent/skeleton_critic.ts",
        double_quoted_after(critic_src, "const SKELETON_CRITIC_DESCRIPTION =\n  \"", "skeleton_critic.ts"),
        literal_after(critic_src, "const SKELETON_CRITIC_SYSTEM_PROMPT = `", "skeleton_critic.ts"))

    finder_start = qa_src.index("const WIKI_QUESTION_FINDER")
    verifier_start = qa_src.index("const WIKI_ANSWER_VERIFIER")
    finder_src, verifier_src = qa_src[finder_start:verifier_start], qa_src[verifier_start:]

    files["subagents/question-finder.md"] = subagent(
        sha, "src/agent/wiki_qa_subagents.ts WIKI_QUESTION_FINDER",
        double_quoted_after(finder_src, "  description:\n    \"", "wiki_qa_subagents.ts"),
        literal_after(finder_src, "  systemPrompt: `", "wiki_qa_subagents.ts"))

    files["subagents/answer-verifier.md"] = subagent(
        sha, "src/agent/wiki_qa_subagents.ts WIKI_ANSWER_VERIFIER",
        double_quoted_after(verifier_src, "  description:\n    \"", "wiki_qa_subagents.ts"),
        literal_after(verifier_src, "  systemPrompt: `", "wiki_qa_subagents.ts"))

    return files


def subagent(sha: str, source: str, description: str, prompt: str) -> str:
    """Render a subagent asset: its dispatch description plus its system prompt."""
    return wrap(f"## description\n\n{description.strip()}\n\n## systemPrompt\n\n{prompt.strip()}",
                sha, source)


def wrap(body: str, sha: str, source: str) -> str:
    """Wrap verbatim official text in provenance + extractable markers."""
    return (
        f"<!-- GENERATED by kb-ingest/port/sync_prompts.py — DO NOT EDIT BY HAND.\n"
        f"     upstream: langchain-ai/openwiki @ {sha}\n"
        f"     source:   {source}\n"
        f"     Everything between the OFFICIAL markers is upstream text with prompt.ts\n"
        f"     placeholders resolved for: no --language, no .openwikiignore.\n"
        f"     skill-bettor additions live in kb-ingest/port/, never inside the markers. -->\n"
        f"{BEGIN}\n{body}\n{END}\n"
    )


def extract_official(content: str) -> str:
    """Return just the verbatim region of a generated asset."""
    start = content.index(BEGIN) + len(BEGIN) + 1
    return content[start:content.index(END)].rstrip("\n")


def git_sha(repo: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() or "unknown"


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    repo = Path(argv[0]).expanduser().resolve()
    check = "--check" in argv[1:]
    if not (repo / "src/agent/prompts/code.ts").is_file():
        print(f"[FAIL] not an openwiki checkout: {repo}", file=sys.stderr)
        return 1

    try:
        files = build(repo)
    except (ValueError, OSError) as exc:
        print(f"[FAIL] extraction failed: {exc}", file=sys.stderr)
        return 1

    stale = []
    for rel, content in sorted(files.items()):
        target = HERE / rel
        current = target.read_text(encoding="utf-8") if target.is_file() else None
        if current == content:
            continue
        stale.append(rel)
        if not check:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

    if check:
        if stale:
            print(f"[STALE] regenerate with sync_prompts.py: {', '.join(stale)}", file=sys.stderr)
            return 1
        print(f"[ok] {len(files)} prompt assets match openwiki @ {git_sha(repo)}")
        return 0

    print(f"[ok] wrote {len(stale)} / {len(files)} assets from openwiki @ {git_sha(repo)}")
    return 0


def _selftest() -> None:
    """Round-trip the parser on the escape cases that actually occur upstream."""
    assert read_template_literal("`a\\`b`", 1) == "a`b"
    assert read_template_literal("plain`", 0) == "plain"
    assert apply_placeholders("x{GIT_HISTORY_HINT}y").startswith("xRead git history")
    assert extract_official(wrap("BODY", "sha", "src")) == "BODY"
    assert double_quoted_after('const D =\n  "a\\"b";', 'const D =\n  "', "t") == 'a"b'
    try:
        read_template_literal("no terminator", 0)
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("unterminated literal must fail loud")
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--selftest"]:
        _selftest()
    else:
        sys.exit(main(sys.argv[1:]))
