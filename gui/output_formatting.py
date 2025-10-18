"""
Output formatting and rich text handling for Generic Scraper GUI.
Handles ANSI codes, Rich markup, and terminal output styling.
"""

import re
import threading
import time
import tkinter as tk
from tkinter import scrolledtext
from typing import Any


class OutputFormatter:
    """Handles formatting and styling of terminal output."""

    def __init__(self, text_widget: scrolledtext.ScrolledText) -> None:
        self.text_widget = text_widget
        self.setup_color_tags()

    def setup_color_tags(self) -> None:
        """Set up color tags for different output types."""
        # ANSI color mappings
        ansi_colors = {
            'black': '#000000',
            'red': '#FF4444',
            'green': '#44FF44',
            'yellow': '#FFFF44',
            'blue': '#4444FF',
            'magenta': '#FF44FF',
            'cyan': '#44FFFF',
            'white': '#FFFFFF',
            'bright_black': '#808080',
            'bright_red': '#FF8888',
            'bright_green': '#88FF88',
            'bright_yellow': '#FFFF88',
            'bright_blue': '#8888FF',
            'bright_magenta': '#FF88FF',
            'bright_cyan': '#88FFFF',
            'bright_white': '#FFFFFF'
        }

        # Configure color tags
        for color_name, color_value in ansi_colors.items():
            self.text_widget.tag_configure(f"fg_{color_name}", foreground=color_value)
            self.text_widget.tag_configure(f"bg_{color_name}", background=color_value)

        # Configure style tags
        self.text_widget.tag_configure("bold", font=('Consolas', 9, 'bold'))
        self.text_widget.tag_configure("italic", font=('Consolas', 9, 'italic'))
        self.text_widget.tag_configure("underline", underline=True)

        # Rich console specific tags
        self.text_widget.tag_configure("info", foreground="#44AAFF")
        self.text_widget.tag_configure("success", foreground="#44FF44")
        self.text_widget.tag_configure("warning", foreground="#FFAA44")
        self.text_widget.tag_configure("error", foreground="#FF4444")
        self.text_widget.tag_configure("progress", foreground="#44FF44")
        self.text_widget.tag_configure(
            "table_header", 
            foreground="#FFFF44", 
            font=('Consolas', 9, 'bold')
        )
        self.text_widget.tag_configure("table_row", foreground="#FFFFFF")

    def log_message(self, message: str, style: str | None = None) -> None:
        """Log a message with optional styling."""
        if not message:
            return

        # Ensure we're on the main thread
        if threading.current_thread() != threading.main_thread():
            self.text_widget.after(0, lambda: self.log_message(message, style))
            return

        try:
            # Detect and handle different content types
            if self.should_display_line(message):
                if style:
                    self.text_widget.insert(tk.END, message, style)
                else:
                    detected_style = self.detect_content_style(message)
                    if detected_style:
                        self.text_widget.insert(tk.END, message, detected_style)
                    else:
                        self.handle_plain_text_with_smart_styling(message)

                # Auto-scroll to bottom
                self.text_widget.see(tk.END)
                self.text_widget.update_idletasks()

        except Exception:
            # Fallback to plain text if styling fails
            self.text_widget.insert(tk.END, message)
            self.text_widget.see(tk.END)

    def parse_ansi_codes(self, text: str) -> list[tuple[str, list[str]]]:
        """Parse ANSI escape codes and return text segments with their styles."""
        # ANSI escape code pattern
        ansi_pattern = re.compile(r'\033\[([0-9;]*)m')

        segments: list[tuple[str, list[str]]] = []
        current_styles: list[str] = []
        last_end = 0

        for match in ansi_pattern.finditer(text):
            # Add text before this escape sequence
            if match.start() > last_end:
                segment_text = text[last_end:match.start()]
                if segment_text:
                    segments.append((segment_text, current_styles.copy()))

            # Parse the escape code
            codes = match.group(1).split(';') if match.group(1) else ['0']
            current_styles = self._process_ansi_codes(codes, current_styles)

            last_end = match.end()

        # Add remaining text
        if last_end < len(text):
            segment_text = text[last_end:]
            if segment_text:
                segments.append((segment_text, current_styles.copy()))

        return segments

    def _process_ansi_codes(self, codes: list[str], current_styles: list[str]) -> list[str]:
        """Process ANSI codes and return updated style list."""
        new_styles = current_styles.copy()

        for code in codes:
            try:
                code_num = int(code) if code else 0

                if code_num == 0:  # Reset
                    new_styles = []
                elif code_num == 1:  # Bold
                    if "bold" not in new_styles:
                        new_styles.append("bold")
                elif code_num == 3:  # Italic
                    if "italic" not in new_styles:
                        new_styles.append("italic")
                elif code_num == 4:  # Underline
                    if "underline" not in new_styles:
                        new_styles.append("underline")
                elif 30 <= code_num <= 37:  # Foreground colors
                    color_names = [
                        'black', 'red', 'green', 'yellow', 
                        'blue', 'magenta', 'cyan', 'white'
                    ]
                    color_name = f"fg_{color_names[code_num - 30]}"
                    # Remove any existing foreground colors
                    new_styles = [s for s in new_styles if not s.startswith('fg_')]
                    new_styles.append(color_name)
                elif 40 <= code_num <= 47:  # Background colors
                    color_names = [
                        'black', 'red', 'green', 'yellow', 
                        'blue', 'magenta', 'cyan', 'white'
                    ]
                    color_name = f"bg_{color_names[code_num - 40]}"
                    # Remove any existing background colors
                    new_styles = [s for s in new_styles if not s.startswith('bg_')]
                    new_styles.append(color_name)
                elif 90 <= code_num <= 97:  # Bright foreground colors
                    color_names = [
                        'black', 'red', 'green', 'yellow', 
                        'blue', 'magenta', 'cyan', 'white'
                    ]
                    color_name = f"fg_bright_{color_names[code_num - 90]}"
                    # Remove any existing foreground colors
                    new_styles = [s for s in new_styles if not s.startswith('fg_')]
                    new_styles.append(color_name)

            except ValueError:
                continue

        return new_styles

    def strip_ansi_codes(self, text: str) -> str:
        """Remove ANSI escape codes from text."""
        ansi_pattern = re.compile(r'\033\[[0-9;]*m')
        return ansi_pattern.sub('', text)

    def should_display_line(self, text: str) -> bool:
        """Determine if a line should be displayed in the output."""
        # Skip empty lines
        if not text.strip():
            return False

        # Skip certain debug or verbose lines
        skip_patterns = [
            r'^\s*DEBUG:',
            r'^\s*TRACE:',
            r'aiohttp\.access',
            r'charset_normalizer\.from_fp'
        ]

        for pattern in skip_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False

        return True

    def parse_rich_markup(self, text: str) -> list[tuple[str, list[str]]]:
        """Parse Rich console markup and return styled segments."""
        # Rich markup patterns
        patterns = {
            r'\[bold\](.*?)\[/bold\]': ('bold',),
            r'\[italic\](.*?)\[/italic\]': ('italic',),
            r'\[underline\](.*?)\[/underline\]': ('underline',),
            r'\[red\](.*?)\[/red\]': ('fg_red',),
            r'\[green\](.*?)\[/green\]': ('fg_green',),
            r'\[blue\](.*?)\[/blue\]': ('fg_blue',),
            r'\[yellow\](.*?)\[/yellow\]': ('fg_yellow',),
            r'\[cyan\](.*?)\[/cyan\]': ('fg_cyan',),
            r'\[magenta\](.*?)\[/magenta\]': ('fg_magenta',),
            r'\[white\](.*?)\[/white\]': ('fg_white',),
        }

        segments: list[tuple[str, list[str]]] = []
        remaining_text = text

        while remaining_text:
            earliest_match = None
            earliest_pos = len(remaining_text)
            earliest_pattern = None

            # Find the earliest markup pattern
            for pattern, styles in patterns.items():
                match = re.search(pattern, remaining_text)
                if match and match.start() < earliest_pos:
                    earliest_match = match
                    earliest_pos = match.start()
                    earliest_pattern = (pattern, styles)

            if earliest_match and earliest_pattern:
                # Add text before the markup
                if earliest_pos > 0:
                    segments.append((remaining_text[:earliest_pos], []))

                # Add the styled text
                styled_text = earliest_match.group(1)
                segments.append((styled_text, list(earliest_pattern[1])))

                # Continue with remaining text
                remaining_text = remaining_text[earliest_match.end():]
            else:
                # No more markup, add remaining text
                if remaining_text:
                    segments.append((remaining_text, []))
                break

        return segments

    def log_rich_output(self, text: str) -> None:
        """Log text that may contain Rich markup or ANSI codes."""
        if not text:
            return

        # First try to parse as Rich markup
        rich_segments = self.parse_rich_markup(text)
        if len(rich_segments) > 1 or (len(rich_segments) == 1 and rich_segments[0][1]):
            # Has Rich markup
            for segment_text, styles in rich_segments:
                if segment_text:
                    if styles:
                        # Combine multiple styles
                        combined_tag = "_".join(styles)
                        self.text_widget.tag_configure(combined_tag, **self._get_tag_config(styles))
                        self.text_widget.insert(tk.END, segment_text, combined_tag)
                    else:
                        self.text_widget.insert(tk.END, segment_text)
        else:
            # Try to parse as ANSI codes
            ansi_segments = self.parse_ansi_codes(text)
            if len(ansi_segments) > 1 or (len(ansi_segments) == 1 and ansi_segments[0][1]):
                # Has ANSI codes
                for segment_text, styles in ansi_segments:
                    if segment_text:
                        if styles:
                            # Use first style or combine them
                            style_tag = styles[0] if len(styles) == 1 else "_".join(styles)
                            self.text_widget.insert(tk.END, segment_text, style_tag)
                        else:
                            self.text_widget.insert(tk.END, segment_text)
            else:
                # Plain text
                self.log_message(text)

        self.text_widget.see(tk.END)
        self.text_widget.update_idletasks()

    def _get_tag_config(self, styles: list[str]) -> dict[str, Any]:
        """Get tag configuration for multiple styles."""
        config = {}

        for style in styles:
            if style.startswith('fg_'):
                # Extract color from existing tag config
                try:
                    existing_config = self.text_widget.tag_cget(style, 'foreground')
                    if existing_config:
                        config['foreground'] = existing_config
                except tk.TclError:
                    pass
            elif style.startswith('bg_'):
                try:
                    existing_config = self.text_widget.tag_cget(style, 'background')
                    if existing_config:
                        config['background'] = existing_config
                except tk.TclError:
                    pass
            elif style == 'bold':
                config['font'] = ('Consolas', 9, 'bold')
            elif style == 'italic':
                config['font'] = ('Consolas', 9, 'italic')
            elif style == 'underline':
                config['underline'] = True

        return config

    def detect_content_style(self, text: str) -> str | None:
        """Detect the style of content based on patterns."""
        text_lower = text.lower().strip()

        # Progress indicators
        indicators = ['processing', 'scraping', 'found', 'completed']
        if any(indicator in text_lower for indicator in indicators):
            return "progress"

        # Error patterns
        if any(error in text_lower for error in ['error', 'failed', 'exception', 'traceback']):
            return "error"

        # Warning patterns
        if any(warning in text_lower for warning in ['warning', 'warn', 'skipping', 'retry']):
            return "warning"

        # Success patterns
        if any(success in text_lower for success in ['success', 'done', 'finished', 'saved']):
            return "success"

        # Info patterns
        if any(info in text_lower for info in ['info', 'starting', 'loading', 'config']):
            return "info"

        # Table headers (lines with | and underscores)
        if '|' in text and ('─' in text or '-' in text):
            return "table_header"

        # Table rows (lines with | but no underscores)
        if '|' in text and '─' not in text and '-' not in text:
            return "table_row"

        return None

    def handle_plain_text_with_smart_styling(self, text: str) -> None:
        """Handle plain text with intelligent styling detection."""
        # Check for URLs
        url_pattern = re.compile(r'https?://[^\s]+')
        urls = list(url_pattern.finditer(text))

        if urls:
            # Handle text with URLs
            last_end = 0
            for url_match in urls:
                # Add text before URL
                if url_match.start() > last_end:
                    before_text = text[last_end:url_match.start()]
                    style = self.detect_content_style(before_text)
                    self.text_widget.insert(tk.END, before_text, style or "")

                # Add URL with special styling
                url_text = url_match.group()
                self.text_widget.tag_configure("url", foreground="#88AAFF", underline=True)
                self.text_widget.insert(tk.END, url_text, "url")

                last_end = url_match.end()

            # Add remaining text
            if last_end < len(text):
                remaining_text = text[last_end:]
                style = self.detect_content_style(remaining_text)
                self.text_widget.insert(tk.END, remaining_text, style or "")
        else:
            # Plain text without URLs
            style = self.detect_content_style(text)
            self.text_widget.insert(tk.END, text, style or "")


class ProgressTracker:
    """Handles progress tracking and display updates."""

    def __init__(self, progress_var: tk.StringVar) -> None:
        self.progress_var = progress_var
        self.current_progress = ""
        self.last_update_time = 0.0

    def update_progress(self, message: str) -> None:
        """Update progress message with rate limiting."""
        current_time = time.time()

        # Rate limit updates to avoid overwhelming the UI
        if current_time - self.last_update_time < 0.1:  # Max 10 updates per second
            return

        self.current_progress = message
        self.progress_var.set(message)
        self.last_update_time = current_time

    def update_progress_from_line(self, line: str) -> None:
        """Extract progress information from a log line."""
        line = line.strip()

        # Progress patterns
        progress_patterns = [
            r'Processing (\d+/\d+)',
            r'Scraping.*?(\d+/\d+)',
            r'Found (\d+) results',
            r'Completed (\d+) of (\d+)',
            r'Progress: (\d+%)',
        ]

        for pattern in progress_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                self.update_progress(f"Progress: {match.group(1)}")
                return

        # Fallback to showing the line itself if it looks like progress
        if any(word in line.lower() for word in ['processing', 'scraping', 'found', 'completed']):
            # Truncate long lines
            display_line = line[:100] + "..." if len(line) > 100 else line
            self.update_progress(display_line)
