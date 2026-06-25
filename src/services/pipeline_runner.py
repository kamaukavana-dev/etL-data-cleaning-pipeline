from __future__ import annotations

import uuid
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.core.config import AppConfig
from src.core.exceptions import NotificationError, StartupError
from src.core.logging import ContextLogger, get_logger
from src.core.observability import RunTelemetry
from src.models.pipeline_metrics import ValidationStats
from src.models.report_models import ReportArtifact
from src.services.analysis_service import AnalysisService, IncrementalAnalysisAccumulator
from src.services.ingestion_service import IngestionService, IngestionResult
from src.services.metrics_service import MetricsService
from src.services.notification_service import NotificationService
from src.services.reporting_service import ReportingService
from src.services.thresholds_service import ThresholdsService
from src.services.validation_service import ValidationService


class PipelineRunner:
    def __init__(self, config: AppConfig, *, run_id: str | None = None) -> None:
        self.config = config
        self.run_id = run_id or str(uuid.uuid4())
        self.telemetry = RunTelemetry()
        self.logger: ContextLogger = get_logger("etl.pipeline", run_id=self.run_id)

        thresholds_bundle = ThresholdsService(self.config.paths.thresholds_file).load()
        self.thresholds = thresholds_bundle

        self.ingestion_service = IngestionService(config)
        self.validation_service = ValidationService(config)
        self.analysis_service = AnalysisService()
        self.metrics_service = MetricsService(config, thresholds_bundle)
        self.reporting_service = ReportingService(config)
        self.notification_service = NotificationService(config)

    def run(self) -> dict[str, Any]:
        self.logger.info("Pipeline run started.", extra={"stage": "startup"})
        self.telemetry.heartbeat(logger=self.logger, stage="startup", run_id=self.run_id)
        source_path = self.config.data_file

        cached = self._load_cached_result()
        if cached:
            self.logger.info(
                "Cache hit: returning previous run artifacts.",
                extra={"stage": "startup", "cached_run_id": cached.get("run_id")},
            )
            return cached

        self.validation_service.reset()

        # 1. Ingestion Planning & Execution
        with self.telemetry.measure_stage(logger=self.logger, stage="ingestion"):
            ingestion_result = self.ingestion_service.load(source_path)

        artifact: ReportArtifact
        analysis: dict[str, Any]
        stats: ValidationStats

        if ingestion_result.is_streaming:
            artifact, analysis, stats = self._run_streaming(ingestion_result)
        else:
            artifact, analysis, stats = self._run_in_memory(ingestion_result)

        self.telemetry.heartbeat(logger=self.logger, stage="completion", run_id=self.run_id)

        metrics = self.metrics_service.build_metrics(
            run_id=self.run_id,
            stats=stats,
            stage_metrics=self.telemetry.snapshot(),
        )

        if not self.config.dry_run and self.config.smtp.is_enabled:
            self._notify(metrics=metrics, report_path=artifact.report_path)
        elif not self.config.smtp.is_enabled:
            self.logger.warning(
                "Notifications skipped because SMTP is disabled.",
                extra={"stage": "notification", "reason": self.config.smtp.disabled_reason},
            )
        else:
            self.logger.info("DRY_RUN enabled: notification skipped.", extra={"stage": "notification"})

        self.logger.info(
            "Pipeline run completed.",
            extra={
                "stage": "complete",
                "report_path": str(artifact.report_path),
                "rows_loaded": stats.original_rows,
                "rows_cleaned": stats.final_rows,
            },
        )
        result = {
            "run_id": self.run_id,
            "report_path": str(artifact.report_path),
            "cleaned_data_path": str(artifact.cleaned_data_path) if artifact.cleaned_data_path else None,
            "drop_reasons_path": str(artifact.drop_reasons_path) if artifact.drop_reasons_path else None,
            "summary_path": str(artifact.summary_path) if artifact.summary_path else None,
            "rows_loaded": stats.original_rows,
            "rows_cleaned": stats.final_rows,
            "drop_rate_pct": f"{stats.drop_rate:.2%}",
            "analysis_mode": analysis.get("meta", {}).get("analysis_mode"),
        }
        self._store_cached_result(result)
        return result

    def _cache_path(self) -> Path:
        return self.config.paths.temp_dir / "run_cache.json"

    def _load_cached_result(self) -> dict[str, Any] | None:
        cache_key, signature = self._build_cache_key()
        cache = self._read_cache()
        entry = cache.get("entries", {}).get(cache_key)
        if not entry:
            return None
        if entry.get("signature") != signature:
            return None
        result = entry.get("result")
        if not isinstance(result, dict):
            return None
        if not self._cache_entry_valid(result):
            return None
        return result

    def _store_cached_result(self, result: dict[str, Any]) -> None:
        cache_key, signature = self._build_cache_key()
        cache = self._read_cache()
        entries = cache.setdefault("entries", {})
        entries[cache_key] = {
            "signature": signature,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "result": result,
        }
        cache["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._write_cache(cache)

    def _cache_entry_valid(self, result: dict[str, Any]) -> bool:
        report = result.get("report_path")
        drop_reasons = result.get("drop_reasons_path")
        summary = result.get("summary_path")
        cleaned = result.get("cleaned_data_path")

        required_paths = [report, drop_reasons, summary]
        for path_value in required_paths:
            if not path_value:
                return False
            if not Path(path_value).exists():
                return False

        if cleaned and not Path(cleaned).exists():
            return False
        return True

    def _build_cache_key(self) -> tuple[str, dict[str, Any]]:
        data_hash = self._hash_file(self.config.data_file)
        thresholds_meta = self._file_meta(self.config.paths.thresholds_file)
        logging_meta = self._file_meta(self.config.paths.logging_file)

        signature = {
            "data_file": str(self.config.data_file),
            "data_hash": data_hash,
            "app_version": self.config.app_version,
            "required_columns": list(self.config.required_columns),
            "enable_streaming_for_csv": self.config.enable_streaming_for_csv,
            "csv_chunk_size": self.config.csv_chunk_size,
            "stream_file_size_mb_threshold": self.config.stream_file_size_mb_threshold,
            "report_mode": self.config.report_mode,
            "report_format": self.config.report_format,
            "include_cleaned_data_in_report": self.config.include_cleaned_data_in_report,
            "max_report_rows": self.config.max_report_rows,
            "enable_excel_formatting": self.config.enable_excel_formatting,
            "thresholds_meta": thresholds_meta,
            "logging_meta": logging_meta,
        }
        signature_json = json.dumps(signature, sort_keys=True).encode("utf-8")
        cache_key = hashlib.sha256(signature_json).hexdigest()
        return cache_key, signature

    def _hash_file(self, path: Path) -> str:
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _file_meta(self, path: Path) -> dict[str, float] | None:
        if not path.exists():
            return None
        stat = path.stat()
        return {"mtime": stat.st_mtime, "size": float(stat.st_size)}

    def _read_cache(self) -> dict[str, Any]:
        cache_path = self._cache_path()
        if not cache_path.exists():
            return {"entries": {}}
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self.logger.warning("Cache file is invalid JSON; ignoring.", extra={"stage": "startup"})
            return {"entries": {}}

    def _write_cache(self, cache: dict[str, Any]) -> None:
        cache_path = self._cache_path()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, indent=2, ensure_ascii=True), encoding="utf-8")

    def _run_in_memory(self, ingestion_result: IngestionResult) -> tuple[ReportArtifact, dict[str, Any], ValidationStats]:
        df = ingestion_result.dataframe
        if df is None or df.empty:
            # Handle empty data
            stats = ValidationStats(original_rows=0, final_rows=0)
            analysis = self.analysis_service.analyze(pd.DataFrame())
            artifact = self.reporting_service.generate_report(
                 metrics=self.metrics_service.build_metrics(run_id=self.run_id, stats=stats, stage_metrics=[]),
                 analysis_results=analysis,
                 cleaned_df=pd.DataFrame()
            )
            return artifact, analysis, stats

        with self.telemetry.measure_stage(
            logger=self.logger,
            stage="validation",
            rows_in=len(df),
        ):
            validation_result, _ = self.validation_service.validate_and_clean(df)

        self.logger.info(
            "Validation distribution.",
            extra={
                "stage": "validation",
                "validation_error_counts": validation_result.stats.validation_error_counts,
                "rows_processed": validation_result.stats.original_rows,
            },
        )

        with self.telemetry.measure_stage(
            logger=self.logger,
            stage="analysis",
            rows_in=len(validation_result.cleaned_df),
        ):
            analysis = self.analysis_service.analyze(validation_result.cleaned_df)

        with self.telemetry.measure_stage(logger=self.logger, stage="reporting"):
            artifact = self.reporting_service.generate_report(
                metrics=self.metrics_service.build_metrics(
                    run_id=self.run_id,
                    stats=validation_result.stats,
                    stage_metrics=self.telemetry.snapshot(),
                ),
                analysis_results=analysis,
                cleaned_df=validation_result.cleaned_df,
            )

        return artifact, analysis, validation_result.stats

    def _run_streaming(self, ingestion_result: IngestionResult) -> tuple[ReportArtifact, dict[str, Any], ValidationStats]:
        aggregated_stats = ValidationStats()
        analysis_accumulator = IncrementalAnalysisAccumulator()
        export_path = self.config.paths.exports_dir / f"cleaned_stream_{self.run_id}.csv"
        wrote_header = False
        seen_ids: set[str] = set()

        with self.telemetry.measure_stage(logger=self.logger, stage="ingestion_stream"):
            for chunk in self.ingestion_service.iter_csv_chunks(ingestion_result.source_path):
                validation_result, seen_ids = self.validation_service.validate_and_clean(chunk, seen_ids=seen_ids)
                aggregated_stats = aggregated_stats.merge(validation_result.stats)
                analysis_accumulator.update(validation_result.cleaned_df)
                self.telemetry.heartbeat(logger=self.logger, stage="ingestion_stream", run_id=self.run_id)

                if not validation_result.cleaned_df.empty:
                    validation_result.cleaned_df.to_csv(
                        export_path,
                        index=False,
                        mode="a" if wrote_header else "w",
                        header=not wrote_header,
                    )
                    wrote_header = True

        if not wrote_header:
            # Fallback for completely filtered data
            pd.DataFrame(columns=list(self.config.required_columns)).to_csv(export_path, index=False)

        analysis = analysis_accumulator.finalize()

        self.logger.info(
            "Streaming validation distribution.",
            extra={
                "stage": "validation",
                "validation_error_counts": aggregated_stats.validation_error_counts,
                "rows_processed": aggregated_stats.original_rows,
            },
        )

        with self.telemetry.measure_stage(logger=self.logger, stage="reporting_stream"):
            artifact = self.reporting_service.generate_report(
                metrics=self.metrics_service.build_metrics(
                    run_id=self.run_id,
                    stats=aggregated_stats,
                    stage_metrics=self.telemetry.snapshot(),
                ),
                analysis_results=analysis,
                cleaned_df=None,
                cleaned_data_path=export_path,
            )

        return artifact, analysis, aggregated_stats

    def _notify(self, *, metrics: Any, report_path: Path) -> None:
        context = {
            "CLIENT_NAME": metrics.client_name,
            "ROWS_LOADED": metrics.stats.original_rows,
            "ROWS_CLEANED": metrics.stats.final_rows,
            "DROP_RATE": metrics.drop_rate_pct,
            "SEVERITY": metrics.severity,
            "PIPELINE_VERSION": metrics.version,
            "EMAIL_FREQUENCY": "daily",
        }
        subject = f"[{metrics.severity}] Data Quality Report - {metrics.client_name}"
        body = self.notification_service.render_template("report_email.txt", context)
        try:
            self.notification_service.send_email(
                subject=subject,
                body=body,
                recipient=self.config.smtp.recipient_email,
                attachment=report_path,
            )
        except NotificationError:
            self.logger.exception("Notification failed.", extra={"stage": "notification"})
            raise


def build_runner(config: AppConfig) -> PipelineRunner:
    if config.csv_chunk_size <= 0:
        raise StartupError(
            "CSV_CHUNK_SIZE must be a positive integer.",
            error_code="STARTUP_INVALID_CHUNK_SIZE",
            context={"csv_chunk_size": config.csv_chunk_size},
        )
    return PipelineRunner(config)
