#!/usr/bin/env python3
# ruff: noqa: F401,F403,F405  # this module family composes through star imports; the names ruff reads as unused are deliberate re-exports the downstream modules import through.
"""Sentinel entry for adapters that are declared but not physically exercised."""

raise SystemExit(
    "This host adapter is not physically admitted. Use the gateway probe/status path."
)
