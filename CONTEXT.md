# Project Context

## Learning Plan
600 hour automation -> data -> cloud -> AI roadmap.
Currently on Big Project 1 — Business Automation Platform.
Week 16 complete (FastAPI Dashboard + Docker containerization).

## Roadmap Ahead
- Week 17 — Database layer (SQLite → PostgreSQL)

## Mentoring Preferences
- Full concept explanation before code
- Complex functions built step by step, not handed all at once
- Practical work at end of each week
- Cross-platform code always
- Commit regularly, not just at end
- Guide toward answers, don't hand them directly
- Be generous with explanations — goal is to learn and understand, not just build

## Current Project: csv_engine
Location: C:\csv_engine
Stack: Python 3.14.2 local / Python 3.11 in Docker, pandas, FastAPI, uvicorn, Jinja2, APScheduler, Docker, VSCode, Windows 11
Repo: github.com/murspi/CSV-engine

## What's Built
- logger.py — logging setup with file and console handlers + handler accumulation guard
- processor.py — full validation and cleaning pipeline, returns ProcessResponse
- main.py — CLI entry point with argparse, generates report after pipeline run
- config.json — config-driven rules
- input.csv — test dataset with intentional errors
- schemas.py — Pydantic response models for API layer
- api.py — FastAPI service with six endpoints + scheduler startup + dashboard route
- reporter.py — Jinja2 HTML report generator, saves to data/reports/report.html
- mailer.py — Gmail SMTP email sender with retry logic (3 attempts, 5s delay)
- scheduler.py — APScheduler background scheduler, self-stops after successful send
- templates/report.html — Jinja2 HTML report template
- templates/dashboard.html — browser-based user dashboard with fetch() API calls
- Dockerfile — Docker image definition
- docker-compose.yml — local container orchestration
- .dockerignore — excludes .env, venv, pycache, logs, generated files
- README.md — full project documentation

## API Endpoints
- GET / — serves browser dashboard (dashboard.html)
- GET /health — returns {"status": "healthy"}
- POST /process — accepts CSV upload, runs pipeline, returns ProcessResponse
- GET /status — returns last ProcessResponse or "No previous runs detected"
- GET /last-file — returns filename of last uploaded file or "No files have been used"
- GET /report — serves last generated HTML report via FileResponse
- GET /docs — Swagger UI

## Pipeline Steps (in order)
1. Load config
2. Validate columns
3. Drop duplicates
4. Handle numeric fields (fills defaults, records audit)
5. Handle date fields
6. Drop required field violations
7. Add _changes column to output if any defaults were applied
8. Save output
9. Generate HTML report (reporter.py)
10. Send report via email (mailer.py) — scheduled or on demand

## Key Architectural Decisions
- processor.py returns ProcessResponse instead of None
- Every exit point in run_pipeline() returns a structured response
- /process uses two temp files: one for uploaded CSV, one for modified config
- Temp files deleted after pipeline run via os.unlink()
- last_result, last_file, last_report_path stored as module-level variables in api.py
- reporter.py is pure — receives ProcessResponse, renders template, writes file, returns path
- Timestamp generated in reporter.py at render time, not in ProcessResponse
- mailer.py loads credentials from .env via python-dotenv, never hardcoded
- scheduler fires every 1 minute for testing (change to cron for production)
- scheduler self-removes job after successful email send
- setup_logger() has handler accumulation guard (if logger.handlers: return logger)
- Logger initialized in startup_event before scheduler starts to avoid thread issues
- Docker uses volumes for data/ and logs/ so generated files persist after container stops
- .env injected at runtime via env_file in docker-compose.yml, never baked into image
- Dashboard uses fetch() to POST to /process and display results without page reload

## Environment Variables (in .env, never committed)
- GMAIL_ADDRESS — sender Gmail address
- GMAIL_APP_PASSWORD — Gmail app password (requires 2FA enabled)
- RECIPIENT_EMAIL — report recipient email

## Running the Project
### Docker (recommended)
```
docker-compose build
docker-compose up
```
Open http://127.0.0.1:8000

### Local
```
uvicorn api:app --reload
```
Open http://127.0.0.1:8000

---

## config.json
```json
{
    "input_file": "data/input.csv",
    "output_file": "data/output.csv",
    "log_file": "logs/run.log",
    "required_columns": [
        "order_id",
        "customer_name",
        "email",
        "product",
        "quantity",
        "price",
        "order_date"
    ],
    "required_fields": [
        "order_id",
        "customer_name",
        "email"
    ],
    "numeric_fields": [
        "quantity",
        "price"
    ],
    "date_fields": [
        "order_date"
    ],
    "date_format": "%Y-%m-%d",
    "fill_defaults": {
        "quantity": 1,
        "price": 0.0
    },
    "drop_duplicates": true
}
```

---

## logger.py
```python
import logging
import os

def setup_logger(log_file: str) -> logging.Logger:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger("csv_engine")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
```

---

## schemas.py
```python
from pydantic import BaseModel

class ProcessResponse(BaseModel):
    success_or_failure: bool
    rows_in: int
    rows_out: int
    duplicates_dropped: int
    required_field_violations_dropped: int
    columns_validated: list[str]
```

---

## reporter.py
```python
import os
from schemas import ProcessResponse
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

env = Environment(loader=FileSystemLoader("templates"))
template = env.get_template("report.html")

def generate_report(result: ProcessResponse) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs("data/reports", exist_ok=True)
    output_path = os.path.join("data", "reports", "report.html")
    context = {
        "timestamp": timestamp,
        "success": result.success_or_failure,
        "rows_in": result.rows_in,
        "rows_out": result.rows_out,
        "duplicates_dropped": result.duplicates_dropped,
        "violations_dropped": result.required_field_violations_dropped,
        "columns_validated": result.columns_validated
    }
    html = template.render(context)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path
```

---

## mailer.py
```python
import smtplib
import os
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import logging

load_dotenv()

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

logger = logging.getLogger("csv_engine")

def send_report(report_path: str) -> bool:
    max_attempts = 3
    delay = 5
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD or not RECIPIENT_EMAIL:
        logger.error("Email credentials not found. Check your .env file.")
        return False

    with open(report_path, "r", encoding="utf-8") as f:
        report_content = f.read()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "CSV Engine Report"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = RECIPIENT_EMAIL
    msg.attach(MIMEText(report_content, "html"))

    for attempt in range(max_attempts):
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
                server.sendmail(GMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
                logger.info(f"Report sent successfully to {RECIPIENT_EMAIL}")
                return True
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_attempts - 1:
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
    logger.error("All attempts to send the report failed.")
    return False
```

---

## scheduler.py
```python
from apscheduler.schedulers.background import BackgroundScheduler
from processor import run_pipeline
from reporter import generate_report
from mailer import send_report
from logger import setup_logger
import logging
import json

logger = logging.getLogger("csv_engine")
scheduler = BackgroundScheduler()

def scheduled_job(config_path: str):
    with open(config_path, "r") as f:
        config = json.load(f)
    setup_logger(config["log_file"])
    logger.info("Scheduled job started.")
    result = run_pipeline(config_path)
    report_path = generate_report(result)
    if send_report(report_path):
        logger.info("Report send successfully.")
        scheduler.remove_job("scheduled_job")
    else:
        logger.error("Failed to send report.")

def start_scheduler(config_path: str):
    scheduler.add_job(scheduled_job, "interval", minutes=1, id="scheduled_job", args=[config_path])
    scheduler.start()
    logger.info("Scheduler started.")
```

---

## api.py
```python
from fastapi import FastAPI, UploadFile, File
from processor import run_pipeline
import tempfile
import shutil
import os
import json
from logger import setup_logger
from reporter import generate_report
from scheduler import start_scheduler
from fastapi.responses import FileResponse, HTMLResponse

last_result = None
last_file = None
last_report_path = None

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    with open("config.json", "r") as f:
        config = json.load(f)
    setup_logger(config["log_file"])
    start_scheduler("config.json")

@app.get("/")
async def get_dashboard():
    with open("templates/dashboard.html", "r", encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(content=html)

@app.get("/health")
async def get_health():
    return {"status": "healthy"}

@app.post("/process")
async def process_file(file: UploadFile = File(...)):
    global last_result, last_file, last_report_path

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_csv:
        shutil.copyfileobj(file.file, tmp_csv)
        tmp_csv_path = tmp_csv.name

    with open("config.json", "r") as f:
        config = json.load(f)
    config["input_file"] = tmp_csv_path

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w") as tmp_cfg:
        json.dump(config, tmp_cfg)
        tmp_cfg_path = tmp_cfg.name

    last_file = file.filename
    result = run_pipeline(tmp_cfg_path)
    last_result = result
    last_report_path = generate_report(result)

    os.unlink(tmp_csv_path)
    os.unlink(tmp_cfg_path)

    return result

@app.get("/status")
async def check_status():
    if last_result is not None:
        return last_result
    else:
        return {"message": "No previous runs detected"}

@app.get("/last-file")
async def check_last_file():
    if last_file is not None:
        return last_file
    else:
        return {"message:": "No files have been used"}

@app.get("/report")
async def get_report():
    if last_report_path is not None:
        return FileResponse(last_report_path)
    else:
        return {"message": "No report available."}
```

---

## main.py
```python
import argparse
from logger import setup_logger
from processor import run_pipeline
from reporter import generate_report
import json

def main():
    parser = argparse.ArgumentParser(description="CSV Processing Engine")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = json.load(f)

    setup_logger(config["log_file"])
    result = run_pipeline(args.config)
    report_path = generate_report(result)
    print(f"Report saved to: {report_path}")

if __name__ == "__main__":
    main()
```