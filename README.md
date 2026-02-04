🚀 Data Quality Automation Pipeline
Clean • Validate • Analyze • Report • Notify

Dockerized • Config-Driven • Async • Production-Style

<div align="center"> <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=40&duration=3500&pause=900&color=00F7FF&center=true&vCenter=true&width=1400&lines=Enterprise-Style+Data+Quality+Automation;Clean+Dirty+Data+at+Scale;Reports+%7C+Alerts+%7C+Docker+Ready" /> <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=160&section=header&text=Data+Quality+Automation&fontSize=48&fontColor=ffffff" /> </div>
🏷️ Trust & Technology Badges
<div align="center">






















</div>
🌍 Project Overview

This project is a fully automated data-quality pipeline designed to process real-world dirty datasets with zero manual intervention.

It ingests CSV / Excel files, validates them against strict rules, cleans invalid data, generates professional Excel reports, and sends automated email alerts based on configurable thresholds.

This is not a demo script.
It is designed to behave like a real production pipeline.

❌ The Problem

Most datasets in the real world are:

Inconsistent

Partially invalid

Poorly formatted

Silently broken

Manual cleaning does not scale.

✅ The Solution

This pipeline enforces data discipline through:

Deterministic validation rules

Transparent row-level drops

Quantitative quality metrics

Automated notifications

Reproducible execution

🧠 Core Capabilities
🔍 Validation Engine

Email format validation

Phone number validation

Numeric field validation

Date parsing & validation

Missing required column detection

Unexpected column detection

🧹 Cleaning Engine

Row-level filtering

Consistent rule application

Full drop accounting

📊 Analytics Layer

Drop-rate calculation

Severity classification

Threshold comparison

Dataset health scoring

📈 Reporting System

Auto-generated Excel reports

Summary sheets

Validation breakdowns

Time-stamped outputs

📧 Notification Engine

SMTP-based email alerts

Configurable recipients

Severity-based warnings

Instant delivery

🖼️ Visual Pipeline Architecture
┌───────────────────┐
│   Raw Data File   │  CSV / Excel
└─────────┬─────────┘
          ↓
┌───────────────────┐
│   Validation      │
│ Emails | Phones   │
│ Dates  | Numbers  │
└─────────┬─────────┘
          ↓
┌───────────────────┐
│   Cleaning        │
│ Drop Invalid Rows │
└─────────┬─────────┘
          ↓
┌───────────────────┐
│   Analysis        │
│ Drop Rates        │
│ Severity          │
└─────────┬─────────┘
          ↓
┌───────────────────┐
│   Reporting       │
│ Excel Outputs     │
└─────────┬─────────┘
          ↓
┌───────────────────┐
│   Notifications   │
│ Email Alerts      │
└───────────────────┘

🗂️ Project Structure (Production-Style)
workproject/
│
├── data/
│   ├── raw/                # Client input files
│   ├── cleaned/            # Cleaned outputs
│   └── reports/            # Excel analysis reports
│
├── src/
│   ├── main.py             # Entry point
│   ├── pipeline/           # Async orchestration
│   ├── validators/         # Validation rules
│   ├── cleaners/           # Cleaning logic
│   ├── analysis/           # Metrics & severity
│   ├── reporting/          # Excel generation
│   ├── notifications/      # Email system
│   └── utils/              # Shared utilities
│
├── configs/
│   ├── client_basic.env
│   ├── client_email.env
│   └── client_enterprise.env
│
├── Dockerfile
├── requirements.txt
└── README.md

⚙️ Configuration-Driven Design

Each client uses their own environment file.

DATA_FILE=data/raw/input.csv

DROP_RATE_THRESHOLD=50
INVALID_EMAIL_THRESHOLD=1000
INVALID_PHONE_THRESHOLD=1500

SEND_EMAIL=true
RECIPIENT_EMAIL=alerts@company.com

DRY_RUN=false


✔ No hard-coded values
✔ Safe for multiple clients
✔ Easy to audit & customize

▶️ Execution Options
🐍 Local Python
CLIENT_ENV=configs/client_basic.env python -m src.main

🐳 Docker (Recommended)
docker build -t data-quality-pipeline .
docker run --env-file configs/client_enterprise.env data-quality-pipeline

🖥️ Standalone Executable

Built with PyInstaller

No Python required

One-click execution for non-technical clients

📬 Real Execution Example
rows=10000 → 3513
drop_rate=64.87%
severity=HIGH ⚠️
report=analysis_report_20260203_163521.xlsx
email_status=SENT


✔ Logs generated
✔ Report saved
✔ Email delivered instantly

🔐 Reliability & Safety

Explicit exception handling

No silent failures

Threshold-based alerts

Deterministic output

Full logging trail

🧪 Quality & Testing
pytest tests/


Test coverage includes:

Validation accuracy

Pipeline execution

Failure scenarios

Config parsing

🧰 Technology Stack
<div align="center"> <img src="https://skillicons.dev/icons?i=python,docker,linux,github,vscode" /> </div>

Python 3.10+

Pandas

AsyncIO

Docker

PyInstaller

SMTP

Pytest

🎯 Use Cases

Freelance data cleaning

Client data audits

Analytics preprocessing

Automated data checks

Internal pipelines

👤 Author

Daniel Maina
Aspiring Full-Stack Engineer,Cloud Architect & Automation Enthusiast🤖
📍 Nairobi, Kenya

📧 Email: kavana.daniel1@gmail.com

🔗 LinkedIn: https://www.linkedin.com/in/daniel-kamau-ab9631389

🐙 GitHub: https://github.com/kamaukavana-dev

Built as a project with real engineering discipline.

📄 License

MIT License — free to use, extend, and modify.

<div align="center"> <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=140&section=footer&reversal=true" />
Clean Data Is Not Optional.
Automate It.
</div>
