import pandas as pd
import logging
from src.exceptions import AnalysisError

logger = logging.getLogger(__name__)

def analyze_data(df: pd.DataFrame, numeric_columns: list[str] | None = None) -> dict:
    """
    Perform structured, client-safe analysis.
    - Schema awareness: optional numeric column allowlist with validation.
    - Metadata includes missing values (only non-zero).
    - Correlation capped to avoid explosion.
    - Versioning for traceability.
    - Queryable logging.
    """

    if df.empty:
        logger.warning("No data available for analysis.")
        return {}

    try:
        # ✅ Schema awareness: validate allowlist
        if numeric_columns:
            missing = set(numeric_columns) - set(df.columns)
            if missing:
                raise AnalysisError(f"Missing numeric columns: {missing}")

            numeric_df = df[numeric_columns].select_dtypes(include="number")
        else:
            numeric_df = df.select_dtypes(include="number")

        # ✅ Metadata with missing values (signal only)
        missing = df.isna().sum()
        missing = missing[missing > 0].to_dict()

        analysis = {
            "meta": {
                "row_count": len(df),
                "column_count": len(df.columns),
                "numeric_columns": list(numeric_df.columns),
                "missing_values": missing,
                "analysis_version": "1.0",
            }
        }

        # ✅ Statistics
        if not numeric_df.empty:
            analysis["statistics"] = {
                "mean": numeric_df.mean().to_dict(),
                "min": numeric_df.min().to_dict(),
                "max": numeric_df.max().to_dict(),
                "sum": numeric_df.sum().to_dict(),
            }

            # ✅ Correlation capped to 10 numeric columns
            if 2 <= numeric_df.shape[1] <= 10:
                try:
                    analysis["correlation"] = numeric_df.corr().to_dict()
                except Exception as e:
                    logger.warning(f"Correlation calculation failed: {e}")
        else:
            logger.info("No numeric columns found for statistical analysis.")

        # ✅ Queryable logging
        logger.info(
            "Analysis complete | rows=%d cols=%d numeric=%d",
            len(df),
            len(df.columns),
            numeric_df.shape[1],
        )

        return analysis

    except Exception as e:
        logger.exception("Data analysis failed.")
        raise AnalysisError("Analysis stage failed") from e