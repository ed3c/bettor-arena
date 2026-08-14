#!/usr/bin/env python3
"""Materialize the reviewed LoopX Worker Gateway terminal leaf from verified chunks."""
from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path, PurePosixPath
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CORRUPT_ARCHIVE = ROOT / ".delivery/loopx-worker-gateway-v1.tar.gz"
CHUNK_DIR = ROOT / ".delivery/loopx-worker-gateway-v1.chunks"
SELF = ROOT / ".delivery/materialize_loopx_worker_gateway_v1.py"
WORKFLOW = ROOT / ".github/workflows/zz-materialize-loopx-worker-gateway-v1.yml"
EXPECTED_ARCHIVE_SHA256 = "fed2e20a4cef8c36e21086e40842bbcf8d80d5fa3b4bb44ace5c5b0ec13b3494"
CHUNKS = [
    ("00.bin", "c50d2293642487a322762bc7129b8399c956cde401b05c2216c36b33d3e0c695"),
    ("01.bin", "b99a8ff0bcca89d8b78a39d76302d179fabf5a8f984ff693aacff7fc09bb251d"),
    ("02a.bin", "61a5f06a40f4cd14fdd4ff2a6e56a59a7fc0e9b9cb8fc4288987af6f5fa23e0a"),
    ("02b.bin", "c1c0419115a3f36633a21c24bc2af9e239b8d3c5c1423999a76052fb0d8b4694"),
    ("03.bin", "4a333b1bab8385f32588fcf839711ba58029b53513fb63882e7f32170c490b80"),
    ("04.bin", "0dbaaadf22ec43c87698d2bdfa4bf2b7e90fee8ed0d453a7f1b96d5d983b966d"),
    ("05.bin", "c1b99347731a667d06411f681f3f0f0ec19a84df3af7bae008450b35699f9652"),
    ("06.bin", "b5780b029f72cc88b7e287cc36138d0305728f42e6d59c5adaea92c3d079744f"),
]
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


def load_archive() -> bytes:
    parts: list[bytes] = []
    for name, expected in CHUNKS:
        path = CHUNK_DIR / name
        raw = path.read_bytes()
        observed = hashlib.sha256(raw).hexdigest()
        if observed != expected:
            raise SystemExit(f"chunk digest mismatch {name}: {observed}")
        parts.append(raw)
    archive = b"".join(parts)
    observed = hashlib.sha256(archive).hexdigest()
    if observed != EXPECTED_ARCHIVE_SHA256:
        raise SystemExit(f"archive digest mismatch after chunk assembly: {observed}")
    return archive


def main() -> int:
    raw = load_archive()
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
    if CORRUPT_ARCHIVE.exists():
        CORRUPT_ARCHIVE.unlink()
    for name, _ in CHUNKS:
        (CHUNK_DIR / name).unlink()
    stale = CHUNK_DIR / "02.bin"
    if stale.exists():
        stale.unlink()
    CHUNK_DIR.rmdir()
    SELF.unlink()
    WORKFLOW.unlink()
    delivery = ROOT / ".delivery"
    try:
        delivery.rmdir()
    except OSError:
        pass
    print(f"materialized {len(staged)} LoopX Worker Gateway files from sha256:{EXPECTED_ARCHIVE_SHA256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
