from __future__ import annotations

from pathlib import Path

from src.core.config import bootstrap_filesystem, load_config
from src.core.logging import configure_logging
from src.services.pipeline_runner import build_runner


def test_pipeline_runner_end_to_end(runtime_root: Path, monkeypatch) -> None:
    csv_path = runtime_root / "data" / "raw" / "input.csv"
    csv_path.write_text(
        "\n".join(
            [
                "id,name,email,phone,salary,date_joined,department,notes",
                "1,Alice,a@example.com,+1234567890,100,2024-01-01,Ops,ok",
                "2,Bob,broken,+1,100,2024-01-01,Ops,bad",
                "3,Carol,c@example.com,+1234567899,200,2024-01-02,Ops,ok",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("DATA_FILE", str(csv_path))
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("ENABLE_STREAMING_FOR_CSV", "false")

    config, _ = load_config(project_root=runtime_root, env_file=runtime_root / ".env", dotenv_optional=True)
    bootstrap_filesystem(config)
    configure_logging(config, run_id="integration-test")

    runner = build_runner(config)
    result = runner.run()

    report_path = Path(result["report_path"])
    assert report_path.exists()
    assert Path(result["drop_reasons_path"]).exists()
    assert Path(result["summary_path"]).exists()
    assert result["rows_loaded"] == 3
    assert result["rows_cleaned"] == 2

    second_result = runner.run()
    assert second_result == result
