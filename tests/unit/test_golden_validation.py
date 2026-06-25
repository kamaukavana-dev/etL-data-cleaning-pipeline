from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.core.config import load_config
from src.services.validation_service import ValidationService


def test_golden_validation_stats(runtime_root: Path, monkeypatch) -> None:
    source = Path("tests/fixtures/dirty_small.csv").resolve(strict=False)
    golden = Path("tests/golden/expected_stats_dirty_small.json").resolve(strict=False)

    target_csv = runtime_root / "data" / "raw" / "dirty_small.csv"
    target_csv.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    monkeypatch.setenv("DATA_FILE", str(target_csv))
    config, _ = load_config(project_root=runtime_root, env_file=runtime_root / ".env", dotenv_optional=True)
    service = ValidationService(config)

    df = pd.read_csv(target_csv)
    result, _ = service.validate_and_clean(df)
    expected = json.loads(golden.read_text(encoding="utf-8"))

    assert result.stats.original_rows == expected["original_rows"]
    assert result.stats.final_rows == expected["final_rows"]
    assert result.stats.duplicates_dropped == expected["duplicates_dropped"]
    assert result.stats.invalid_emails_dropped == expected["invalid_emails_dropped"]
    assert result.stats.invalid_phones_dropped == expected["invalid_phones_dropped"]
    assert result.stats.invalid_numbers_dropped == expected["invalid_numbers_dropped"]
    assert result.stats.invalid_dates_dropped == expected["invalid_dates_dropped"]
