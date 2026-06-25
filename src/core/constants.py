from __future__ import annotations

from pathlib import Path
from typing import Final

APP_NAME: Final[str] = "enterprise-etl-pipeline"
APP_VERSION: Final[str] = "3.0.0"

SUPPORTED_INPUT_SUFFIXES: Final[set[str]] = {".csv", ".xlsx", ".xls"}
DEFAULT_ENCODING: Final[str] = "utf-8"

DEFAULT_DROP_RATE_THRESHOLDS: Final[dict[str, float]] = {
    "low": 0.10,
    "medium": 0.30,
    "high": 0.50,
}

DEFAULT_ALERT_THRESHOLDS: Final[dict[str, float | int]] = {
    "drop_rate": 0.50,
    "invalid_emails": 1000,
    "invalid_phones": 1500,
}

DEFAULT_SEVERITY_LABELS: Final[dict[str, str]] = {
    "low": "LOW",
    "medium": "MEDIUM",
    "high": "HIGH",
}

DEFAULT_REQUIRED_COLUMNS: Final[tuple[str, ...]] = ()

DEFAULT_CHUNK_SIZE: Final[int] = 100_000
DEFAULT_MAX_REPORT_ROWS: Final[int] = 200_000
DEFAULT_MAX_COLUMN_WIDTH: Final[int] = 60
DEFAULT_COLUMN_WIDTH_SAMPLE_ROWS: Final[int] = 500

PRODUCTION_ENV_NAMES: Final[set[str]] = {"prod", "production"}

REPO_HARDENING_FILES: Final[tuple[Path, ...]] = (
    Path(".gitignore"),
    Path(".dockerignore"),
)
