from pydantic import BaseModel, ConfigDict


class StatlogBaseModel(BaseModel):
    """Pydantic model that defines configurations which applies to all Models in this package."""

    model_config = ConfigDict(validate_assignment=True, use_enum_values=True)
