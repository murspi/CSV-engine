import argparse
from logger import setup_logger
from processor import run_pipeline
import json
from reporter import generate_report

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