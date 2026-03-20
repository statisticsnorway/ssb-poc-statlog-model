import subprocess
from pathlib import Path

import click
import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from ssb_poc_statlog_model.generate_pydantic_models import (
    _derive_output_filename,
    _discover_schemas,
    _fix_docstrings,
    _run_codegen,
    main,
)

PROJECT_ROOT = Path(__file__).parents[1]


# --- _derive_output_filename ---


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("change-data-log-json-schema.json", "change_data_log.py"),
        ("quality-control-result-json-schema.json", "quality_control_result.py"),
        ("release-json-schema.json", "release.py"),
        ("linage-json-schema.json", "linage.py"),
        ("my-model-schema.json", "my_model.py"),
        ("any-name.json", "any_name.py"),
    ],
)
def test_derive_output_filename(filename: str, expected: str) -> None:
    result = _derive_output_filename(Path(filename))
    assert result == expected


# --- _discover_schemas ---


def test_discover_schemas_with_explicit_paths(tmp_path: Path) -> None:
    schema_a = tmp_path / "a-json-schema.json"
    schema_b = tmp_path / "b-json-schema.json"
    schema_a.write_text("{}")
    schema_b.write_text("{}")

    result = _discover_schemas(tmp_path, explicit_paths=[schema_a, schema_b])
    assert result == [schema_a.resolve(), schema_b.resolve()]


def test_discover_schemas_from_directory(tmp_path: Path) -> None:
    schema_a = tmp_path / "a-json-schema.json"
    schema_b = tmp_path / "b-json-schema.json"
    other = tmp_path / "not-a-schema.txt"
    schema_a.write_text("{}")
    schema_b.write_text("{}")
    other.write_text("ignored")

    result = _discover_schemas(tmp_path)
    assert result == sorted([schema_a.resolve(), schema_b.resolve()])


def test_discover_schemas_fallback_to_all_json(tmp_path: Path) -> None:
    schema = tmp_path / "some.json"
    schema.write_text("{}")

    result = _discover_schemas(tmp_path)
    assert result == [schema.resolve()]


def test_discover_schemas_empty_directory_returns_empty(tmp_path: Path) -> None:
    result = _discover_schemas(tmp_path)
    assert result == []


# --- _run_codegen ---


def test_run_codegen_success(tmp_path: Path, mocker: MockerFixture) -> None:
    input_schema = tmp_path / "schema.json"
    input_schema.write_text("{}")
    output_file = tmp_path / "out" / "model.py"

    mock_run = mocker.patch(
        "ssb_poc_statlog_model.generate_pydantic_models.subprocess.run"
    )
    mock_run.return_value = mocker.MagicMock(returncode=0)
    _run_codegen(input_schema, output_file)

    mock_run.assert_called_once()
    assert output_file.parent.exists()


def test_run_codegen_file_not_found_raises_click_exception(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    input_schema = tmp_path / "schema.json"
    input_schema.write_text("{}")
    output_file = tmp_path / "out" / "model.py"

    mocker.patch(
        "ssb_poc_statlog_model.generate_pydantic_models.subprocess.run",
        side_effect=FileNotFoundError,
    )
    with pytest.raises(click.ClickException, match="datamodel-code-generator"):
        _run_codegen(input_schema, output_file)


def test_run_codegen_called_process_error_raises_click_exception(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    input_schema = tmp_path / "schema.json"
    input_schema.write_text("{}")
    output_file = tmp_path / "out" / "model.py"

    mocker.patch(
        "ssb_poc_statlog_model.generate_pydantic_models.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "cmd"),
    )
    with pytest.raises(click.ClickException, match="datamodel-codegen failed"):
        _run_codegen(input_schema, output_file)


def test_run_codegen_passes_extra_args(tmp_path: Path, mocker: MockerFixture) -> None:
    input_schema = tmp_path / "schema.json"
    input_schema.write_text("{}")
    output_file = tmp_path / "model.py"

    mock_run = mocker.patch(
        "ssb_poc_statlog_model.generate_pydantic_models.subprocess.run"
    )
    mock_run.return_value = mocker.MagicMock(returncode=0)
    _run_codegen(input_schema, output_file, extra_args=["--collapse-root"])

    cmd_used = mock_run.call_args[0][0]
    assert "--collapse-root" in cmd_used


# --- _fix_docstrings ---


def test_fix_docstrings_success(tmp_path: Path, mocker: MockerFixture) -> None:
    mock_run = mocker.patch(
        "ssb_poc_statlog_model.generate_pydantic_models.subprocess.run"
    )
    mock_run.return_value = mocker.MagicMock(returncode=0)
    _fix_docstrings(tmp_path)

    mock_run.assert_called_once()


def test_fix_docstrings_file_not_found_raises_click_exception(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    mocker.patch(
        "ssb_poc_statlog_model.generate_pydantic_models.subprocess.run",
        side_effect=FileNotFoundError,
    )
    with pytest.raises(click.ClickException, match="ruff"):
        _fix_docstrings(tmp_path)


def test_fix_docstrings_called_process_error_raises_click_exception(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    mocker.patch(
        "ssb_poc_statlog_model.generate_pydantic_models.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "cmd"),
    )
    with pytest.raises(click.ClickException, match="ruff formatting failed"):
        _fix_docstrings(tmp_path)


# --- main CLI (via CliRunner) ---


def test_main_no_schemas_found_exits_with_error(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        main, ["--schemas-dir", str(tmp_path), "--out-dir", str(tmp_path)]
    )

    assert result.exit_code != 0
    assert "No schema files found" in result.output


def test_main_runs_codegen_for_each_schema(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    out_dir = tmp_path / "out"
    (schemas_dir / "a-json-schema.json").write_text("{}")
    (schemas_dir / "b-json-schema.json").write_text("{}")

    mock_codegen = mocker.patch(
        "ssb_poc_statlog_model.generate_pydantic_models._run_codegen"
    )
    mock_fix = mocker.patch(
        "ssb_poc_statlog_model.generate_pydantic_models._fix_docstrings"
    )

    runner = CliRunner()
    result = runner.invoke(
        main, ["--schemas-dir", str(schemas_dir), "--out-dir", str(out_dir)]
    )

    assert result.exit_code == 0
    assert mock_codegen.call_count == 2
    mock_fix.assert_called_once_with(out_dir)
    assert "Done." in result.output


def test_main_with_explicit_schema(tmp_path: Path, mocker: MockerFixture) -> None:
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    out_dir = tmp_path / "out"
    schema = tmp_path / "my-json-schema.json"
    schema.write_text("{}")

    mock_codegen = mocker.patch(
        "ssb_poc_statlog_model.generate_pydantic_models._run_codegen"
    )
    mocker.patch("ssb_poc_statlog_model.generate_pydantic_models._fix_docstrings")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--schemas-dir",
            str(schemas_dir),
            "--out-dir",
            str(out_dir),
            "--schemas",
            str(schema),
        ],
    )

    assert result.exit_code == 0
    assert mock_codegen.call_count == 1


def test_main_forwards_extra_args_to_codegen(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    out_dir = tmp_path / "out"
    (schemas_dir / "a-json-schema.json").write_text("{}")

    mock_codegen = mocker.patch(
        "ssb_poc_statlog_model.generate_pydantic_models._run_codegen"
    )
    mocker.patch("ssb_poc_statlog_model.generate_pydantic_models._fix_docstrings")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--schemas-dir",
            str(schemas_dir),
            "--out-dir",
            str(out_dir),
            "--extra-arg",
            "--collapse-root",
        ],
    )

    assert result.exit_code == 0
    _, kwargs = mock_codegen.call_args
    assert "--collapse-root" in kwargs.get("extra_args", [])
