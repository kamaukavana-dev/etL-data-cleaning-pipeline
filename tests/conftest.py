from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def runtime_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / "config").mkdir(parents=True)
    (root / "data" / "raw").mkdir(parents=True)
    (root / "data" / "processed").mkdir(parents=True)
    (root / "data" / "reports").mkdir(parents=True)
    (root / "data" / "exports").mkdir(parents=True)
    (root / "emails" / "templates").mkdir(parents=True)

    (root / "config" / "thresholds.yaml").write_text(
        "\n".join(
            [
                "thresholds:",
                "  drop_rate:",
                "    low: 0.10",
                "    medium: 0.30",
                "    high: 0.50",
                "  alerts:",
                "    drop_rate: 0.50",
                "    invalid_emails: 10",
                "    invalid_phones: 10",
                "  severity_labels:",
                '    low: "LOW"',
                '    medium: "MEDIUM"',
                '    high: "HIGH"',
            ]
        ),
        encoding="utf-8",
    )

    (root / "config" / "logging.yaml").write_text(
        "version: 1\nformatters: {}\nhandlers: {}\nroot: {}\n",
        encoding="utf-8",
    )

    (root / "emails" / "templates" / "report_email.txt").write_text(
        "Hello ${CLIENT_NAME}\nRows cleaned: ${ROWS_CLEANED}\n",
        encoding="utf-8",
    )

    return root


@pytest.fixture(autouse=True)
def clean_runtime_env(monkeypatch: pytest.MonkeyPatch) -> None:
    keys = [
        "APP_ENV",
        "CLIENT_NAME",
        "DATA_FILE",
        "DRY_RUN",
        "REQUIRED_COLUMNS",
        "ENABLE_STREAMING_FOR_CSV",
        "CSV_CHUNK_SIZE",
        "STREAM_FILE_SIZE_MB_THRESHOLD",
        "MAX_REPORT_ROWS",
        "INCLUDE_CLEANED_DATA_IN_REPORT",
        "REPORT_MODE",
        "REPORT_FORMAT",
        "ENABLE_EXCEL_FORMATTING",
        "LOG_LEVEL",
        "JSON_LOGS",
        "SENTRY_DSN",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "SMTP_SERVER",
        "SMTP_PORT",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "SENDER_EMAIL",
        "RECIPIENT_EMAIL",
        "ALERT_EMAIL",
        "EXCEL_SHEET_MODE",
        "EXCEL_SHEET_NAME",
        "PROJECT_ROOT",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)
