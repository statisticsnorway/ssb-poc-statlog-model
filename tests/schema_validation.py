import json
from pathlib import Path
from urllib.parse import urljoin

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

SCHEMA_DIR = Path(__file__).parents[1] / "src" / "model"


def schema_validator(schema: dict) -> Draft202012Validator:
    """Resolve sibling schemas locally, without fetching published schemas."""
    registry = Registry()
    for path in SCHEMA_DIR.glob("*.json"):
        contents = json.loads(path.read_text(encoding="utf-8"))
        resource = Resource.from_contents(contents)
        registry = registry.with_resource(contents["$id"], resource)
        registry = registry.with_resource(urljoin(schema["$id"], path.name), resource)
    return Draft202012Validator(
        schema, format_checker=FormatChecker(), registry=registry
    )
