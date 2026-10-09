from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from ssb_poc_statlog_model.lineage import DatasetReference, Lineage


def _valid_payload() -> dict[str, Any]:
    return {
        "data_source": [
            {"path": "gs://source-bucket/input.parquet", "generation": "123"}
        ],
        "data_target": [
            {"path": "gs://target-bucket/output.parquet", "generation": "456"}
        ],
    }


def test_lineage_valid_minimal() -> None:
    model = Lineage(**_valid_payload())
    assert model.data_source[0].generation == "123"
    assert model.data_target[0].path == "gs://target-bucket/output.parquet"
    assert model.schema_version == "3.0.0"
    assert model.step is None


def test_lineage_execution_provenance() -> None:
    timestamp = datetime(2026, 10, 7, tzinfo=UTC)
    model = Lineage(
        **_valid_payload(),
        event_id="lineage-1",
        segment_id="segment-1",
        recorded_at=timestamp,
        git_commit_hash="abc123",
        git_dirty=False,
        image_name="registry/image:tag",
        dapla_environment="PROD",
        dapla_region="DAPLA_LAB",
        dapla_service="JUPYTERLAB",
        dapla_team_google_project_id="utd-nudb-p-dy",
        execution_started_at=timestamp,
        execution_finished_at=timestamp,
        timezone="Europe/Oslo",
        configured_tz="Europe/Oslo",
        utc_offset_seconds=7200,
        gsbpm_code="5.3",
        producer_metadata={"method": {"name": "prepare"}},
    )
    assert model.segment_id == "segment-1"
    assert model.git_dirty is False
    assert model.dapla_environment == "PROD"
    assert model.recorded_at == timestamp
    assert model.producer_metadata == {"method": {"name": "prepare"}}
    assert "run_id" not in type(model).model_fields


@pytest.mark.parametrize("field", ["data_source", "data_target"])
def test_lineage_missing_dataset_field(field: str) -> None:
    payload = _valid_payload()
    payload.pop(field)
    with pytest.raises(ValidationError):
        Lineage(**payload)


@pytest.mark.parametrize(
    "path",
    [
        "/buckets/produkt/file.parquet",
        "file.parquet",
        "https://bucket/file",
        "gs://bucket/file?query",
    ],
)
def test_dataset_requires_gcs_path(path: str) -> None:
    with pytest.raises(ValidationError):
        DatasetReference(path=path, generation="123")


@pytest.mark.parametrize("generation", ["abc", "-1", "1.5", "", 123])
def test_generation_requires_decimal_string(generation: Any) -> None:
    with pytest.raises(ValidationError):
        DatasetReference(path="gs://bucket/file", generation=generation)


def test_generation_unknown_and_mutable_paths() -> None:
    first = DatasetReference(path="gs://bucket/file_v0.parquet", generation="123")
    second = DatasetReference(path=first.path, generation="456")
    assert first != second
    assert DatasetReference(path=first.path).generation is None


@pytest.mark.parametrize(
    "field", ["recorded_at", "execution_started_at", "execution_finished_at"]
)
def test_lineage_rejects_naive_timestamps(field: str) -> None:
    with pytest.raises(ValidationError):
        Lineage(**(_valid_payload() | {field: datetime(2026, 10, 7)}))


def test_lineage_rejects_old_schema_and_string_references() -> None:
    with pytest.raises(ValidationError):
        Lineage(**(_valid_payload() | {"schema_version": "1.0.0"}))
    with pytest.raises(ValidationError):
        Lineage(data_source=["gs://bucket/file"], data_target=[])
