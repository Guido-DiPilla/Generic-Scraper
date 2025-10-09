#!/usr/bin/env python3
"""Simple test for Typer to diagnose issues."""

from enum import Enum
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer()

class OutputFormat(str, Enum):
    csv = "csv"
    json = "json"
    excel = "excel"

@app.command()
def hello(
    name: str = typer.Argument("World"),
    formal: bool = False,
):
    """Say hello to someone."""
    if formal:
        print(f"Good day, {name}.")
    else:
        print(f"Hello, {name}!")

if __name__ == "__main__":
    app()