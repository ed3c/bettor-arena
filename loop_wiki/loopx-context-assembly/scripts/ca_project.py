#!/usr/bin/env python3
"""Six host projections of one IR, and the law that must survive all six.

Each host wants a different wrapper: a heading style, a fence, an ordering
convention. Those are presentation. What must not differ is the normative law --
the paragraph that says what may and may not be done -- because six
hand-maintained prompts diverge in exactly that paragraph, and the divergence is
found by an agent doing something on one host that was forbidden on another.

So each renderer wraps, and `law_matrix` extracts the delimited region from every
projection and compares digests. A renderer that edited the law, reordered it, or
dropped a line shows up as a different digest against five others.

`cache_observation` is here because it is the other thing that gets generalised.
A hit rate measured on one host with one model on one provider is a fact about
that combination. It is not a property of the prompt, and it does not transfer.
"""

from __future__ import annotations

from typing import Any

from ca_common import (
    CACHE_OBSERVATION_SCOPE,
    HOSTS,
    ContractError,
    digest,
    non_empty_str,
    normative_region,
    text_digest,
)

# Presentation only. Each entry wraps the same prefix and suffix; none of them
# may touch the text between the normative delimiters.
WRAPPERS = {
    "ante": ("<!-- ante -->\n", "\n<!-- /ante -->"),
    "claude": ("", ""),
    "codex": ("<!-- codex:instructions -->\n", "\n<!-- /codex:instructions -->"),
    "grok-build": ("### GROK BUILD\n", "\n### END"),
    "opencode": ("<!-- opencode -->\n", "\n<!-- /opencode -->"),
    "pi": ("<!-- pi -->\n", "\n<!-- /pi -->"),
}


def project(
    host: str, prefix: dict[str, Any], suffix: dict[str, Any]
) -> dict[str, Any]:
    """One host's rendering. Wraps; never edits the law."""
    if host not in HOSTS:
        raise ContractError(f"unknown host {host!r}; the IR renders {list(HOSTS)}")

    # The prefix and suffix were scanned for volatile and forbidden content when
    # they were rendered. Re-scanning here would be a guard that cannot fire --
    # the wrappers are constants, so this function adds nothing to scan. What it
    # can check is that the text still matches the digest it was scanned under,
    # which is the one way scanned text arrives here having since been edited.
    for part, label in ((prefix, "prefix"), (suffix, "suffix")):
        if text_digest(part["text"]) != part[f"{label}_digest"]:
            raise ContractError(
                f"the {label} handed to the {host} projection does not match its own "
                f"{label}_digest. It was scanned for volatile and forbidden content, "
                "and then changed; the scan result on the record is about text that no "
                "longer exists"
            )

    head, tail = WRAPPERS[host]
    text = f"{head}{prefix['text']}\n{suffix['text']}{tail}"

    return {
        "host": host,
        "text": text,
        "projection_digest": text_digest(text),
        # Carried separately so a cache receipt can name the prefix it applies
        # to without the suffix, which changes on every request.
        "prefix_digest": prefix["prefix_digest"],
        "suffix_digest": suffix["suffix_digest"],
        "normative_digest": text_digest(normative_region(text, f"{host} projection")),
        "authority": "PRESENTATION_ONLY",
    }


def law_matrix(projections: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare the normative region across every projection.

    The comparison that six hand-maintained prompts cannot pass for long. A
    renderer that reworded one line of the law shows up here as a digest that
    disagrees with the others, before anyone acts on the difference.
    """
    if not projections:
        raise ContractError("no projections to compare")
    by_digest: dict[str, list[str]] = {}
    for projection in projections:
        by_digest.setdefault(projection["normative_digest"], []).append(
            projection["host"]
        )

    hosts = sorted(projection["host"] for projection in projections)
    missing = sorted(set(HOSTS) - set(hosts))
    agreed = len(by_digest) == 1

    return {
        "hosts": hosts,
        "missing_hosts": missing,
        "distinct_law_digests": len(by_digest),
        "groups": {law: sorted(members) for law, members in sorted(by_digest.items())},
        "agreed": agreed,
        "reason": (
            "every projection carries the same normative region"
            if agreed
            else (
                f"{len(by_digest)} different laws across {len(hosts)} hosts. An agent "
                "will do on one host what another forbids, and the divergence is "
                "found by the thing it allowed"
            )
        ),
    }


def require_law_agreement(matrix: dict[str, Any]) -> None:
    if not matrix["agreed"]:
        raise ContractError(matrix["reason"] + f": {matrix['groups']}")
    if matrix["missing_hosts"]:
        raise ContractError(
            f"hosts {matrix['missing_hosts']} were not projected. A host that was "
            "never rendered is not in agreement -- it is absent, and absence is the "
            "state a hand-maintained prompt drifts in"
        )


CACHE_KEYS = {"host", "model", "provider", "prefix_digest", "hits", "misses"}


def cache_observation(value: Any) -> dict[str, Any]:
    """A cache measurement, scoped to what it actually measured."""
    if not isinstance(value, dict) or set(value) != CACHE_KEYS:
        raise ContractError(
            f"cache observation fields drifted; expected {sorted(CACHE_KEYS)}"
        )
    for field in ("host", "model", "provider"):
        non_empty_str(value[field], f"cache.{field}")
    if value["host"] not in HOSTS:
        raise ContractError(f"cache observation names unknown host {value['host']!r}")
    for field in ("hits", "misses"):
        count = value[field]
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise ContractError(f"cache.{field} must be a non-negative integer")

    total = value["hits"] + value["misses"]
    return {
        **value,
        "hit_rate": (value["hits"] / total) if total else None,
        # The scope, on the observation itself. A hit rate is a fact about one
        # host with one model on one provider; it is not a property of the
        # prompt, and it does not transfer to the other five.
        "applies_to": CACHE_OBSERVATION_SCOPE,
        "universal_claim": False,
        "observation_digest": digest(value),
    }


def require_same_environment(
    observation: dict[str, Any], host: str, model: str, provider: str
) -> None:
    """Refuse a cache receipt being read as evidence about another environment."""
    if (
        observation["host"] != host
        or observation["model"] != model
        or observation["provider"] != provider
    ):
        raise ContractError(
            f"a cache receipt from {observation['host']}/{observation['model']}/"
            f"{observation['provider']} is being read as evidence about {host}/{model}/"
            f"{provider}. Cache behaviour is a property of a tokenizer, a serving "
            "stack and a billing policy -- none of which are shared here"
        )
