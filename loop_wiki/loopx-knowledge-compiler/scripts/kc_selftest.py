#!/usr/bin/env python3
"""Positive run plus one planted control per named failure in #70.

Each control mutates the good fixtures in exactly one place and asserts that the
compile refuses. One place matters: a control that changes two things can pass
because of the change nobody was testing, and then it reports a rule as enforced
when the rule enforcing it is the other one.

The refusal message is matched on a substring as well, so a control cannot be
satisfied by an unrelated error further up the pipeline.
"""

from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any, Callable

from kc_common import ContractError, digest
from kc_compile import compile_subject
from kc_scaffold import validate_receipt


def _load(root: Path) -> dict[str, Any]:
    good = root / "tests/fixtures/good"
    return {
        name: json.loads((good / f"{name}.json").read_text(encoding="utf-8"))
        for name in (
            "source-manifest",
            "assertion-graph",
            "grouping",
            "system-spec",
            "codeop-plan",
        )
    }


def _compile(bundle: dict[str, Any], output_root: Path) -> dict[str, Any]:
    return compile_subject(
        bundle["source-manifest"],
        bundle["assertion-graph"],
        bundle["grouping"],
        bundle["system-spec"],
        bundle["codeop-plan"],
        output_root,
    )


def _assertion(bundle: dict[str, Any], assertion_id: str) -> dict[str, Any]:
    for assertion in bundle["assertion-graph"]["assertions"]:
        if assertion["assertion_id"] == assertion_id:
            return assertion
    raise KeyError(assertion_id)


def _source(bundle: dict[str, Any], source_id: str) -> dict[str, Any]:
    for source in bundle["source-manifest"]["sources"]:
        if source["source_id"] == source_id:
            return source
    raise KeyError(source_id)


def _requirement(bundle: dict[str, Any], requirement_id: str) -> dict[str, Any]:
    for requirement in bundle["system-spec"]["requirements"]:
        if requirement["requirement_id"] == requirement_id:
            return requirement
    raise KeyError(requirement_id)


# --- the controls -------------------------------------------------------------
# (name, mutation, substring the refusal must contain)


def _fabricated_metadata(bundle: dict[str, Any]) -> None:
    _source(bundle, "s-whiteboard")["recorded_at"] = "2026-08-01T09:00:00Z"


def _double_counted_corroboration(bundle: dict[str, Any]) -> None:
    # Both citations descend from the same upstream RFC, so the claim rests on
    # one source quoted twice -- and the count says two.
    _assertion(bundle, "a-003")["source_ids"] = ["s-quote-a", "s-quote-b"]


def _unknown_filled_from_memory(bundle: dict[str, Any]) -> None:
    _assertion(bundle, "a-005")["resolution"] = "30 days, per common practice"


def _unknown_gains_sources(bundle: dict[str, Any]) -> None:
    _assertion(bundle, "a-005")["source_ids"] = ["s-arch"]


def _contradiction_reconciled(bundle: dict[str, Any]) -> None:
    bundle["assertion-graph"]["contradictions"][0]["state"] = "RESOLVED"


def _contradiction_record_dropped(bundle: dict[str, Any]) -> None:
    bundle["assertion-graph"]["contradictions"] = []


def _prose_marked_tested(bundle: dict[str, Any]) -> None:
    _assertion(bundle, "a-001")["execution_receipt"] = None


def _failed_run_counted_as_verification(bundle: dict[str, Any]) -> None:
    _assertion(bundle, "a-001")["execution_receipt"]["exit_code"] = 1


def _inference_above_ceiling(bundle: dict[str, Any]) -> None:
    assertion = _assertion(bundle, "a-003")
    assertion["verification_state"] = "VERIFIED_BY_EXECUTION"
    assertion["execution_receipt"] = {
        "command": "pytest -q",
        "exit_code": 0,
        "output_digest": "sha256:" + "cd" * 32,
    }


def _citation_to_absent_source(bundle: dict[str, Any]) -> None:
    _assertion(bundle, "a-004")["source_ids"] = ["s-does-not-exist"]


def _mutable_branch_as_identity(bundle: dict[str, Any]) -> None:
    for layer in ("source-manifest", "assertion-graph", "system-spec", "codeop-plan"):
        bundle[layer]["notes_subject"]["ref_kind"] = "BRANCH"


def _layers_pinned_to_different_subjects(bundle: dict[str, Any]) -> None:
    bundle["system-spec"]["notes_subject"]["commit"] = "9c" * 20


def _assertion_dropped_before_cards(bundle: dict[str, Any]) -> None:
    del bundle["grouping"]["a-004"]


def _unstable_card_grouping_key(bundle: dict[str, Any]) -> None:
    # Two definitions claiming one canonical key: the same card compiled two
    # ways, and whichever is seen last would win silently.
    bundle["grouping"]["a-004"] = {"title": "Retry interval", "kind": "RULE"}
    bundle["grouping"]["a-006"] = {"title": "retry  interval", "kind": "RULE"}


def _compressed_acceptance_cases(bundle: dict[str, Any]) -> None:
    requirement = _requirement(bundle, "r-001")
    requirement["acceptance_cases"] = requirement["acceptance_cases"][:1]


def _requirement_derived_from_unknown(bundle: dict[str, Any]) -> None:
    requirement = _requirement(bundle, "r-002")
    requirement["derived_from_assertions"] = ["a-003", "a-005"]
    requirement["acceptance_cases"].append(
        {
            "case_id": "case-004",
            "given": "a card older than the retention window",
            "expect": "it is evicted",
            "assertion_id": "a-005",
        }
    )


def _unknown_dropped_from_spec(bundle: dict[str, Any]) -> None:
    bundle["system-spec"]["open_unknowns"] = []


def _requirement_with_no_source(bundle: dict[str, Any]) -> None:
    _requirement(bundle, "r-002")["derived_from_assertions"] = []


def _component_effect_without_rollback(bundle: dict[str, Any]) -> None:
    bundle["system-spec"]["components"][0]["rollback"] = None


def _codeop_without_precondition(bundle: dict[str, Any]) -> None:
    bundle["codeop-plan"]["operations"][0]["precondition"]["kind"] = "NONE"


def _codeop_without_rollback(bundle: dict[str, Any]) -> None:
    bundle["codeop-plan"]["operations"][0]["rollback"]["kind"] = "NONE"


def _codeop_without_target_selector(bundle: dict[str, Any]) -> None:
    bundle["codeop-plan"]["operations"][0]["target"]["selector_kind"] = "SYMBOL"


def _codeop_unbounded_diff(bundle: dict[str, Any]) -> None:
    bundle["codeop-plan"]["operations"][0]["expected_diff_shape"][
        "max_changed_files"
    ] = 0


def _create_over_existing_path(bundle: dict[str, Any]) -> None:
    bundle["codeop-plan"]["operations"][0]["precondition"]["kind"] = "PATH_PRESENT"


def _codeop_without_provenance(bundle: dict[str, Any]) -> None:
    bundle["codeop-plan"]["operations"][0]["provenance"]["locators"] = []


def _scaffold_outside_lease(bundle: dict[str, Any]) -> None:
    bundle["codeop-plan"]["operations"][0]["target"]["path"] = "src/ledger_append.py"


def _interface_change_without_version(bundle: dict[str, Any]) -> None:
    bundle["codeop-plan"]["operations"][0]["public_interface_change"] = True


def _removal_not_declared_as_interface_change(bundle: dict[str, Any]) -> None:
    bundle["codeop-plan"]["operations"][0]["expected_diff_shape"]["removed_symbols"] = [
        "append_event_legacy"
    ]


def _codeop_for_absent_requirement(bundle: dict[str, Any]) -> None:
    bundle["codeop-plan"]["operations"][0]["requirement_ids"] = ["r-999"]


CONTROLS: list[tuple[str, Callable[[dict[str, Any]], None], str]] = [
    ("source-without-locator-gains-metadata", _fabricated_metadata, "fabricated"),
    ("corroboration-counted-twice", _double_counted_corroboration, "dependency key"),
    ("unknown-filled-from-model-memory", _unknown_filled_from_memory, "did not say"),
    ("unknown-carrying-sources", _unknown_gains_sources, "not unknown"),
    (
        "contradiction-silently-reconciled",
        _contradiction_reconciled,
        "deleted one side",
    ),
    (
        "contradiction-record-dropped",
        _contradiction_record_dropped,
        "appears in no contradiction",
    ),
    ("prose-marked-tested", _prose_marked_tested, "prose"),
    (
        "failed-run-counted-as-verification",
        _failed_run_counted_as_verification,
        "verified nothing",
    ),
    ("inference-above-its-ceiling", _inference_above_ceiling, "above its ceiling"),
    (
        "citation-to-absent-source",
        _citation_to_absent_source,
        "not in the source manifest",
    ),
    (
        "mutable-branch-as-release-identity",
        _mutable_branch_as_identity,
        "IMMUTABLE_COMMIT",
    ),
    (
        "layers-pinned-to-different-subjects",
        _layers_pinned_to_different_subjects,
        "different notes subject",
    ),
    (
        "assertion-dropped-before-cards",
        _assertion_dropped_before_cards,
        "not assigned to a card",
    ),
    (
        "one-canonical-key-two-definitions",
        _unstable_card_grouping_key,
        "two different card definitions",
    ),
    ("independent-cases-compressed", _compressed_acceptance_cases, "folds"),
    (
        "requirement-derived-from-unknown",
        _requirement_derived_from_unknown,
        "derived from UNKNOWN",
    ),
    ("unknown-dropped-from-spec", _unknown_dropped_from_spec, "answered by omission"),
    (
        "requirement-with-no-source",
        _requirement_with_no_source,
        "derived from no assertion",
    ),
    ("effect-without-rollback", _component_effect_without_rollback, "one-way door"),
    (
        "codeop-without-precondition",
        _codeop_without_precondition,
        "tree it never checked",
    ),
    ("codeop-without-rollback", _codeop_without_rollback, "applied on faith"),
    (
        "codeop-without-target-selector",
        _codeop_without_target_selector,
        "target.selector",
    ),
    ("codeop-with-unbounded-diff", _codeop_unbounded_diff, "unbounded diff shape"),
    ("create-over-existing-path", _create_over_existing_path, "overwrites"),
    ("codeop-without-provenance", _codeop_without_provenance, "the model remembered"),
    ("scaffold-target-outside-lease", _scaffold_outside_lease, "outside the leased"),
    (
        "interface-change-without-version",
        _interface_change_without_version,
        "breaking change",
    ),
    (
        "removal-not-declared",
        _removal_not_declared_as_interface_change,
        "only private if someone said so",
    ),
    (
        "codeop-for-absent-requirement",
        _codeop_for_absent_requirement,
        "unknown requirement",
    ),
]


def run_selftest(root: Path) -> tuple[int, int]:
    """Positive properties first, then every control. Returns (positives, controls)."""
    base = _load(root)
    positives = 0

    with tempfile.TemporaryDirectory(prefix="loopx-kc-selftest-") as tmp:
        scratch = Path(tmp)

        first = _compile(copy.deepcopy(base), scratch / "one")
        validate_receipt(first["receipt"])
        positives += 1

        # Idempotence, compared on the compile digest rather than on the receipt
        # object: the receipt embeds paths, and comparing those would pass for
        # the wrong reason if the tree were rendered into the same directory.
        second = _compile(copy.deepcopy(base), scratch / "two")
        if first["compile_digest"] != second["compile_digest"]:
            raise ContractError(
                "compiling the same notes subject twice produced different digests "
                f"({first['compile_digest']} vs {second['compile_digest']}); with no "
                "declared entropy source, that is nondeterminism nobody recorded"
            )
        positives += 1

        # And the rendered bytes themselves, not only the summary digest.
        left = sorted(
            (path.relative_to(scratch / "one").as_posix(), path.read_bytes())
            for path in (scratch / "one").rglob("*")
            if path.is_file()
        )
        right = sorted(
            (path.relative_to(scratch / "two").as_posix(), path.read_bytes())
            for path in (scratch / "two").rglob("*")
            if path.is_file()
        )
        if not left:
            raise ContractError(
                "the compile wrote no files; a scaffold nobody rendered cannot be "
                "compared for determinism, and this check would pass vacuously"
            )
        if left != right:
            raise ContractError("two renders of one plan produced different bytes")
        positives += 1

        # Provenance survives into the generated file, not only into the receipt.
        body = (scratch / "one" / "generated/ledger_append.py").read_text(
            encoding="utf-8"
        )
        for needle in ("a-001", "notes/architecture.md#L10-L24", "CANDIDATE"):
            if needle not in body:
                raise ContractError(
                    f"generated symbol lost {needle!r}; a scaffold that cannot be "
                    "traced back to its source is indistinguishable from invention"
                )
        positives += 1

        # One acceptance case per assertion survives into the generated file, so
        # the compression the spec layer refused cannot reappear at render time.
        for case_id in ("case-001", "case-002"):
            if case_id not in body:
                raise ContractError(
                    f"generated scaffold omits acceptance case {case_id}; the cases "
                    "the spec kept separate were folded back together by the renderer"
                )
        positives += 1

        if first["receipt"]["unresolved"]["open_unknowns"] != ["a-005"]:
            raise ContractError("the open unknown did not survive into the receipt")
        if first["receipt"]["unresolved"]["open_contradictions"] != ["c-001"]:
            raise ContractError(
                "the open contradiction did not survive into the receipt"
            )
        positives += 1

        # Two equivalent inputs must digest the same. Reordering a sorted list is
        # rejected upstream, so this checks the encoding, not the ordering rule.
        if digest(first["card_graph"]) != digest(second["card_graph"]):
            raise ContractError("card graph digest is not stable across compiles")
        positives += 1

        failures = []
        for index, (name, mutate, needle) in enumerate(CONTROLS):
            bundle = copy.deepcopy(base)
            mutate(bundle)
            try:
                _compile(bundle, scratch / f"control-{index}")
            except ContractError as exc:
                if needle not in str(exc):
                    failures.append(
                        f"{name} was refused, but for the wrong reason: expected a "
                        f"message containing {needle!r}, got {exc}"
                    )
                continue
            except Exception as exc:  # noqa: BLE001
                failures.append(
                    f"{name} raised {type(exc).__name__}: {exc} -- that is a broken "
                    "control, not a refusal; nothing was measured"
                )
                continue
            failures.append(f"{name} was accepted")

        if failures:
            raise ContractError(
                "planted controls did not behave:\n  " + "\n  ".join(failures)
            )

    return positives, len(CONTROLS)
