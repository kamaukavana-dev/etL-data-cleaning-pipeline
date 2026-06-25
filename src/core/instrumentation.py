from __future__ import annotations

import logging

from src.core.config import AppConfig


def setup_sentry(config: AppConfig, logger: logging.LoggerAdapter) -> None:
    if not config.sentry_dsn:
        return
    try:
        import sentry_sdk  # type: ignore
    except ModuleNotFoundError:
        logger.warning(
            "SENTRY_DSN provided but sentry-sdk is not installed.",
            extra={"stage": "observability"},
        )
        return

    sentry_sdk.init(dsn=config.sentry_dsn, traces_sample_rate=0.1)
    logger.info("Sentry initialized.", extra={"stage": "observability"})


def setup_opentelemetry(config: AppConfig, logger: logging.LoggerAdapter) -> None:
    if not config.otel_endpoint:
        return
    try:
        from opentelemetry import trace  # type: ignore
    except ModuleNotFoundError:
        logger.warning(
            "OTEL endpoint provided but opentelemetry packages are not installed.",
            extra={"stage": "observability"},
        )
        return

    tracer_provider = trace.get_tracer_provider()
    logger.info(
        "OpenTelemetry hook enabled (provider detected).",
        extra={"stage": "observability", "tracer_provider": str(type(tracer_provider).__name__)},
    )
