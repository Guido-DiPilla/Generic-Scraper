#!/usr/bin/env python3
"""
Generic Scraper - GUI Launcher
This script provides a simple launcher for the Generic Scraper GUI.
"""

import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
import subprocess

# Add project root to path if needed
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Make sure GUI modules are loaded
gui_path = project_root / "gui"
if str(gui_path) not in sys.path:
    sys.path.append(str(gui_path))


def check_requirements():
    """Check if all required modules are installed."""
    try:
        import client_generator  # noqa: F401
        return True
    except ImportError as e:
        messagebox.showerror(
            "Missing Dependencies",
            f"Failed to import required modules: {e}\n\n"
            "Please make sure you've installed all dependencies with:\n"
            "pip install -r requirements.txt"
        )
        return False


def main():
    """Run the GUI application by launching client_generator.py."""
    if not check_requirements():
        return 1

    try:
        # Import required modules for auto-registration
        try:
            import clients  # noqa: F401
            import G2S  # noqa: F401
        except ImportError:
            print("Warning: Unable to import client modules")

        # Import the main client generator GUI
        from client_generator import ClientGeneratorGUI

        # Create and run the application
        app = ClientGeneratorGUI()
        
        # Ensure the first tab (Run Scraper) is selected by default
        if hasattr(app, 'notebook'):
            app.notebook.select(0)
            
        # Start the application
        app.run()
        
        return 0
    except Exception as e:
        messagebox.showerror(
            "Startup Error",
            f"Failed to start the application: {e}"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
