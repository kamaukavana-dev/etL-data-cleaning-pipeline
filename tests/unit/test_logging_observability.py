from __future__ import annotations

import logging

from src.core.logging import get_logger
from src.core.observability import RunTelemetry


def test_logger_name_is_canonicalized() -> None:
    logger = get_logger("src.services.validation_service", run_id="r1")
    assert logger.logger.name.startswith("etl.")


def test_telemetry_snapshot_contains_performance_fields() -> None:
    base_logger = logging.getLogger("etl.test")
    logger = logging.LoggerAdapter(base_logger, {"run_id": "r1"})
    telemetry = RunTelemetry()

    with telemetry.measure_stage(logger=logger, stage="validation", rows_in=10):
        _ = [x for x in range(10)]

    snapshot = telemetry.snapshot()
    assert snapshot
    stage = snapshot[0]
    assert "duration_ms" in stage
    assert "rows_per_second" in stage
    assert "memory_usage_mb" in stage

