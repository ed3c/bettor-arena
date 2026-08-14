#!/usr/bin/env python3
"""Materialize the reviewed LoopX Worker Gateway terminal leaf from a content-addressed archive."""
from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path, PurePosixPath
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / ".delivery/loopx-worker-gateway-v1.tar.gz"
EXPECTED_SHA256 = "86d0ca832a7858801b4d2d3f8643b318bd24e35ed48a36784fadca251193519c"
SELF = ROOT / ".delivery/materialize_loopx_worker_gateway_v1.py"
WORKFLOW = ROOT / ".github/workflows/zz-materialize-loopx-worker-gateway-v1.yml"
ALLOWED_EXACT = {
    ".arena/modules/README.md",
    ".github/workflows/loopx-worker-gateway.yml",
}
ALLOWED_PREFIXES = (
    ".arena/modules/loopx-worker-gateway/",
    "loop_wiki/loopx-worker-gateway/",
)


def admitted(name: str) -> bool:
    return name in ALLOWED_EXACT or any(name.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def main() -> int:
    raw = ARCHIVE.read_bytes()
    observed = hashlib.sha256(raw).hexdigest()
    if observed != EXPECTED_SHA256:
        raise SystemExit(f"archive digest mismatch: {observed}")
    staged: list[tuple[Path, bytes, int]] = []
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        for member in archive.getmembers():
            name = PurePosixPath(member.name).as_posix()
            if member.name != name or name.startswith("/") or any(part in {"", ".", ".."} for part in PurePosixPath(name).parts):
                raise SystemExit(f"unsafe archive path: {member.name!r}")
            if not member.isfile() or not admitted(name):
                raise SystemExit(f"unadmitted archive entry: {name}")
            extracted = archive.extractfile(member)
            if extracted is None:
                raise SystemExit(f"missing archive bytes: {name}")
            target = (ROOT / name).resolve()
            try:
                target.relative_to(ROOT.resolve())
            except ValueError as exc:
                raise SystemExit(f"archive path escaped repository: {name}") from exc
            staged.append((target, extracted.read(), member.mode & 0o777))
    if not staged:
        raise SystemExit("archive contained no files")
    for target, data, mode in staged:
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
        temp = Path(temporary)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp, mode or 0o644)
            os.replace(temp, target)
        finally:
            if temp.exists():
                temp.unlink()
    ARCHIVE.unlink()
    SELF.unlink()
    WORKFLOW.unlink()
    delivery = ROOT / ".delivery"
    try:
        delivery.rmdir()
    except OSError:
        pass
    print(f"materialized {len(staged)} LoopX Worker Gateway files from sha256:{observed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
