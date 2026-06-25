from __future__ import annotations

import logging
import re
import yaml
from dataclasses import dataclass, field

import pandas as pd

from src.core.config import AppConfig
from src.core.constants import DEFAULT_REQUIRED_COLUMNS
from src.core.exceptions import ValidationError
from src.contracts.employee_contract import EmployeeDataContract
from src.models.validation_result import ValidationResult
from src.models.pipeline_metrics import ValidationStats

LOGGER = logging.getLogger("etl.validation")


@dataclass(frozen=True)
class ValidationRules:
    required_columns: tuple[str, ...] = ()
    optional_columns: tuple[str, ...] = (
        "department",
        "notes",
        "position",
        "location",
        "status",
        "manager",
        "dob",
        "gender",
        "contract_type",
        "last_updated",
        "source_sheet",
    )


class ValidationService:
    EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        required_columns = self._resolve_required_columns(config)
        self.rules = ValidationRules(required_columns=required_columns)
        self.contract = EmployeeDataContract(required_columns)

    def reset(self) -> None:
        # Reserved for future stateful validation; kept for safe reuse across runs.
        return

    def _resolve_required_columns(self, config: AppConfig) -> tuple[str, ...]:
        # 1. Check CLI/Env override
        if config.required_columns:
            return config.required_columns

        # 2. Check schema.yaml
        if config.paths.schema_file.exists():
            try:
                with config.paths.schema_file.open("r") as f:
                    schema_data = yaml.safe_load(f)
                    if schema_data and "required_columns" in schema_data:
                        LOGGER.info(f"Loaded required columns from {config.paths.schema_file}")
                        return tuple(schema_data["required_columns"])
            except Exception as e:
                LOGGER.warning(f"Failed to load schema from {config.paths.schema_file}: {e}")

        # 3. Default (empty tuple means dynamic/skip validation)
        return ()

    def validate_and_clean(self, df: pd.DataFrame, seen_ids: set[str] | None = None) -> tuple[ValidationResult, set[str]]:
        if df.empty:
            stats = ValidationStats(original_rows=0, final_rows=0)
            return ValidationResult(cleaned_df=df.copy(), stats=stats), seen_ids or set()

        working = df.copy()
        working.columns = (
            working.columns.astype(str).str.strip().str.lower().str.replace(" ", "_", regex=False)
        )
        original_rows = len(working)

        # Skip validation if no required columns defined
        missing = []
        if self.rules.required_columns:
            missing = sorted(set(self.rules.required_columns) - set(working.columns))
            if missing:
                raise ValidationError(
                    "Schema validation failed due to missing required columns.",
                    error_code="VALIDATION_SCHEMA_MISSING_COLUMNS",
                    context={"missing_columns": missing, "required_columns": self.rules.required_columns},
                )

        contract_result = self.contract.validate(working)

        extra_columns = tuple(
            sorted(set(working.columns) - set(self.rules.required_columns) - set(self.rules.optional_columns))
        )

        # Cross-chunk deduplication logic
        duplicates_dropped = 0
        current_seen_ids = seen_ids if seen_ids is not None else set()
        
        if "id" in working.columns:
            # 1. Intra-chunk duplicates
            intra_dupes = working.duplicated(subset=["id"], keep="first")
            
            # 2. Cross-chunk duplicates
            id_str = working["id"].astype(str)
            cross_dupes = id_str.isin(current_seen_ids)
            
            is_duplicate = intra_dupes | cross_dupes
            duplicates_dropped = int(is_duplicate.sum())
            
            if duplicates_dropped:
                working = working.loc[~is_duplicate].copy()
            
            # Update seen_ids with the current chunk's unique IDs
            current_seen_ids.update(id_str.unique())
        else:
            # Fallback to standard dataframe deduplication if no ID column
            duplicates_dropped = int(working.duplicated().sum())
            if duplicates_dropped:
                working = working.drop_duplicates()

        # Dynamic cleaning based on column presence
        email_valid = pd.Series(True, index=working.index)
        if "email" in working.columns:
            email_series = working["email"].astype("string").str.strip().str.lower()
            email_valid = email_series.str.match(self.EMAIL_PATTERN, na=False)
            working["email"] = email_series
        else:
            LOGGER.warning("Column 'email' missing; skipping email validation.")

        phone_valid = pd.Series(True, index=working.index)
        if "phone" in working.columns:
            phone_series = (
                working["phone"]
                .astype("string")
                .str.strip()
                .str.replace(r"[^\d+]", "", regex=True)
            )
            phone_digits = phone_series.str.replace("+", "", n=1, regex=False)
            phone_valid = phone_digits.str.fullmatch(r"\d{7,15}", na=False)
            working["phone"] = phone_series
        else:
            LOGGER.warning("Column 'phone' missing; skipping phone validation.")

        salary_valid = pd.Series(True, index=working.index)
        if "salary" in working.columns:
            salary_series = (
                working["salary"]
                .astype("string")
                .str.replace(",", "", regex=False)
                .str.replace("$", "", regex=False)
                .str.strip()
            )
            salary_values = pd.to_numeric(salary_series, errors="coerce")
            salary_valid = salary_values.notna() & (salary_values >= 0)
            working["salary"] = salary_values
        elif "total_amount" in working.columns: # Support alternative name for numeric validation
            salary_series = (
                working["total_amount"]
                .astype("string")
                .str.replace(",", "", regex=False)
                .str.replace("$", "", regex=False)
                .str.strip()
            )
            salary_values = pd.to_numeric(salary_series, errors="coerce")
            salary_valid = salary_values.notna() & (salary_values >= 0)
            working["total_amount"] = salary_values
        else:
            LOGGER.warning("Numeric column ('salary' or 'total_amount') missing; skipping numeric validation.")

        date_valid = pd.Series(True, index=working.index)
        if "date_joined" in working.columns:
            date_values = pd.to_datetime(working["date_joined"], errors="coerce", format="mixed")
            date_valid = date_values.notna()
            working["date_joined"] = date_values
        elif "order_date" in working.columns:
            date_values = pd.to_datetime(working["order_date"], errors="coerce", format="mixed")
            date_valid = date_values.notna()
            working["order_date"] = date_values
        else:
            LOGGER.warning("Date column ('date_joined' or 'order_date') missing; skipping date validation.")

        # Logic for dropping invalid rows
        invalid_mask = ~(email_valid & phone_valid & salary_valid & date_valid)

        # Mutually exclusive buckets to prevent double-counting
        email_drop_mask = ~email_valid
        phone_drop_mask = ~phone_valid & ~email_drop_mask
        salary_drop_mask = ~salary_valid & ~email_drop_mask & ~phone_drop_mask
        date_drop_mask = ~date_valid & ~email_drop_mask & ~phone_drop_mask & ~salary_drop_mask

        # Temp diagnostic
        LOGGER.debug(
            "Validation drop counts.",
            extra={
                "dedupe_dropped": duplicates_dropped,
                "invalid_email": int(email_drop_mask.sum()),
                "invalid_phone": int(phone_drop_mask.sum()),
                "invalid_salary": int(salary_drop_mask.sum()),
                "invalid_date": int(date_drop_mask.sum()),
            },
        )
        
        cleaned = working.loc[~invalid_mask].copy()

        stats = ValidationStats(
            original_rows=original_rows,
            final_rows=len(cleaned),
            duplicates_dropped=duplicates_dropped,
            invalid_emails_dropped=int(email_drop_mask.sum()),
            invalid_phones_dropped=int(phone_drop_mask.sum()),
            invalid_numbers_dropped=int(salary_drop_mask.sum()),
            invalid_dates_dropped=int(date_drop_mask.sum()),
            validation_error_counts={
                "invalid_email": int(email_drop_mask.sum()),
                "invalid_phone": int(phone_drop_mask.sum()),
                "invalid_salary": int(salary_drop_mask.sum()),
                "invalid_date": int(date_drop_mask.sum()),
            },
            schema_version=contract_result.schema_version,
            missing_required_columns=tuple(missing),
            extra_columns=extra_columns,
        )

        LOGGER.info(
            "Validation completed.",
            extra={
                "stage": "validation",
                "original_rows": original_rows,
                "final_rows": len(cleaned),
                "duplicates_dropped": duplicates_dropped,
                "validation_error_counts": stats.validation_error_counts,
                "schema_version": stats.schema_version,
            },
        )
        return ValidationResult(cleaned_df=cleaned, stats=stats), current_seen_ids
