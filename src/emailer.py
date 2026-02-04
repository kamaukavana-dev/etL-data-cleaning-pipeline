import os
import smtplib
import ssl
import logging
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from string import Template

from src.exceptions import EmailError

logger = logging.getLogger(__name__)

EMAILER_VERSION = "1.1"

REQUIRED_ENV_VARS = [
    "SMTP_SERVER",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "SENDER_EMAIL",
]


def _validate_email_config():
    missing = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]
    if missing:
        raise EmailError(f"Missing email configuration variables: {missing}")


def load_template(template_file: str, context: dict) -> str:
    """
    Load and render an email template using string.Template.
    """
    templates_dir = os.getenv("TEMPLATES_DIR", "emails/templates")
    template_path = Path(templates_dir) / template_file

    try:
        with template_path.open("r", encoding="utf-8") as f:
            template = Template(f.read())

        rendered = template.safe_substitute(context)

        # Warn if placeholders remain unsubstituted
        if "$" in rendered:
            logger.warning("Template rendering left unsubstituted placeholders.")

        return rendered

    except FileNotFoundError:
        raise EmailError(f"Email template not found: {template_file}")
    except Exception as e:
        logger.exception("Failed to load email template.")
        raise EmailError("Template rendering failed") from e


def send_email(
    *,
    recipient: str,
    subject: str,
    body: str,
    attachment_path: str | None = None,
    attachment_required: bool = False,
):
    """
    Send an email with optional attachment.
    """

    if not recipient or "@" not in recipient:
        raise EmailError(f"Invalid recipient email address: {recipient}")

    _validate_email_config()

    try:
        msg = MIMEMultipart()
        msg["From"] = os.getenv("SENDER_EMAIL")
        msg["To"] = recipient
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        # Attachment handling
        if attachment_path:
            path = Path(attachment_path)
            if not path.exists():
                raise EmailError(f"Attachment not found: {attachment_path}")
            if path.stat().st_size == 0:
                raise EmailError(f"Attachment is empty: {attachment_path}")

            with path.open("rb") as f:
                part = MIMEApplication(f.read(), Name=path.name)

            part["Content-Disposition"] = f'attachment; filename="{path.name}"'
            msg.attach(part)

        elif attachment_required:
            raise EmailError("Attachment required but not provided.")

        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")

        logger.info(
            "Connecting to SMTP server=%s | port=%s | recipient=%s | version=%s",
            smtp_server,
            smtp_port,
            recipient,
            EMAILER_VERSION,
        )

        if smtp_port == 465:
            # SSL/TLS connection directly
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context, timeout=30) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
        else:
            # Normal connect, then upgrade to TLS
            with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

        logger.info("Email sent successfully to %s", recipient)

    except EmailError:
        raise
    except Exception as e:
        logger.exception("SMTP send failed.")
        raise EmailError("Email delivery failed") from e