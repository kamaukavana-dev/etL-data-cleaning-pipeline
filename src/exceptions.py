class PipelineError(Exception):
    """Base class for all pipeline errors."""
    def __init__(self, message: str, *, error_code: str | None = None, context: dict | None = None):
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}

    def __str__(self):
        base = super().__str__()
        if self.error_code:
            base = f"[{self.error_code}] {base}"
        if self.context:
            base = f"{base} | Context: {self.context}"
        return base


class DataLoadError(PipelineError):
    """Raised when data loading fails."""


class CleaningError(PipelineError):
    """Raised when data cleaning fails."""
    def __init__(self, message: str, *, rows_affected: int | None = None, error_code: str | None = None):
        context = {}
        if rows_affected is not None:
            context["rows_affected"] = rows_affected
        super().__init__(message, error_code=error_code, context=context)


class AnalysisError(PipelineError):
    """Raised when data analysis fails."""


class ReportError(PipelineError):
    """Raised when report generation fails."""


class EmailError(PipelineError):
    """Raised when email sending fails."""