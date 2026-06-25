import pandas as pd
from typing import Union, Optional

def clean_numeric(value: Union[str, float, int]) -> Optional[float]:
    """Normalize and return numeric value if valid and non-negative, else None."""
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.replace(",", "").replace("$", "").strip()
    try:
        num = float(value)
        return num if num >= 0 else None
    except (ValueError, TypeError):
        return None
