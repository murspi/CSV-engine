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