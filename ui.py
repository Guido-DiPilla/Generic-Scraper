"""
Unified user interface for the G2S scraper.
Supports both CLI and GUI file selection, and uses rich.progress for beautiful
progress bars.

Security:
- No secrets or credentials are handled in the UI layer.

Extensibility:
- To add new UI modes (e.g., web, API), add new functions here.
- TODO: Add support for additional progress bar styles or UI themes.

Maintainability:
- All UI functions should be type-annotated and have clear error handling.
"""

from pathlib import Path
from typing import Literal

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

console = Console()

def select_file(dialog_type: Literal["open", "save"] = "open") -> Path:
    """
    Open a file dialog for the user to select a file (input or output).
    Falls back to CLI input if tkinter is not available.
    """
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        if dialog_type == "open":
            file_path = filedialog.askopenfilename(
                title="Select input CSV file",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            )
        else:
            file_path = filedialog.asksaveasfilename(
                title="Select output CSV file",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            )
    except ImportError:
        file_path = input(
            f"Enter {'input' if dialog_type == 'open' else 'output'} CSV file path: "
        )
    if not file_path:
        console.print("[red]No file selected. Exiting.[/red]")
        raise SystemExit(1)
    return Path(file_path)

def get_progress_bars(total_items: int, chunk_size: int) -> tuple[Progress, int, int]:
    """
    Returns a rich Progress context manager for overall and chunk progress bars.
    """
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=True,
    )
    overall_task = progress.add_task("Overall Progress", total=total_items)
    chunk_task = progress.add_task("Chunk Progress", total=chunk_size)
    return progress, overall_task, chunk_task
