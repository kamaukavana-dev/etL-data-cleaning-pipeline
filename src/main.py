import os
import sys
import time
import logging
import datetime
import asyncio
from pathlib import Path
from typing import Optional
import schedule
import aiohttp
import chardet
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

from src import loader, cleaner, analyzer, excel_writer, emailer
from src.exceptions import (
    PipelineError,
    DataLoadError,
    CleaningError,
    AnalysisError,
    ReportError,
    EmailError,
)

# ======================================================
# Helper functions
# ======================================================

def build_subject(severity: str) -> str:
    """Return an email subject line based on severity level."""
    if severity.startswith("HIGH"):
        return "[ACTION REQUIRED] Data Quality Alert: High Drop Rate"
    elif severity.startswith("MEDIUM"):
        return "[NOTICE] Data Quality Report: Moderate Issues"
    else:
        return "Data Quality Report: Clean Run"

# ======================================================
# Pipeline metadata
# ======================================================
PIPELINE_VERSION = "1.4"

# ======================================================
# Logging setup
# ======================================================
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logger = logging.getLogger("AsyncPipeline")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=5_000_000,
    backupCount=5,
    encoding="utf-8",
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# ======================================================
# Load environment
# ======================================================
env_path = Path.cwd() / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.info("Loaded environment from %s", env_path)
else:
    logger.warning(".env file not found at %s, using defaults", env_path)

# ======================================================
# Environment validation
# ======================================================
def validate_env() -> None:
    required = [
        "SMTP_SERVER",
        "SMTP_PORT",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "RECIPIENT_EMAIL",
        "DATA_FILE",
    ]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise PipelineError(f"Missing environment variables: {missing}")

# ======================================================
# Encoding detection
# ======================================================
def detect_file_encoding(filepath: str) -> str:
    try:
        with open(filepath, "rb") as file:
            raw = file.read(10_000)
        result = chardet.detect(raw)
        encoding = result.get("encoding") or "utf-8"
        return "utf-8" if encoding.lower() == "ascii" else encoding
    except OSError as exc:
        logger.warning(
            "Encoding detection failed (%s). Using utf-8 fallback.", exc
        )
        return "utf-8"

# ======================================================
# Schema drift handling
# ======================================================
REQUIRED_COLUMNS = ["id", "name", "email", "phone", "salary", "date_joined"]
OPTIONAL_COLUMNS = [
    "department",
    "notes",
    "position",
    "location",
    "status",
    "manager",
    "dob",
    "gender",
    "contract_type",
    "last_updated",
]
EXPECTED_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

def handle_schema_drift(df):
    missing_required = set(REQUIRED_COLUMNS) - set(df.columns)
    for col in missing_required:
        logger.warning("Adding missing required column: %s", col)
        df[col] = None

    for col in OPTIONAL_COLUMNS:
        if col not in df.columns:
            df[col] = None

    return df[[col for col in EXPECTED_COLUMNS if col in df.columns]]

# ======================================================
# Alerting
# ======================================================
async def send_webhook_alert(url: str, message: str) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, json={"text": f"Pipeline failure: {message}"}
        ) as response:
            if response.status >= 400:
                raise PipelineError(
                    f"Webhook failed with HTTP {response.status}"
                )

async def alert_failure(message: str) -> None:
    webhook_url = os.getenv("ALERT_WEBHOOK_URL")

    if webhook_url:
        try:
            await send_webhook_alert(webhook_url, message)
            logger.info("Failure alert sent via webhook")
            return
        except PipelineError as exc:
            logger.error("Webhook alert failed: %s", exc)

    alert_email = os.getenv("ALERT_EMAIL", "admin@example.com")
    try:
        emailer.send_email(
            recipient=alert_email,
            subject="Pipeline Failure Alert",
            body=f"Pipeline failure: {message}",
        )
        logger.info("Failure alert sent via email")
    except EmailError as exc:
        logger.error("Failed to send alert email: %s", exc)

# ======================================================
# Email sender with backoff
# ======================================================
async def send_with_backoff(
    *,
    recipient: str,
    subject: str,
    body: str,
    attachment_path: Optional[str] = None,
    max_retries: int = 3,
) -> None:
    delays = [1, 5, 10]

    for attempt in range(max_retries):
        try:
            emailer.send_email(
                recipient=recipient,
                subject=subject,
                body=body,
                attachment_path=attachment_path,
                attachment_required=True,
            )
            logger.info("Email sent successfully (attempt %d)", attempt + 1)
            return
        except EmailError as exc:
            if attempt == max_retries - 1:
                raise
            wait = delays[attempt]
            logger.warning(
                "Email failed (attempt %d/%d): %s | retry in %ds",
                attempt + 1,
                max_retries,
                exc,
                wait,
            )
            await asyncio.sleep(wait)

# ======================================================
# Pipeline execution
# ======================================================
async def run_pipeline_async() -> dict:
    try:
        validate_env()

        filepath = os.getenv("DATA_FILE")
        if filepath.lower().endswith(".csv"):
            encoding = detect_file_encoding(filepath)
            df = loader.load_csv(filepath, encoding=encoding)
        else:
            df = loader.load_excel(filepath)

        df = handle_schema_drift(df)

        clean_df, cleaning_report = cleaner.clean_data(df)
        logger.info("Cleaning report: %s", cleaning_report)

        processed_dir = Path("data/processed")
        processed_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_path = processed_dir / f"cleaned_{timestamp}.csv"
        clean_df.to_csv(clean_path, index=False)

        results = analyzer.analyze_data(clean_df)
        stats = results.get("statistics", {})

        report_info = excel_writer.write_analysis_to_excel(
            results,
            f"analysis_report_{timestamp}.xlsx",
            clean_df=clean_df,
            cleaning_report=cleaning_report,
        )

        report_path = report_info["filepath"]
        report_file = Path(report_path)

        if not report_file.exists() or report_file.stat().st_size == 0:
            raise ReportError("Generated report is empty or missing")

        # ✅ Compute drop rate and severity classification
        drop_rate = 1 - (cleaning_report["final_rows"] / cleaning_report["original_rows"])
        if drop_rate < 0.10:
            severity = "LOW"
        elif drop_rate <= 0.30:
            severity = "MEDIUM"
        else:
            severity = "HIGH ⚠️"

        # ✅ Threshold checks (configurable via .env)
        drop_rate_threshold = float(os.getenv("ALERT_DROP_RATE", "0.5"))
        invalid_emails_threshold = int(os.getenv("ALERT_INVALID_EMAILS", "1000"))

        if drop_rate > drop_rate_threshold:
            logger.warning(
                "Drop rate exceeded threshold | actual=%s | threshold=%s",
                f"{drop_rate:.2%}", f"{drop_rate_threshold:.0%}"
            )
            # optional: trigger alert email/webhook here

        if cleaning_report.get("invalid_emails_dropped", 0) > invalid_emails_threshold:
            logger.warning(
                "Invalid emails exceeded threshold | actual=%d | threshold=%d",
                cleaning_report["invalid_emails_dropped"], invalid_emails_threshold
            )
            # optional: trigger alert email/webhook here
        # ✅ Enrich cleaning_report with all placeholders expected by the template
        cleaning_report["CLIENT_NAME"] = os.getenv("CLIENT_NAME", "Customer")
        cleaning_report["EMAIL_FREQUENCY"] = os.getenv("EMAIL_FREQUENCY", "weekly")
        cleaning_report["ROWS_LOADED"] = len(df)
        cleaning_report["ROWS_CLEANED"] = len(clean_df)
        cleaning_report["PIPELINE_VERSION"] = PIPELINE_VERSION
        cleaning_report["REPORT_PATH"] = report_path
        cleaning_report["MEAN_VALUES"] = stats.get("mean")
        cleaning_report["MIN_VALUES"] = stats.get("min")
        cleaning_report["MAX_VALUES"] = stats.get("max")
        cleaning_report["DROP_RATE"] = f"{drop_rate:.2%}"
        cleaning_report["SEVERITY"] = severity

        # Ensure optional placeholders always exist
        cleaning_report.setdefault("missing_required_columns", [])
        cleaning_report.setdefault("extra_columns", [])

        # ✅ Pass enriched dict into template
        email_body = emailer.load_template("report_email.txt", cleaning_report)

        # ✅ Build subject dynamically based on severity
        if severity.startswith("HIGH"):
            subject = "[ACTION REQUIRED] Data Quality Alert: High Drop Rate"
        elif severity.startswith("MEDIUM"):
            subject = "[NOTICE] Data Quality Report: Moderate Issues"
        else:
            subject = "Data Quality Report: Clean Run"

        # ✅ Use the subject when sending email
        if os.getenv("DRY_RUN", "false").lower() != "true":
            await send_with_backoff(
                recipient=os.getenv("RECIPIENT_EMAIL"),
                subject=subject,
                body=email_body,
                attachment_path=report_path,
            )
        else:
            logger.info("Dry-run enabled — email skipped")

        summary = {
            "report_path": report_path,
            "rows_loaded": len(df),
            "rows_cleaned": len(clean_df),
            "processed_path": str(clean_path),
            "timestamp": timestamp,
            "drop_rate": f"{drop_rate:.2%}",
            "severity": severity,
        }

        logger.info(
            "Pipeline completed successfully | rows=%d → %d | drop_rate=%s | severity=%s | report=%s",
            cleaning_report["original_rows"],
            cleaning_report["final_rows"],
            cleaning_report["DROP_RATE"],
            cleaning_report["SEVERITY"],
            report_path,
        )

        return summary

    except (
        DataLoadError,
        CleaningError,
        AnalysisError,
        ReportError,
        EmailError,
        PipelineError,
    ) as exc:
        logger.error("Pipeline failed: %s", exc)
        await alert_failure(str(exc))
        sys.exit(1)

# ======================================================
# Scheduler
# ======================================================

def schedule_pipeline_async() -> None:
    frequency = os.getenv("EMAIL_FREQUENCY", "weekly").lower()
    schedule_times = os.getenv("SCHEDULE_TIMES", "09:00").split(",")
    schedule_times = [t.strip() for t in schedule_times]

    job = lambda: asyncio.run(run_pipeline_async())

    # Configure frequency
    if frequency == "daily":
        for t in schedule_times:
            schedule.every().day.at(t).do(job)
    elif frequency == "weekly":
        for t in schedule_times:
            schedule.every().monday.at(t).do(job)
    elif frequency == "monthly":
        # Approximate monthly run: every 30 days
        for t in schedule_times:
            schedule.every(30).days.at(t).do(job)
    else:
        logger.warning("Unknown frequency '%s', defaulting weekly", frequency)
        for t in schedule_times:
            schedule.every().monday.at(t).do(job)

    logger.info(
        "Scheduler started | frequency=%s | times=%s | version=%s",
        frequency,
        schedule_times,
        PIPELINE_VERSION,
    )

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        sys.exit(0)

# ======================================================
# Entry point
# ======================================================
if __name__ == "__main__":
    run_mode = os.getenv("RUN_MODE", "manual").lower()

    if run_mode == "manual":
        asyncio.run(run_pipeline_async())
    elif run_mode == "scheduled":
        schedule_pipeline_async()
    else:
        logger.warning("Unknown RUN_MODE '%s', defaulting to manual", run_mode)
        asyncio.run(run_pipeline_async())
