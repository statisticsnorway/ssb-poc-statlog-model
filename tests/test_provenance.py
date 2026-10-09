import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from ssb_poc_statlog_model.change_data_log import ChangeDataLog
from ssb_poc_statlog_model.lineage import Lineage
from ssb_poc_statlog_model.quality_control_description import QualityControlDescription
from ssb_poc_statlog_model.quality_control_result import QualityControlResult
from ssb_poc_statlog_model.release import Release
from tests.schema_validation import schema_validator
from tests.test_change_data_log import make_common_fields
from tests.test_lineage import _valid_payload as lineage_payload
from tests.test_quality_control_description import _valid_payload as definition_payload
from tests.test_quality_control_result import _valid_payload as result_payload
from tests.test_release import _valid_payload as release_payload


def _cases():
    return [
        (Lineage, lineage_payload(), "lineage"),
        (Release, release_payload(), "release"),
        (
            QualityControlDescription,
            definition_payload("I"),
            "quality-control-description",
        ),
        (QualityControlResult, result_payload("0"), "quality-control-result"),
        (
            ChangeDataLog,
            make_common_fields()
            | {
                "change_details": {
                    "detail_type": "rows",
                    "rows_affected": 1,
                    "variable_name": "income",
                }
            },
            "change-data-log",
        ),
    ]


@pytest.mark.parametrize("model_type,payload,schema_name", _cases())
def test_added_fields_and_schema_agree(model_type, payload, schema_name):
    payload |= {
        "event_id": "event-1",
        "recorded_at": datetime(2026, 10, 7, tzinfo=UTC),
        "producer_metadata": {"custom": [1, "text", True, None, {"nested": 2.5}]},
    }
    if "segment_id" in model_type.model_fields:
        payload["segment_id"] = "segment-1"
    model = model_type(**payload)
    assert model.producer_metadata == payload["producer_metadata"]
    assert "run_id" not in model_type.model_fields
    schema_path = (
        Path(__file__).parents[1] / "src" / "model" / f"{schema_name}-json-schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema_validator(schema).validate(
        json.loads(model.model_dump_json(exclude_none=True))
    )


@pytest.mark.parametrize("model_type,payload,_schema_name", _cases())
def test_recorded_at_requires_timezone(model_type, payload, _schema_name):
    with pytest.raises(ValidationError):
        model_type(**payload, recorded_at=datetime(2026, 10, 7))


@pytest.mark.parametrize(
    "invalid",
    [
        {"bad": {1, 2}},
        {"bad": datetime.now(UTC)},
        {"bad": float("nan")},
        {"bad": {"nested": float("inf")}},
    ],
)
def test_producer_metadata_rejects_non_json_values(invalid):
    with pytest.raises(ValidationError):
        Lineage(**lineage_payload(), producer_metadata=invalid)


def test_metadata_does_not_override_named_fields_and_assignment_is_validated():
    model = Lineage(
        **lineage_payload(),
        segment_id="real",
        producer_metadata={"segment_id": "custom"},
    )
    assert model.segment_id == "real"
    with pytest.raises(ValidationError):
        model.producer_metadata = {"invalid": {1, 2}}


@pytest.mark.parametrize("value", [12, 12.5, "12", True, False, None])
def test_quality_value_preserves_scalar_type(value):
    model = QualityControlResult(**result_payload("1"), value=value, unit="percent")
    assert type(model.value) is type(value)
    assert json.loads(model.model_dump_json())["value"] == value
    assert model.quality_control_results == "1"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), [1, 2], {"value": 1}])
def test_quality_value_rejects_nonfinite_or_nonscalar(value):
    with pytest.raises(ValidationError):
        QualityControlResult(**result_payload("0"), value=value)


@pytest.mark.parametrize("code", ["5", "5.1", "5.3"])
def test_optional_gsbpm_on_definitions(code):
    model = QualityControlDescription(**definition_payload("I"), gsbpm_code=code)
    assert model.gsbpm_code == code
    assert "segment_id" not in type(model).model_fields


@pytest.mark.parametrize("code", ["0", "9.1", "five", "5.X", 5.1])
def test_invalid_gsbpm_shape(code):
    with pytest.raises(ValidationError):
        QualityControlDescription(**definition_payload("I"), gsbpm_code=code)


def test_git_provenance_only_on_lineage_and_release():
    assert Release(**release_payload(), git_dirty=False).git_dirty is False
    assert Lineage(**lineage_payload()).git_dirty is None
    for model_type in (ChangeDataLog, QualityControlResult, QualityControlDescription):
        assert "git_commit_hash" not in model_type.model_fields
        assert "git_dirty" not in model_type.model_fields
