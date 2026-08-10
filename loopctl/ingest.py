#!/usr/bin/env python3
"""Turn an outside document or repo into a packet the micro loop already accepts.

    ingest.py packet --source PATH --task TEXT --out DIR [--kind ...] [--packet-id ID]
    ingest.py --selftest

The micro loop has taken a .md or a repo directory since it was written:
contracts.ts carries source_kind x source_path, and reduce.ts really reads them
— line-wise for a document, file-wise for a repo. What was missing was a way to
hand it one without hand-writing a packet, which is the reading that ends in
someone editing the loop to fit their call site.

.pdf and .html need extraction first, and it deliberately does NOT happen inside
the factory. That sandbox has zero runtime dependencies and its whole claim is
`git archive | bun install --frozen-lockfile | verify`; making it shell out to
poppler would move the claim to "works where poppler is installed", and it would
stay green here forever regardless. Extraction is a boundary concern, so it lives
here, and the factory is untouched.

Traceability survives extraction because the extraction is recorded, not hidden:
provenance.json carries the original path and sha256, the exact extractor argv
and version, and the extracted sha256. An evidence line reading extracted.txt:42
is resolvable back through that record. Without it, extraction would quietly
replace the source with a derived artifact wearing the source's name.

An unknown format is FATAL, never "read it as text": a .docx decoded as utf-8
produces lines that look exactly like evidence and are noise. An absent extractor
is FATAL too, naming the tool and how to install it — the gate judges with the
tool it has or refuses, it never guesses.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

SCHEMA = "perfect-seed-input@1.0.0"
SOURCE_KINDS = ("dr", "gcr", "repo", "grill-me")
# contracts.ts:54 — the declared shape for a source with no repo provenance.
# Reusing it rather than inventing one keeps refs_status truthful: an outside
# document is genuinely "sentinel", not "declared".
SENTINEL_REF = {
    "repo": "unknown",
    "commit": "0000000",
    "path": "unmigrated/unknown",
    "anchor": "pre-source-refs",
}
PASSTHROUGH = {".md", ".txt", ".markdown"}


def fatal(msg: str) -> None:
    print(f"ingest FATAL: {msg}", file=sys.stderr)
    raise SystemExit(64)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class _TextExtractor(HTMLParser):
    """HTML to text on the stdlib, which is already a dependency of everything here.

    script and style hold source code, not prose; keeping them would put minified
    JavaScript into the evidence set line by line.
    """

    SKIP = {"script", "style", "head", "noscript"}
    BLOCK = {
        "p",
        "div",
        "br",
        "li",
        "tr",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "section",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skipping = 0

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001 - stdlib signature
        if tag in self.SKIP:
            self._skipping += 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP and self._skipping:
            self._skipping -= 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skipping and data.strip():
            self.parts.append(re.sub(r"[ \t\r\f\v]+", " ", data.strip()))

    def text(self) -> str:
        joined = "".join(p if p == "\n" else p + " " for p in self.parts)
        return re.sub(r"\n{2,}", "\n", joined).strip() + "\n"


def extract(source: Path, outdir: Path) -> tuple[Path, dict]:
    """Return (path the packet should point at, provenance record)."""
    suffix = source.suffix.lower()
    # The directory case comes first: a repo source has no bytes of its own to
    # hash, and reaching for them is an IsADirectoryError rather than a verdict.
    if source.is_dir():
        return source, {
            "original_path": str(source),
            "original_sha256": None,
            "format": "directory",
            "extractor": None,
            "note": "a repo source is hashed file by file by the factory's own reducer, not here",
        }
    original = {
        "original_path": str(source),
        "original_sha256": sha256_file(source),
        "original_bytes": source.stat().st_size,
        "format": suffix or "(none)",
    }
    if suffix in PASSTHROUGH:
        return source, {
            **original,
            "extractor": None,
            "note": "text already; the packet points at the original",
        }

    outdir.mkdir(parents=True, exist_ok=True)
    target = outdir / "extracted.txt"

    if suffix in {".html", ".htm"}:
        parser = _TextExtractor()
        parser.feed(source.read_text(encoding="utf-8", errors="replace"))
        target.write_text(parser.text(), encoding="utf-8")
        extractor = {
            "tool": "python:html.parser",
            "argv": None,
            "version": sys.version.split()[0],
        }
    elif suffix == ".pdf":
        # PDFTOTEXT is a seam for the selftest's absent-tool control, not a
        # caller knob: pointing it elsewhere changes what produced the evidence.
        binary = os.environ.get("PDFTOTEXT", "pdftotext")
        argv = [binary, "-layout", str(source), str(target)]
        try:
            proc = subprocess.run(argv, capture_output=True, text=True, check=False)
        except OSError:
            fatal(
                f"{binary} not found — .pdf extraction needs poppler "
                "(brew install poppler). No fallback: a PDF decoded as text is noise "
                "that looks like evidence."
            )
        if proc.returncode != 0:
            fatal(
                f"{binary} failed on {source} (exit {proc.returncode}): {proc.stderr.strip()[:200]}"
            )
        version = subprocess.run(
            [binary, "-v"], capture_output=True, text=True, check=False
        ).stderr.splitlines()
        extractor = {
            "tool": binary,
            "argv": argv,
            "version": version[0] if version else "unknown",
        }
    else:
        fatal(
            f"unsupported source format {suffix or '(none)'} for {source}. "
            "Supported: .md/.txt (as-is), .html/.htm, .pdf, or a directory. "
            "Reading an unknown format as text produces lines that look like evidence "
            "and are not."
        )

    return target, {
        **original,
        "extractor": extractor,
        "extracted_path": str(target),
        "extracted_sha256": sha256_file(target),
        "extracted_bytes": target.stat().st_size,
    }


def slug(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", text).strip("-")
    cleaned = re.sub(r"-{2,}", "-", cleaned)[:60]
    return cleaned or "source"


def build_packet(
    source: Path, task: str, kind: str, outdir: Path, packet_id: str | None
) -> Path:
    if kind not in SOURCE_KINDS:
        fatal(f"unknown --kind {kind!r}; declared: {list(SOURCE_KINDS)}")
    if not source.exists():
        fatal(f"source not found: {source}")
    if kind == "repo" and not source.is_dir():
        fatal(f"--kind repo needs a directory, got a file: {source}")
    if kind != "repo" and source.is_dir():
        fatal(
            f"--kind {kind} needs a file, got a directory: {source} (use --kind repo)"
        )

    outdir.mkdir(parents=True, exist_ok=True)
    resolved, provenance = extract(source, outdir)
    pid = packet_id or f"ingest-{slug(source.stem or source.name)}"
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{2,80}", pid):
        fatal(f"packet_id {pid!r} does not match the factory's contract")

    packet = {
        "schema_version": SCHEMA,
        "packet_id": pid,
        "packet_state": "admitted",
        "source_kind": kind,
        "source_path": str(resolved.resolve()),
        "task": task,
        "fixed_prompt_context": ["PROMPT.md", "modules/semantic-truth-context.md"],
        "emergent_prompt_context": "N/A-none",
        "source_refs": [SENTINEL_REF],
        "human_gate": "required_before_seed_admit",
    }
    (outdir / "provenance.json").write_text(
        json.dumps(
            {
                "schema_version": "bettor-arena-ingest-provenance@1.0.0",
                "packet_id": pid,
                "source_kind": kind,
                **provenance,
                "refs_note": "source_refs is the factory's declared sentinel: an outside "
                "document has no repo provenance, and claiming one would be a fabricated ref",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    packet_path = outdir / "packet.json"
    packet_path.write_text(
        json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return packet_path


def main(argv: list[str]) -> int:
    if argv[:1] == ["--selftest"]:
        return _selftest()
    if not argv or argv[0] != "packet":
        print(__doc__.strip(), file=sys.stderr)
        return 64
    opts: dict[str, str] = {}
    rest = argv[1:]
    while rest:
        flag = rest.pop(0)
        if not flag.startswith("--") or not rest:
            print(__doc__.strip(), file=sys.stderr)
            return 64
        opts[flag] = rest.pop(0)
    for required in ("--source", "--task", "--out"):
        if required not in opts:
            fatal(f"missing required {required}")
    path = build_packet(
        Path(opts["--source"]).expanduser().resolve(),
        opts["--task"],
        opts.get("--kind", "dr"),
        Path(opts["--out"]).expanduser().resolve(),
        opts.get("--packet-id"),
    )
    print(path)
    return 0


# ---------------------------------------------------------------- selftest

MINIMAL_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]/Contents 4 0 R"
    b"/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    b"4 0 obj<</Length 52>>stream\nBT /F1 12 Tf 20 100 Td (HELLO EVIDENCE LINE) Tj ET\n"
    b"endstream\nendobj\n5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"trailer<</Root 1 0 R>>\n"
)


def _selftest() -> int:
    import tempfile

    red = 0

    def case(name: str, got, want) -> None:
        nonlocal red
        if got != want:
            print(
                f"SELFTEST case failed — {name}: got {got!r}, want {want!r}",
                file=sys.stderr,
            )
            red = 1

    with tempfile.TemporaryDirectory() as td:
        base = Path(td)

        # HTML: prose survives, script and style do not become evidence lines.
        html = base / "doc.html"
        html.write_text(
            "<html><head><style>.a{color:red}</style></head><body>"
            "<h1>Title Line</h1><script>var x=1;</script>"
            "<p>Body prose here.</p><p>Second para.</p></body></html>",
            encoding="utf-8",
        )
        packet_path = build_packet(html, "t", "dr", base / "outh", None)
        text = (base / "outh" / "extracted.txt").read_text(encoding="utf-8")
        case("html-keeps-prose", "Body prose here." in text, True)
        case("html-keeps-heading", "Title Line" in text, True)
        case("html-drops-script", "var x=1" in text, False)
        case("html-drops-style", "color:red" in text, False)
        prov = json.loads(
            (base / "outh" / "provenance.json").read_text(encoding="utf-8")
        )
        case(
            "provenance-keeps-original-sha", prov["original_sha256"], sha256_file(html)
        )
        case(
            "provenance-names-extractor",
            prov["extractor"]["tool"],
            "python:html.parser",
        )
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        case(
            "packet-points-at-extracted",
            packet["source_path"].endswith("extracted.txt"),
            True,
        )
        case("packet-uses-declared-sentinel", packet["source_refs"], [SENTINEL_REF])

        # PDF: the real extractor, on a real (minimal) PDF.
        pdf = base / "doc.pdf"
        pdf.write_bytes(MINIMAL_PDF)
        build_packet(pdf, "t", "dr", base / "outp", None)
        pdf_text = (base / "outp" / "extracted.txt").read_text(encoding="utf-8")
        case("pdf-extracts-text", "HELLO EVIDENCE LINE" in pdf_text, True)

        # An absent extractor is FATAL, never a silent fallback to raw bytes.
        os.environ["PDFTOTEXT"] = "/nonexistent/pdftotext"
        try:
            build_packet(pdf, "t", "dr", base / "outp2", None)
            case("absent-extractor-is-fatal", "returned", "SystemExit 64")
        except SystemExit as exc:
            case("absent-extractor-is-fatal", exc.code, 64)
        finally:
            del os.environ["PDFTOTEXT"]

        # Markdown passes through: the packet must point at the ORIGINAL, or the
        # evidence anchors move for no reason.
        md = base / "note.md"
        md.write_text("# hi\nline two\n", encoding="utf-8")
        p = json.loads(
            build_packet(md, "t", "dr", base / "outm", None).read_text(encoding="utf-8")
        )
        case("md-passthrough-points-at-original", p["source_path"], str(md.resolve()))

        # A directory is the repo kind; a file is not, and each mismatch is named.
        d = base / "adir"
        (d / "sub").mkdir(parents=True)
        (d / "sub" / "f.txt").write_text("x\n", encoding="utf-8")
        p = json.loads(
            build_packet(d, "t", "repo", base / "outd", None).read_text(
                encoding="utf-8"
            )
        )
        case("repo-kind-points-at-directory", p["source_path"], str(d.resolve()))
        for label, src, kind in (
            ("repo-kind-on-file", md, "repo"),
            ("doc-kind-on-dir", d, "dr"),
        ):
            try:
                build_packet(src, "t", kind, base / "outx", None)
                case(label, "returned", "SystemExit 64")
            except SystemExit as exc:
                case(label, exc.code, 64)

        # An unknown format must refuse rather than decode noise into evidence.
        odd = base / "thing.docx"
        odd.write_bytes(b"PK\x03\x04binary")
        try:
            build_packet(odd, "t", "dr", base / "outz", None)
            case("unknown-format-is-fatal", "returned", "SystemExit 64")
        except SystemExit as exc:
            case("unknown-format-is-fatal", exc.code, 64)

    print("SELFTEST " + ("GREEN" if not red else "RED"))
    return red


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
