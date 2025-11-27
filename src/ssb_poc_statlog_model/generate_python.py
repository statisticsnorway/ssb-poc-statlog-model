r"""CLI to generate Pydantic v2 models from JSON Schema files in src/model.

Usage examples (run inside the Poetry environment):

  # Generate models for all *-json-schema.json files in src/model → src/ssb_poc_statlog_model
  poetry run python -m ssb_poc_statlog_model.generate_python

  # Be explicit about directories
  poetry run python -m ssb_poc_statlog_model.generate_python \
      --schemas-dir src\model \
      --out-dir src\ssb_poc_statlog_model

  # Only (re)generate a single specific schema file
  poetry run python -m ssb_poc_statlog_model.generate_python \
      --schemas src\model\change-data-log-json-schema.json

This script shells out to the module `datamodel_code_generator` via the same
interpreter, so it works when launched under `poetry run ...`.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

import click


def _derive_output_filename(schema_path: Path) -> str:
    """Derive a Python file name from a schema file name.

    Examples:
      - change-data-log-json-schema.json → change_data_log.py
      - quality-control-result-json-schema.json → quality_control_result.py
      - fallback: any-name.json → any_name.py
    """
    stem = schema_path.stem  # e.g. "change-data-log-json-schema"
    # Remove the common suffix if present
    for suffix in ("-json-schema", "-schema"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    # Convert hyphens to underscores
    snake = stem.replace("-", "_") or "model"
    return f"{snake}.py"


def _run_codegen(
    input_schema: Path, output_file: Path, extra_args: Sequence[str] | None = None
) -> None:
    """Invoke datamodel-codegen with the required options."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    cmd: list[str] = [
        sys.executable,
        "-m",
        "datamodel_code_generator",
        "--input-file-type",
        "jsonschema",
        "--input",
        str(input_schema),
        "--output-model-type",
        "pydantic_v2.BaseModel",
        "--use-default",
        "--use-title-as-name",
        "--use-one-literal-as-default",
        "--use-subclass-enum",
        "--use-standard-collections",
        "--use-double-quotes",
        "--use-union-operator",
        "--disable-timestamp",
        # "--use-schema-description",
        # The project targets >=3.10; keep generated syntax compatible with 3.10
        "--target-python-version",
        "3.10",
        "--output",
        str(output_file),
    ]
    if extra_args:
        cmd.extend(extra_args)

    click.echo(f"[codegen] {input_schema} -> {output_file}")
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as e:
        raise click.ClickException(
            "datamodel-code-generator is not available. Install dev deps with:\n"
            "  poetry install --with dev\n"
            "Or add it explicitly:\n"
            "  poetry add -G dev datamodel-code-generator"
        ) from e
    except subprocess.CalledProcessError as e:
        raise click.ClickException(
            f"datamodel-codegen failed for {input_schema} (exit code {e.returncode})."
        ) from e


def _discover_schemas(
    schemas_dir: Path, explicit_paths: Iterable[Path] | None = None
) -> list[Path]:
    if explicit_paths:
        return [p.resolve() for p in explicit_paths]
    # Discover the conventional schema naming pattern used in this repo
    candidates = list(schemas_dir.glob("*-json-schema.json")) or list(
        schemas_dir.glob("*.json")
    )
    # Sort for stable output
    return sorted(p.resolve() for p in candidates)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--schemas-dir",
    type=click.Path(path_type=Path, exists=True, file_okay=False, dir_okay=True),
    default=Path("src") / "model",
    show_default=True,
    help="Directory containing JSON Schema files.",
)
@click.option(
    "--out-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=Path("src") / "ssb_poc_statlog_model",
    show_default=True,
    help="Directory where generated Python models will be written.",
)
@click.option(
    "--schemas",
    type=click.Path(path_type=Path, exists=True, dir_okay=False, file_okay=True),
    multiple=True,
    help=(
        "Optional explicit schema JSON file(s) to generate. If omitted, all files matching "
        "*-json-schema.json in --schemas-dir are generated."
    ),
)
@click.option(
    "--extra-arg",
    multiple=True,
    help=(
        "Optional extra argument(s) forwarded to datamodel-codegen. "
        "Example: --extra-arg --collapse-root --extra-arg --alias-customization some.json"
    ),
)
def main(
    schemas_dir: Path, out_dir: Path, schemas: Sequence[Path], extra_arg: Sequence[str]
) -> None:
    """Generate Pydantic v2 models from JSON Schemas using datamodel-codegen.

    Run this command via Poetry, e.g.:
      poetry run python -m ssb_poc_statlog_model.generate_python
    """
    targets = _discover_schemas(schemas_dir, schemas)
    if not targets:
        raise click.ClickException(f"No schema files found under {schemas_dir}")

    for schema_path in targets:
        out_file = out_dir / _derive_output_filename(schema_path)
        _run_codegen(schema_path, out_file, extra_args=list(extra_arg))

    click.echo("\nDone.")


if __name__ == "__main__":
    main()
