"""
Backward-compatible wrapper around ReportingService.
"""

from pathlib import Path
from typing import Any

import pandas as pd

from src.core.config import load_config
from src.models.pipeline_metrics import PipelineMetrics
from src.services.reporting_service import ReportingService


class ReportService:
    def __init__(self, reports_dir: Path | None = None):
        config, _ = load_config()
        _ = reports_dir
        self.service = ReportingService(config)

    def generate_report(
        self,
        metrics: PipelineMetrics,
        results: dict[str, Any],
        clean_df: pd.DataFrame,
        filename: str = "analysis_report.xlsx",
    ) -> str:
        _ = filename
        artifact = self.service.generate_report(
            metrics=metrics,
            analysis_results=results,
            cleaned_df=clean_df,
        )
        return str(artifact.report_path)
