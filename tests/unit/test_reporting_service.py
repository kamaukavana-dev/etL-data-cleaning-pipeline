from __future__ import annotations

from pathlib import Path

from src.core.config import load_config
from src.models.pipeline_metrics import PipelineMetrics, ValidationStats, utc_timestamp
from src.services.reporting_service import ReportingService


def test_reporting_csv_mode(runtime_root: Path, monkeypatch) -> None:
    csv_path = runtime_root / "data" / "raw" / "input.csv"
    csv_path.write_text("id,name,email,phone,salary,date_joined\n", encoding="utf-8")

    monkeypatch.setenv("DATA_FILE", str(csv_path))
    monkeypatch.setenv("REPORT_FORMAT", "csv")
    config, _ = load_config(project_root=runtime_root, env_file=runtime_root / ".env", dotenv_optional=True)

    service = ReportingService(config)
    metrics = PipelineMetrics(
        run_id="r1",
        client_name="client",
        version="1",
        created_at_utc=utc_timestamp(),
        severity="LOW",
        stats=ValidationStats(original_rows=1, final_rows=1),
        thresholds={},
        is_drop_rate_alert=False,
        is_email_alert=False,
        is_phone_alert=False,
        stage_metrics=[],
    )

    artifact = service.generate_report(metrics=metrics, analysis_results={}, cleaned_df=None)
    assert artifact.report_path.suffix == ".csv"
    assert artifact.report_path.exists()
    assert artifact.drop_reasons_path is not None
    assert artifact.drop_reasons_path.exists()
    assert artifact.summary_path is not None
    assert artifact.summary_path.exists()
