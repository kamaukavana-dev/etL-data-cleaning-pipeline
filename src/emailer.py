"""
Backward-compatible email helpers.
Prefer src.services.notification_service.NotificationService.
"""

from pathlib import Path

from src.core.config import load_config
from src.services.notification_service import NotificationService


def _service() -> NotificationService:
    config, _ = load_config()
    return NotificationService(config)


def load_template(template_file: str, context: dict) -> str:
    return _service().render_template(template_file, context)


def send_email(
    *,
    recipient: str,
    subject: str,
    body: str,
    attachment_path: str | Path | None = None,
    attachment_required: bool = False,
) -> None:
    if attachment_required and not attachment_path:
        raise ValueError("attachment_required=True but attachment_path not supplied")
    attachment = Path(attachment_path).resolve(strict=False) if attachment_path else None
    _service().send_email(subject=subject, body=body, recipient=recipient, attachment=attachment)
