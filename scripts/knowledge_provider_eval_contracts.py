"""Load the checked-in evaluation contract, schemas, and immutable fixture subject."""

from __future__ import annotations

from pathlib import Path

from knowledge_provider_eval_common import (
    EVALS,
    FAMILIES,
    SHA256,
    common_safety,
    digest,
    load,
    require,
    strict_keys,
    validate_subject,
)

SCHEMA_FILES = {
    "participant": "participant.schema.json",
    "case": "eval-case.schema.json",
    "observation": "eval-observation.schema.json",
    "report": "eval-report.schema.json",
    "config": "eval-config.schema.json",
    "subject": "subject.schema.json",
}


def load_contract(root: Path) -> tuple[dict, dict, dict[str, str]]:
    config = load(root / EVALS / "config.json")
    strict_keys(
        config,
        required={
            "schema_version",
            "families",
            "fixture_only",
            "require_complete_pair_coverage",
            "allow_mixed_fixture_scope",
            "automatic_admission",
        },
        label="eval config",
    )
    require(
        config["schema_version"] == "knowledge-provider-evals/v1",
        "eval config schema_version",
    )
    families = config["families"]
    require(
        isinstance(families, list)
        and len(families) == len(set(families))
        and set(families) == FAMILIES,
        "eval config family coverage",
    )
    require(isinstance(config["fixture_only"], bool), "eval config fixture_only")
    require(
        config["require_complete_pair_coverage"] is True,
        "eval config must require complete pair coverage",
    )
    require(
        config["allow_mixed_fixture_scope"] is False,
        "eval config must reject mixed fixture scope",
    )
    require(
        config["automatic_admission"] is False,
        "automatic provider admission is forbidden",
    )

    subject = load(root / EVALS / "subject.json")
    validate_subject(subject, "eval subject")

    schemas: dict[str, str] = {}
    for schema_id, filename in SCHEMA_FILES.items():
        value = load(root / EVALS / "contracts" / filename)
        strict_keys(
            value,
            required={
                "$schema",
                "$id",
                "title",
                "type",
                "additionalProperties",
                "properties",
                "required",
            },
            optional={"$defs", "allOf", "oneOf", "if", "then", "else"},
            label=f"schema {schema_id}",
        )
        require(
            value["$schema"] == "https://json-schema.org/draft/2020-12/schema",
            f"schema {schema_id}: draft",
        )
        require(value["type"] == "object", f"schema {schema_id}: root type")
        require(
            value["additionalProperties"] is False, f"schema {schema_id}: closed root"
        )
        require(
            isinstance(value["$id"], str) and value["$id"].endswith(filename),
            f"schema {schema_id}: id",
        )
        schemas[schema_id] = digest(value)

    for value in (config, subject):
        common_safety(value)
    require(all(SHA256.fullmatch(item) for item in schemas.values()), "schema digest")
    return config, subject, schemas
