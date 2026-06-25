from __future__ import annotations

import logging
import threading
from typing import Any

from prometheus_client import start_http_server

from src.core.config import AppConfig

LOGGER = logging.getLogger("etl.prometheus")

class PrometheusService:
    """
    Handles the explicit export of Prometheus metrics.
    Can start a standalone HTTP server for scraping.
    """
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._server_thread: threading.Thread | None = None
        self._port = int(getattr(config, "prometheus_port", 9090))
        self._enabled = getattr(config, "enable_prometheus_exporter", False)

    def start_exporter(self) -> None:
        if not self._enabled:
            LOGGER.info("Prometheus exporter is disabled.")
            return

        try:
            LOGGER.info(f"Starting Prometheus exporter on port {self._port}...")
            start_http_server(self._port)
            LOGGER.info(f"Prometheus exporter is live at http://localhost:{self._port}/metrics")
        except Exception as exc:
            LOGGER.error(f"Failed to start Prometheus exporter: {exc}")

    @staticmethod
    def get_metrics_text() -> str:
        """Helper to get metrics as text without a server."""
        from src.core.observability import RunTelemetry
        # This assumes RunTelemetry is using the global REGISTRY
        from src.core.observability import generate_latest, REGISTRY
        return generate_latest(REGISTRY).decode("utf-8")
