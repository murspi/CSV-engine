from fastapi import FastAPI, UploadFile, File
from processor import run_pipeline
import tempfile
import shutil
import os
import json

last_result = None

app = FastAPI()

@app.get("/health")
async def get_health():
    return {"status": "healthy"}

@app.post("/process")
async def process_file(file: UploadFile = File(...)):
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

    global last_result

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