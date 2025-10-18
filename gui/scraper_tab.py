"""
Scraper Tab functionality for Generic Scraper GUI.
Contains the main scraping and terminal output functionality.
"""

import asyncio
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Any


class ScraperTab:
    """Tab containing scraper execution and terminal output functionality."""

    def __init__(self, parent: ttk.Notebook, main_app: Any) -> None:
        self.parent = parent
        self.main_app = main_app
        self.frame = ttk.Frame(parent)
        self.terminal_output: scrolledtext.ScrolledText | None = None
        self.progress_var: tk.StringVar | None = None
        self.stop_scraping = False
        self.setup_tab()

    def setup_tab(self) -> None:
        """Set up the scraper tab."""
        # Create main frame
        main_frame = tk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Control buttons frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        # Test scraper button
        test_btn = tk.Button(
            button_frame,
            text="Test Scraper",
            command=self._test_scraper,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        test_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Run full scrape button
        run_btn = tk.Button(
            button_frame,
            text="Run Full Scrape",
            command=self._run_full_scrape,
            bg='#2196F3',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        run_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Stop button
        stop_btn = tk.Button(
            button_frame,
            text="Stop",
            command=self._stop_scraping,
            bg='#f44336',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        stop_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Clear output button
        clear_btn = tk.Button(
            button_frame,
            text="Clear Output",
            command=self._clear_output,
            bg='#FF9800',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        clear_btn.pack(side=tk.LEFT)

        # Progress label
        self.progress_var = tk.StringVar()
        progress_label = tk.Label(main_frame, textvariable=self.progress_var)
        progress_label.pack(pady=(0, 5))

        # Terminal output area
        output_frame = tk.LabelFrame(main_frame, text="Output", font=('Arial', 10, 'bold'))
        output_frame.pack(fill=tk.BOTH, expand=True)

        self.terminal_output = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg='#1e1e1e',
            fg='#ffffff',
            insertbackground='#ffffff'
        )
        self.terminal_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _test_scraper(self) -> None:
        """Test the scraper with a single part number."""
        if not self._validate_config():
            return

        self._write_output("Starting scraper test...\n", "info")

        # Run test in background thread
        thread = threading.Thread(target=self._run_test_async, daemon=True)
        thread.start()

    def _run_full_scrape(self) -> None:
        """Run the full scraping process."""
        if not self._validate_config():
            return

        self._write_output("Starting full scrape...\n", "info")

        # Run scrape in background thread
        thread = threading.Thread(target=self._run_scrape_async, daemon=True)
        thread.start()

    def _stop_scraping(self) -> None:
        """Stop the current scraping operation."""
        self.stop_scraping = True
        self._write_output("Stopping scraper...\n", "warning")

    def _clear_output(self) -> None:
        """Clear the terminal output."""
        if self.terminal_output:
            self.terminal_output.delete(1.0, tk.END)

    def _validate_config(self) -> bool:
        """Validate the current configuration."""
        # Get config from main app
        config = getattr(self.main_app, 'config', {})

        if not config.get('base_url'):
            messagebox.showerror("Error", "Base URL is required")
            return False

        if not config.get('part_number_field'):
            messagebox.showerror("Error", "Part number field is required")
            return False

        return True

    def _run_test_async(self) -> None:
        """Run test scraper in async context."""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Run the async test
            loop.run_until_complete(self._async_test())

        except Exception as e:
            self._write_output(f"Test failed: {str(e)}\n", "error")
        finally:
            loop.close()

    def _run_scrape_async(self) -> None:
        """Run full scraper in async context."""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Run the async scrape
            loop.run_until_complete(self._async_scrape())

        except Exception as e:
            self._write_output(f"Scrape failed: {str(e)}\n", "error")
        finally:
            loop.close()

    async def _async_test(self) -> None:
        """Async test implementation."""
        self._write_output("Running async test...\n", "info")

        # Simulate test operation
        await asyncio.sleep(1)
        test_part = "TEST123"

        self._write_output(f"Testing with part number: {test_part}\n", "info")

        # Here would be the actual scraper test logic
        # For now, just simulate success
        await asyncio.sleep(2)

        if not self.stop_scraping:
            self._write_output("Test completed successfully!\n", "success")
        else:
            self._write_output("Test stopped by user.\n", "warning")

    async def _async_scrape(self) -> None:
        """Async scrape implementation."""
        self._write_output("Running full scrape...\n", "info")

        # Simulate scraping operation
        total_parts = 10  # This would come from input file

        for i in range(total_parts):
            if self.stop_scraping:
                self._write_output("Scrape stopped by user.\n", "warning")
                break

            part_num = f"PART{i+1:03d}"
            self._update_progress(f"Processing {i+1}/{total_parts}: {part_num}")
            self._write_output(f"Scraping part: {part_num}\n", "info")

            # Simulate processing time
            await asyncio.sleep(0.5)

        if not self.stop_scraping:
            self._write_output("Scrape completed successfully!\n", "success")
            self._update_progress("Scrape completed")
        else:
            self._update_progress("Scrape stopped")

    def _write_output(self, text: str, level: str = "info") -> None:
        """Write text to terminal output with color coding."""
        if not self.terminal_output:
            return

        # Color mapping
        colors = {
            "info": "#ffffff",
            "success": "#4CAF50",
            "warning": "#FF9800",
            "error": "#f44336"
        }

        color = colors.get(level, "#ffffff")

        # Configure tag for this color
        self.terminal_output.tag_configure(level, foreground=color)

        # Insert text with color tag
        self.terminal_output.insert(tk.END, text, level)
        self.terminal_output.see(tk.END)

        # Force update
        self.terminal_output.update_idletasks()

    def _update_progress(self, message: str) -> None:
        """Update the progress message."""
        if self.progress_var:
            self.progress_var.set(message)

    def get_data(self) -> dict[str, Any]:
        """Get scraper tab data."""
        return {
            "stop_scraping": self.stop_scraping
        }

    def set_data(self, data: dict[str, Any]) -> None:
        """Set scraper tab data."""
        if "stop_scraping" in data:
            self.stop_scraping = data["stop_scraping"]
