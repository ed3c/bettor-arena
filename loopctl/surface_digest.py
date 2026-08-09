#!/usr/bin/env python3
"""The external surface's canonical digest, and the relock that guards it.

Two jobs live behind one definition of "surface", which is why they share a file:
what an outside caller may SAY. That is the loops, the modes, and each command's
required and optional flags — nothing else. Which file implements a command, what
it writes, how it is invoked and every word of prose are internal and excluded on
purpose, so ordinary internal iteration cannot move this number.

    surface_digest.py digest <contract>            print the digest
    surface_digest.py check  <contract> <lock>     0 match · 2 drift
    surface_digest.py relock <contract> <lock>     rewrite the lock, versioned

relock refuses while surface_version still matches the lock's: a changed promise
has to be a versioned promise, or callers pinning a version get a different
surface under the same name.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def surface(contract: dict) -> list[dict]:
    """Only the fields a caller can depend on, in a canonical order."""
    return sorted(
        (
            {
                "loop": c["loop"],
                "mode": c["mode"],
                "required": sorted(c["required"]),
                "optional": sorted(c["optional"]),
                "mcp_exposed": c.get("mcp_exposed", True),
                "mcp_carrier": (
                    {
                        key: c["mcp_carrier"][key]
                        for key in ("kind", "max_request_bytes", "input_schema")
                        if key in c["mcp_carrier"]
                    }
                    if c.get("mcp_carrier")
                    else None
                ),
            }
            for c in contract["commands"]
        ),
        key=lambda c: (c["loop"], c["mode"]),
    )


def digest(contract: dict) -> str:
    canonical = json.dumps(surface(contract), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def read_lock(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__.strip(), file=sys.stderr)
        return 64
    cmd = argv[0]
    if cmd == "--selftest":
        return _selftest()
    contract = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    if cmd == "digest":
        print(digest(contract))
        return 0
    lock = read_lock(Path(argv[2]))
    now, declared = digest(contract), contract["surface_version"]
    if cmd == "check":
        if not lock:
            print("surface: no surface.lock — the promise is unpinned", file=sys.stderr)
            return 2
        if lock.get("semantic_digest") != now:
            print(
                f"surface: the external surface changed (locked {lock.get('semantic_digest', '?')[:12]}, "
                f"now {now[:12]}). Bump surface_version in contract.json, then run "
                "`sh loopctl/loopctl.sh surface-relock`.",
                file=sys.stderr,
            )
            return 2
        if lock.get("surface_version") != declared:
            print(
                f"surface: surface_version says {declared} but the lock pins "
                f"{lock.get('surface_version')} for the same surface — relock or restore",
                file=sys.stderr,
            )
            return 2
        return 0
    if cmd == "relock":
        if (
            lock.get("semantic_digest") == now
            and lock.get("surface_version") == declared
        ):
            print(f"surface: already locked at {declared} ({now[:12]}); nothing to do")
            return 0
        if (
            lock
            and lock.get("semantic_digest") != now
            and lock.get("surface_version") == declared
        ):
            print(
                f"surface FATAL: the surface changed but surface_version is still {declared}. "
                "A changed promise must be a versioned promise, or a caller pinning this "
                "version gets a different surface under the same name.",
                file=sys.stderr,
            )
            return 64
        Path(argv[2]).write_text(
            f"surface_version={declared}\nsemantic_digest={now}\n", encoding="utf-8"
        )
        print(
            f"surface: relocked {lock.get('surface_version', 'none')} "
            f"({lock.get('semantic_digest', 'none')[:12]}) -> {declared} ({now[:12]})"
        )
        return 0
    print(__doc__.strip(), file=sys.stderr)
    return 64


# ---------------------------------------------------------------- selftest


def _selftest() -> int:
    red = 0

    def case(name: str, got, want) -> None:
        nonlocal red
        if got != want:
            print(
                f"SELFTEST case failed — {name}: got {got}, want {want}",
                file=sys.stderr,
            )
            red = 1

    base = {
        "surface_version": "1.0.0",
        "commands": [
            {
                "loop": "a",
                "mode": "run",
                "target": "x.sh",
                "required": ["--in"],
                "optional": [],
                "writes": ["out"],
            }
        ],
    }
    d0 = digest(base)

    # Internal iteration must NOT move the surface: target, writes and prose are
    # exactly the things a repo changes every week.
    moved = json.loads(json.dumps(base))
    moved["commands"][0]["target"] = "somewhere/else.sh"
    moved["commands"][0]["writes"] = ["a totally different place"]
    moved["purpose"] = ["rewritten prose"]
    case("internal-iteration-does-not-move-surface", digest(moved), d0)

    # Anything a caller can say must move it.
    for label, mutate in (
        ("added-optional-flag", lambda c: c["commands"][0]["optional"].append("--new")),
        (
            "changed-required-flag",
            lambda c: c["commands"][0].__setitem__("required", ["--other"]),
        ),
        (
            "new-command",
            lambda c: c["commands"].append({**c["commands"][0], "mode": "test"}),
        ),
        ("renamed-loop", lambda c: c["commands"][0].__setitem__("loop", "b")),
        (
            "changed-mcp-exposure",
            lambda c: c["commands"][0].__setitem__("mcp_exposed", False),
        ),
        (
            "changed-mcp-carrier",
            lambda c: c["commands"][0].__setitem__(
                "mcp_carrier",
                {
                    "kind": "inline_bundle_v1",
                    "input_schema": {"type": "object", "required": ["bundle"]},
                },
            ),
        ),
    ):
        mutated = json.loads(json.dumps(base))
        mutate(mutated)
        if digest(mutated) == d0:
            print(
                f"SELFTEST case failed — {label} did not move the surface digest",
                file=sys.stderr,
            )
            red = 1

    # Flag order is not part of the promise; the same surface written differently
    # must hash the same, or every reordering looks like a broken promise.
    reordered = json.loads(json.dumps(base))
    reordered["commands"][0]["required"] = list(
        reversed(reordered["commands"][0]["required"])
    )
    case("flag-order-is-not-surface", digest(reordered), d0)

    print("SELFTEST " + ("GREEN" if not red else "RED"))
    return red


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
