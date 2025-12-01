import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

SCHEMA_DIR = Path(__file__).parents[1] / "src" / "model"


def _iter_example_files() -> list[Path]:
    return sorted(SCHEMA_DIR.glob("*.json"))


@pytest.mark.parametrize("file", _iter_example_files(), ids=lambda p: p.name)
def test_file(file: Path) -> None:
    payload = json.loads(file.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(payload)
