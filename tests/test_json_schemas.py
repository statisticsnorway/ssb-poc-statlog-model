import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tests.schema_validation import schema_validator

SCHEMA_DIR = Path(__file__).parents[1] / "src" / "model"


def _iter_example_files() -> list[Path]:
    return sorted(SCHEMA_DIR.glob("*.json"))


@pytest.mark.parametrize("file", _iter_example_files(), ids=lambda p: p.name)
def test_file(file: Path) -> None:
    payload = json.loads(file.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(payload)


@pytest.mark.parametrize(
    "file", sorted((SCHEMA_DIR / "example_logs").glob("*.json")), ids=lambda p: p.name
)
def test_examples_match_json_schema(file: Path) -> None:
    if "lineage" in file.name:
        schema_name = "lineage"
    elif "release" in file.name:
        schema_name = "release"
    else:
        schema_name = "change-data-log"
    schema = json.loads(
        (SCHEMA_DIR / f"{schema_name}-json-schema.json").read_text(encoding="utf-8")
    )
    payload = json.loads(file.read_text(encoding="utf-8"))
    schema_validator(schema).validate(payload)
