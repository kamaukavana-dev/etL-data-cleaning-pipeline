🚀 Project Overview

This project is a configurable data quality pipeline designed to clean, validate, analyze, and report on CSV/Excel datasets at scale.

It automatically:

Cleans invalid records (emails, phone numbers, dates, numeric fields)

Tracks drop rates and data quality metrics

Generates structured Excel reports

Sends email notifications and alerts based on thresholds

Runs locally, as a standalone executable, or inside Docker

Built for real-world datasets, not toy examples.

🧠 Why This Project Exists

Dirty data silently destroys decisions.

This pipeline ensures:

Transparency → You know what was dropped and why

Automation → No manual cleaning

Accountability → Reports + logs + alerts

Scalability → Handles large files consistently

🛠️ Core Features

✅ CSV & Excel ingestion
✅ Data validation & cleaning
✅ Drop-rate analysis & severity scoring
✅ Excel report generation
✅ Automated email notifications
✅ Config-driven thresholds
✅ Async pipeline execution
✅ Docker & PyInstaller support
✅ Logging & audit trail

📦 Deployment Options
Mode	Target User	Description
Manual Run	Analysts / Individuals	Run locally using Python
Standalone EXE	Non-technical users	One-click execution (PyInstaller)
Dockerized	Teams / Enterprises	Consistent, repeatable execution
🏗️ Architecture Overview
data/
 ├── raw/            # Input CSV / Excel files
 ├── cleaned/        # Cleaned outputs
 └── reports/        # Analysis reports

src/
 ├── main.py         # Pipeline entry point
 ├── cleaners/       # Validation & cleaning logic
 ├── reporting/      # Excel report generation
 ├── notifications/ # Email & alert system
 └── utils/          # Shared utilities

configs/
 ├── client_basic.env
 ├── client_email.env
 └── client_enterprise.env

⚙️ Configuration (Environment-Driven)

All behavior is controlled via .env files:

DATA_FILE=data/raw/input.csv
RECIPIENT_EMAIL=alerts@company.com
DROP_RATE_THRESHOLD=50
INVALID_EMAIL_THRESHOLD=1000
DRY_RUN=false


✔ No hardcoded client data
✔ Easy per-client customization
✔ Safe for production use

▶️ Running the Pipeline
Local (Python)
CLIENT_ENV=configs/client_email.env python -m src.main

Docker
docker build -t data-pipeline .
docker run --env-file configs/client_enterprise.env data-pipeline

Standalone (EXE)
Double-click the executable → pipeline runs automatically

📧 Email & Alerting

The pipeline automatically sends:

Summary reports

Drop-rate warnings

Data quality alerts

Severity levels:

🟢 LOW

🟡 MEDIUM

🔴 HIGH

Example log output:

rows=10000 → 3513 | drop_rate=64.87% | severity=HIGH ⚠️

📊 Sample Output

✔ Cleaned Excel file
✔ Detailed analysis report
✔ Logged validation metrics
✔ Email notification (instant)

🔒 Reliability & Safety

Defensive validation

Explicit error handling

Logged failures

No silent data loss

Async-safe execution

🧪 Testing
pytest tests/


Includes:

Pipeline execution tests

Validation behavior checks

Failure-mode handling

🧰 Tech Stack
<div align="center"> <img src="https://skillicons.dev/icons?i=python,docker,github,linux" /> </div>

Python 3

Pandas

AsyncIO

Docker

PyInstaller

SMTP / Email

Pytest

📌 Intended Use Cases

Data cleaning services

Analytics preprocessing

Client data audits

Automated reporting pipelines

Internal data quality monitoring

👤 Author

Daniel Maina
Aspiring Full-Stack Engineer & Automation Enthusiast
📍 Nairobi, Kenya

📧 Email: kavana.daniel1@gmail.com

🔗 LinkedIn: https://www.linkedin.com/in/daniel-kamau-ab9631389

🐙 GitHub: https://github.com/kamaukavana-dev

📄 License

MIT License — free to use, modify, and extend.

<div align="center"> <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=120&section=footer&reversal=true" />

Built with discipline, curiosity, and real datasets.

</div>
