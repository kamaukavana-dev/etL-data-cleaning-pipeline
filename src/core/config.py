from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from src.core.constants import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_MAX_REPORT_ROWS,
    DEFAULT_REQUIRED_COLUMNS,
    PRODUCTION_ENV_NAMES,
)
from src.core.exceptions import ConfigurationError

LOGGER = logging.getLogger("etl.config")


@dataclass(frozen=True)
class PathConfig:
    project_root: Path
    env_file: Path
    config_dir: Path
    thresholds_file: Path
    logging_file: Path
    data_dir: Path
    raw_data_dir: Path
    processed_data_dir: Path
    reports_dir: Path
    exports_dir: Path
    logs_dir: Path
    temp_dir: Path
    emails_dir: Path
    templates_dir: Path
    schema_file: Path


@dataclass(frozen=True)
class SMTPConfig:
    server: str | None
    port: int | None
    user: str | None
    password: str | None
    sender_email: str | None
    recipient_email: str | None
    disabled_reason: str | None = None

    @property
    def is_enabled(self) -> bool:
        return self.disabled_reason is None


@dataclass(frozen=True)
class AppConfig:
    app_name: str
    app_version: str
    environment: str
    client_name: str
    dry_run: bool
    data_file: Path
    required_columns: tuple[str, ...]
    enable_streaming_for_csv: bool
    csv_chunk_size: int
    stream_file_size_mb_threshold: int
    max_report_rows: int
    include_cleaned_data_in_report: bool
    report_mode: str
    report_format: str
    enable_excel_formatting: bool
    json_logs: bool
    log_level: str
    sentry_dsn: str | None
    otel_endpoint: str | None
    enable_prometheus_exporter: bool
    prometheus_port: int
    paths: PathConfig
    smtp: SMTPConfig
    alert_email: str | None


def discover_project_root() -> Path:
    """
    Resolve project root deterministically from module location or PROJECT_ROOT override.
    """
    override = os.getenv("PROJECT_ROOT")
    if override:
        root = Path(override).expanduser().resolve(strict=False)
    else:
        root = Path(__file__).resolve().parent.parent.parent

    if not root.exists():
        raise ConfigurationError(
            "Resolved project root does not exist.",
            error_code="CFG_PROJECT_ROOT_NOT_FOUND",
            context={"attempted_path": str(root)},
        )
    if not root.is_dir():
        raise ConfigurationError(
            "Resolved project root is not a directory.",
            error_code="CFG_PROJECT_ROOT_INVALID",
            context={"attempted_path": str(root)},
        )
    return root


def build_path_config(project_root: Path) -> PathConfig:
    return PathConfig(
        project_root=project_root,
        env_file=project_root / ".env",
        config_dir=project_root / "config",
        thresholds_file=project_root / "config" / "thresholds.yaml",
        logging_file=project_root / "config" / "logging.yaml",
        data_dir=project_root / "data",
        raw_data_dir=project_root / "data" / "raw",
        processed_data_dir=project_root / "data" / "processed",
        reports_dir=project_root / "data" / "reports",
        exports_dir=project_root / "data" / "exports",
        logs_dir=project_root / "logs",
        temp_dir=project_root / "tmp",
        emails_dir=project_root / "emails",
        templates_dir=project_root / "emails" / "templates",
        schema_file=project_root / "config" / "schema.yaml",
    )


def load_environment(env_file: Path, *, allow_missing: bool = True) -> bool:
    if not env_file.exists():
        if allow_missing:
            return False
        raise ConfigurationError(
            "Environment file is missing.",
            error_code="CFG_ENV_FILE_MISSING",
            context={"attempted_path": str(env_file)},
        )

    try:
        load_dotenv(dotenv_path=env_file, override=False)
        return True
    except Exception as exc:  # pragma: no cover - defensive
        raise ConfigurationError(
            "Failed to load .env file.",
            error_code="CFG_ENV_LOAD_FAILED",
            context={"attempted_path": str(env_file)},
        ) from exc


def parse_bool(raw: str | None, *, default: bool = False) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_int(raw: str | None, *, default: int, field_name: str) -> int:
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigurationError(
            f"Invalid integer value for {field_name}.",
            error_code="CFG_INVALID_INTEGER",
            context={"field": field_name, "value": raw},
        ) from exc
    return value


def parse_choice(raw: str | None, *, default: str, allowed: set[str], field_name: str) -> str:
    candidate = (raw or default).strip().lower()
    if candidate not in allowed:
        raise ConfigurationError(
            f"Invalid value for {field_name}.",
            error_code="CFG_INVALID_CHOICE",
            context={"field": field_name, "value": candidate, "allowed": sorted(allowed)},
            remediation_hint=f"Use one of: {', '.join(sorted(allowed))}",
        )
    return candidate


def read_env_value(key: str) -> str | None:
    raw = os.getenv(key)
    if raw is None:
        return None
    value = raw.strip()
    return value or None


def require_env(key: str) -> str:
    value = read_env_value(key)
    if value is None:
        raise ConfigurationError(
            f"Missing required environment variable: {key}",
            error_code="CFG_REQUIRED_ENV_MISSING",
            context={"variable": key},
        )
    return value


def resolve_path(value: str, *, project_root: Path) -> Path:
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = project_root / candidate
    return candidate.resolve(strict=False)


def parse_required_columns(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()

    cols = tuple(col.strip().lower() for col in raw.split(",") if col.strip())
    return cols


def build_smtp_config() -> SMTPConfig:
    keys = (
        "SMTP_SERVER",
        "SMTP_PORT",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "SENDER_EMAIL",
        "RECIPIENT_EMAIL",
    )
    values = {key: read_env_value(key) for key in keys}
    missing = [key for key, value in values.items() if value is None]

    if len(missing) == len(keys):
        return SMTPConfig(
            server=None,
            port=None,
            user=None,
            password=None,
            sender_email=None,
            recipient_email=None,
            disabled_reason="SMTP disabled: optional configuration not provided.",
        )

    if missing:
        return SMTPConfig(
            server=values["SMTP_SERVER"],
            port=None,
            user=values["SMTP_USER"],
            password=values["SMTP_PASSWORD"],
            sender_email=values["SENDER_EMAIL"],
            recipient_email=values["RECIPIENT_EMAIL"],
            disabled_reason=f"SMTP disabled: incomplete configuration missing {', '.join(sorted(missing))}.",
        )

    raw_port = values["SMTP_PORT"]
    try:
        parsed_port = int(raw_port) if raw_port is not None else None
    except ValueError:
        return SMTPConfig(
            server=values["SMTP_SERVER"],
            port=None,
            user=values["SMTP_USER"],
            password=values["SMTP_PASSWORD"],
            sender_email=values["SENDER_EMAIL"],
            recipient_email=values["RECIPIENT_EMAIL"],
            disabled_reason=f"SMTP disabled: invalid SMTP_PORT '{raw_port}'.",
        )

    if parsed_port is None or not (1 <= parsed_port <= 65535):
        return SMTPConfig(
            server=values["SMTP_SERVER"],
            port=None,
            user=values["SMTP_USER"],
            password=values["SMTP_PASSWORD"],
            sender_email=values["SENDER_EMAIL"],
            recipient_email=values["RECIPIENT_EMAIL"],
            disabled_reason=f"SMTP disabled: SMTP_PORT out of range '{raw_port}'.",
        )

    return SMTPConfig(
        server=values["SMTP_SERVER"],
        port=parsed_port,
        user=values["SMTP_USER"],
        password=values["SMTP_PASSWORD"],
        sender_email=values["SENDER_EMAIL"],
        recipient_email=values["RECIPIENT_EMAIL"],
        disabled_reason=None,
    )


def validate_secret_strategy(config: AppConfig, *, env_loaded_from_file: bool) -> list[str]:
    warnings: list[str] = []
    if env_loaded_from_file and config.environment in PRODUCTION_ENV_NAMES:
        warnings.append(
            "Production mode is loading secrets from .env file. Use a secret manager or injected environment variables."
        )
    if config.smtp.password:
        lowered = config.smtp.password.lower()
        if lowered in {"changeme", "example", "password", "secret"}:
            warnings.append("SMTP password appears to be a placeholder value.")
    return warnings


def bootstrap_filesystem(config: AppConfig) -> None:
    required_dirs = (
        config.paths.data_dir,
        config.paths.raw_data_dir,
        config.paths.config_dir,
    )
    managed_dirs = (
        config.paths.processed_data_dir,
        config.paths.reports_dir,
        config.paths.exports_dir,
        config.paths.logs_dir,
        config.paths.temp_dir,
    )

    for directory in required_dirs:
        if not directory.exists():
            raise ConfigurationError(
                "Required directory is missing.",
                error_code="CFG_REQUIRED_DIR_MISSING",
                context={"attempted_path": str(directory)},
            )
        if not directory.is_dir():
            raise ConfigurationError(
                "Required path exists but is not a directory.",
                error_code="CFG_REQUIRED_DIR_INVALID",
                context={"attempted_path": str(directory)},
            )

    for directory in managed_dirs:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ConfigurationError(
                "Failed to initialize managed directory.",
                error_code="CFG_MANAGED_DIR_INIT_FAILED",
                context={"attempted_path": str(directory)},
            ) from exc

    if not config.paths.thresholds_file.exists():
        raise ConfigurationError(
            "Threshold configuration file is missing.",
            error_code="CFG_THRESHOLDS_FILE_MISSING",
            context={"attempted_path": str(config.paths.thresholds_file)},
        )

    if not config.paths.logging_file.exists():
        raise ConfigurationError(
            "Logging configuration file is missing.",
            error_code="CFG_LOGGING_FILE_MISSING",
            context={"attempted_path": str(config.paths.logging_file)},
        )

    if not config.data_file.exists():
        raise ConfigurationError(
            "Configured data file does not exist.",
            error_code="CFG_DATA_FILE_MISSING",
            context={"attempted_path": str(config.data_file)},
        )
    if not config.data_file.is_file():
        raise ConfigurationError(
            "Configured data file path is not a file.",
            error_code="CFG_DATA_FILE_INVALID",
            context={"attempted_path": str(config.data_file)},
        )


def load_config(
    *,
    project_root: Path | None = None,
    env_file: Path | None = None,
    dotenv_optional: bool = True,
) -> tuple[AppConfig, list[str]]:
    """
    Build immutable application configuration.
    No filesystem writes occur in this function.
    """
    resolved_project_root = project_root or discover_project_root()
    paths = build_path_config(resolved_project_root)

    target_env_file = env_file or paths.env_file
    env_loaded = load_environment(target_env_file, allow_missing=dotenv_optional)

    data_file_raw = require_env("DATA_FILE")
    data_file = resolve_path(data_file_raw, project_root=resolved_project_root)

    smtp = build_smtp_config()
    environment = parse_choice(
        read_env_value("APP_ENV"),
        default="dev",
        allowed={"dev", "test", "prod"},
        field_name="APP_ENV",
    )

    app_config = AppConfig(
        app_name=APP_NAME,
        app_version=APP_VERSION,
        environment=environment,
        client_name=read_env_value("CLIENT_NAME") or "Enterprise_Client",
        dry_run=parse_bool(read_env_value("DRY_RUN"), default=False),
        data_file=data_file,
        required_columns=parse_required_columns(read_env_value("REQUIRED_COLUMNS")),
        enable_streaming_for_csv=parse_bool(read_env_value("ENABLE_STREAMING_FOR_CSV"), default=True),
        csv_chunk_size=parse_int(
            read_env_value("CSV_CHUNK_SIZE"),
            default=DEFAULT_CHUNK_SIZE,
            field_name="CSV_CHUNK_SIZE",
        ),
        stream_file_size_mb_threshold=parse_int(
            read_env_value("STREAM_FILE_SIZE_MB_THRESHOLD"),
            default=100,
            field_name="STREAM_FILE_SIZE_MB_THRESHOLD",
        ),
        max_report_rows=parse_int(
            read_env_value("MAX_REPORT_ROWS"),
            default=DEFAULT_MAX_REPORT_ROWS,
            field_name="MAX_REPORT_ROWS",
        ),
        include_cleaned_data_in_report=parse_bool(
            read_env_value("INCLUDE_CLEANED_DATA_IN_REPORT"),
            default=True,
        ),
        report_mode=parse_choice(
            read_env_value("REPORT_MODE"),
            default="standard",
            allowed={"minimal", "standard", "detailed"},
            field_name="REPORT_MODE",
        ),
        report_format=parse_choice(
            read_env_value("REPORT_FORMAT"),
            default="excel",
            allowed={"excel", "csv", "parquet"},
            field_name="REPORT_FORMAT",
        ),
        enable_excel_formatting=parse_bool(read_env_value("ENABLE_EXCEL_FORMATTING"), default=False),
        json_logs=parse_bool(read_env_value("JSON_LOGS"), default=True),
        log_level=(read_env_value("LOG_LEVEL") or "INFO").upper(),
        sentry_dsn=read_env_value("SENTRY_DSN"),
        otel_endpoint=read_env_value("OTEL_EXPORTER_OTLP_ENDPOINT"),
        enable_prometheus_exporter=parse_bool(read_env_value("ENABLE_PROMETHEUS_EXPORTER"), default=False),
        prometheus_port=parse_int(
            read_env_value("PROMETHEUS_PORT"),
            default=9090,
            field_name="PROMETHEUS_PORT",
        ),
        paths=paths,
        smtp=smtp,
        alert_email=read_env_value("ALERT_EMAIL") or smtp.sender_email,
    )

    warnings = validate_secret_strategy(app_config, env_loaded_from_file=env_loaded)
    return app_config, warnings


def diagnostics(config: AppConfig, warnings: list[str]) -> dict[str, Any]:
    return {
        "project_root": str(config.paths.project_root),
        "env_file": str(config.paths.env_file),
        "env_file_exists": config.paths.env_file.exists(),
        "data_dir_exists": config.paths.data_dir.exists(),
        "reports_dir_exists": config.paths.reports_dir.exists(),
        "logging_file": str(config.paths.logging_file),
        "logging_file_exists": config.paths.logging_file.exists(),
        "data_file": str(config.data_file),
        "data_file_exists": config.data_file.exists(),
        "smtp_enabled": config.smtp.is_enabled,
        "smtp_reason": config.smtp.disabled_reason,
        "warnings": warnings,
    }
