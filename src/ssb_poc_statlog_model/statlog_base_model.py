import json
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    JsonValue,
    TypeAdapter,
    field_validator,
    model_validator,
)

_JSON_VALUE: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)


class StatlogBaseModel(BaseModel):
    """Pydantic model that defines configurations which applies to all Models in this package."""

    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        allow_inf_nan=False,
        extra="forbid",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_record(cls, value: Any) -> Any:
        """Enforce cross-field rules that JSON Schema generation cannot express."""
        if isinstance(value, BaseModel):
            value = value.model_dump()
        if not isinstance(value, dict):
            return value
        if "quality_control_results" in cls.model_fields and (
            value.get("value") is None and value.get("quality_control_results") is None
        ):
            raise ValueError(
                "A quality result requires a value or categorical measurement; execution failures are not results."
            )
        if "members" in cls.model_fields and value.get("members") is not None:
            if value.get("generation") is not None:
                raise ValueError(
                    "Partitioned roots have member generations, not a root generation."
                )
            if isinstance(value.get("path"), str):
                value = value | {"path": value["path"].rstrip("/") + "/"}
        return value

    @field_validator("path", check_fields=False)
    @classmethod
    def validate_member_path(cls, value: str) -> str:
        """Reject ambiguous or escaping relative partition member paths."""
        if "generation" in cls.model_fields and "members" not in cls.model_fields:
            if any(part in {"", ".", ".."} for part in value.split("/")):
                raise ValueError(
                    "Partition member paths must be relative and contain no traversal or empty components."
                )
        return value

    @field_validator("members", check_fields=False)
    @classmethod
    def validate_members(cls, value: list[Any] | None) -> list[Any] | None:
        """Sort member identities and reject duplicate relative object paths."""
        if value is not None:
            paths = [member.path for member in value]
            if len(set(paths)) != len(paths):
                raise ValueError("Partition member paths must be unique.")
            return sorted(value, key=lambda member: member.path)
        return value

    @field_validator("producer_metadata", check_fields=False)
    @classmethod
    def validate_producer_metadata(
        cls, value: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        """Keep arbitrary producer details JSON-compatible and finite."""
        if value is not None:
            _JSON_VALUE.validate_python(value, strict=True)
            json.dumps(value, allow_nan=False)
        return value
