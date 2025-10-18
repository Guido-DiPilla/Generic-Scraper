"""
ToolTip component for GUI elements.
Provides hover tooltips for better user experience.
"""

import tkinter as tk
from typing import Any


class ToolTip:
    """
    Create a tooltip for a given widget with proper type safety.
    """

    def __init__(self, widget: tk.Widget, text: str = 'widget info') -> None:
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.tooltip_window: tk.Toplevel | None = None

    def enter(self, event: Any | None = None) -> None:
        """Show tooltip on mouse enter."""
        try:
            # Try to get cursor position (works for text widgets)
            if hasattr(self.widget, 'bbox'):
                bbox = self.widget.bbox("insert")  # type: ignore
                if bbox:
                    x, y, cx, cy = bbox
                else:
                    x, y = 0, 0
            else:
                x, y = 0, 0
        except Exception:
            # For other widgets, use widget position
            x, y = 0, 0

        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        # Create tooltip window
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(tw, text=self.text, justify='left',
                        background="#ffffe0", foreground="#000000",
                        relief='solid', borderwidth=1,
                        font=("Arial", 8), wraplength=300)
        label.pack(ipadx=5, ipady=3)

    def leave(self, event: Any | None = None) -> None:
        """Hide tooltip on mouse leave."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None
