from __future__ import annotations

from typing import Any

from src.core.config import AppConfig
from src.core.exceptions import MetricsError
from src.models.pipeline_metrics import PipelineMetrics, ValidationStats, utc_timestamp


class MetricsService:
    def __init__(self, config: AppConfig, thresholds: dict[str, Any]) -> None:
        self.config = config
        self.thresholds = thresholds.get("thresholds", {})

    def build_metrics(
        self,
        *,
        run_id: str,
        stats: ValidationStats,
        stage_metrics: list[dict[str, Any]],
    ) -> PipelineMetrics:
        try:
            drop_rate_cfg = self.thresholds.get("drop_rate", {})
            alert_cfg = self.thresholds.get("alerts", {})
            labels = self.thresholds.get("severity_labels", {})

            drop_rate = stats.drop_rate
            if drop_rate < float(drop_rate_cfg.get("low", 0.10)):
                severity = str(labels.get("low", "LOW"))
            elif drop_rate <= float(drop_rate_cfg.get("medium", 0.30)):
                severity = str(labels.get("medium", "MEDIUM"))
            else:
                severity = str(labels.get("high", "HIGH"))

            is_drop_rate_alert = drop_rate > float(alert_cfg.get("drop_rate", 0.50))
            is_email_alert = stats.invalid_emails_dropped > int(alert_cfg.get("invalid_emails", 1000))
            is_phone_alert = stats.invalid_phones_dropped > int(alert_cfg.get("invalid_phones", 1500))

            return PipelineMetrics(
                run_id=run_id,
                client_name=self.config.client_name,
                version=self.config.app_version,
                created_at_utc=utc_timestamp(),
                severity=severity,
                stats=stats,
                thresholds=self.thresholds,
                is_drop_rate_alert=is_drop_rate_alert,
                is_email_alert=is_email_alert,
                is_phone_alert=is_phone_alert,
                stage_metrics=stage_metrics,
            )
        except Exception as exc:
            raise MetricsError(
                "Failed to calculate pipeline metrics.",
                error_code="METRICS_BUILD_FAILED",
                context={"run_id": run_id},
            ) from exc
