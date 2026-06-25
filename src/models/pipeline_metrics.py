from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ValidationStats:
    original_rows: int = 0
    final_rows: int = 0
    duplicates_dropped: int = 0
    invalid_emails_dropped: int = 0
    invalid_phones_dropped: int = 0
    invalid_numbers_dropped: int = 0
    invalid_dates_dropped: int = 0
    validation_error_counts: dict[str, int] = field(default_factory=dict)
    schema_version: str = "v1"
    lineage_source: str = "unknown"
    missing_required_columns: tuple[str, ...] = field(default_factory=tuple)
    extra_columns: tuple[str, ...] = field(default_factory=tuple)

    @property
    def dropped_rows(self) -> int:
        return self.original_rows - self.final_rows

    @property
    def drop_rate(self) -> float:
        if self.original_rows == 0:
            return 0.0
        return self.dropped_rows / self.original_rows

    def merge(self, other: "ValidationStats") -> "ValidationStats":
        return ValidationStats(
            original_rows=self.original_rows + other.original_rows,
            final_rows=self.final_rows + other.final_rows,
            duplicates_dropped=self.duplicates_dropped + other.duplicates_dropped,
            invalid_emails_dropped=self.invalid_emails_dropped + other.invalid_emails_dropped,
            invalid_phones_dropped=self.invalid_phones_dropped + other.invalid_phones_dropped,
            invalid_numbers_dropped=self.invalid_numbers_dropped + other.invalid_numbers_dropped,
            invalid_dates_dropped=self.invalid_dates_dropped + other.invalid_dates_dropped,
            validation_error_counts={
                key: self.validation_error_counts.get(key, 0) + other.validation_error_counts.get(key, 0)
                for key in set(self.validation_error_counts) | set(other.validation_error_counts)
            },
            schema_version=other.schema_version or self.schema_version,
            lineage_source=other.lineage_source or self.lineage_source,
            missing_required_columns=tuple(
                sorted(set(self.missing_required_columns).union(other.missing_required_columns))
            ),
            extra_columns=tuple(sorted(set(self.extra_columns).union(other.extra_columns))),
        )


@dataclass(frozen=True)
class PipelineMetrics:
    run_id: str
    client_name: str
    version: str
    created_at_utc: str
    severity: str
    stats: ValidationStats
    thresholds: dict[str, Any]
    is_drop_rate_alert: bool
    is_email_alert: bool
    is_phone_alert: bool
    stage_metrics: list[dict[str, Any]]

    @property
    def drop_rate_pct(self) -> str:
        return f"{self.stats.drop_rate:.2%}"

    @property
    def dropped_rows(self) -> int:
        return self.stats.dropped_rows


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()
