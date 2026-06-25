import pandas as pd
from typing import Union, Optional

def clean_date(value: Union[str, float, int, pd.Timestamp]) -> Optional[pd.Timestamp]:
    """Normalize and return parsed timestamp if valid, else None."""
    if pd.isna(value) or value == "":
        return None
    try:
        parsed = pd.to_datetime(value, errors="coerce")
        return parsed if not pd.isna(parsed) else None
    except (ValueError, TypeError):
        return None
