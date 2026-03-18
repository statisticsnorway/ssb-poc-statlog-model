from datetime import UTC, datetime
from pathlib import Path

from ssb_poc_statlog_model.change_data_log import (
    ChangeDataLog,
    DataChangeType,
)
from ssb_poc_statlog_model.linage import Linage
from ssb_poc_statlog_model.release import Release

OUTPUT_DIR = Path(__file__).parent.parent.parent / "src" / "model" / "example_logs"

change = ChangeDataLog(
    statistics_name="arblonn",
    data_source=[
        "gs://ssb-prod-superteam-data-produkt/arblonn/inndata/arbeidloenn_p2023-12_v1.parquet"
    ],
    data_target="gs://ssb-prod-superteam-data-produkt/arblonn/klargjorte-data/arbeidloenn_p2023-12_v1.parquet",
    data_period="2023-12",
    change_event="A",
    change_event_reason="OTHER_SOURCE",
    change_datetime=datetime(2024, 1, 10, 15, 0, tzinfo=UTC),
    changed_by="user@example.com",
    data_change_type=DataChangeType.NEW,
    change_comment="Opprettet ny enhet (person) fra ny datakilde ...",
    change_details={
        "detail_type": "unit",
        "unit_id": [
            {"unit_id_variable": "fnr", "unit_id_value": "170598nnnnn"},
            {"unit_id_variable": "orgnr", "unit_id_value": "123456789"},
        ],
        "new_value": [
            {"variable_name": "bostedskommune", "value": "0101"},
            {"variable_name": "type_loenn", "value": "time"},
            {"variable_name": "loenn", "value": "38000"},
            {"variable_name": "overtid_loenn", "value": "3000"},
        ],
    },
)
print(change.model_dump_json())
change_file = OUTPUT_DIR / "example_change_data_log.json"
change_file.write_text(change.model_dump_json(indent=2))

release = Release(
    statistics_name="metstat",
    git_tag="2025.12",
    git_commit_hash="5faec80b4746112ef9df340cbaf779bff0a00a7f",
    data_source=[
        "gs://ssb-tip-tutorials-data-produkt-prod/metstat/utdata/observations_p2025-12-01_p2025-12-31_v1.parquet",
        "gs://ssb-tip-tutorials-data-produkt-prod/metstat/utdata/weather_stations_p2025-01-01_v1.parquet",
    ],
    daplalab_image="ghcr.io/statisticsnorway/daplalab-jupyter:0.18.10",
)
print(release.model_dump_json())
release_file = OUTPUT_DIR / "example_release_log.json"
release_file.write_text(release.model_dump_json(indent=2))

linage = Linage(
    data_source=[
        "gs://ssb-tip-tutorials-data-produkt-prod/metstat/inndata/observations_p2025-12-01_p2025-12-31_v1.parquet",
    ],
    data_target=[
        "gs://ssb-tip-tutorials-data-produkt-prod/metstat/klargjorte-data/observations_p2025-12-01_p2025-12-31_v1.parquet",
    ],
)
print(linage.model_dump_json())
linage_file = OUTPUT_DIR / "example_linage_log.json"
linage_file.write_text(linage.model_dump_json(indent=2))
