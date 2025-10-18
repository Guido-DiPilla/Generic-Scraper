#!/usr/bin/env python3
"""
Generic Scraper - GUI Main Entry Point
This module provides a standalone GUI interface for the Generic Scraper tool.
"""

import sys
import types
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Make sure GUI modules are loaded
gui_path = project_root / "gui"
if str(gui_path) not in sys.path:
    sys.path.append(str(gui_path))

from client_generator import ClientGeneratorGUI  # noqa: E402

# Try to import client modules
try:
    # Import required client modules for auto-registration
    import clients  # noqa: F401, E402
    import G2S  # noqa: F401, E402
except ImportError:
    print("Warning: Unable to import client modules")


def setup_exception_handler() -> None:
    """Set up a global exception handler to catch and display errors."""
    original_hook = sys.excepthook

    def exception_handler(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: types.TracebackType | None
    ) -> None:
        """Handle uncaught exceptions by showing a dialog."""
        import traceback
        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        try:
            # Try to show error in GUI if possible
            from tkinter import messagebox
            messagebox.showerror("Error", f"An unexpected error occurred:\n\n{error_msg}")
        except Exception:
            # Fall back to console error
            print(f"ERROR: {error_msg}")

        # Call the original exception handler
        original_hook(exc_type, exc_value, exc_traceback)

    sys.excepthook = exception_handler


def main() -> None:
    """Run the GUI application."""
    # Set up exception handling
    setup_exception_handler()

    # Initialize the GUI
    app = ClientGeneratorGUI()

    # Ensure the first tab (Run Scraper) is selected by default
    if hasattr(app, 'notebook'):
        app.notebook.select(0)

    # Log application start
    if hasattr(app, 'log_message'):
        app.log_message("Generic Scraper GUI started", "success")
        app.log_message("Ready to process scraping requests", "info")

    # Start the application
    app.run()


if __name__ == "__main__":
    main()
