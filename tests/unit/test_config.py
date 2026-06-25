from __future__ import annotations

from pathlib import Path

from src.core.config import bootstrap_filesystem, load_config


def test_load_config_resolves_relative_data_file(runtime_root: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_FILE", "data/raw/sample.csv")
    monkeypatch.setenv("DRY_RUN", "true")
    (runtime_root / "data" / "raw" / "sample.csv").write_text("id,name,email,phone,salary,date_joined\n", encoding="utf-8")

    config, warnings = load_config(project_root=runtime_root, env_file=runtime_root / ".env", dotenv_optional=True)
    bootstrap_filesystem(config)

    assert config.data_file == (runtime_root / "data" / "raw" / "sample.csv").resolve(strict=False)
    assert config.smtp.is_enabled is False
    assert isinstance(warnings, list)


def test_load_config_requires_data_file_env(runtime_root: Path, monkeypatch) -> None:
    monkeypatch.delenv("DATA_FILE", raising=False)
    try:
        load_config(project_root=runtime_root, env_file=runtime_root / ".env", dotenv_optional=True)
    except Exception as exc:
        assert "DATA_FILE" in str(exc)
    else:
        raise AssertionError("Expected missing DATA_FILE to raise configuration error.")
