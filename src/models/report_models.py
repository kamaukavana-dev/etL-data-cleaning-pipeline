from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReportArtifact:
    report_path: Path
    cleaned_data_path: Path | None
    drop_reasons_path: Path | None = None
    summary_path: Path | None = None
