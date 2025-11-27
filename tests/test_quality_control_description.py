import pytest
from pydantic import ValidationError

from ssb_poc_statlog_model.quality_control_description import (
    QualityControlDescription,
    QualityControlType,
)


def _valid_payload(qc_type: QualityControlType) -> dict:
    return {
        "quality_control_id": "QC-001",
        "quality_control_description": "Checks that X holds for Y",
        "quality_control_type": qc_type,
        "variables": [
            {"variable_description": "var_a description"},
            {},  # allowed: defaults to None
        ],
    }


@pytest.mark.parametrize(
    "qc_type",
    [QualityControlType.H, QualityControlType.S, QualityControlType.I],
)
def test_quality_control_description_valid_for_all_types(
    qc_type: QualityControlType,
) -> None:
    payload = _valid_payload(qc_type)
    model = QualityControlDescription(**payload)

    assert model.quality_control_id == "QC-001"
    assert model.quality_control_type == qc_type
    # variables should be parsed into model instances and preserve order/length
    assert isinstance(model.variables, list)
    assert len(model.variables) == 2
    assert model.variables[0].variable_description == "var_a description"
    assert model.variables[1].variable_description is None


def test_quality_control_description_invalid_type_raises() -> None:
    payload = _valid_payload(QualityControlType.H)
    payload["quality_control_type"] = "X"  # not in {H, S, I}

    with pytest.raises(ValidationError):
        QualityControlDescription(**payload)


def test_quality_control_description_missing_variables_raises() -> None:
    payload = _valid_payload(QualityControlType.S)
    payload.pop("variables")

    with pytest.raises(ValidationError):
        QualityControlDescription(**payload)
