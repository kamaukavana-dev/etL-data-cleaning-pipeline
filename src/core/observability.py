from __future__ import annotations

import logging
import resource
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, generate_latest

# Global Prometheus Registry
REGISTRY = CollectorRegistry()

# Define Prometheus Metrics
FAILURES = Counter("etl_pipeline_failures_total", "Total number of pipeline failures", registry=REGISTRY)
HEARTBEATS = Counter("etl_pipeline_heartbeats_total", "Total number of heartbeats emitted", registry=REGISTRY)
STAGE_DURATION = Histogram(
    "etl_stage_duration_seconds", 
    "Duration of ETL stages in seconds", 
    ["stage", "status"], 
    registry=REGISTRY
)
ROWS_PROCESSED = Counter(
    "etl_rows_processed_total", 
    "Total number of rows processed", 
    ["stage"], 
    registry=REGISTRY
)
MEMORY_USAGE = Gauge(
    "etl_memory_usage_mb", 
    "Current memory usage in MB", 
    registry=REGISTRY
)

@dataclass
class StageMetric:
    name: str
    duration_ms: float
    cpu_time_seconds: float
    memory_usage_mb: float
    rows_processed: int
    rows_per_second: float
    io_read_mb: float
    io_write_mb: float
    status: str
    validation_error_counts: dict[str, int]
    rows_in: int = 0
    rows_out: int = 0
    error_count: int = 0


class RunTelemetry:
    def __init__(self) -> None:
        self.stage_metrics: list[StageMetric] = []
        self._counters: dict[str, int] = {
            "pipeline_failures_total": 0,
            "pipeline_retries_total": 0,
            "pipeline_heartbeats_total": 0,
        }

    def heartbeat(self, *, logger: logging.LoggerAdapter, stage: str, run_id: str) -> None:
        self._counters["pipeline_heartbeats_total"] += 1
        HEARTBEATS.inc()
        logger.info(
            "Pipeline heartbeat.",
            extra={
                "stage": stage,
                "run_id": run_id,
                "heartbeat_count": self._counters["pipeline_heartbeats_total"],
            },
        )

    @contextmanager
    def measure_stage(
        self,
        *,
        logger: logging.LoggerAdapter,
        stage: str,
        rows_in: int = 0,
        validation_error_counts: dict[str, int] | None = None,
    ) -> Iterator[None]:
        usage_start = resource.getrusage(resource.RUSAGE_SELF)
        process_cpu_start = time.process_time()
        start = time.perf_counter()
        try:
            logger.info("Stage started.", extra={"stage": stage, "rows_in": rows_in})
            yield
            duration = time.perf_counter() - start
            STAGE_DURATION.labels(stage=stage, status="ok").observe(duration)
            if rows_in > 0:
                ROWS_PROCESSED.labels(stage=stage).inc(rows_in)
            
            usage_end = resource.getrusage(resource.RUSAGE_SELF)
            cpu_time = max(time.process_time() - process_cpu_start, 0.0)
            rows_per_second = (rows_in / duration) if duration > 0 and rows_in > 0 else 0.0
            io_read_mb = max((usage_end.ru_inblock - usage_start.ru_inblock) / 1024.0, 0.0)
            io_write_mb = max((usage_end.ru_oublock - usage_start.ru_oublock) / 1024.0, 0.0)
            memory_mb = usage_end.ru_maxrss / 1024.0
            MEMORY_USAGE.set(memory_mb)
            
            metric = StageMetric(
                name=stage,
                duration_ms=duration * 1000,
                cpu_time_seconds=cpu_time,
                memory_usage_mb=memory_mb,
                rows_processed=rows_in,
                rows_per_second=rows_per_second,
                io_read_mb=io_read_mb,
                io_write_mb=io_write_mb,
                status="ok",
                validation_error_counts=validation_error_counts or {},
                rows_in=rows_in,
                rows_out=rows_in,
            )
            self.stage_metrics.append(metric)
            logger.info(
                "Stage completed.",
                extra={
                    "stage": stage,
                    "duration_ms": round(metric.duration_ms, 3),
                    "rows_processed": metric.rows_processed,
                    "rows_per_second": round(metric.rows_per_second, 3),
                    "memory_usage_mb": round(metric.memory_usage_mb, 3),
                    "cpu_time_seconds": round(metric.cpu_time_seconds, 3),
                    "io_read_mb": round(metric.io_read_mb, 3),
                    "io_write_mb": round(metric.io_write_mb, 3),
                },
            )
        except Exception:
            duration = time.perf_counter() - start
            STAGE_DURATION.labels(stage=stage, status="error").observe(duration)
            FAILURES.inc()
            
            usage_end = resource.getrusage(resource.RUSAGE_SELF)
            metric = StageMetric(
                name=stage,
                duration_ms=duration * 1000,
                cpu_time_seconds=max(time.process_time() - process_cpu_start, 0.0),
                memory_usage_mb=usage_end.ru_maxrss / 1024.0,
                rows_processed=rows_in,
                rows_per_second=0.0,
                io_read_mb=max((usage_end.ru_inblock - usage_start.ru_inblock) / 1024.0, 0.0),
                io_write_mb=max((usage_end.ru_oublock - usage_start.ru_oublock) / 1024.0, 0.0),
                status="error",
                validation_error_counts=validation_error_counts or {},
                rows_in=rows_in,
                error_count=1,
            )
            self.stage_metrics.append(metric)
            self._counters["pipeline_failures_total"] += 1
            logger.exception(
                "Stage failed.",
                extra={
                    "stage": stage,
                    "duration_ms": round(metric.duration_ms, 3),
                    "rows_processed": rows_in,
                    "failure_count": self._counters["pipeline_failures_total"],
                },
            )
            raise

    def snapshot(self) -> list[dict[str, Any]]:
        return [
            {
                "stage": metric.name,
                "duration_ms": round(metric.duration_ms, 3),
                "cpu_time_seconds": round(metric.cpu_time_seconds, 6),
                "memory_usage_mb": round(metric.memory_usage_mb, 6),
                "rows_processed": metric.rows_processed,
                "rows_per_second": round(metric.rows_per_second, 6),
                "io_read_mb": round(metric.io_read_mb, 6),
                "io_write_mb": round(metric.io_write_mb, 6),
                "status": metric.status,
                "validation_error_counts": metric.validation_error_counts,
                "rows_in": metric.rows_in,
                "rows_out": metric.rows_out,
                "error_count": metric.error_count,
            }
            for metric in self.stage_metrics
        ]

    def prometheus_text(self) -> str:
        """Returns the current metrics in Prometheus text format."""
        return generate_latest(REGISTRY).decode("utf-8")
