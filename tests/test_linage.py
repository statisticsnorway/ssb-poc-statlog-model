from typing import Any

import pytest
from pydantic import ValidationError

from ssb_poc_statlog_model.linage import Linage


def _valid_payload() -> dict[str, Any]:
    return {
        "data_source": ["path/to/input_a.parquet", "path/to/input_b.parquet"],
        "data_target": ["path/to/output.parquet"],
    }


def test_linage_valid_minimal() -> None:
    payload = _valid_payload()
    model = Linage(**payload)

    assert model.data_source == ["path/to/input_a.parquet", "path/to/input_b.parquet"]
    assert model.data_target == ["path/to/output.parquet"]
    assert model.schema_version == "1.0.0"
    assert model.step is None
    assert model.file_hash is None


def test_linage_valid_with_optional_fields() -> None:
    payload = _valid_payload()
    payload["step"] = "inndata"
    payload["file_hash"] = ["abc123", "def456"]
    model = Linage(**payload)

    assert model.step == "inndata"
    assert model.file_hash == ["abc123", "def456"]


def test_linage_missing_data_source_raises() -> None:
    payload = _valid_payload()
    payload.pop("data_source")

    with pytest.raises(ValidationError):
        Linage(**payload)


def test_linage_missing_data_target_raises() -> None:
    payload = _valid_payload()
    payload.pop("data_target")

    with pytest.raises(ValidationError):
        Linage(**payload)


def test_linage_invalid_schema_version_raises() -> None:
    payload = _valid_payload()
    payload["schema_version"] = "2.0.0"  # not the allowed literal "1.0.0"

    with pytest.raises(ValidationError):
        Linage(**payload)
