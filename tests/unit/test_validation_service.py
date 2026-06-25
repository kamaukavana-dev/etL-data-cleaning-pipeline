from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.core.config import load_config
from src.services.validation_service import ValidationService


def test_validation_drops_invalid_rows_vectorized(runtime_root: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_FILE", "data/raw/placeholder.csv")
    (runtime_root / "data" / "raw" / "placeholder.csv").write_text(
        "id,name,email,phone,salary,date_joined\n",
        encoding="utf-8",
    )

    config, _ = load_config(project_root=runtime_root, env_file=runtime_root / ".env", dotenv_optional=True)
    service = ValidationService(config)

    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "email": ["a@example.com", "invalid", "c@example.com"],
            "phone": ["+1234567890", "+1", "+1234567899"],
            "salary": ["100", "50", "-1"],
            "date_joined": ["2024-01-01", "2024-01-02", "invalid"],
        }
    )

    result, _ = service.validate_and_clean(df)

    assert result.stats.original_rows == 3
    assert result.stats.final_rows == 1
    assert result.stats.invalid_emails_dropped == 1
    assert result.stats.invalid_phones_dropped == 0
    assert result.stats.invalid_numbers_dropped == 1
    assert result.stats.invalid_dates_dropped == 0
