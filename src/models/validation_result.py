from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.models.pipeline_metrics import ValidationStats


@dataclass(frozen=True)
class ValidationResult:
    cleaned_df: pd.DataFrame
    stats: ValidationStats
