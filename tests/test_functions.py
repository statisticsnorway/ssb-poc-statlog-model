from ssb_poc_statlog_model.functions import example_function


def test_example_function() -> None:
    assert example_function(1, 2) == "1 is less than 2"
    assert example_function(1, 0) == "1 is greater than or equal to 0"


from datetime import UTC, datetime

from ssb_poc_statlog_model.change_data_log import ChangeDataLog, DataChangeType

payload = {
    "statistics_name": "arblonn",
    "data_source": ["gs://bucket/path/input.parquet"],
    "data_target": "gs://bucket/path/target.parquet",
    "data_period": "2023-12",
    "variable_name": "loenn",
    "change_event": "M",
    "change_event_reason": "REVIEW",
    # The models use Pydantic's AwareDatetime → must be timezone aware
    "change_datetime": datetime(2024, 1, 10, 15, 0, tzinfo=UTC),
    "changed_by": "user@example.com",
    "data_change_type": DataChangeType.UPD,
    "change_comment": "Some reason…",
    "change_details": {
        "kind": "rows",
        "rows_affected": 12,
    },
}

model = ChangeDataLog(**payload)
print(model.model_dump())
