"""
Field Mapping Dialog for configuring data extraction fields.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Tuple, Union


class FieldMappingDialog:
    """Dialog for creating/editing field mapping configurations."""
    
    def __init__(self, parent: tk.Tk, initial_values: Optional[Tuple[str, str, str]] = None) -> None:
        self.result: Optional[Tuple[str, str, str]] = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Field Mapping")
        self.dialog.geometry("500x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Variables
        self.field_name_var = tk.StringVar(value=initial_values[0] if initial_values else "")
        self.css_selector_var = tk.StringVar(value=initial_values[1] if initial_values else "")
        self.transform_var = tk.StringVar(value=initial_values[2] if initial_values else "clean_text")
        
        self.setup_dialog()
    
    def setup_dialog(self) -> None:
        """Set up the dialog interface."""
        # Main frame
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Field name
        ttk.Label(main_frame, text="Field Name:").grid(row=0, column=0, sticky='w', pady=5)
        ttk.Entry(main_frame, textvariable=self.field_name_var, width=40).grid(row=0, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # CSS Selector
        ttk.Label(main_frame, text="CSS Selector:").grid(row=1, column=0, sticky='w', pady=5)
        ttk.Entry(main_frame, textvariable=self.css_selector_var, width=40).grid(row=1, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Transform function
        ttk.Label(main_frame, text="Transform Function:").grid(row=2, column=0, sticky='w', pady=5)
        transform_combo = ttk.Combobox(main_frame, textvariable=self.transform_var, width=37)
        transform_combo['values'] = ('none', 'clean_text', 'extract_numeric', 'normalize_part')
        transform_combo.grid(row=2, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Help text
        help_text = tk.Text(main_frame, height=8, width=60, wrap='word')
        help_text.grid(row=3, column=0, columnspan=2, pady=10)
        
        help_content = """CSS Selector Examples:
• .price - Element with class 'price'
• #product-price - Element with ID 'product-price' 
• .price, .product-price - Multiple selectors (first match)
• .product-info .price - Nested elements
• [data-price] - Element with data-price attribute

Transform Functions:
• none - No transformation
• clean_text - Remove extra whitespace
• extract_numeric - Extract numbers from text
• normalize_part - Normalize part numbers (lowercase, no dashes)"""
        
        help_text.insert(1.0, help_content)
        help_text.config(state='disabled')
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side='left', padx=5)
    
    def ok_clicked(self) -> None:
        """Handle OK button click."""
        field_name = self.field_name_var.get().strip()
        css_selector = self.css_selector_var.get().strip()
        transform = self.transform_var.get()
        
        if not field_name or not css_selector:
            messagebox.showerror("Error", "Field name and CSS selector are required.")
            return
        
        self.result = (field_name, css_selector, transform)
        self.dialog.destroy()
    
    def cancel_clicked(self) -> None:
        """Handle Cancel button click."""
        self.dialog.destroy()