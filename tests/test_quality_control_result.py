from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ssb_poc_statlog_model.quality_control_result import (
    QualityControlResult,
    QualityControlResults,
)


def _valid_payload(result_value: QualityControlResults) -> dict:
    return {
        "statistics_name": "arblonn",
        "quality_control_id": "QC-001",
        "data_location": [
            "gs://bucket/path/input.parquet",
        ],
        "data_period": "2023-12",
        "quality_control_datetime": datetime(2024, 1, 10, 15, 0, 0, tzinfo=UTC),
        "quality_control_results": result_value,
        "quality_result_comment": "All good",
    }


@pytest.mark.parametrize(
    "result_value",
    [
        QualityControlResults.field_0,
        QualityControlResults.field_1,
        QualityControlResults.field_2,
    ],
)
def test_quality_control_result_valid_for_all_results(
    result_value: QualityControlResults,
) -> None:
    payload = _valid_payload(result_value)
    model = QualityControlResult(**payload)

    assert model.statistics_name == "arblonn"
    assert model.quality_control_results == result_value
    assert isinstance(model.data_location, list)
    assert model.data_location[0].endswith("input.parquet")


def test_quality_control_result_naive_datetime_rejected() -> None:
    payload = _valid_payload(QualityControlResults.field_0)
    payload["quality_control_datetime"] = datetime(2024, 1, 10, 15, 0, 0)  # naive

    with pytest.raises(ValidationError):
        QualityControlResult(**payload)


def test_quality_control_result_invalid_enum_value_raises() -> None:
    payload = _valid_payload(QualityControlResults.field_1)
    payload["quality_control_results"] = "3"  # not in {"0","1","2"}

    with pytest.raises(ValidationError):
        QualityControlResult(**payload)


def test_quality_control_result_missing_required_field_raises() -> None:
    payload = _valid_payload(QualityControlResults.field_2)
    payload.pop("data_location")  # required list[str]

    with pytest.raises(ValidationError):
        QualityControlResult(**payload)
