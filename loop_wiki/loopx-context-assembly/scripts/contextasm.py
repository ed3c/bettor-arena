#!/usr/bin/env python3
"""LoopX Context Assembly public port. Exits 0 ok, 2 refused, 64 unusable.

`assemble` renders every host projection from one IR and reports the law matrix.
`emit` writes those projections to a directory. `verify` reads a directory back
and compares the delimited law across whatever it finds there -- which is the
check that catches a projection edited after it was written.

There is no subcommand that turns a cache measurement into a claim about prompt
assembly in general, and none that renders a single host in isolation: a host
rendered alone cannot disagree with anything.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ca_common import (  # noqa: E402
    BAD,
    OK,
    USAGE,
    ContractError,
    InputError,
    find_forbidden,
    find_volatile,
    text_digest,
    normative_region,
)
from ca_contract import check_contracts, run_contract_selftest  # noqa: E402
from ca_pipeline import assemble  # noqa: E402
from ca_project import law_matrix, require_law_agreement  # noqa: E402
from ca_selftest import IR, run_selftest  # noqa: E402

DEFAULT_ROOT = Path(__file__).resolve().parents[1]


class UsageParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"FATAL: {message}", file=sys.stderr)
        raise SystemExit(USAGE)


def build_parser() -> argparse.ArgumentParser:
    root = UsageParser(description=__doc__)
    sub = root.add_subparsers(dest="operation", required=True, parser_class=UsageParser)
    for name in ("check", "selftest", "assemble", "emit", "verify"):
        parser = sub.add_parser(name)
        parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
        parser.add_argument("--output", type=Path)
        if name in ("emit", "verify"):
            parser.add_argument("--dir", type=Path, required=True)
    return root


def _emit(value: object, output: Path | None) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"WROTE {output}")


def emit_projections(target: Path) -> dict[str, object]:
    result = assemble(IR)
    target.mkdir(parents=True, exist_ok=True)
    for projection in result["projections"]:
        (target / f"{projection['host']}.md").write_text(
            projection["text"], encoding="utf-8"
        )
    (target / "assembly.json").write_text(
        json.dumps(
            {
                "assembly_digest": result["assembly_digest"],
                "law_matrix": result["law_matrix"],
                "prefix_digest": result["prefix"]["prefix_digest"],
                "budget_report": result["suffix"]["budget_report"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return result


def verify_directory(target: Path) -> dict[str, object]:
    """Read projections back off disk and compare the law across them.

    Deliberately reads the files rather than the in-memory result. A projection
    is written to disk and then read by something else; a comparison that never
    leaves the process would stay green while the file on disk said otherwise.
    """
    paths = sorted(target.glob("*.md"))
    if not paths:
        raise InputError(f"no projections found in {target}")
    projections = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        volatile = find_volatile(text)
        forbidden = find_forbidden(text)
        if volatile or forbidden:
            raise ContractError(
                f"{path.name} on disk contains {volatile + forbidden}; it was scanned "
                "clean when it was rendered, so it changed after it was written"
            )
        projections.append(
            {
                "host": path.stem,
                "normative_digest": text_digest(normative_region(text, path.name)),
            }
        )
    matrix = law_matrix(projections)
    require_law_agreement(matrix)
    return matrix


def run(args: argparse.Namespace) -> int:
    op = args.operation
    root = args.root.resolve()
    if op == "check":
        schemas, files = check_contracts(root)
        print(f"loopx-context-assembly PASS: {schemas} schemas, {files} contract files")
    elif op == "selftest":
        positive, controls = run_selftest(root)
        manifest_controls = run_contract_selftest(root)
        print(
            f"loopx-context-assembly selftest PASS: {positive} positive, {controls} "
            f"controls, {manifest_controls} manifest mutations"
        )
    elif op == "assemble":
        _emit(assemble(IR), args.output)
    elif op == "emit":
        result = emit_projections(args.dir)
        print(
            f"loopx-context-assembly EMIT: {len(result['projections'])} projections, "
            f"{result['law_matrix']['distinct_law_digests']} law"
        )
        _emit(result["law_matrix"], args.output)
    elif op == "verify":
        matrix = verify_directory(args.dir)
        print(
            f"loopx-context-assembly VERIFY: {len(matrix['hosts'])} projections read "
            f"from disk, {matrix['distinct_law_digests']} law"
        )
        _emit(matrix, args.output)
    return OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ContractError as exc:
        print(f"loopx-context-assembly RED: {exc}", file=sys.stderr)
        return BAD
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
