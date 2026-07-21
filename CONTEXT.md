# Project Context

## Learning Plan
600 hour automation -> data -> cloud -> AI roadmap.
Currently on Big Project 1 — Business Automation Platform.
Week 13 complete (FastAPI service with three endpoints + /last-file practical task).

## Roadmap Ahead
- Week 14 — Report Generator layered onto csv_engine

## Mentoring Preferences
- Full concept explanation before code
- Complex functions built step by step, not handed all at once
- Practical work at end of each week
- Cross-platform code always
- Commit regularly, not just at end
- Guide toward answers, don't hand them directly

## Current Project: csv_engine
Location: C:\csv_engine
Stack: Python 3.14.2, pandas, FastAPI, uvicorn, VSCode, Windows 11
Repo: github.com/YOURUSERNAME/csv-engine

## What's Built
- logger.py — logging setup with file and console handlers
- processor.py — full validation and cleaning pipeline, returns ProcessResponse
- main.py — CLI entry point with argparse
- config.json — config-driven rules
- input.csv — test dataset with intentional errors
- schemas.py — Pydantic response models for API layer
- api.py — FastAPI service with four endpoints

## API Endpoints
- GET /health — returns {"status": "healthy"} to confirm service is alive
- POST /process — accepts CSV upload, runs pipeline, returns ProcessResponse
- GET /status — returns last ProcessResponse or "No previous runs detected"
- GET /last-file — returns filename of last uploaded file or "No files have been used"

## Pipeline Steps (in order)
1. Load config
2. Validate columns
3. Drop duplicates
4. Handle numeric fields (fills defaults, records audit)
5. Handle date fields
6. Drop required field violations
7. Add _changes column to output if any defaults were applied
8. Save output

## Key architectural decisions (Week 13)
- processor.py refactored to return ProcessResponse instead of None
- Every exit point in run_pipeline() returns a structured response
- /process uses two temp files: one for the uploaded CSV, one for modified config
- Temp files deleted after pipeline run via os.unlink()
- last_result and last_file stored as module-level variables in api.py

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

## processor.py
```python
import pandas as pd
import json
import logging
from typing import Tuple
from datetime import datetime
from schemas import ProcessResponse

logger = logging.getLogger("csv_engine")

def load_config(config_path: str) -> dict:
    with open(config_path, "r") as f:
        return json.load(f)

def load_csv(file_path: str) -> pd.DataFrame:
    logger.info(f"Loading file: {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    return df

def validate_columns(df: pd.DataFrame, required_columns: list) -> list[str]:
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}. Aborting.")
        return missing
    logger.info("Column validation passed")
    return missing

def drop_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    before = len(df)
    df = df.drop_duplicates()
    dropped = before - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} duplicate row(s)")
    return df, dropped

def handle_numeric_fields(df: pd.DataFrame, numeric_fields: list, fill_defaults: dict) -> Tuple[pd.DataFrame, dict]:
    audit_dict = {}

    for field in numeric_fields:
        if field not in df.columns:
            continue

        if field in fill_defaults:
            index_with_nan = df[field].index[df[field].isna()]
            for row_index in index_with_nan:
                audit_dict.setdefault(row_index, []).append(field)
            before = df[field].isna().sum()
            df[field] = df[field].fillna(fill_defaults[field])
            if before > 0:
                logger.warning(f"Field '{field}': filled {before} missing value(s) with default {fill_defaults[field]}")

        original = df[field].copy()
        df[field] = pd.to_numeric(df[field], errors="coerce")
        invalid = df[field].isna() & original.notna()
        if invalid.any():
            logger.warning(f"Field '{field}': {invalid.sum()} non-numeric value(s) found")
            if field in fill_defaults:
                invalid_with_nan = invalid.index[invalid]
                for row_index in invalid_with_nan:
                    audit_dict.setdefault(row_index, []).append(field)
                df.loc[invalid, field] = fill_defaults[field]
                logger.warning(f"Field '{field}': replaced non-numeric value(s) with default {fill_defaults[field]}")
            else:
                df = df[~invalid]
                logger.warning(f"Field '{field}': dropped {invalid.sum()} row(s) with non-numeric values")

    return df, audit_dict

def handle_date_fields(df: pd.DataFrame, date_fields: list, date_format: str) -> pd.DataFrame:
    for field in date_fields:
        if field not in df.columns:
            continue
        parsed = pd.to_datetime(df[field], format=date_format, errors="coerce")
        invalid = parsed.isna() & df[field].notna()
        if invalid.any():
            logger.warning(f"Field '{field}': {invalid.sum()} invalid date(s) — rows dropped")
            df = df[~invalid]
        df[field] = parsed
    return df

def drop_required_field_violations(df: pd.DataFrame, required_fields: list) -> Tuple[pd.DataFrame, int]:
    before = len(df)
    df = df.dropna(subset=required_fields)
    dropped = before - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} row(s) missing in fields: {required_fields}")
    return df, dropped

def save_output(df: pd.DataFrame, output_path: str) -> None:
    df.to_csv(output_path, index=False)
    logger.info(f"Clean file saved to: {output_path}")

def run_pipeline(config_path: str) -> ProcessResponse:
    config = load_config(config_path)

    logger.info("=== CSV Engine Started ===")

    df = load_csv(config["input_file"])
    original_count = len(df)

    missing_columns = validate_columns(df, config["required_columns"])
    if missing_columns:
        return ProcessResponse(
            success_or_failure=False,
            rows_in=original_count,
            rows_out=0,
            duplicates_dropped=0,
            required_field_violations_dropped=0,
            columns_validated=missing_columns
        )

    df, duplicates_dropped = drop_duplicates(df)

    df, audit_dict = handle_numeric_fields(df, config["numeric_fields"], config.get("fill_defaults", {}))
    if audit_dict:
        changes_map = {key: ", ".join(f"{field}->default" for field in fields) for key, fields in audit_dict.items()}
        df["_changes"] = df.index.map(changes_map)

    df = handle_date_fields(df, config["date_fields"], config["date_format"])
    df, required_field_violations = drop_required_field_violations(df, config["required_fields"])

    save_output(df, config["output_file"])

    logger.info(f"=== Pipeline Complete | {original_count} rows in -> {len(df)} rows out ===")

    return ProcessResponse(
        success_or_failure=True,
        rows_in=original_count,
        rows_out=len(df),
        duplicates_dropped=duplicates_dropped,
        required_field_violations_dropped=required_field_violations,
        columns_validated=missing_columns
    )
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

last_result = None
last_file = None

app = FastAPI()

@app.get("/health")
async def get_health():
    return {"status": "healthy"}

@app.post("/process")
async def process_file(file: UploadFile = File(...)):
    global last_result, last_file

    # Save uploaded CSV to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_csv:
        shutil.copyfileobj(file.file, tmp_csv)
        tmp_csv_path = tmp_csv.name

    # Load config and override input_file with the temp CSV path
    with open("config.json", "r") as f:
        config = json.load(f)
    config["input_file"] = tmp_csv_path

    # Save modified config to its own temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w") as tmp_cfg:
        json.dump(config, tmp_cfg)
        tmp_cfg_path = tmp_cfg.name

    last_file = file.filename

    # Run pipeline with the modified config
    result = run_pipeline(tmp_cfg_path)
    last_result = result

    # Clean up both temp files
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
        return {"message": "No files have been used"}
```

---

## main.py
```python
import argparse
from logger import setup_logger
from processor import run_pipeline
import json

def main():
    parser = argparse.ArgumentParser(description="CSV Processing Engine")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = json.load(f)

    setup_logger(config["log_file"])
    run_pipeline(args.config)

if __name__ == "__main__":
    main()
```