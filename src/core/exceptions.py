from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


@dataclass
class ErrorContext:
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.details)


class ErrorSeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    CONFIGURATION = "configuration"
    STARTUP = "startup"
    INGESTION = "ingestion"
    VALIDATION = "validation"
    METRICS = "metrics"
    REPORTING = "reporting"
    NOTIFICATION = "notification"
    INFRASTRUCTURE = "infrastructure"


class PipelineError(Exception):
    """Base class for all platform errors with structured context."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str,
        context: dict[str, Any] | None = None,
        category: ErrorCategory = ErrorCategory.INFRASTRUCTURE,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        retryable: bool = False,
        remediation_hint: str | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.context = ErrorContext(context or {})
        self.category = category
        self.severity = severity
        self.retryable = retryable
        self.remediation_hint = remediation_hint

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "category": self.category.value,
            "severity": self.severity.value,
            "retryable": self.retryable,
            "remediation_hint": self.remediation_hint,
            "context": self.context.to_dict(),
            "message": super().__str__(),
        }

    def __str__(self) -> str:
        base = f"[{self.error_code}] {super().__str__()}"
        if self.context.details:
            return f"{base} | Context: {self.context.to_dict()}"
        return base


class ConfigurationError(PipelineError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(
            message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.ERROR,
            retryable=False,
            **kwargs,
        )


class StartupError(PipelineError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(
            message,
            category=ErrorCategory.STARTUP,
            severity=ErrorSeverity.CRITICAL,
            retryable=False,
            **kwargs,
        )


class IngestionError(PipelineError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(
            message,
            category=ErrorCategory.INGESTION,
            severity=ErrorSeverity.ERROR,
            retryable=True,
            **kwargs,
        )


class ValidationError(PipelineError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.ERROR,
            retryable=False,
            **kwargs,
        )


class MetricsError(PipelineError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(
            message,
            category=ErrorCategory.METRICS,
            severity=ErrorSeverity.WARNING,
            retryable=False,
            **kwargs,
        )


class ReportingError(PipelineError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(
            message,
            category=ErrorCategory.REPORTING,
            severity=ErrorSeverity.ERROR,
            retryable=True,
            **kwargs,
        )


class NotificationError(PipelineError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(
            message,
            category=ErrorCategory.NOTIFICATION,
            severity=ErrorSeverity.WARNING,
            retryable=True,
            **kwargs,
        )
