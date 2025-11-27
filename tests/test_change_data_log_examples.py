import json
from pathlib import Path

import pytest

from ssb_poc_statlog_model.change_data_log import ChangeDataLog

EXAMPLES_DIR = Path(__file__).parents[1] / "src" / "model" / "example_log_change_data"


def _iter_example_files() -> list[Path]:
    return sorted(EXAMPLES_DIR.glob("*.json"))


@pytest.mark.parametrize("file", _iter_example_files(), ids=lambda p: p.name)
def test_validate_file(file: Path) -> None:
    payload = json.loads(file.read_text(encoding="utf-8"))
    ChangeDataLog(**payload)
