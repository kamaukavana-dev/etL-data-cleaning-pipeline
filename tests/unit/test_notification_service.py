from __future__ import annotations

from pathlib import Path

from src.core.config import load_config
from src.services.notification_service import NotificationService


def test_notification_disabled_without_smtp(runtime_root: Path, monkeypatch) -> None:
    csv_path = runtime_root / "data" / "raw" / "input.csv"
    csv_path.write_text("id,name,email,phone,salary,date_joined\n", encoding="utf-8")

    monkeypatch.setenv("DATA_FILE", str(csv_path))
    monkeypatch.setenv("SMTP_SERVER", "")
    monkeypatch.setenv("SMTP_PORT", "")
    monkeypatch.setenv("SMTP_USER", "")
    monkeypatch.setenv("SMTP_PASSWORD", "")
    monkeypatch.setenv("SENDER_EMAIL", "")
    monkeypatch.setenv("RECIPIENT_EMAIL", "")

    config, _ = load_config(project_root=runtime_root, env_file=runtime_root / ".env", dotenv_optional=True)
    service = NotificationService(config)

    try:
        service.send_email(subject="x", body="y")
    except Exception as exc:
        assert "SMTP is disabled" in str(exc)
    else:
        raise AssertionError("Expected disabled SMTP to raise notification error.")
