# CSV Processing Engine

A config-driven CSV validation and cleaning pipeline.
Part of a larger Business Automation Platform.

## What it does
- Validates CSV structure against defined rules
- Fills missing numeric values with configurable defaults
- Detects and replaces non-numeric values
- Drops invalid dates, duplicates, and rows missing required fields
- Logs every action taken during processing

## Project Structure
```
csv_engine/
├── main.py          # CLI entry point
├── processor.py     # core pipeline logic
├── logger.py        # logging setup
├── config.json      # validation rules
├── data/
│   └── input.csv    # raw input file
└── logs/
    └── run.log      # processing log
```

## Setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Usage
```bash
python main.py
python main.py --config config.json
```