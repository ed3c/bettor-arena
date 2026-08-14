#!/usr/bin/env python3
"""Builds the real tree the rebuild proofs run against.

Shared by the selftest and the physical control on purpose. A rebuild proof
compares bytes on disk, so there has to be a disk -- and if the two suites built
their own trees they would drift, and the control would eventually be proving
something about a tree the selftest never sees.

The four projections are shaped to produce one of each proof state:

    vector-stale     rebuild reproduces it exactly        -> PROVEN
    cache-stale      rebuild reproduces it exactly        -> PROVEN
    graph-divergent  rebuild succeeds, content differs    -> DIVERGENT
    lsp-unprovable   its declared source is absent        -> UNPROVABLE
"""

from __future__ import annotations

from pathlib import Path

# Deterministic content, derived from the sources, so a rebuild reproduces it.
REBUILD_VECTOR = """#!/usr/bin/env python3
import pathlib, sys
out = pathlib.Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
source = pathlib.Path("data/resource-gc/sources/corpus.txt").read_text()
(out / "index.txt").write_text("".join(sorted(source.split())) + "\\n")
"""

REBUILD_CACHE = """#!/usr/bin/env python3
import pathlib, sys
out = pathlib.Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
source = pathlib.Path("data/resource-gc/sources/deps.txt").read_text()
(out / "cache.txt").write_text(source.upper())
"""

# Succeeds, and deliberately does not reproduce what is on disk. This is the
# case a returncode check calls rebuildable.
REBUILD_DIVERGENT = """#!/usr/bin/env python3
import pathlib, sys
out = pathlib.Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
(out / "graph.txt").write_text("a rebuild that does not reproduce the original\\n")
"""

REBUILD_LSP = """#!/usr/bin/env python3
import pathlib, sys
out = pathlib.Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
(out / "lsp.txt").write_text(
    pathlib.Path("data/resource-gc/absent-sources/symbols.txt").read_text()
)
"""


def build_tree(root: Path) -> Path:
    """Create the tree the fixtures describe. Returns the root."""
    data = root / "data/resource-gc"
    (data / "sources").mkdir(parents=True, exist_ok=True)
    (root / "tools").mkdir(parents=True, exist_ok=True)

    (data / "sources/corpus.txt").write_text(
        "delta alpha charlie bravo\n", encoding="utf-8"
    )
    (data / "sources/deps.txt").write_text("left right\n", encoding="utf-8")

    (root / "tools/rebuild_vector.py").write_text(REBUILD_VECTOR, encoding="utf-8")
    (root / "tools/rebuild_cache.py").write_text(REBUILD_CACHE, encoding="utf-8")
    (root / "tools/rebuild_divergent.py").write_text(
        REBUILD_DIVERGENT, encoding="utf-8"
    )
    (root / "tools/rebuild_lsp.py").write_text(REBUILD_LSP, encoding="utf-8")

    # The projections, written to exactly what their rebuild produces.
    vector = data / "vector-stale"
    vector.mkdir(parents=True, exist_ok=True)
    corpus = (data / "sources/corpus.txt").read_text(encoding="utf-8")
    (vector / "index.txt").write_text(
        "".join(sorted(corpus.split())) + "\n", encoding="utf-8"
    )

    cache = data / "cache-stale"
    cache.mkdir(parents=True, exist_ok=True)
    (cache / "cache.txt").write_text(
        (data / "sources/deps.txt").read_text(encoding="utf-8").upper(),
        encoding="utf-8",
    )

    divergent = data / "graph-divergent"
    divergent.mkdir(parents=True, exist_ok=True)
    (divergent / "graph.txt").write_text(
        "the original graph, which the rebuild will not reproduce\n", encoding="utf-8"
    )

    lsp = data / "lsp-unprovable"
    lsp.mkdir(parents=True, exist_ok=True)
    (lsp / "lsp.txt").write_text("symbols\n", encoding="utf-8")

    for name in (
        "ledger-0001",
        "decision-0007",
        "wal-0003",
        "blocked-12",
        "worktree-leased",
        "worktree-dirty",
        "release-tree",
        "cache-fresh",
        "artifact-unknown",
    ):
        path = data / name
        path.mkdir(parents=True, exist_ok=True)
        (path / "content.txt").write_text(f"{name}\n", encoding="utf-8")

    return root
