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

@app.get("/health")
async def get_health():
    return {"status": "healthy"}

@app.post("/process")
async def process_file(file: UploadFile = File(...)):
    global last_result, last_file, last_report_path

    # Save uploaded CSV to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_csv:
        shutil.copyfileobj(file.file, tmp_csv)
        tmp_csv_path = tmp_csv.name

    # Load config and override input_file with the temp  CSV path
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
    last_report_path = generate_report(result)

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
        return {"message:": "No files have been used"}
    
@app.get("/report")
async def get_report():
    if last_report_path is not None:
        return FileResponse(last_report_path)
    else:
        return {"message": "No report available."}

@app.get("/")
async def get_dashboard():
    with open("templates/dashboard.html", "r") as f:
        html = f.read()
        return HTMLResponse(content=html, status_code=200)