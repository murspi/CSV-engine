import pandas as pd
import json
import logging
from typing import Tuple
from datetime import datetime

logger = logging.getLogger("csv_engine")

def load_config(config_path: str) -> dict:
    with open(config_path, "r") as f:
        return json.load(f)
    
def load_csv(file_path: str) -> pd.DataFrame:
    logger.info(f"Loading file: {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    return df

def validate_columns(df: pd.DataFrame, required_columns: list) -> bool:
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}. Aborting.")
        return False
    logger.info("Column validation passed")
    return True

def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    dropped = before - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} duplicate row(s)")
    return df

def handle_numeric_fields(df: pd.DataFrame, numeric_fields: list, fill_defaults: dict) -> Tuple[pd.DataFrame, dict]:
    audit_dict = {}
    
    for field in numeric_fields:
        if field not in df.columns:
            continue

        # Fill missing values with default if one exists
        if field in fill_defaults:
            index_with_nan = df[field].index[df[field].isna()]
            for row_index in index_with_nan:
                audit_dict.setdefault(row_index, []).append(field)
            before = df[field].isna().sum()
            df[field] = df[field].fillna(fill_defaults[field])
            if before > 0:
                logger.warning(f"Field '{field}': filled {before} missing value(s) with default {fill_defaults[field]}")
                
        # Coerce invalid values to NaN, then fill or drop
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

def drop_required_field_violations(df: pd.DataFrame, required_fields: list) -> pd.DataFrame:
    before = len(df)
    df = df.dropna(subset=required_fields)
    dropped = before - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} row(s) missing in fields: {required_fields}")
    return df

def save_output(df: pd.DataFrame, output_path: str) -> None:
    df.to_csv(output_path, index=False)
    logger.info(f"Clean file saved to: {output_path}")

def run_pipeline(config_path: str) -> None:
    config = load_config(config_path)

    logger.info("=== CSV Engine Started ===")

    df = load_csv(config["input_file"])
    original_count = len(df)

    if not validate_columns(df, config["required_columns"]):
        return
    
    if config.get("drop_duplicates"):
        df = drop_duplicates(df)
    
    df, audit_dict = handle_numeric_fields(df, config["numeric_fields"], config.get("fill_defaults", {}))
    if audit_dict:
        changes_map = {key: ", ".join(f"{field}->default" for field in fields) for key, fields in audit_dict.items()}
        df["_changes"] = df.index.map(changes_map)
        
    df = handle_date_fields(df, config["date_fields"], config["date_format"])
    df = drop_required_field_violations(df, config["required_fields"])

    save_output(df, config["output_file"])

    logger.info(f"=== Pipeline Complete | {original_count} rows in -> {len(df)} rows out ===")