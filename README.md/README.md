# SAVE 10+ HOURS/WEEKS : SMART EXCEL REPORTING & EMAIL AUTOMATION 🤖

Turn messy CSVs into board-ready Excel reports and automated email briefings — safely, reliably, and without manual work.

A production-grade Python ETL (Extract, Transform, Load) pipeline designed for real client data — including broken files, schema changes, and large datasets — not just clean demo spreadsheets.

# 🎬 Demo Overview
🔹 Pipeline Execution (End-to-End)


End-to-end execution showing data load, analysis, report generation, and email dispatch.

🔹 Data Cleaning & Analysis Logs


Real-time logs with cleaning report, metrics, and analysis summary.

🔹 Generated Excel Report (Multi-Sheet)

![Excel Report Preview](assets/screenshots/microsoft Excel.jpg)
Auto-formatted Excel report with multiple sheets, bold headers, and highlighted values.

🔹 Email Notification with Attachment

![Email Report Delivery](assets/screenshots/Email Verification Tools.jpg)
Automated email delivery with Excel report attached.

🎥 Video Walkthrough (Optional but Recommended)

▶ Watch Full Demo Video:
Click here to watch the demo

Short walkthrough showing pipeline execution, Excel report creation, and email delivery.

# 🔹 Features (Client-Safe & Production-Ready)
Core Automation

Dynamic Data Loading: Supports CSV and Excel formats

Automated Data Cleaning & Validation: Generates detailed cleaning reports

Automated Analysis: Statistics, summaries, correlations

Excel Report Generation:

Multi-sheet output

Auto column width

Bold headers

Conditional formatting

Email Automation:

SMTP support

Attachments

Retry logic

Dry-run mode (safe testing)

Scheduling: Daily, weekly, or monthly execution

Failure Alerts: Webhook (Slack/Teams) or email fallback

Environment-Based Configuration: .env driven

Logging & Monitoring: Rotating logs + console output

# 🧠 Edge-Case Handling (Where Most Scripts Break)

This pipeline is explicitly designed for dirty, real-world client data:

Encoding Issues

Automatic handling of UTF-8 and ISO-8859-1 encoded files

Prevents crashes caused by special characters or corrupted text

Schema Drift Protection

Detects when clients add, remove, or rename columns

Sends a Data Structure Alert instead of crashing mid-run

Large File Optimization

Chunk-based processing using Pandas (chunksize)

Handles files larger than available RAM (2GB+ CSVs)

Suitable for enterprise-scale datasets

Data Quality Enforcement

Invalid emails, phone numbers, dates, currencies are detected

Detailed reports show exactly what was dropped and why

# 🏗 Professional ETL Architecture (Not a One-Off Script)

Unlike basic automation scripts, this project is built as a modular ETL pipeline:

Raw Data Preservation

Original client files are never overwritten

Always stored safely in data/raw/

Decoupled Architecture

Loader, cleaner, analyzer, reporter, and emailer are isolated

Change report layouts or email templates without breaking core logic

Full Audit Logging

Every step tracked for troubleshooting and compliance

Logs stored in logs/app.log

# 🔐 Security & Privacy (High-Trust Clients)

Local Processing

Data is processed locally or in a private cloud environment

No data sent to third-party AI services unless explicitly requested

Enterprise-Grade Credential Management

All secrets stored securely in .env

No passwords hardcoded in source code

Email Safety

Gmail App Passwords supported

Dry-run mode ensures safe testing before production

📂 Project Structure
project_root/
├─ src/
│ ├─ loader.py
│ ├─ cleaner.py
│ ├─ analyzer.py
│ ├─ excel_writer.py
│ ├─ emailer.py
│ └─ main.py
├─ data/
│ ├─ raw/
│ ├─ reports/
│ └─ processed/
├─ assets/
│ ├─ screenshots/
│ │ ├─ demo_1_pipeline_overview.png
│ │ ├─ demo_2_logs_analysis.png
│ │ ├─ demo_3_excel_report.png
│ │ └─ demo_4_email_delivery.png
│ └─ videos/
│ └─ full_pipeline_demo.mp4
├─ logs/
├─ .env
├─ requirements.txt
└─ README.md

⚡ Setup Instructions
1️⃣ Clone Project
git clone <your-repo-url>
cd <project_root>

2️⃣ Install Dependencies
pip install -r requirements.txt


Includes:

pandas

openpyxl

schedule

aiohttp

aiosmtplib

python-dotenv

3️⃣ Configure Environment

Create a .env file:

# SMTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SENDER_EMAIL=your_email@gmail.com

# Client
CLIENT_NAME=Daniel Maina
RECIPIENT_EMAIL=recipient@example.com
EMAIL_FREQUENCY=weekly

# Pipeline
DATA_FILE=data/raw/input.csv
SCHEDULE_TIME=09:00
DRY_RUN=false

# Logging & Alerts
LOG_FILE=logs/app.log
ALERT_EMAIL=admin@example.com
ALERT_WEBHOOK_URL=


⚠ Important

Use Gmail App Passwords, not your main password

Validate placeholders like {{CLIENT_NAME}}, {{EMAIL_FREQUENCY}}

4️⃣ Quick Test Run (Safe Mode)
DRY_RUN=true python src/main.py


✔ Runs full pipeline
✔ Generates Excel report
❌ Does NOT send emails

# 📊 Logs & Monitoring

Logs rotate automatically

Stored at: logs/app.log

tail -f logs/app.log

📁 Data Input

Default:

data/raw/input.csv
data/raw/input.xlsx


Advanced:

DATA_FILE=/absolute/path/to/client_file.xlsx


Supported formats:

.csv

.xlsx

.xls

📄 License

MIT License — free to use, modify, and distribute.

# 📨 Support

📧 Email: kamaukavana@gmail.com

🔔 Alerts via webhook or email