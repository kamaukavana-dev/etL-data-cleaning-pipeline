import os
import logging
import pandas as pd
from pathlib import Path
from src.exceptions import DataLoadError

logger = logging.getLogger(__name__)

LOADER_VERSION = "1.5"  # bumped version after encoding fallback improvements

# ✅ Column alias mapping for schema drift
COLUMN_ALIASES = {
    "id": ["id", "ID"],
    "name": ["name", "Name"],
    "email": ["email", "Email"],
    "phone": ["phone", "Phone"],
    "salary": ["salary", "Salary"],
    "date_joined": ["date_joined", "Date", "JoinDate", "JoiningDate"],
    # Extended aliases for extra useful fields
    "department": ["department", "Dept", "Division"],
    "notes": ["notes", "Remarks", "Comments"]
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to lowercase and map aliases to expected names."""
    df.columns = [c.strip().lower() for c in df.columns]

    rename_map = {}
    for expected, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias.lower() in df.columns:
                rename_map[alias.lower()] = expected

    df = df.rename(columns=rename_map)
    return df


def load_csv(filepath: str, encoding: str = "utf-8") -> pd.DataFrame:
    """
    Load data from a CSV file with optional encoding.
    Normalizes column names and applies alias mapping for schema consistency.
    Falls back gracefully if encoding issues occur.
    """
    path = Path(filepath)
    if not path.exists():
        raise DataLoadError(f"CSV file not found: {filepath}", error_code="LOAD_FILE_NOT_FOUND")

    try:
        try:
            # ✅ First attempt with provided encoding
            df = pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            # ✅ Fallback: force UTF-8 and ignore undecodable characters
            logger.warning("UnicodeDecodeError with encoding=%s. Retrying with utf-8 and errors='ignore'.", encoding)
            df = pd.read_csv(path, encoding="utf-8", errors="ignore")

        df = normalize_columns(df)

        # ✅ Optional validation
        required_columns = [c.strip().lower() for c in os.getenv("REQUIRED_COLUMNS", "").split(",") if c.strip()]
        if required_columns:
            missing = set(required_columns) - set(df.columns)
            if missing:
                raise DataLoadError(
                    f"Missing required columns: {missing}",
                    error_code="LOAD_MISSING_COLUMNS",
                    context={"required_columns": required_columns}
                )

        logger.info(
            "CSV loaded successfully | file=%s | rows=%d | encoding=%s | version=%s",
            filepath, len(df), encoding, LOADER_VERSION
        )
        return df

    except Exception as e:
        logger.error("Error loading CSV file %s: %s", filepath, e)
        raise DataLoadError(f"Failed to load CSV file {filepath}", error_code="LOAD_GENERIC_ERROR") from e


def load_excel(filepath: str, *, sheet_name: str | None = None) -> pd.DataFrame | dict:
    """
    Load data from an Excel file.
    Normalizes column names and applies alias mapping for schema consistency.
    - If sheet_name is None, returns dict of DataFrames for all sheets.
    - If sheet_name is provided, returns a single DataFrame.
    """
    path = Path(filepath)
    if not path.exists():
        raise DataLoadError(f"Excel file not found: {filepath}", error_code="LOAD_FILE_NOT_FOUND")

    try:
        if sheet_name is None:
            df_dict = pd.read_excel(path, sheet_name=None)
            for sheet, df in df_dict.items():
                df_dict[sheet] = normalize_columns(df)
            df = df_dict
        else:
            df = pd.read_excel(path, sheet_name=sheet_name)
            df = normalize_columns(df)

            # ✅ Optional validation
            required_columns = [c.strip().lower() for c in os.getenv("REQUIRED_COLUMNS", "").split(",") if c.strip()]
            if required_columns:
                missing = set(required_columns) - set(df.columns)
                if missing:
                    raise DataLoadError(
                        f"Missing required columns: {missing}",
                        error_code="LOAD_MISSING_COLUMNS",
                        context={"required_columns": required_columns}
                    )

        logger.info(
            "Excel loaded successfully | file=%s | type=%s | version=%s",
            filepath,
            "multi-sheet" if isinstance(df, dict) else "single-sheet",
            LOADER_VERSION
        )
        return df

    except Exception as e:
        logger.error("Error loading Excel file %s: %s", filepath, e)
        raise DataLoadError(f"Failed to load Excel file {filepath}", error_code="LOAD_GENERIC_ERROR") from e