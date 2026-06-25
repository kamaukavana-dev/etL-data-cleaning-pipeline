from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.core.config import load_config
from src.services.analysis_service import AnalysisService
from src.services.validation_service import ValidationService


def test_validation_empty_dataframe(runtime_root: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_FILE", "data/raw/empty.csv")
    (runtime_root / "data" / "raw" / "empty.csv").write_text("id,name,email,phone,salary,date_joined\n", encoding="utf-8")

    config, _ = load_config(project_root=runtime_root, env_file=runtime_root / ".env", dotenv_optional=True)
    service = ValidationService(config)
    df = pd.DataFrame(columns=["id", "name", "email", "phone", "salary", "date_joined"])

    result, _ = service.validate_and_clean(df)
    assert result.stats.original_rows == 0
    assert result.stats.final_rows == 0


def test_analysis_empty_dataframe() -> None:
    service = AnalysisService()
    df = pd.DataFrame()
    result = service.analyze(df)
    assert result["meta"]["row_count"] == 0
