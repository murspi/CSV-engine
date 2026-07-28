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
    delay = 5 # seconds
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
