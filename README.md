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

- Python >= 3.10

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

payload = {
    "statistics_name": "arblonn",
    "data_source": ["gs://ssb-myteam-produkt-prod/arblonn/inndata/arbeidloenn_p2023-12_v1.parquet"],
    "data_target": "gs://ssb-myteam-produkt-prod/arblonn/klargjorte-data/arbeidloenn_p2023-12_v1.parquet",
    "data_period": "2023-12",
    "change_event": "A",
    "change_event_reason": "OTHER_SOURCE",
    "change_datetime": datetime(2024, 1, 10, 15, 0, tzinfo=timezone.utc),
    "changed_by": "user@example.com",
    "data_change_type": DataChangeType.NEW,
    "change_comment": "Opprettet ny enhet (person) fra ny datakilde ...",
    "change_details": {
        "kind": "unit",
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
}

model = ChangeDataLog(**payload)
print(model.model_dump())
```

Tip about timestamps in JSON: use ISO 8601 with timezone information (e.g. `…Z` for
UTC) to satisfy Pydantic’s `AwareDatetime` requirement used in several models.

## Project structure

- `src/model` → JSON Schemas for the domain models (source of truth)
  - `example_log_change_data/*.json` → Example payloads used in tests
- `src/ssb_poc_statlog_model` → Generated Pydantic models (Python)
- `tests` → Pytest suite validating models and examples

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
