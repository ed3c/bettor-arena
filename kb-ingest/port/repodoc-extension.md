# Appendix — RepoDoc front-matter extension (skill-bettor addition, NOT upstream text)

skill-bettor ingests a converged wiki into its knowledge graph with
`python3 -m indexing.ingest_repodoc_cli <wiki_dir>`. That lane reads front-matter
fields OKF does not define. **No fork is needed**: OKF v0.1 permits
producer-defined extension fields, and the official prompt already instructs
that they be preserved across updates —

> Preserve all existing producer-defined front matter fields when updating a
> concept. Unknown extension fields are valid OKF and must survive round trips.

So one front-matter block satisfies both consumers. Add these keys alongside the
OKF ones; do not remove or rename any OKF field to make room.

```yaml
---
# --- OKF v0.1 (official; `type` is the only required field) ---
type: Architecture
title: Retry and backoff
description: How the worker classifies retryable failures and schedules backoff.
tags: [reliability]
# --- skill-bettor RepoDoc lane (producer extension) ---
node_kind: RepoDoc              # marks the page for the RepoDoc ingest lane
ingest_lane: concept
repo: owner/name
repo_url: <clone url or origin>
commit: <git rev-parse --short HEAD of TARGET at generation time>
covers: [retry-backoff, token-budgeting]   # → Concept nodes, kebab-case
libraries: [httpx, tenacity]               # → Library nodes, canonical manifest name, lowercased
generated_by: <host + model>
generated_at: null              # left null; the KG stamps ingest time
---
```

`indexing/repodoc.py` hard-requires `repo` and `title`, and skips any page that
has neither `node_kind: RepoDoc` nor (`repo` and `covers`). A page missing them
is silently dropped from the graph, so treat them as mandatory even though OKF
does not.

## Vocabulary discipline

`covers` and `libraries` become shared graph nodes, so a synonym fragments the
graph into near-duplicates. Reuse one slug per concept across the whole run and
prefer the most general term (`code-map`, not also `code-map-parsing`). Use the
dependency manifest's exact package name, lowercased, for `libraries`.

## Deliberate divergence from upstream

`okf/frontmatter.ts` carries only `openwiki_translation_pending` across a
front-matter rebuild, so every other producer extension is dropped when a page
fails validation and gets repaired. Applied here that would delete the RepoDoc
routing fields from exactly the pages that were already malformed, breaking KB
ingest silently. `openwiki_post.py` therefore preserves the fields above as well.
This is the one place the port intentionally does not match upstream behavior.
