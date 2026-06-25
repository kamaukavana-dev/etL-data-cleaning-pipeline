"""
Backward-compatible ingestion helpers.
Prefer src.services.ingestion_service.IngestionService.
"""

from pathlib import Path

import pandas as pd

from src.core.config import load_config
from src.services.ingestion_service import IngestionService


def _service() -> IngestionService:
    config, _ = load_config()
    return IngestionService(config)


def load_csv(filepath: str | Path, encoding: str = "utf-8") -> pd.DataFrame:
    _ = encoding
    return _service()._load_csv(Path(filepath).resolve(strict=False))


def load_excel(filepath: str | Path, *, sheet_name: str | None = None) -> pd.DataFrame:
    service = _service()
    if sheet_name:
        # Honor explicit legacy contract.
        frame = pd.read_excel(Path(filepath).resolve(strict=False), sheet_name=sheet_name)
        return service.normalize_columns(frame)
    frame, _mode = service._load_excel(Path(filepath).resolve(strict=False))
    return frame
