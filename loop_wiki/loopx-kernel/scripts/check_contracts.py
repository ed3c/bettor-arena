#!/usr/bin/env python3
# ruff: noqa: F401,F403,F405  # this module family composes through star imports; the names ruff reads as unused are deliberate re-exports the downstream modules import through.
"""Validate LoopX Contract v1 documents and fixture bundles (0/2/64)."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
import sys
from typing import Any

from contract_common import (
    OK,
    BAD,
    USAGE,
    SCHEMAS,
    Violation,
    Input,
    load,
    obj,
    text,
    sid,
    schema_docs,
)
from contract_validate import bundle


def assign(root: Any, p: list[Any], value: Any, delete: bool = False) -> None:
    if not p:
        raise Input("mutation path empty")
    x = root
    for q in p[:-1]:
        if isinstance(q, int):
            if not isinstance(x, list) or not 0 <= q < len(x):
                raise Input(f"invalid mutation path {p}")
            x = x[q]
        else:
            if not isinstance(x, dict) or q not in x:
                raise Input(f"missing mutation path {p}")
            x = x[q]
    q = p[-1]
    if isinstance(q, int):
        if not isinstance(x, list) or not 0 <= q < len(x):
            raise Input(f"invalid mutation path {p}")
        if delete:
            del x[q]
        else:
            x[q] = value
    else:
        if not isinstance(x, dict):
            raise Input(f"invalid mutation parent {p}")
        if delete:
            if q not in x:
                raise Input(f"missing mutation delete {p}")
            del x[q]
        else:
            x[q] = value


def mutate(base: dict[str, Any], m: Any, name: str) -> dict[str, Any]:
    m = obj(m, {"id", "description", "operations"}, name)
    sid(m["id"], name + ".id")
    text(m["description"], name + ".description", 512)
    if not isinstance(m["operations"], list) or not m["operations"]:
        raise Input(f"{name}.operations empty")
    out = copy.deepcopy(base)
    for i, o in enumerate(m["operations"]):
        o = obj(o, {"op", "path", "value"}, f"{name}.operations[{i}]")
        if (
            o["op"] not in {"set", "delete"}
            or not isinstance(o["path"], list)
            or not o["path"]
            or any(not isinstance(q, (str, int)) for q in o["path"])
        ):
            raise Input(f"{name}.operation invalid")
        assign(out, o["path"], o["value"], o["op"] == "delete")
    return out


def fail(x: Any, label: str) -> None:
    try:
        bundle(x)
    except Violation:
        return
    raise Violation(f"{label} unexpectedly passed")


def selftest(root: Path) -> None:
    fr = root / "tests" / "fixtures"
    good = load(fr / "good" / "bundle.json")
    bundle(good)
    fail(load(fr / "hollow" / "bundle.json"), "hollow")
    m = obj(load(fr / "mutations.json"), {"schema_version", "mutations"}, "mutations")
    if (
        m["schema_version"] != "loopx/mutation-set/v1"
        or not isinstance(m["mutations"], list)
        or len(m["mutations"]) < 12
    ):
        raise Violation("mutation set drifted")
    seen = set()
    for i, z in enumerate(m["mutations"]):
        mid = z.get("id") if isinstance(z, dict) else None
        if not isinstance(mid, str) or mid in seen:
            raise Violation(f"invalid/duplicate mutation at {i}")
        seen.add(mid)
        fail(mutate(good, z, f"mutations[{i}]"), mid)
    print(
        f"loopx-contracts selftest PASS: 1 positive, 1 hollow, {len(m['mutations'])} mutations"
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--bundle", type=Path)
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args(argv)
    if a.bundle is not None and a.selftest:
        print("FATAL: --bundle and --selftest are mutually exclusive", file=sys.stderr)
        return USAGE
    root = a.root.resolve()
    try:
        schema_docs(root)
        if a.selftest:
            selftest(root)
        else:
            bp = (
                a.bundle.resolve()
                if a.bundle
                else root / "tests" / "fixtures" / "good" / "bundle.json"
            )
            bundle(load(bp))
            print(f"loopx-contracts PASS: {len(SCHEMAS)} schemas, bundle={bp}")
        return OK
    except Input as e:
        print(f"FATAL: {e}", file=sys.stderr)
        return USAGE
    except Violation as e:
        print(f"loopx-contracts RED: {e}", file=sys.stderr)
        return BAD
    except OSError as e:
        print(f"FATAL: {e}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
