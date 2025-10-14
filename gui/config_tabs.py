"""
Configuration tabs for the Generic Scraper GUI.
Provides modular tab components for better organization.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Any, Dict, List, Optional
from pathlib import Path

from .tooltip import ToolTip


class BaseTab:
    """Base class for GUI tabs with common functionality."""
    
    def __init__(self, parent: ttk.Notebook, main_app: Any) -> None:
        self.parent = parent
        self.main_app = main_app
        self.frame = ttk.Frame(parent)
        self.setup_tab()
    
    def setup_tab(self) -> None:
        """Override in subclasses to set up tab content."""
        raise NotImplementedError("Subclasses must implement setup_tab")
    
    def add_tooltip(self, widget: tk.Widget, text: str) -> None:
        """Helper method to add tooltips to widgets."""
        ToolTip(widget, text)


class BasicTab(BaseTab):
    """Basic information tab for client configuration."""
    
    def __init__(self, parent: ttk.Notebook, main_app: Any) -> None:
        self.client_id_var: tk.StringVar = tk.StringVar()
        self.client_name_var: tk.StringVar = tk.StringVar() 
        self.description_var: tk.StringVar = tk.StringVar()
        self.validation_label: Optional[ttk.Label] = None
        super().__init__(parent, main_app)
    
    def setup_tab(self) -> None:
        """Set up basic information tab."""
        # Title
        ttk.Label(self.frame, text="Client Basic Information", 
                 font=('Arial', 14, 'bold')).pack(pady=(10, 20))
        
        # Create form fields
        form_frame = ttk.Frame(self.frame)
        form_frame.pack(fill='x', padx=20)
        
        # Client ID
        ttk.Label(form_frame, text="Client ID (unique, lowercase, no spaces):").grid(
            row=0, column=0, sticky='w', pady=5)
        client_id_entry = ttk.Entry(form_frame, textvariable=self.client_id_var, width=40)
        client_id_entry.grid(row=0, column=1, sticky='w', padx=(10, 0), pady=5)
        self.client_id_var.trace('w', self.validate_client_id)
        
        # Client Name
        ttk.Label(form_frame, text="Client Display Name:").grid(
            row=1, column=0, sticky='w', pady=5)
        client_name_entry = ttk.Entry(form_frame, textvariable=self.client_name_var, width=40)
        client_name_entry.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(
            row=2, column=0, sticky='w', pady=5)
        description_entry = ttk.Entry(form_frame, textvariable=self.description_var, width=40)
        description_entry.grid(row=2, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Add tooltips
        self.add_tooltip(client_id_entry, 
            "Unique identifier for this client configuration.\n"
            "Must be lowercase, no spaces, only letters, numbers, and underscores.\n"
            "Example: 'digikey', 'mouser_electronics'")
        self.add_tooltip(client_name_entry,
            "Human-readable name for this client.\n"
            "This appears in the client selection dropdown.\n"
            "Example: 'DigiKey Electronics', 'Mouser Electronics'")
        self.add_tooltip(description_entry,
            "Brief description of what this client does.\n"
            "Helps identify the purpose of this configuration.\n"
            "Example: 'Electronic components supplier'")
        
        # Validation label
        self.validation_label = ttk.Label(form_frame, text="", foreground='red')
        self.validation_label.grid(row=3, column=0, columnspan=2, pady=5)
    
    def validate_client_id(self, *args: Any) -> None:
        """Validate client ID format."""
        import re
        
        if not self.validation_label:
            return
            
        client_id = self.client_id_var.get()
        if not client_id:
            self.validation_label.config(text="")
            return
        
        # Check format
        if not re.match(r'^[a-z0-9_]+$', client_id):
            self.validation_label.config(
                text="⚠ Client ID should contain only lowercase letters, numbers, and underscores")
        elif len(client_id) < 3:
            self.validation_label.config(
                text="⚠ Client ID should be at least 3 characters long")
        else:
            # Check if file already exists
            client_file = Path(f"clients/{client_id}.py")
            if client_file.exists():
                self.validation_label.config(
                    text="⚠ A client with this ID already exists")
            else:
                self.validation_label.config(
                    text="✓ Client ID is valid", foreground='green')


class WebsiteTab(BaseTab):
    """Website configuration tab."""
    
    def __init__(self, parent: ttk.Notebook, main_app: Any) -> None:
        self.base_url_var: tk.StringVar = tk.StringVar()
        self.search_endpoint_var: tk.StringVar = tk.StringVar(value="/search")
        self.search_param_var: tk.StringVar = tk.StringVar(value="q")
        self.product_selector_var: tk.StringVar = tk.StringVar(value="a.product-link")
        self.part_regex_var: tk.StringVar = tk.StringVar(value=r'^[\w\-/\.]{1,64}$')
        self.normalize_parts_var: tk.BooleanVar = tk.BooleanVar(value=True)
        self.exact_match_var: tk.BooleanVar = tk.BooleanVar(value=True)
        super().__init__(parent, main_app)
    
    def setup_tab(self) -> None:
        """Set up website configuration tab."""
        ttk.Label(self.frame, text="Website Configuration", 
                 font=('Arial', 14, 'bold')).pack(pady=(10, 20))
        
        form_frame = ttk.Frame(self.frame)
        form_frame.pack(fill='x', padx=20)
        
        # Base URL
        ttk.Label(form_frame, text="Base URL (e.g., https://example.com):").grid(
            row=0, column=0, sticky='w', pady=5)
        base_url_entry = ttk.Entry(form_frame, textvariable=self.base_url_var, width=50)
        base_url_entry.grid(row=0, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Search Endpoint
        ttk.Label(form_frame, text="Search Endpoint (e.g., /search):").grid(
            row=1, column=0, sticky='w', pady=5)
        search_endpoint_entry = ttk.Entry(form_frame, textvariable=self.search_endpoint_var, width=50)
        search_endpoint_entry.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Search Parameter
        ttk.Label(form_frame, text="Search Parameter Name (e.g., q, search, query):").grid(
            row=2, column=0, sticky='w', pady=5)
        search_param_entry = ttk.Entry(form_frame, textvariable=self.search_param_var, width=50)
        search_param_entry.grid(row=2, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Product Link Selector
        ttk.Label(form_frame, text="Product Link CSS Selector:").grid(
            row=3, column=0, sticky='w', pady=5)
        product_selector_entry = ttk.Entry(form_frame, textvariable=self.product_selector_var, width=50)
        product_selector_entry.grid(row=3, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Part Number Regex
        ttk.Label(form_frame, text="Part Number Regex Pattern:").grid(
            row=4, column=0, sticky='w', pady=5)
        regex_entry = ttk.Entry(form_frame, textvariable=self.part_regex_var, width=50)
        regex_entry.grid(row=4, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Add tooltips
        self.add_tooltip(base_url_entry,
            "The main website URL.\n"
            "Example: 'https://www.digikey.com', 'https://www.mouser.com'\n"
            "Do not include search paths, just the domain.")
        self.add_tooltip(search_endpoint_entry,
            "The search page path on the website.\n"
            "Example: '/products/en/search' for DigiKey, '/c/' for Mouser\n"
            "This gets appended to the base URL.")
        self.add_tooltip(search_param_entry,
            "The URL parameter name used for search queries.\n"
            "Example: 'keywords' for DigiKey, 'q' for many sites\n"
            "Check the website's search URL to find this.")
        self.add_tooltip(product_selector_entry,
            "CSS selector to find product links in search results.\n"
            "Example: 'a[href*=\"/product-detail/\"]' for DigiKey\n"
            "Use browser dev tools to inspect the search results page.")
        self.add_tooltip(regex_entry,
            "Regular expression pattern to validate part numbers.\n"
            "Default matches alphanumeric, dashes, slashes, dots, 1-64 chars.\n"
            "Example: '^[A-Z0-9-]{3,20}$' for uppercase alphanumeric with dashes.")
        
        # Add help label for regex
        help_label = ttk.Label(form_frame, 
            text="(Pattern to validate part numbers - e.g., letters, numbers, dashes, dots, 1-64 chars)", 
            font=('Arial', 8), foreground='gray')
        help_label.grid(row=5, column=1, sticky='w', padx=(10, 0), pady=(0, 5))
        
        # Options frame
        options_frame = ttk.LabelFrame(self.frame, text="Options")
        options_frame.pack(fill='x', padx=20, pady=20)
        
        # Checkboxes
        normalize_checkbox = ttk.Checkbutton(options_frame, 
            text="Normalize part numbers (remove dashes, lowercase)", 
            variable=self.normalize_parts_var)
        normalize_checkbox.pack(anchor='w', padx=10, pady=5)
        
        exact_match_checkbox = ttk.Checkbutton(options_frame, 
            text="Require exact match between search and product", 
            variable=self.exact_match_var)
        exact_match_checkbox.pack(anchor='w', padx=10, pady=5)
        
        # Add tooltips for options
        self.add_tooltip(normalize_checkbox,
            "Convert part numbers to standard format before comparing.\n"
            "Removes dashes/spaces and converts to lowercase.\n"
            "Helps match 'ABC-123' with 'abc123'.")
        self.add_tooltip(exact_match_checkbox,
            "Only accept products where the part number exactly matches the search.\n"
            "Prevents false positives from similar part numbers.\n"
            "Recommended: Keep enabled for accuracy.")


class FieldsTab(BaseTab):
    """Field mappings configuration tab."""
    
    def __init__(self, parent: ttk.Notebook, main_app: Any) -> None:
        self.fields_tree: Optional[ttk.Treeview] = None
        super().__init__(parent, main_app)
    
    def setup_tab(self) -> None:
        """Set up field mappings tab."""
        ttk.Label(self.frame, text="Field Mappings Configuration", 
                 font=('Arial', 14, 'bold')).pack(pady=(10, 20))
        
        # Instructions
        instructions = ttk.Label(self.frame, 
            text="Define what data to extract from product pages:", 
            font=('Arial', 10))
        instructions.pack(pady=(0, 10))
        
        # Field list frame
        list_frame = ttk.Frame(self.frame)
        list_frame.pack(fill='both', expand=True, padx=20)
        
        # Treeview for field mappings
        columns = ('Field Name', 'CSS Selector', 'Transform')
        self.fields_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.fields_tree.heading(col, text=col)
            self.fields_tree.column(col, width=200)
        
        self.fields_tree.pack(side='left', fill='both', expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.fields_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.fields_tree.configure(yscrollcommand=scrollbar.set)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.frame)
        buttons_frame.pack(fill='x', padx=20, pady=10)
        
        add_field_btn = ttk.Button(buttons_frame, text="Add Field", command=self.add_field)
        add_field_btn.pack(side='left', padx=5)
        edit_field_btn = ttk.Button(buttons_frame, text="Edit Field", command=self.edit_field)
        edit_field_btn.pack(side='left', padx=5)
        remove_field_btn = ttk.Button(buttons_frame, text="Remove Field", command=self.remove_field)
        remove_field_btn.pack(side='left', padx=5)
        common_fields_btn = ttk.Button(buttons_frame, text="Add Common Fields", command=self.add_common_fields)
        common_fields_btn.pack(side='left', padx=5)
        
        # Add tooltips
        self.add_tooltip(add_field_btn,
            "Add a new field to extract from product pages.\n"
            "Define CSS selectors to capture data like price, availability, etc.")
        self.add_tooltip(edit_field_btn,
            "Modify the selected field mapping.\n"
            "Select a field in the list above first.")
        self.add_tooltip(remove_field_btn,
            "Delete the selected field mapping.\n"
            "Select a field in the list above first.")
        self.add_tooltip(common_fields_btn,
            "Add typical fields like Brand, Category, Model, Weight, Dimensions.\n"
            "Useful starting point for most e-commerce sites.")
        
        # Add some default fields
        self.add_default_fields()
    
    def add_default_fields(self) -> None:
        """Add default field mappings."""
        if not self.fields_tree:
            return
            
        default_fields = [
            ("Price", ".price, .product-price", "extract_numeric"),
            ("In Stock", ".stock-status, .availability", "clean_text"),
            ("Description", ".description, .product-description", "clean_text"),
        ]
        
        for field_name, selector, transform in default_fields:
            self.fields_tree.insert('', 'end', values=(field_name, selector, transform))
    
    def add_field(self) -> None:
        """Add a new field mapping."""
        from .field_dialog import FieldMappingDialog
        
        if not self.fields_tree:
            return
            
        dialog = FieldMappingDialog(self.main_app.root)
        if dialog.result:
            field_name, css_selector, transform = dialog.result
            self.fields_tree.insert('', 'end', values=(field_name, css_selector, transform))
    
    def edit_field(self) -> None:
        """Edit selected field mapping."""
        from .field_dialog import FieldMappingDialog
        
        if not self.fields_tree:
            return
            
        selection = self.fields_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a field to edit.")
            return
        
        item = selection[0]
        current_values = self.fields_tree.item(item, 'values')
        
        # Ensure we have the right type
        if isinstance(current_values, tuple) and len(current_values) >= 3:
            dialog_values = (str(current_values[0]), str(current_values[1]), str(current_values[2]))
            dialog = FieldMappingDialog(self.main_app.root, dialog_values)
        else:
            dialog = FieldMappingDialog(self.main_app.root, None)
        if dialog.result:
            field_name, css_selector, transform = dialog.result
            self.fields_tree.item(item, values=(field_name, css_selector, transform))
    
    def remove_field(self) -> None:
        """Remove selected field mapping."""
        if not self.fields_tree:
            return
            
        selection = self.fields_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a field to remove.")
            return
        
        for item in selection:
            self.fields_tree.delete(item)
    
    def add_common_fields(self) -> None:
        """Add common field mappings."""
        if not self.fields_tree:
            return
            
        common_fields = [
            ("Brand", ".brand, .manufacturer", "clean_text"),
            ("Category", ".category, .breadcrumb li:last-child", "clean_text"),
            ("Model", ".model-number, .part-number", "clean_text"),
            ("Weight", ".weight, .shipping-weight", "extract_numeric"),
            ("Dimensions", ".dimensions, .size", "clean_text"),
        ]
        
        for field_name, selector, transform in common_fields:
            self.fields_tree.insert('', 'end', values=(field_name, selector, transform))


class AdvancedTab(BaseTab):
    """Advanced configuration tab."""
    
    def setup_tab(self) -> None:
        """Set up advanced configuration tab."""
        ttk.Label(self.frame, text="Advanced Configuration", 
                 font=('Arial', 14, 'bold')).pack(pady=(10, 20))
        
        # Placeholder for advanced options
        ttk.Label(self.frame, text="Advanced configuration options will be added here.",
                 font=('Arial', 10)).pack(pady=20)


class PreviewTab(BaseTab):
    """Preview and generation tab."""
    
    def setup_tab(self) -> None:
        """Set up preview and generation tab."""
        ttk.Label(self.frame, text="Preview & Generate Client", 
                 font=('Arial', 14, 'bold')).pack(pady=(10, 20))
        
        # Placeholder for preview functionality
        ttk.Label(self.frame, text="Code preview and generation will be added here.",
                 font=('Arial', 10)).pack(pady=20)