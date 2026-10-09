import json
from datetime import UTC, datetime

import pytest
from jsonschema.exceptions import ValidationError as SchemaValidationError
from pydantic import ValidationError

from ssb_poc_statlog_model.lineage import DatasetReference, Lineage
from ssb_poc_statlog_model.quality_control_description import QualityControlDescription
from ssb_poc_statlog_model.quality_control_result import QualityControlResult
from ssb_poc_statlog_model.release import Release
from tests.schema_validation import SCHEMA_DIR, schema_validator
from tests.test_provenance import _cases
from tests.test_quality_control_description import _valid_payload as definition_payload
from tests.test_quality_control_result import _valid_payload as result_payload
from tests.test_release import _valid_payload as release_payload


def _partition():
    return {
        "path": "gs://bucket/dataset_p2026_v1/",
        "members": [
            {"path": "aar=2026/part-0.parquet", "generation": "456"},
            {"path": "aar=2025/part-0.parquet", "generation": "123"},
        ],
    }


def test_partition_normalizes_root_and_member_order():
    payload = _partition()
    model = DatasetReference(**payload)
    reordered = DatasetReference(
        **(
            payload
            | {
                "path": payload["path"].rstrip("/"),
                "members": list(reversed(payload["members"])),
            }
        )
    )
    assert model == reordered
    assert model.members[0].path == "aar=2025/part-0.parquet"
    assert model.generation is None
    assert "generation" not in model.model_dump(exclude_none=True)


@pytest.mark.parametrize("change", ["added", "removed", "replaced", "renamed"])
def test_partition_changes_change_identity(change):
    original = _partition()
    members = [member.copy() for member in original["members"]]
    if change == "added":
        members.append({"path": "aar=2027/part-0.parquet", "generation": "789"})
    elif change == "removed":
        members.pop()
    elif change == "replaced":
        members[1]["generation"] = "999"
    else:
        members[1]["path"] = "aar=2025/renamed.parquet"
    assert DatasetReference(**original) != DatasetReference(
        **(original | {"members": members})
    )


@pytest.mark.parametrize(
    "members",
    [
        [],
        [
            {"path": "part.parquet", "generation": "1"},
            {"path": "part.parquet", "generation": "2"},
        ],
    ],
)
def test_empty_or_duplicate_partition_members_rejected(members):
    with pytest.raises(ValidationError):
        DatasetReference(path="gs://bucket/root/", members=members)


@pytest.mark.parametrize(
    "path",
    [
        "../part.parquet",
        "a/../part.parquet",
        "/part.parquet",
        "gs://bucket/part.parquet",
        "a//part.parquet",
        "a/./part.parquet",
        "a\\part.parquet",
    ],
)
def test_invalid_member_paths_rejected(path):
    with pytest.raises(ValidationError):
        DatasetReference(
            path="gs://bucket/root/", members=[{"path": path, "generation": "1"}]
        )


def test_root_generation_and_members_cannot_coexist():
    with pytest.raises(ValidationError):
        DatasetReference(**_partition(), generation="123")


def test_shared_reference_can_pass_between_generated_models():
    dataset = DatasetReference(**_partition())
    release = Release(**(release_payload() | {"data_source": [dataset]}))
    lineage = Lineage(data_source=[], data_target=[dataset])
    assert release.data_source[0].model_dump() == lineage.data_target[0].model_dump()


@pytest.mark.parametrize(
    "model_type,payload,schema_name",
    [case for case in _cases() if case[0] is not QualityControlDescription],
)
def test_dataset_references_share_schema_and_validation(
    model_type, payload, schema_name
):
    field = "data_location" if model_type is QualityControlResult else "data_source"
    model = model_type(**(payload | {field: [_partition()]}))
    reference = getattr(model, field)[0]
    assert reference.members[0].path == "aar=2025/part-0.parquet"
    schema = json.loads(
        (SCHEMA_DIR / f"{schema_name}-json-schema.json").read_text(encoding="utf-8")
    )
    schema_validator(schema).validate(model.model_dump(mode="json", exclude_none=True))
    with pytest.raises(ValidationError):
        model_type(
            **(
                payload
                | {
                    field: [
                        {"path": _partition()["path"], "generation": "not-a-generation"}
                    ]
                }
            )
        )


def test_partition_schema_and_model_agree():
    schema = json.loads(
        (SCHEMA_DIR / "lineage-json-schema.json").read_text(encoding="utf-8")
    )
    payload = Lineage(data_source=[], data_target=[_partition()]).model_dump(
        mode="json", exclude_none=True
    )
    schema_validator(schema).validate(payload)
    payload["data_target"][0]["generation"] = "123"
    with pytest.raises(SchemaValidationError):
        schema_validator(schema).validate(payload)


@pytest.mark.parametrize("model_type,payload,_schema", _cases())
def test_unknown_fields_rejected_but_producer_details_allowed(
    model_type, payload, _schema
):
    with pytest.raises(ValidationError):
        model_type(**payload, custom_detail="not allowed")
    assert model_type(
        **payload, producer_metadata={"custom_detail": "allowed"}
    ).producer_metadata == {"custom_detail": "allowed"}


@pytest.mark.parametrize("value", [0, False, "", 12.5])
def test_value_only_quality_measurement_is_valid(value):
    payload = result_payload("0")
    payload.pop("quality_control_results")
    model = QualityControlResult(**payload, value=value)
    assert model.quality_control_results is None
    schema = json.loads(
        (SCHEMA_DIR / "quality-control-result-json-schema.json").read_text(
            encoding="utf-8"
        )
    )
    schema_validator(schema).validate(model.model_dump(mode="json", exclude_none=True))


def test_empty_quality_result_rejected_by_model_and_schema():
    payload = result_payload("0")
    payload.pop("quality_control_results")
    with pytest.raises(ValidationError, match="requires a value"):
        QualityControlResult(**payload)
    with pytest.raises(ValidationError):
        QualityControlResult(**payload, value=None, quality_control_results=None)
    schema = json.loads(
        (SCHEMA_DIR / "quality-control-result-json-schema.json").read_text(
            encoding="utf-8"
        )
    )
    payload["schema_version"] = "3.0.0"
    payload["quality_control_datetime"] = payload[
        "quality_control_datetime"
    ].isoformat()
    with pytest.raises(SchemaValidationError):
        schema_validator(schema).validate(payload)


def test_execution_exception_is_not_a_quality_result():
    with pytest.raises(ValidationError):
        QualityControlResult(
            **result_payload("0"), quality_control_run_exception="could not execute"
        )


def test_definition_name_and_timestamp_preserved():
    payload = definition_payload("I")
    first = QualityControlDescription(
        **payload, recorded_at=datetime(2026, 10, 1, tzinfo=UTC)
    )
    second = QualityControlDescription(
        **(payload | {"quality_control_id": "QC-002"}),
        recorded_at=datetime(2026, 10, 7, tzinfo=UTC),
    )
    assert first.quality_control_name == second.quality_control_name
    assert first.recorded_at < second.recorded_at
    payload.pop("quality_control_name")
    with pytest.raises(ValidationError):
        QualityControlDescription(**payload)


def test_repository_recorded_on_release_and_lineage():
    uri = "https://github.com/statisticsnorway/production"
    assert Release(**release_payload(), git_repository=uri).git_repository == uri
    assert (
        Lineage(data_source=[], data_target=[], git_repository=uri).git_repository
        == uri
    )
