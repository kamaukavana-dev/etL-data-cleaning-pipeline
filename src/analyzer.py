"""
Backward-compatible analysis helper.
Prefer src.services.analysis_service.AnalysisService.
"""

import pandas as pd

from src.services.analysis_service import AnalysisService


def analyze_data(df: pd.DataFrame, numeric_columns: list[str] | None = None) -> dict:
    _ = numeric_columns
    return AnalysisService().analyze(df)
