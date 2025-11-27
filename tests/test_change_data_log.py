from datetime import datetime, timezone
from typing import Any

import pytest
from pydantic import ValidationError

from ssb_poc_statlog_model.change_data_log import (
    ChangeDataLog,
    ChangeDetails,
    ChangeEvent,
    ChangeEventReason,
    DataChangeType,
)


def make_common_fields() -> dict[str, Any]:
    return {
        "statistics_name": "arblonn",
        "data_source": [
            "gs://bucket/path/input.parquet",
        ],
        "data_target": "gs://bucket/path/target.parquet",
        "data_period": "2023-12",
        "variable_name": "loenn",
        "change_event": ChangeEvent.M,
        "change_event_reason": ChangeEventReason.REVIEW,
        "change_datetime": datetime(2024, 1, 10, 15, 0, 0, tzinfo=timezone.utc),
        "changed_by": "user@example.com",
        "data_change_type": DataChangeType.UPD,
        "change_comment": "Some reason...",
    }


def test_change_data_log_unit_change_simple() -> None:
    payload = make_common_fields() | {
        "change_details": {
            "kind": "unit",
            "unit_id": [
                {"unit_id_variable": "fnr", "unit_id_value": "170598nnnnn"},
            ],
            "old_value": "43000",
            "new_value": "45000",
        }
    }

    model = ChangeDataLog(**payload)

    assert model.change_details.kind == "unit"
    # Ensure union discriminates into the unit variant containing the unit_id list
    assert isinstance(model.change_details.unit_id, list)
    assert model.change_details.unit_id[0].unit_id_variable == "fnr"
    assert model.data_change_type == DataChangeType.UPD


def test_change_data_log_rows_affected() -> None:
    payload = make_common_fields() | {
        "change_details": {
            "kind": "rows",
            "rows_affected": 12,
        }
    }

    model = ChangeDataLog(**payload)
    assert model.change_details.kind == "rows"
    assert isinstance(model.change_details, ChangeDetails)
    assert model.change_details.rows_affected == 12


def test_naive_datetime_is_rejected() -> None:
    payload = make_common_fields()
    # Replace aware timestamp with naive one
    payload["change_datetime"] = datetime(2024, 1, 10, 15, 0, 0)
    payload["change_details"] = {"kind": "rows", "rows_affected": 1}

    with pytest.raises(ValidationError):
        ChangeDataLog(**payload)


def test_invalid_field_name_change_by_raises() -> None:
    payload = make_common_fields() | {
        # Intentionally wrong field name according to the updated model (expects changed_by)
        "change_by": "wrong@ssb.no",
        "change_details": {"kind": "rows", "rows_affected": 2},
    }
    # Remove the correct field to only provide the wrong one
    payload.pop("changed_by", None)

    with pytest.raises(ValidationError):
        ChangeDataLog(**payload)


def test_extra_fields_forbidden_in_change_details_rows() -> None:
    payload = make_common_fields() | {
        "change_details": {
            "kind": "rows",
            "rows_affected": 3,
            "extra": "not-allowed",
        }
    }

    with pytest.raises(ValidationError):
        ChangeDataLog(**payload)


def test_discriminator_kind_unit_requires_unit_id() -> None:
    payload = make_common_fields() | {
        "change_details": {
            "kind": "unit",
            # Missing required unit_id
            "old_value": "x",
            "new_value": "y",
        }
    }

    with pytest.raises(ValidationError):
        ChangeDataLog(**payload)


def test_old_and_new_value_variants_supported() -> None:
    payload = make_common_fields() | {
        "change_details": {
            "kind": "unit",
            "unit_id": [
                {"unit_id_variable": "fnr", "unit_id_value": "170598nnnnn"},
                {"unit_id_variable": "orgnr", "unit_id_value": "123456789"},
            ],
            # list of items for old value
            "old_value": [
                {"variable_name": "loenn", "value": "43000"},
                {"variable_name": "skatt", "value": "10000"},
            ],
            # dict for new value
            "new_value": {"loenn": "45000", "skatt": "10500"},
        }
    }

    model = ChangeDataLog(**payload)
    assert model.change_details.kind == "unit"
    assert isinstance(model.change_details.old_value, list)
    assert isinstance(model.change_details.new_value, dict)
