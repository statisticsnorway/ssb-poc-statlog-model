# SSB POC Statlog Model

This repo is a proof of concept (POC) of models for logging data from a statistics
production run.

[![PyPI](https://img.shields.io/pypi/v/ssb-poc-statlog-model.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/ssb-poc-statlog-model.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/ssb-poc-statlog-model)][pypi status]
[![License](https://img.shields.io/pypi/l/ssb-poc-statlog-model)][license]

[![Documentation](https://github.com/statisticsnorway/ssb-poc-statlog-model/actions/workflows/docs.yml/badge.svg)][documentation]
[![Tests](https://github.com/statisticsnorway/ssb-poc-statlog-model/actions/workflows/tests.yml/badge.svg)][tests]
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=statisticsnorway_ssb-poc-statlog-model&metric=coverage)][sonarcov]
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=statisticsnorway_ssb-poc-statlog-model&metric=alert_status)][sonarquality]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)][poetry]

[pypi status]: https://pypi.org/project/ssb-poc-statlog-model/
[documentation]: https://statisticsnorway.github.io/ssb-poc-statlog-model
[tests]: https://github.com/statisticsnorway/ssb-poc-statlog-model/actions?workflow=Tests
[sonarcov]: https://sonarcloud.io/summary/overall?id=statisticsnorway_ssb-poc-statlog-model
[sonarquality]: https://sonarcloud.io/summary/overall?id=statisticsnorway_ssb-poc-statlog-model
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black
[poetry]: https://python-poetry.org/

## Features

- Contains json schema models for the data to be logged.
- Contains pydantic models, that is python data validation classes for the json schemas.

## Requirements

- Python >= 3.13

## Installation

You can install _SSB POC Statlog Model_ via [pip] from [PyPI]:

```console
pip install ssb-poc-statlog-model
```

## Usage

Please see the [Reference Guide] for API details. A quick example using the
generated `ChangeDataLog` model:

```python
from datetime import datetime, timezone
from ssb_poc_statlog_model.change_data_log import ChangeDataLog, DataChangeType

change = ChangeDataLog(
    statistics_name="arblonn",
    data_source=[{"path": "gs://ssb-prod-superteam-data-produkt/arblonn/inndata/arbeidloenn_p2023-12_v1.parquet", "generation": "123"}],
    data_target="gs://ssb-prod-superteam-data-produkt/arblonn/klargjorte-data/arbeidloenn_p2023-12_v1.parquet",
    data_period="2023-12",
    change_event="A",
    change_event_reason="OTHER_SOURCE",
    change_datetime = datetime(2024, 1, 10, 15, 0, tzinfo=timezone.utc),
    changed_by="user@example.com",
    data_change_type=DataChangeType.NEW,
    change_comment="Opprettet ny enhet (person) fra ny datakilde ...",
    change_details={
        "detail_type": "unit",
        "unit_id": [
            {"unit_id_variable": "fnr", "unit_id_value": "170598nnnnn"},
            {"unit_id_variable": "orgnr", "unit_id_value": "123456789"}
        ],
        "new_value": [
            {"variable_name": "bostedskommune", "value": "0101"},
            {"variable_name": "type_loenn", "value": "time"},
            {"variable_name": "loenn", "value": "38000"},
            {"variable_name": "overtid_loenn", "value": "3000"}
        ]
    }
)

print(change.model_dump_json())
```

Tip about timestamps in JSON: use ISO 8601 with timezone information (e.g. `…Z` for
UTC) to satisfy Pydantic’s `AwareDatetime` requirement used in several models.

## Development Model Changes

The development branch uses `ssb_poc_statlog_model.lineage.Lineage` (corrected
from the former misspelling) with lineage schema version `3.0.0`. Input/output
entries are now objects, not strings:

```python
from datetime import UTC, datetime
from ssb_poc_statlog_model.lineage import Lineage

lineage = Lineage(
    event_id="event-1",
    segment_id="segment-1",
    recorded_at=datetime.now(UTC),
    data_source=[{"path": "gs://source-bucket/input_v1.parquet", "generation": "123"}],
    data_target=[{"path": "gs://target-bucket/output_v1.parquet", "generation": "456"}],
    git_commit_hash="actual-commit",
    git_dirty=False,
    git_repository="https://github.com/statisticsnorway/example",
    image_name="registry/image:tag",
    dapla_environment="PROD",
    timezone="Europe/Oslo",
    producer_metadata={"method": "prepare"},
)
```

`path` must be a GCS object URI. `generation` is a decimal string or unknown
(`None`); identity is the pair, not the generation alone. This replaces the
old parallel input-checksum field. Existing lineage imports and payloads need
migration; there is no alias for the misspelled class/module.

Partitioned Parquet uses the dataset root and an inline, complete member list:

```python
dataset = {
    "path": "gs://target-bucket/output_p2026_v1/",
    "members": [
        {"path": "year=2026/part-0.parquet", "generation": "456"},
        {"path": "year=2026/part-1.parquet", "generation": "457"},
    ],
}
```

Members use unique relative paths and are sorted by path. Root generation and
members are mutually exclusive. The logger must collect a stable, complete list;
validation cannot prove completeness. No separate manifest model/file is needed.
Release `data_source`, change `data_source`, and result `data_location` use the
same reference shape. Non-GCS artifacts are outside this development scope.

All main models support optional `event_id`, timezone-aware `recorded_at`, and
`producer_metadata` (nested JSON-compatible team details). Lineage, change logs,
and quality results also support optional `segment_id`; definitions and releases
are not owned by a single transformation segment. No session ID or separate
context/status record is introduced. The logger will supply IDs and timestamps;
the models do not generate them or query environment variables themselves.

Lineage carries optional Git commit/dirty state, image and Dapla environment
fields, execution start/end times, timezone, UTC offset, and configured `TZ`.
Release retains its required Git commit and adds optional `git_dirty`.
Both release and lineage support `git_repository`; configuration belongs in that
version-controlled repository. Unknown fields are rejected; custom details belong
only in `producer_metadata`.
No separate runtime-version fields are collected. Git provenance is not repeated on quality
or change events. Missing dirty state is unknown, not clean.

Quality results add optional scalar `value` and `unit`, separate from their
optional categorical outcome. At least one non-null value or outcome is required;
zero and False are valid. Execution errors raise in caller code and produce no
result; `quality_control_run_exception` has been removed. Scalar types are preserved and numeric
values must be finite. Optional `gsbpm_code` is available on quality definitions,
lineage, and changes; classification 933 is implicit. The model checks code shape,
not codelist membership, and results refer to their definition's code.

Definitions require `quality_control_name`; history groups by name and recording
timestamp. Logger registration should warn that a new name may be a rename that
breaks history grouping. No predecessor link is required.

Change/quality schemas are now `3.0.0`, release is `2.0.0`. Explicit old schema
version literals must be migrated. These are unreleased development changes;
the package version and published dependency constraints have not been changed.
When writing schema-valid JSON, use `model_dump_json(exclude_none=True)` to omit
unset legacy optional fields whose schemas do not permit explicit null values.

## Project structure

- `src/model` → JSON Schemas for the domain models (source of truth)
  - `example_logs/*.json` → Example payloads used in tests
- `src/ssb_poc_statlog_model` → Generated Pydantic models (Python)
- `src/scripts` → Scripts for generating examples from the pydantic models
- `tests` → Pytest suite validating models and examples

## Schema versioning

The schema version is defined in the `schema_version` and `$id` field in the root
of each schema. It uses semantic versioning (major.minor.patch) with the following rules:

- **Major (breaking change)**:
  - Field removed or renamed
  - Field type changed
  - Required field added
- **Minor (backward compatible)**:
  - New optional field added
  - Enum extended
- **Patch (non-structural change)**:
  - Description changes





## Development

Set up the environment (installs runtime + dev tools):

```console
poetry install
```

Run tests:

```console
poetry run pytest -v
```

Code style and quality:

```console
poetry run pre-commit run --all-files
```

### Regenerate the Pydantic models from JSON Schemas

This repository keeps the source of truth for the models as JSON Schema files in
`src\model`. Python classes are generated into `src\ssb_poc_statlog_model` using
`datamodel-code-generator` via a small helper CLI.

You can run the generator using the console script (defined in `pyproject.toml`).
All examples assume you are in the project root.

```console
# Ensure dev dependencies are available (only needed once)
poetry install

# Generate models for all *-json-schema.json files under src/model
poetry run generate-ssb-models
```

Useful options:

- Generate a single schema only:

```console
poetry run generate-ssb-models --schemas src/model/change-data-log-json-schema.json
```

- Use explicit directories (defaults shown):

```console
poetry run generate-ssb-models \
  --schemas-dir src/model \
  --out-dir src/ssb_poc_statlog_model
```

- Forward extra flags directly to `datamodel-code-generator` (repeatable):

```console
poetry run generate-ssb-models \
  --extra-arg --collapse-root \
  --extra-arg --use-schema-description
```

What the helper does under the hood:
- Discovers `*-json-schema.json` files in `src/model` (or uses `--schemas` if given)
- Runs `datamodel-code-generator` targeting Pydantic v2 with options compatible with
  Python 3.10+ (see `src/ssb_poc_statlog_model/generate_python.py` for the exact flags)
- Writes the generated models into `src/ssb_poc_statlog_model`

After regenerating, commit the updated Python files to version control.

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [MIT license][license],
_SSB POC Statlog Model_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from [Statistics Norway]'s [SSB PyPI Template].

[statistics norway]: https://www.ssb.no/en
[pypi]: https://pypi.org/
[ssb pypi template]: https://github.com/statisticsnorway/ssb-pypitemplate
[file an issue]: https://github.com/statisticsnorway/ssb-poc-statlog-model/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/statisticsnorway/ssb-poc-statlog-model/blob/main/LICENSE
[contributor guide]: https://github.com/statisticsnorway/ssb-poc-statlog-model/blob/main/CONTRIBUTING.md
[reference guide]: https://statisticsnorway.github.io/ssb-poc-statlog-model/reference.html
