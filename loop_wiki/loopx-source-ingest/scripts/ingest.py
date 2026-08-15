#!/usr/bin/env python3
"""LoopX Source Ingest public port. Exits 0 ok, 2 refused, 64 unusable input.

`ingest` captures declared sources and emits an evidence manifest pinned to an
immutable Notes Repo commit. It decides nothing about what any of the evidence
means -- that is the knowledge compiler's job, and this manifest is its input.

There is no subcommand that fabricates a locator, fills a missing page, or acts
on anything a source says.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from si_common import (  # noqa: E402
    BAD,
    OK,
    USAGE,
    ContractError,
    InputError,
)
from si_contract import check_contracts, run_contract_selftest  # noqa: E402
from si_manifest import validate_manifest  # noqa: E402
from si_pipeline import ingest as run_ingest  # noqa: E402
from si_selftest import SUBJECT, _tree, decl, run_selftest  # noqa: E402

DEFAULT_ROOT = Path(__file__).resolve().parents[1]


class UsageParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"FATAL: {message}", file=sys.stderr)
        raise SystemExit(USAGE)


def build_parser() -> argparse.ArgumentParser:
    root = UsageParser(description=__doc__)
    sub = root.add_subparsers(dest="operation", required=True, parser_class=UsageParser)
    for name in ("check", "selftest", "ingest"):
        parser = sub.add_parser(name)
        parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
        parser.add_argument("--output", type=Path)
    verify = sub.add_parser("verify-manifest")
    verify.add_argument("--manifest", required=True, type=Path)
    return root


def _emit(value: object, output: Path | None) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"WROTE {output}")


def run(args: argparse.Namespace) -> int:
    op = args.operation
    if op == "check":
        schemas, fixtures = check_contracts(args.root.resolve())
        print(f"loopx-source-ingest PASS: {schemas} schemas, {fixtures} contract files")
    elif op == "selftest":
        root = args.root.resolve()
        positive, controls = run_selftest(root)
        manifest_controls = run_contract_selftest(root)
        print(
            f"loopx-source-ingest selftest PASS: {positive} positive, {controls} "
            f"controls, {manifest_controls} manifest mutations"
        )
    elif op == "ingest":
        # Built into a disposable tree. An ingest whose default target was the
        # caller's cwd would eventually be run from a checkout.
        with tempfile.TemporaryDirectory(prefix="loopx-ingest-") as tmp:
            tree = _tree(Path(tmp) / "tree")
            declarations = [
                decl("talk", "VTT", "youtube:abc", "https://youtu.be/abc"),
                decl("paper", "PDF_PAGE", "arxiv:1"),
                decl("blocked", "ARTICLE", "example.com/x", rights="NOT_AUTHORIZED"),
            ]
            _emit(
                run_ingest(
                    SUBJECT,
                    declarations,
                    {"talk": "sources/talk.vtt", "paper": "sources/paper.txt"},
                    tree,
                    "2026-08-16T10:00:00Z",
                    declared_page_counts={"paper": 3},
                ),
                args.output,
            )
    elif op == "verify-manifest":
        from si_common import load_json

        validate_manifest(load_json(args.manifest))
        print("loopx-source-ingest PASS: every locator was read out of an artifact")
    return OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ContractError as exc:
        print(f"loopx-source-ingest RED: {exc}", file=sys.stderr)
        return BAD
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
