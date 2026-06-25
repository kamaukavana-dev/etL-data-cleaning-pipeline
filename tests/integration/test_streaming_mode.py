from __future__ import annotations

from pathlib import Path

from src.core.config import bootstrap_filesystem, load_config
from src.core.logging import configure_logging
from src.services.pipeline_runner import build_runner


def test_streaming_pipeline_mode(runtime_root: Path, monkeypatch) -> None:
    csv_path = runtime_root / "data" / "raw" / "stream.csv"
    csv_path.write_text(
        "\n".join(
            [
                "id,name,email,phone,salary,date_joined",
                "1,Alice,a@example.com,+1234567890,100,2024-01-01",
                "2,Bob,b@example.com,+1234567891,120,2024-01-02",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("DATA_FILE", str(csv_path))
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("ENABLE_STREAMING_FOR_CSV", "true")
    monkeypatch.setenv("STREAM_FILE_SIZE_MB_THRESHOLD", "0")
    monkeypatch.setenv("CSV_CHUNK_SIZE", "1")

    config, _ = load_config(project_root=runtime_root, env_file=runtime_root / ".env", dotenv_optional=True)
    bootstrap_filesystem(config)
    configure_logging(config, run_id="streaming-test")

    runner = build_runner(config)
    result = runner.run()

    assert result["analysis_mode"] == "streaming"
    cleaned_path = Path(result["cleaned_data_path"])
    assert cleaned_path.exists()
