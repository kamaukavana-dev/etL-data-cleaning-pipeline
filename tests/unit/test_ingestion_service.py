from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.core.config import load_config
from src.services.ingestion_service import IngestionService


def test_excel_combine_mode_returns_dataframe(runtime_root: Path, monkeypatch) -> None:
    excel_path = runtime_root / "data" / "raw" / "sample.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        pd.DataFrame({"ID": [1], "Name": ["Alice"], "Email": ["a@example.com"], "Phone": ["+1234567890"], "Salary": [100], "Date": ["2024-01-01"]}).to_excel(
            writer, sheet_name="sheet_a", index=False
        )
        pd.DataFrame({"ID": [2], "Name": ["Bob"], "Email": ["b@example.com"], "Phone": ["+1234567891"], "Salary": [120], "Date": ["2024-01-02"]}).to_excel(
            writer, sheet_name="sheet_b", index=False
        )

    monkeypatch.setenv("DATA_FILE", str(excel_path))
    monkeypatch.setenv("EXCEL_SHEET_MODE", "combine_sheets")

    config, _ = load_config(project_root=runtime_root, env_file=runtime_root / ".env", dotenv_optional=True)
    service = IngestionService(config)
    result = service.load()

    assert isinstance(result.dataframe, pd.DataFrame)
    assert "source_sheet" in result.dataframe.columns
    assert len(result.dataframe) == 2


def test_ingestion_rejects_unsupported_suffix(runtime_root: Path, monkeypatch) -> None:
    file_path = runtime_root / "data" / "raw" / "bad.json"
    file_path.write_text("{}", encoding="utf-8")

    monkeypatch.setenv("DATA_FILE", str(file_path))
    config, _ = load_config(project_root=runtime_root, env_file=runtime_root / ".env", dotenv_optional=True)
    service = IngestionService(config)

    try:
        service.load()
    except Exception as exc:
        assert "unsupported" in str(exc).lower()
    else:
        raise AssertionError("Expected unsupported file type error.")


def test_csv_chunking_matches_in_memory(runtime_root: Path, monkeypatch) -> None:
    csv_path = runtime_root / "data" / "raw" / "sample.csv"
    csv_path.write_text(
        "ID,Name,Email,Phone,Salary,Date,Notes\n"
        "1,Alice,alice@example.com,+1234567890,100,2024-01-01,\n"
        "2,Bob,,+1234567891,120,2024-01-02,NA\n"
        "3,Carla,carla@example.com,, ,,note\n"
        "4,Dan,dan@example.com,+1234567892,130,2024-01-04,ok\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("DATA_FILE", str(csv_path))
    monkeypatch.setenv("CSV_CHUNK_SIZE", "2")

    config, _ = load_config(project_root=runtime_root, env_file=runtime_root / ".env", dotenv_optional=True)
    service = IngestionService(config)

    in_memory = service._load_csv(csv_path)
    streamed = pd.concat(list(service.iter_csv_chunks(csv_path)), ignore_index=True)

    pd.testing.assert_frame_equal(in_memory, streamed)
