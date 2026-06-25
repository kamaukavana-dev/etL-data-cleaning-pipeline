from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from src.core.exceptions import MetricsError

LOGGER = logging.getLogger("etl.analysis")


class AnalysisService:
    def analyze(self, df: pd.DataFrame) -> dict[str, Any]:
        if df.empty:
            return {
                "meta": {
                    "row_count": 0,
                    "column_count": len(df.columns),
                    "numeric_columns": [],
                    "missing_values": {},
                    "analysis_mode": "in_memory",
                }
            }

        numeric_df = df.select_dtypes(include="number")
        missing_values = df.isna().sum()
        missing_values = missing_values[missing_values > 0].to_dict()

        result: dict[str, Any] = {
            "meta": {
                "row_count": len(df),
                "column_count": len(df.columns),
                "numeric_columns": list(numeric_df.columns),
                "missing_values": missing_values,
                "analysis_mode": "in_memory",
            }
        }
        if not numeric_df.empty:
            result["statistics"] = {
                "mean": numeric_df.mean().to_dict(),
                "min": numeric_df.min().to_dict(),
                "max": numeric_df.max().to_dict(),
                "sum": numeric_df.sum().to_dict(),
            }
            if 2 <= numeric_df.shape[1] <= 20:
                result["correlation"] = numeric_df.corr().to_dict()
        return result


@dataclass
class IncrementalAnalysisAccumulator:
    """
    Aggregates statistics safely across chunked processing.
    Correlation is skipped in streaming mode to avoid O(n^2) state growth.
    """

    rows: int = 0
    columns: set[str] = field(default_factory=set)
    missing_values: dict[str, int] = field(default_factory=dict)
    numeric_sum: dict[str, float] = field(default_factory=dict)
    numeric_min: dict[str, float] = field(default_factory=dict)
    numeric_max: dict[str, float] = field(default_factory=dict)
    numeric_count: dict[str, int] = field(default_factory=dict)

    def update(self, df: pd.DataFrame) -> None:
        self.rows += len(df)
        self.columns.update(df.columns.tolist())

        missing = df.isna().sum()
        for column, value in missing.items():
            if value > 0:
                self.missing_values[column] = self.missing_values.get(column, 0) + int(value)

        numeric_df = df.select_dtypes(include="number")
        if numeric_df.empty:
            return

        for column in numeric_df.columns:
            series = numeric_df[column].dropna()
            if series.empty:
                continue

            col_sum = float(series.sum())
            col_min = float(series.min())
            col_max = float(series.max())
            col_count = int(series.count())

            self.numeric_sum[column] = self.numeric_sum.get(column, 0.0) + col_sum
            self.numeric_count[column] = self.numeric_count.get(column, 0) + col_count

            if column not in self.numeric_min:
                self.numeric_min[column] = col_min
                self.numeric_max[column] = col_max
            else:
                self.numeric_min[column] = min(self.numeric_min[column], col_min)
                self.numeric_max[column] = max(self.numeric_max[column], col_max)

    def finalize(self) -> dict[str, Any]:
        means: dict[str, float] = {}
        for column, total in self.numeric_sum.items():
            count = self.numeric_count.get(column, 0)
            if count <= 0:
                continue
            means[column] = total / count

        return {
            "meta": {
                "row_count": self.rows,
                "column_count": len(self.columns),
                "numeric_columns": sorted(self.numeric_sum.keys()),
                "missing_values": self.missing_values,
                "analysis_mode": "streaming",
            },
            "statistics": {
                "mean": means,
                "min": self.numeric_min,
                "max": self.numeric_max,
                "sum": self.numeric_sum,
            },
        }

    def ensure_has_data(self) -> None:
        if self.rows == 0:
            raise MetricsError(
                "Streaming analysis accumulator has no data.",
                error_code="ANALYSIS_STREAM_EMPTY",
                context={},
            )
