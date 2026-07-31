# CSV Engine

A CSV processing platform that validates, cleans, and transforms CSV files
using configurable rules. Includes a FastAPI backend, browser-based dashboard,
automated HTML report generation, scheduled email delivery, and full Docker
containerization for consistent deployment anywhere.

## What it does

- Validates and cleans CSV files based on config-defined rules
- Drops duplicates, handles missing values, enforces required fields
- Generates styled HTML reports after every pipeline run
- Sends reports automatically via email on a daily schedule
- Provides both a developer API (Swagger) and a user-friendly dashboard

## Project Structure

```
csv_engine/
├── api.py              # FastAPI service and endpoints
├── processor.py        # Core CSV cleaning pipeline
├── reporter.py         # HTML report generator
├── mailer.py           # Email automation with retry logic
├── scheduler.py        # Automated scheduling with APScheduler
├── schemas.py          # Pydantic response models
├── logger.py           # Logging setup
├── main.py             # CLI entry point
├── config.json         # Pipeline configuration
├── Dockerfile          # Docker image definition
├── docker-compose.yml  # Local container orchestration
├── templates/          # Jinja2 HTML templates
│   ├── dashboard.html  # Browser dashboard
│   └── report.html     # Pipeline report template
└── data/               # Input/output CSV files
```

## Running with Docker (recommended)

1. Clone the repo
2. Create a `.env` file in the project root:

```
GMAIL_ADDRESS=you@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
RECIPIENT_EMAIL=recipient@gmail.com
```

3. Build and run:

```
docker-compose build
docker-compose up
```

4. Open `http://127.0.0.1:8000` in your browser

## Running locally

1. Create and activate a virtual environment
2. Install dependencies:

```
pip install -r requirements.txt
```

3. Create `.env` file (see above)
4. Run:

```
uvicorn api:app --reload
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | Browser dashboard |
| GET | /health | Service health check |
| POST | /process | Upload and process a CSV file |
| GET | /status | Last pipeline result |
| GET | /last-file | Last uploaded filename |
| GET | /report | Last generated HTML report |
| GET | /docs | Swagger API documentation |

## Configuration

Edit `config.json` to customize pipeline behavior — required columns,
numeric fields, date formats, fill defaults, and file paths.

## Stack

Python 3.11 · FastAPI · pandas · Jinja2 · APScheduler · Docker