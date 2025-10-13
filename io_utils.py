"""
File and CSV utilities for G2S scraper.
Includes streaming CSV read/write and schema validation.
"""

import logging
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Union

import pandas as pd

from exceptions import ParseError
from log_utils import mask_secrets


def read_part_numbers_in_chunks(input_csv: Path, chunksize: int) -> Iterator[list[str]]:
    """
    Stream part numbers from a CSV file in chunks.
    Yields lists of part numbers (as strings).
    """
    try:
        chunk_iter = pd.read_csv(input_csv, chunksize=chunksize, header=None)
        for chunk in chunk_iter:
            part_numbers = chunk.iloc[:, 0].dropna().astype(str).tolist()
            yield part_numbers
    except Exception as e:  # noqa: BLE001
        safe_msg = mask_secrets(str(e))
        logging.error(f"Failed to read input CSV: {safe_msg}")
        raise ParseError(f"Failed to read input CSV: {safe_msg}") from e

def save_results_atomic(
    out_path: Path, results: list[dict[str, str]], column_names: list[str]
) -> None:
    """
    Atomically save results to CSV, reindexing columns and filling missing values.
    Writes to a temp file and moves into place to avoid partial/corrupt files.
    """
    try:
        df = pd.DataFrame(results)
        df = df.reindex(columns=column_names, fill_value="Not found")
        df["Status"] = df["Status"].replace("Not found", "Failed")
        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            dir=out_path.parent,
            suffix=".csv",
            encoding="utf-8",
            newline="",
        ) as tmp:
            df.to_csv(tmp.name, index=False)
            tmp_path = Path(tmp.name)
        shutil.move(str(tmp_path), str(out_path))
    except Exception as e:  # noqa: BLE001
        safe_msg = mask_secrets(str(e))
        logging.error(f"Failed to save results atomically: {safe_msg}")
        raise ParseError(f"Failed to save results atomically: {safe_msg}") from e

def generate_summary_report(
    results: list[dict[str, str]], 
    elapsed: float, 
    input_file: Union[str, Path, None] = None, 
    output_file: Union[str, Path, None] = None
) -> str:
    """
    Generate a summary report as a string (for email or terminal output).
    Optionally includes input and output file names.
    """
    total = len(results)
    success = sum(1 for r in results if r.get("Status") == "Success")
    failed = sum(1 for r in results if r.get("Status") == "Failed")
    not_found = sum(1 for r in results if r.get("Status") == "Not Found")
    no_match = sum(1 for r in results if r.get("Status") == "No Exact Match")
    
    # Build the summary with optional file information
    summary = (
        f"All items processed. Total: {total}. Success: {success}. Failed: {failed}. "
        f"Not Found: {not_found}. No Exact Match: {no_match}. "
        f"Total elapsed time: {elapsed:.2f} seconds."
    )
    
    # Add file information if provided
    if input_file or output_file:
        summary += "\n\nFile Information:"
        if input_file:
            # Extract just the filename from the path
            input_filename = Path(input_file).name if input_file else input_file
            summary += f'\n- Input file: "{input_filename}"'
        if output_file:
            # Extract just the filename from the path
            output_filename = Path(output_file).name if output_file else output_file
            summary += f'\n- Output file: "{output_filename}"'
    
    return summary

# TODO: Add support for reading/writing other formats (e.g., Excel, JSON) as needed.

def validate_input_schema(input_csv: Path) -> None:
    """
    Validate that the input CSV has at least one column (part numbers).
    """
    try:
        df = pd.read_csv(input_csv, nrows=1)
        if df.shape[1] < 1:
            raise ParseError("Input CSV must have at least one column for part numbers.")
    except Exception as e:  # noqa: BLE001
        logging.error(f"Input schema validation failed: {e}")
        raise ParseError(f"Input schema validation failed: {e}") from e

def validate_output_schema(output_csv: Path, column_names: list[str]) -> None:
    """
    Validate that the output CSV (if exists) has the expected columns.
    """
    if not output_csv.exists():
        return
    try:
        df = pd.read_csv(output_csv, nrows=1)
        missing = [col for col in column_names if col not in df.columns]
        if missing:
            raise ParseError(f"Output CSV missing columns: {missing}")
    except Exception as e:  # noqa: BLE001
        logging.error(f"Output schema validation failed: {e}")
        raise ParseError(f"Output schema validation failed: {e}") from e
