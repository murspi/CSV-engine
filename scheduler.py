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