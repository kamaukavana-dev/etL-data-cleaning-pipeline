from __future__ import annotations

import logging
import smtplib
import ssl
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from string import Template
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.core.config import AppConfig
from src.core.exceptions import NotificationError

LOGGER = logging.getLogger("etl.notifications")


class NotificationService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        # ... (unchanged)
        template_path = self.config.paths.templates_dir / template_name
        try:
            with template_path.open("r", encoding="utf-8") as handle:
                template = Template(handle.read())
        except FileNotFoundError as exc:
            raise NotificationError(
                "Email template file is missing.",
                error_code="NOTIFY_TEMPLATE_MISSING",
                context={"template_path": str(template_path)},
            ) from exc
        except OSError as exc:
            raise NotificationError(
                "Email template file could not be read.",
                error_code="NOTIFY_TEMPLATE_READ_FAILED",
                context={"template_path": str(template_path)},
            ) from exc

        body = template.safe_substitute(context)
        if "$" in body:
            LOGGER.warning("Email template contains unresolved placeholders.")
        return body

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((smtplib.SMTPException, ConnectionError)),
        reraise=True,
    )
    def send_email(
        self,
        *,
        subject: str,
        body: str,
        recipient: str | None = None,
        attachment: Path | None = None,
    ) -> None:
        smtp = self.config.smtp
        if not smtp.is_enabled:
            raise NotificationError(
                "SMTP is disabled.",
                error_code="NOTIFY_SMTP_DISABLED",
                context={"reason": smtp.disabled_reason},
            )

        target_recipient = recipient or smtp.recipient_email
        if not target_recipient:
            raise NotificationError(
                "Recipient email is required.",
                error_code="NOTIFY_RECIPIENT_MISSING",
                context={},
            )

        message = MIMEMultipart()
        message["From"] = smtp.sender_email
        message["To"] = target_recipient
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        if attachment is not None:
            path = attachment.resolve(strict=False)
            if not path.exists() or not path.is_file():
                raise NotificationError(
                    "Attachment path is invalid.",
                    error_code="NOTIFY_ATTACHMENT_INVALID",
                    context={"attachment_path": str(path)},
                )
            with path.open("rb") as file_handle:
                part = MIMEApplication(file_handle.read(), Name=path.name)
            part["Content-Disposition"] = f'attachment; filename="{path.name}"'
            message.attach(part)

        try:
            assert smtp.server is not None
            assert smtp.port is not None
            assert smtp.user is not None
            assert smtp.password is not None

            if smtp.port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(smtp.server, smtp.port, context=context, timeout=30) as server:
                    server.login(smtp.user, smtp.password)
                    server.send_message(message)
            else:
                with smtplib.SMTP(smtp.server, smtp.port, timeout=30) as server:
                    server.ehlo()
                    server.starttls(context=ssl.create_default_context())
                    server.login(smtp.user, smtp.password)
                    server.send_message(message)
        except (smtplib.SMTPException, ConnectionError) as exc:
            LOGGER.warning(f"Email delivery attempt failed: {exc}. Retrying...")
            raise
        except Exception as exc:
            raise NotificationError(
                "Email delivery failed (non-retryable).",
                error_code="NOTIFY_SEND_FAILED",
                context={"recipient": target_recipient},
            ) from exc

        LOGGER.info("Email delivered.", extra={"stage": "notification", "recipient": target_recipient})
