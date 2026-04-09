from typing import Any

import pytest
from pydantic import ValidationError

from ssb_poc_statlog_model.release import Release


def _valid_payload() -> dict[str, Any]:
    return {
        "dapla_team": "tip-tutorials",
        "statistics_name": "metstat",
        "git_tag": "2025.12-2",
        "git_commit_hash": "a1b2c3d4e5f6",
        "data_source": ["path/to/utdata.parquet"],
    }


def test_release_valid_minimal() -> None:
    payload = _valid_payload()
    model = Release(**payload)

    assert model.git_tag == "2025.12-2"
    assert model.git_commit_hash == "a1b2c3d4e5f6"
    assert model.data_source == ["path/to/utdata.parquet"]
    assert model.schema_version == "1.0.0"
    assert model.dapla_team == "tip-tutorials"
    assert model.statistics_name == "metstat"
    assert model.daplalab_image is None


def test_release_valid_with_optional_fields() -> None:
    payload = _valid_payload()
    payload["statistics_name"] = "my-statistics"
    payload["daplalab_image"] = "statisticsnorway/dapla-lab-jupyter-r:1.2.3"
    model = Release(**payload)

    assert model.statistics_name == "my-statistics"
    assert model.daplalab_image == "statisticsnorway/dapla-lab-jupyter-r:1.2.3"


def test_release_missing_git_tag_raises() -> None:
    payload = _valid_payload()
    payload.pop("git_tag")

    with pytest.raises(ValidationError):
        Release(**payload)


def test_release_missing_git_commit_hash_raises() -> None:
    payload = _valid_payload()
    payload.pop("git_commit_hash")

    with pytest.raises(ValidationError):
        Release(**payload)


def test_release_missing_data_source_raises() -> None:
    payload = _valid_payload()
    payload.pop("data_source")

    with pytest.raises(ValidationError):
        Release(**payload)


def test_release_invalid_schema_version_raises() -> None:
    payload = _valid_payload()
    payload["schema_version"] = "2.0.0"  # not the allowed literal "1.0.0"

    with pytest.raises(ValidationError):
        Release(**payload)
