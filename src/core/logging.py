from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any

from src.core.config import AppConfig


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "line": record.lineno,
        }

        run_id = getattr(record, "run_id", None)
        if run_id:
            payload["run_id"] = run_id

        correlation_id = getattr(record, "correlation_id", None)
        if correlation_id:
            payload["correlation_id"] = correlation_id

        stage = getattr(record, "stage", None)
        if stage:
            payload["stage"] = stage

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


class ContextLogger(logging.LoggerAdapter):
    def process(self, msg: Any, kwargs: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        extra = kwargs.setdefault("extra", {})
        for key, value in self.extra.items():
            extra.setdefault(key, value)
        return msg, kwargs


def _canonical_logger_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        return "etl.unknown"
    if cleaned.startswith("etl."):
        return cleaned

    remapped = cleaned.replace("src.services.", "").replace("src.core.", "")
    remapped = remapped.replace("service", "").replace("_", ".")
    remapped = remapped.strip(".")
    return f"etl.{remapped or 'app'}"


def _build_extra_context(*, run_id: str, correlation_id: str | None = None) -> dict[str, Any]:
    extra: dict[str, Any] = {"run_id": run_id}
    if correlation_id:
        extra["correlation_id"] = correlation_id
    return extra


def configure_logging(config: AppConfig, *, run_id: str) -> None:
    root_logger = logging.getLogger()
    log_level = getattr(logging, config.log_level, logging.INFO)
    root_logger.setLevel(log_level)

    # Reset handlers for deterministic logger setup in repeated invocations.
    root_logger.handlers.clear()

    if config.json_logs:
        formatter: logging.Formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s [run_id=%(run_id)s]: %(message)s"
        )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    log_file = config.paths.logs_dir / "app.log"
    file_handler = RotatingFileHandler(log_file, maxBytes=10_000_000, backupCount=10)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Quiet noisy third-party logs unless explicitly overridden.
    if os.getenv("VERBOSE_THIRD_PARTY_LOGS", "0") != "1":
        logging.getLogger("urllib3").setLevel(logging.WARNING)

    root_logger.info(
        "Logging configured.",
        extra={"run_id": run_id, "stage": "startup"},
    )


def get_logger(name: str, *, run_id: str, correlation_id: str | None = None) -> ContextLogger:
    canonical = _canonical_logger_name(name)
    extra = _build_extra_context(run_id=run_id, correlation_id=correlation_id)
    return ContextLogger(logging.getLogger(canonical), extra=extra)
