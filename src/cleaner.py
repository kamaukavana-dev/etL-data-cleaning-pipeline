import pandas as pd
import logging
import re
from typing import Optional, Union, Tuple, List
from src.exceptions import CleaningError

logger = logging.getLogger(__name__)

CLEANING_VERSION = "4.6"  # bumped version since we added validators

# ---------------------------
# Helper functions
# ---------------------------

def validate_email(email: Optional[str]) -> bool:
    """
    Return True if email looks valid, else False.
    """
    if not isinstance(email, str):
        return False
    email = email.strip().lower()
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return bool(re.match(pattern, email))

def validate_phone(phone: Optional[str]) -> bool:
    """
    Return True if phone looks valid, else False.
    Accepts numbers with optional +countrycode and 7–15 digits.
    """
    if not isinstance(phone, str):
        return False
    phone = re.sub(r"[^\d+]", "", phone.strip())
    digits = phone[1:] if phone.startswith("+") else phone
    return digits.isdigit() and 7 <= len(digits) <= 15

def fix_email(email: Optional[str]) -> Optional[str]:
    if not isinstance(email, str):
        return None
    email = email.strip().lower()
    return email if validate_email(email) else None

def normalize_phone(phone: Optional[str]) -> Optional[str]:
    if not isinstance(phone, str):
        return None
    phone = re.sub(r"[^\d+]", "", phone.strip())
    digits = phone[1:] if phone.startswith("+") else phone
    return phone if digits.isdigit() and 7 <= len(digits) <= 15 else None

def clean_numeric(value: Union[str, float, int]) -> Optional[float]:
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.replace(",", "").replace("$", "").strip()
    try:
        num = float(value)
        return num if num >= 0 else None
    except (ValueError, TypeError):
        return None

def clean_date(value: Union[str, float, int, pd.Timestamp]) -> Optional[pd.Timestamp]:
    parsed = pd.to_datetime(value, errors="coerce")
    return parsed if not pd.isna(parsed) else None

def clean_text(value: Optional[str]) -> Optional[str]:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value if value else None

# ---------------------------
# Schema
# ---------------------------

REQUIRED_COLUMNS = ["id", "name", "email", "phone", "salary", "date_joined"]
OPTIONAL_COLUMNS = [
    "department", "notes", "position", "location", "status",
    "manager", "dob", "gender", "contract_type", "last_updated"
]

# ---------------------------
# Main cleaner
# ---------------------------

def clean_data(
    df: pd.DataFrame,
    *,
    drop_duplicates: bool = True,
    required_columns: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, dict]:

    if df.empty:
        return df, {
            "original_rows": 0,
            "final_rows": 0,
            "duplicates_dropped": 0,
            "invalid_emails_dropped": 0,
            "invalid_phones_dropped": 0,
            "invalid_numbers_dropped": 0,
            "invalid_dates_dropped": 0,
            "missing_required_columns": [],
            "extra_columns": [],
            "cleaning_version": CLEANING_VERSION,
        }

    try:
        report = {
            "original_rows": len(df),
            "duplicates_dropped": 0,
            "invalid_emails_dropped": 0,
            "invalid_phones_dropped": 0,
            "invalid_numbers_dropped": 0,
            "invalid_dates_dropped": 0,
            "missing_required_columns": [],
            "extra_columns": [],
            "cleaning_version": CLEANING_VERSION,
        }

        df = df.copy()
        df.columns = (
            df.columns.str.strip()
            .str.lower()
            .str.replace(" ", "_", regex=False)
        )

        required = required_columns or REQUIRED_COLUMNS
        missing = sorted(set(required) - set(df.columns))
        if missing:
            report["missing_required_columns"] = missing
            raise CleaningError(f"Missing required columns: {missing}")

        report["extra_columns"] = sorted(
            set(df.columns) - set(required) - set(OPTIONAL_COLUMNS)
        )

        if drop_duplicates:
            before = len(df)
            df = df.drop_duplicates()
            report["duplicates_dropped"] = before - len(df)

        invalid_mask = pd.Series(False, index=df.index)

        email_invalid = df["email"].apply(fix_email).isna()
        df["email"] = df["email"].apply(fix_email)
        report["invalid_emails_dropped"] = int(email_invalid.sum())
        invalid_mask |= email_invalid

        phone_invalid = df["phone"].apply(normalize_phone).isna()
        df["phone"] = df["phone"].apply(normalize_phone)
        report["invalid_phones_dropped"] = int(phone_invalid.sum())
        invalid_mask |= phone_invalid

        salary_invalid = df["salary"].apply(clean_numeric).isna()
        df["salary"] = df["salary"].apply(clean_numeric)
        report["invalid_numbers_dropped"] = int(salary_invalid.sum())
        invalid_mask |= salary_invalid

        date_invalid = df["date_joined"].apply(clean_date).isna()
        df["date_joined"] = df["date_joined"].apply(clean_date)
        report["invalid_dates_dropped"] = int(date_invalid.sum())
        invalid_mask |= date_invalid

        df = df.loc[~invalid_mask]

        for col in OPTIONAL_COLUMNS:
            if col in df.columns:
                df[col] = df[col].apply(clean_text)

        report["final_rows"] = len(df)

        return df, report

    except (ValueError, TypeError, KeyError) as exc:
        logger.error("Cleaning failed due to invalid data: %s", exc)
        raise CleaningError(str(exc)) from exc