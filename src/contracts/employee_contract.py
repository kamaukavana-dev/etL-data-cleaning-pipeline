from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ContractValidationResult:
    schema_version: str
    valid: bool
    missing_columns: tuple[str, ...]
    type_violations: dict[str, int]


class EmployeeDataContract:
    """Lightweight schema contract with optional pandera acceleration when installed."""

    SCHEMA_VERSION = "v1"

    def __init__(self, required_columns: tuple[str, ...]) -> None:
        self.required_columns = required_columns

    def validate(self, df: pd.DataFrame) -> ContractValidationResult:
        missing_columns = ()
        if self.required_columns:
            missing_columns = tuple(sorted(set(self.required_columns) - set(df.columns)))
        
        type_violations: dict[str, int] = {}

        if "salary" in df.columns:
            numeric_salary = pd.to_numeric(df["salary"], errors="coerce")
            type_violations["salary"] = int(numeric_salary.isna().sum())
        elif "total_amount" in df.columns:
            numeric_total = pd.to_numeric(df["total_amount"], errors="coerce")
            type_violations["total_amount"] = int(numeric_total.isna().sum())

        if "date_joined" in df.columns:
            parsed_dates = pd.to_datetime(df["date_joined"], errors="coerce")
            type_violations["date_joined"] = int(parsed_dates.isna().sum())
        elif "order_date" in df.columns:
            parsed_order = pd.to_datetime(df["order_date"], errors="coerce")
            type_violations["order_date"] = int(parsed_order.isna().sum())

        is_valid = not missing_columns
        return ContractValidationResult(
            schema_version=self.SCHEMA_VERSION,
            valid=is_valid,
            missing_columns=missing_columns,
            type_violations=type_violations,
        )

