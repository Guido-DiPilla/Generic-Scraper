"""
Unit tests for io_utils.py
"""

import pytest
from pathlib import Path
import pandas as pd
import tempfile
import os
import sys

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from io_utils import read_part_numbers_in_chunks, save_results_atomic, validate_input_schema, validate_output_schema, generate_summary_report
from exceptions import ParseError
def test_read_part_numbers_in_chunks(tmp_path: Path) -> None:
    # Create a sample CSV
    csv_path = tmp_path / "input.csv"
    pd.DataFrame({0: ["A", "B", "C", "D"]}).to_csv(csv_path, index=False, header=False)
    chunks = list(read_part_numbers_in_chunks(csv_path, 2))
    assert chunks == [["A", "B"], ["C", "D"]]

def test_save_results_atomic_and_validate(tmp_path: Path) -> None:
    out_path = tmp_path / "out.csv"
    results = [
        {"Part Number": "A", "Status": "Success"},
        {"Part Number": "B", "Status": "Failed"}
    ]
    columns = ["Part Number", "Status"]
    save_results_atomic(out_path, results, columns)
    df = pd.read_csv(out_path)
    assert set(df["Part Number"]) == {"A", "B"}
    validate_output_schema(out_path, columns)

def test_validate_input_schema(tmp_path: Path) -> None:
    csv_path = tmp_path / "input.csv"
    pd.DataFrame({0: ["A"]}).to_csv(csv_path, index=False, header=False)
    validate_input_schema(csv_path)
    # Now test with no columns
    bad_path = tmp_path / "bad.csv"
    pd.DataFrame().to_csv(bad_path, index=False)
    with pytest.raises(ParseError):
        validate_input_schema(bad_path)

def test_generate_summary_report() -> None:
    results = [
        {"Status": "Success"},
        {"Status": "Failed"},
        {"Status": "Not Found"},
        {"Status": "No Exact Match"},
        {"Status": "Success"}
    ]
    # Test without file names
    summary = generate_summary_report(results, 12.5)
    assert "Total: 5" in summary
    assert "Success: 2" in summary
    assert "Failed: 1" in summary
    assert "Not Found: 1" in summary
    assert "No Exact Match: 1" in summary
    assert "12.50 seconds" in summary
    assert "File Information:" not in summary
    
    # Test with file names
    summary_with_files = generate_summary_report(
        results, 12.5, 
        input_file="input.csv", 
        output_file="output.csv"
    )
    assert "Total: 5" in summary_with_files
    assert "Success: 2" in summary_with_files
    assert "File Information:" in summary_with_files
    assert 'Input file: "input.csv"' in summary_with_files
    assert 'Output file: "output.csv"' in summary_with_files
