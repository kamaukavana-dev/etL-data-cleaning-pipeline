"""
Backward-compatible exception aliases.
Use src.core.exceptions for new implementations.
"""

from src.core.exceptions import (
    ConfigurationError,
    IngestionError,
    MetricsError,
    NotificationError,
    PipelineError,
    ReportingError,
    StartupError,
    ValidationError,
)

# Legacy aliases
DataLoadError = IngestionError
CleaningError = ValidationError
AnalysisError = MetricsError
ReportError = ReportingError
EmailError = NotificationError
