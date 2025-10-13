"""
GUI Client Generator for Generic Scraper
Creates new client configurations with a user-friendly interface.

This tool provides a GUI form to collect client information and automatically
generates the client configuration file with proper templates.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from pathlib import Path
import re
from typing import Dict, List, Optional
import json


class ClientGeneratorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Generic Scraper - Main Application")
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Set window to reasonable width but nearly full height
        window_width = min(1200, int(screen_width * 0.7))  # 70% of screen width, max 1200px
        window_height = int(screen_height * 0.9)           # 90% of screen height
        
        # Calculate position to center horizontally
        x_position = (screen_width - window_width) // 2
        y_position = 20  # Small margin from top
        
        # Set geometry: width x height + x_offset + y_offset
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.root.minsize(800, 600)     # Set minimum size
        
        # Client configuration data
        self.client_data = {}
        self.field_mappings = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the GUI interface."""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        self.notebook = notebook  # Store reference for later use
        
        # Tab 1: Run Scraper (NEW - Main functionality)
        scraper_frame = ttk.Frame(notebook)
        notebook.add(scraper_frame, text="Run Scraper")
        self.setup_scraper_tab(scraper_frame)
        
        # Tab 2: Create Client - Basic Information
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="Create Client")
        self.setup_basic_tab(basic_frame)
        
        # Tab 3: Website Configuration
        website_frame = ttk.Frame(notebook)
        notebook.add(website_frame, text="Website Config")
        self.setup_website_tab(website_frame)
        
        # Tab 4: Field Mappings
        fields_frame = ttk.Frame(notebook)
        notebook.add(fields_frame, text="Field Mappings")
        self.setup_fields_tab(fields_frame)
        
        # Tab 5: Advanced Settings
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="Advanced")
        self.setup_advanced_tab(advanced_frame)
        
        # Tab 6: Preview & Generate
        preview_frame = ttk.Frame(notebook)
        notebook.add(preview_frame, text="Preview & Generate")
        self.setup_preview_tab(preview_frame)
        
        # Ensure the first tab (Run Scraper) is selected by default
        notebook.select(0)
    
    def setup_scraper_tab(self, parent):
        """Set up the main scraper execution tab."""
        # Title Section
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill='x', padx=20, pady=(15, 10))
        
        # Main title
        ttk.Label(title_frame, text="🚀 Generic Multi-Client Web Scraper", 
                 font=('Arial', 18, 'bold')).pack(side='left')
        
        # Status indicator with better styling
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(title_frame, textvariable=self.status_var, 
                                font=('Arial', 11, 'bold'), foreground='#007700')
        status_label.pack(side='right')
        
        # Subtitle
        subtitle_frame = ttk.Frame(parent)
        subtitle_frame.pack(fill='x', padx=20, pady=(0, 15))
        ttk.Label(subtitle_frame, text="Select input file, output location, and client to begin scraping operations", 
                 font=('Arial', 10), foreground='#666666').pack()
        
        # Separator
        separator = ttk.Separator(parent, orient='horizontal')
        separator.pack(fill='x', padx=20, pady=(0, 20))
        
        # Client Selection Section
        client_frame = ttk.LabelFrame(parent, text="Client Selection")
        client_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(client_frame, text="Select scraping client:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        
        # Get available clients by scanning directories and importing them
        client_names = []
        try:
            from client_config import registry
            
            # Import G2S client to trigger registration
            try:
                import G2S.g2s_client  # Just importing triggers auto-registration
            except ImportError:
                pass
            
            # Scan clients directory for additional clients
            from pathlib import Path
            clients_dir = Path(__file__).parent / "clients"
            if clients_dir.exists():
                for client_file in clients_dir.glob("*.py"):
                    if client_file.name.startswith("__"):
                        continue
                    try:
                        # Import client module to trigger any auto-registration
                        module_name = f"clients.{client_file.stem}"
                        __import__(module_name)
                    except ImportError:
                        continue
            
            # Get all registered clients
            available_clients = registry.get_client_ids()
            for client_id in available_clients:
                client = registry.get_client(client_id)
                if client:
                    client_names.append(f"{client.client_name} ({client_id})")
            
            # If no clients found in registry, add G2S manually as fallback
            if not client_names:
                client_names = ['G2S Equipment (g2s)']
                
        except Exception as e:
            # Fallback list if everything fails
            client_names = ['G2S Equipment (g2s)', 'Demo Client (demo)']
            print(f"Warning: Could not load client registry: {e}")
        
        self.selected_client_var = tk.StringVar()
        client_dropdown = ttk.Combobox(client_frame, textvariable=self.selected_client_var, 
                                      values=client_names, state='readonly', width=50)
        client_dropdown.grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        # Bind client selection change to populate configuration
        client_dropdown.bind('<<ComboboxSelected>>', self.on_client_selected)
        
        # Set G2S as default if available and load its configuration
        if client_names:
            for i, name in enumerate(client_names):
                if 'g2s' in name.lower():
                    client_dropdown.current(i)
                    # Load the default client configuration
                    self.root.after(100, self.on_client_selected)  # Delay to ensure GUI is ready
                    break
            else:
                client_dropdown.current(0)
                # Load the first client configuration
                self.root.after(100, self.on_client_selected)
        
        # File Selection Section
        files_frame = ttk.LabelFrame(parent, text="File Selection")
        files_frame.pack(fill='x', padx=20, pady=10)
        
        # Input file selection
        ttk.Label(files_frame, text="Input CSV file:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.input_file_var = tk.StringVar()
        input_entry = ttk.Entry(files_frame, textvariable=self.input_file_var, width=50)
        input_entry.grid(row=0, column=1, sticky='w', padx=5, pady=5)
        ttk.Button(files_frame, text="Browse...", 
                  command=self.browse_input_file).grid(row=0, column=2, padx=5, pady=5)
        
        # Output file selection
        ttk.Label(files_frame, text="Output CSV file:").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        self.output_file_var = tk.StringVar()
        output_entry = ttk.Entry(files_frame, textvariable=self.output_file_var, width=50)
        output_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        ttk.Button(files_frame, text="Browse...", 
                  command=self.browse_output_file).grid(row=1, column=2, padx=5, pady=5)
        
        # Options Section
        options_frame = ttk.LabelFrame(parent, text="Scraping Options")
        options_frame.pack(fill='x', padx=20, pady=10)
        
        # Concurrency
        ttk.Label(options_frame, text="Concurrency limit:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.concurrency_var = tk.StringVar(value="3")
        ttk.Entry(options_frame, textvariable=self.concurrency_var, width=10).grid(row=0, column=1, sticky='w', padx=5)
        
        # Chunk size
        ttk.Label(options_frame, text="Chunk size:").grid(row=0, column=2, sticky='w', pady=5, padx=(20, 5))
        self.chunk_size_var = tk.StringVar(value="500")
        ttk.Entry(options_frame, textvariable=self.chunk_size_var, width=10).grid(row=0, column=3, sticky='w', padx=5)
        
        # Email notification
        self.email_notify_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Send email notification when complete", 
                       variable=self.email_notify_var).grid(row=1, column=0, columnspan=4, sticky='w', padx=5, pady=5)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(parent, text="Progress")
        progress_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.pack(pady=10)
        
        # Progress text
        self.progress_text_var = tk.StringVar(value="Ready to start scraping...")
        ttk.Label(progress_frame, textvariable=self.progress_text_var).pack(pady=5)
        
        # Terminal-like log area with frame styling
        log_frame = tk.Frame(progress_frame, bg='#000000', relief='sunken', bd=2)
        log_frame.pack(fill='both', expand=True, pady=10)
        
        # Create terminal-like text widget with black background
        self.log_text = tk.Text(
            log_frame, 
            height=15,  # Increased height for better visibility
            wrap='word',
            bg='#000000',  # Black background
            fg='#00FF00',  # Green text (classic terminal)
            insertbackground='#00FF00',  # Green cursor
            selectbackground='#333333',  # Dark selection
            selectforeground='#FFFFFF',  # White selected text
            font=('Consolas', 9) if tk.TkVersion >= 8.5 else ('Courier', 9),
            relief='flat',
            bd=0,
            padx=10,
            pady=5
        )
        
        log_scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        # Configure color tags for Rich output
        self.setup_color_tags()
        
        # Add initial terminal welcome message
        self.add_terminal_welcome()
        
        self.log_text.pack(side='left', fill='both', expand=True)
        log_scrollbar.pack(side='right', fill='y')
        
        # Control Buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', padx=20, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start Scraping", 
                                      command=self.start_scraping, style='Accent.TButton')
        self.start_button.pack(side='left', padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop", 
                                     command=self.stop_scraping, state='disabled')
        self.stop_button.pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="Clear Log", 
                  command=self.clear_log).pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="Open Results Folder", 
                  command=self.open_results_folder).pack(side='right', padx=5)
    
    def setup_basic_tab(self, parent):
        """Set up basic information tab."""
        # Title
        ttk.Label(parent, text="Client Basic Information", font=('Arial', 14, 'bold')).pack(pady=(10, 20))
        
        # Create form fields
        form_frame = ttk.Frame(parent)
        form_frame.pack(fill='x', padx=20)
        
        # Client ID
        ttk.Label(form_frame, text="Client ID (unique, lowercase, no spaces):").grid(row=0, column=0, sticky='w', pady=5)
        self.client_id_var = tk.StringVar()
        self.client_id_entry = ttk.Entry(form_frame, textvariable=self.client_id_var, width=40)
        self.client_id_entry.grid(row=0, column=1, sticky='w', padx=(10, 0), pady=5)
        self.client_id_var.trace('w', self.validate_client_id)
        
        # Client Name
        ttk.Label(form_frame, text="Client Display Name:").grid(row=1, column=0, sticky='w', pady=5)
        self.client_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.client_name_var, width=40).grid(row=1, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=2, column=0, sticky='w', pady=5)
        self.description_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.description_var, width=40).grid(row=2, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Validation label
        self.validation_label = ttk.Label(form_frame, text="", foreground='red')
        self.validation_label.grid(row=3, column=0, columnspan=2, pady=5)
    
    def setup_website_tab(self, parent):
        """Set up website configuration tab."""
        ttk.Label(parent, text="Website Configuration", font=('Arial', 14, 'bold')).pack(pady=(10, 20))
        
        form_frame = ttk.Frame(parent)
        form_frame.pack(fill='x', padx=20)
        
        # Base URL
        ttk.Label(form_frame, text="Base URL (e.g., https://example.com):").grid(row=0, column=0, sticky='w', pady=5)
        self.base_url_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.base_url_var, width=50).grid(row=0, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Search Endpoint
        ttk.Label(form_frame, text="Search Endpoint (e.g., /search):").grid(row=1, column=0, sticky='w', pady=5)
        self.search_endpoint_var = tk.StringVar(value="/search")
        ttk.Entry(form_frame, textvariable=self.search_endpoint_var, width=50).grid(row=1, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Search Parameter
        ttk.Label(form_frame, text="Search Parameter Name (e.g., q, search, query):").grid(row=2, column=0, sticky='w', pady=5)
        self.search_param_var = tk.StringVar(value="q")
        ttk.Entry(form_frame, textvariable=self.search_param_var, width=50).grid(row=2, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Product Link Selector
        ttk.Label(form_frame, text="Product Link CSS Selector:").grid(row=3, column=0, sticky='w', pady=5)
        self.product_selector_var = tk.StringVar(value="a.product-link")
        ttk.Entry(form_frame, textvariable=self.product_selector_var, width=50).grid(row=3, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Options frame
        options_frame = ttk.LabelFrame(parent, text="Options")
        options_frame.pack(fill='x', padx=20, pady=20)
        
        # Checkboxes
        self.normalize_parts_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Normalize part numbers (remove dashes, lowercase)", 
                       variable=self.normalize_parts_var).pack(anchor='w', padx=10, pady=5)
        
        self.exact_match_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Require exact match between search and product", 
                       variable=self.exact_match_var).pack(anchor='w', padx=10, pady=5)
    
    def setup_fields_tab(self, parent):
        """Set up field mappings tab."""
        ttk.Label(parent, text="Field Mappings Configuration", font=('Arial', 14, 'bold')).pack(pady=(10, 20))
        
        # Instructions
        instructions = ttk.Label(parent, text="Define what data to extract from product pages:", 
                                font=('Arial', 10))
        instructions.pack(pady=(0, 10))
        
        # Field list frame
        list_frame = ttk.Frame(parent)
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
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(buttons_frame, text="Add Field", command=self.add_field).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Edit Field", command=self.edit_field).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Remove Field", command=self.remove_field).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Add Common Fields", command=self.add_common_fields).pack(side='left', padx=5)
        
        # Add some default fields
        self.add_default_fields()
    
    def setup_advanced_tab(self, parent):
        """Set up advanced configuration tab."""
        ttk.Label(parent, text="Advanced Configuration", font=('Arial', 14, 'bold')).pack(pady=(10, 20))
        
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Rate Limiting Section
        rate_frame = ttk.LabelFrame(scrollable_frame, text="Rate Limiting & Performance")
        rate_frame.pack(fill='x', padx=20, pady=10)
        
        # Rate limit
        ttk.Label(rate_frame, text="Requests per second:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.rate_limit_var = tk.StringVar(value="1.0")
        ttk.Entry(rate_frame, textvariable=self.rate_limit_var, width=10).grid(row=0, column=1, sticky='w', padx=5)
        
        # Timeout settings
        ttk.Label(rate_frame, text="Request timeout (seconds):").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        self.request_timeout_var = tk.StringVar(value="30")
        ttk.Entry(rate_frame, textvariable=self.request_timeout_var, width=10).grid(row=1, column=1, sticky='w', padx=5)
        
        ttk.Label(rate_frame, text="Total timeout (seconds):").grid(row=2, column=0, sticky='w', pady=5, padx=5)
        self.total_timeout_var = tk.StringVar(value="300")
        ttk.Entry(rate_frame, textvariable=self.total_timeout_var, width=10).grid(row=2, column=1, sticky='w', padx=5)
        
        # Retry settings
        ttk.Label(rate_frame, text="Max retries:").grid(row=3, column=0, sticky='w', pady=5, padx=5)
        self.max_retries_var = tk.StringVar(value="3")
        ttk.Entry(rate_frame, textvariable=self.max_retries_var, width=10).grid(row=3, column=1, sticky='w', padx=5)
        
        # Proxy Configuration Section
        proxy_frame = ttk.LabelFrame(scrollable_frame, text="Proxy Configuration")
        proxy_frame.pack(fill='x', padx=20, pady=10)
        
        # Add instruction label
        instruction_label = ttk.Label(proxy_frame, text="Default proxy settings are pre-filled but can be edited for different clients:", 
                                    font=('Arial', 9), foreground='gray')
        instruction_label.pack(anchor='w', padx=5, pady=(5, 0))
        
        # Default to proxy enabled with your credentials pre-filled
        self.use_proxy_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(proxy_frame, text="Use proxy", variable=self.use_proxy_var,
                       command=self.toggle_proxy_fields).pack(anchor='w', padx=5, pady=5)
        
        # Proxy fields frame
        self.proxy_fields_frame = ttk.Frame(proxy_frame)
        self.proxy_fields_frame.pack(fill='x', padx=20, pady=5)
        
        ttk.Label(self.proxy_fields_frame, text="Proxy URL:").grid(row=0, column=0, sticky='w', pady=5)
        self.proxy_url_var = tk.StringVar(value="rp.proxyscrape.com:6060")
        ttk.Entry(self.proxy_fields_frame, textvariable=self.proxy_url_var, width=40).grid(row=0, column=1, sticky='w', padx=5)
        
        ttk.Label(self.proxy_fields_frame, text="Username:").grid(row=1, column=0, sticky='w', pady=5)
        self.proxy_username_var = tk.StringVar(value="ukxv6pnb5wervp3")
        ttk.Entry(self.proxy_fields_frame, textvariable=self.proxy_username_var, width=40).grid(row=1, column=1, sticky='w', padx=5)
        
        ttk.Label(self.proxy_fields_frame, text="Password:").grid(row=2, column=0, sticky='w', pady=5)
        self.proxy_password_var = tk.StringVar(value="eww7ejd4luzk3vn")
        ttk.Entry(self.proxy_fields_frame, textvariable=self.proxy_password_var, width=40, show='*').grid(row=2, column=1, sticky='w', padx=5)
        
        # Headers Section
        headers_frame = ttk.LabelFrame(scrollable_frame, text="Custom Headers")
        headers_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(headers_frame, text="User Agent:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.user_agent_var = tk.StringVar(value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        ttk.Entry(headers_frame, textvariable=self.user_agent_var, width=60).grid(row=0, column=1, sticky='w', padx=5)
        
        # Additional headers
        ttk.Label(headers_frame, text="Additional Headers (JSON format):").grid(row=1, column=0, sticky='nw', pady=5, padx=5)
        self.custom_headers_text = tk.Text(headers_frame, height=4, width=50)
        self.custom_headers_text.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        self.custom_headers_text.insert('1.0', '{\n  "Accept": "text/html,application/xhtml+xml",\n  "Accept-Language": "en-US,en;q=0.9"\n}')
        
        # Validation & Processing Section
        validation_frame = ttk.LabelFrame(scrollable_frame, text="Validation & Processing")
        validation_frame.pack(fill='x', padx=20, pady=10)
        
        self.strict_validation_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(validation_frame, text="Strict field validation", 
                       variable=self.strict_validation_var).pack(anchor='w', padx=5, pady=5)
        
        self.save_html_var = tk.BooleanVar()
        ttk.Checkbutton(validation_frame, text="Save HTML responses for debugging", 
                       variable=self.save_html_var).pack(anchor='w', padx=5, pady=5)
        
        self.log_requests_var = tk.BooleanVar()
        ttk.Checkbutton(validation_frame, text="Log HTTP requests/responses", 
                       variable=self.log_requests_var).pack(anchor='w', padx=5, pady=5)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0))
        scrollbar.pack(side="right", fill="y", padx=(0, 20))
        
        # Initially disable proxy fields
        self.toggle_proxy_fields()
    
    def toggle_proxy_fields(self):
        """Enable/disable proxy fields based on checkbox."""
        state = 'normal' if self.use_proxy_var.get() else 'disabled'
        for widget in self.proxy_fields_frame.winfo_children():
            if isinstance(widget, ttk.Entry):
                widget.configure(state=state)
    
    def setup_preview_tab(self, parent):
        """Set up preview and generation tab."""
        ttk.Label(parent, text="Preview & Generate Client", font=('Arial', 14, 'bold')).pack(pady=(10, 20))
        
        # Preview text area
        preview_frame = ttk.LabelFrame(parent, text="Generated Code Preview")
        preview_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        self.preview_text = tk.Text(preview_frame, wrap='none', font=('Courier', 10))
        preview_scrollbar_v = ttk.Scrollbar(preview_frame, orient='vertical', command=self.preview_text.yview)
        preview_scrollbar_h = ttk.Scrollbar(preview_frame, orient='horizontal', command=self.preview_text.xview)
        
        self.preview_text.configure(yscrollcommand=preview_scrollbar_v.set, xscrollcommand=preview_scrollbar_h.set)
        
        self.preview_text.pack(side='left', fill='both', expand=True)
        preview_scrollbar_v.pack(side='right', fill='y')
        preview_scrollbar_h.pack(side='bottom', fill='x')
        
        # Buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(button_frame, text="Update Preview", command=self.update_preview).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Generate Client File", command=self.generate_client).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Save Template", command=self.save_template).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Load Template", command=self.load_template).pack(side='left', padx=5)
    
    def validate_client_id(self, *args):
        """Validate client ID format."""
        client_id = self.client_id_var.get()
        if not client_id:
            self.validation_label.config(text="")
            return
        
        # Check format
        if not re.match(r'^[a-z0-9_]+$', client_id):
            self.validation_label.config(text="⚠ Client ID should contain only lowercase letters, numbers, and underscores")
        elif len(client_id) < 3:
            self.validation_label.config(text="⚠ Client ID should be at least 3 characters long")
        else:
            # Check if file already exists
            client_file = Path(f"clients/{client_id}.py")
            if client_file.exists():
                self.validation_label.config(text="⚠ A client with this ID already exists")
            else:
                self.validation_label.config(text="✓ Client ID is valid", foreground='green')
    
    def add_default_fields(self):
        """Add default field mappings."""
        default_fields = [
            ("Price", ".price, .product-price", "extract_numeric"),
            ("In Stock", ".stock-status, .availability", "clean_text"),
            ("Description", ".description, .product-description", "clean_text"),
        ]
        
        for field_name, selector, transform in default_fields:
            self.fields_tree.insert('', 'end', values=(field_name, selector, transform))
    
    def add_field(self):
        """Add a new field mapping."""
        dialog = FieldMappingDialog(self.root)
        if dialog.result:
            field_name, css_selector, transform = dialog.result
            self.fields_tree.insert('', 'end', values=(field_name, css_selector, transform))
    
    def edit_field(self):
        """Edit selected field mapping."""
        selection = self.fields_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a field to edit.")
            return
        
        item = selection[0]
        current_values = self.fields_tree.item(item, 'values')
        
        dialog = FieldMappingDialog(self.root, current_values)
        if dialog.result:
            field_name, css_selector, transform = dialog.result
            self.fields_tree.item(item, values=(field_name, css_selector, transform))
    
    def remove_field(self):
        """Remove selected field mapping."""
        selection = self.fields_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a field to remove.")
            return
        
        for item in selection:
            self.fields_tree.delete(item)
    
    def add_common_fields(self):
        """Add common field mappings."""
        common_fields = [
            ("Brand", ".brand, .manufacturer", "clean_text"),
            ("Category", ".category, .breadcrumb li:last-child", "clean_text"),
            ("Model", ".model-number, .part-number", "clean_text"),
            ("Weight", ".weight, .shipping-weight", "extract_numeric"),
            ("Dimensions", ".dimensions, .size", "clean_text"),
        ]
        
        for field_name, selector, transform in common_fields:
            self.fields_tree.insert('', 'end', values=(field_name, selector, transform))
    
    def update_preview(self):
        """Update the code preview."""
        try:
            code = self.generate_client_code()
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, code)
        except Exception as e:
            messagebox.showerror("Preview Error", f"Error generating preview: {str(e)}")
    
    def generate_client_code(self) -> str:
        """Generate the client configuration code."""
        client_id = self.client_id_var.get()
        client_name = self.client_name_var.get()
        description = self.description_var.get()
        base_url = self.base_url_var.get()
        search_endpoint = self.search_endpoint_var.get()
        search_param = self.search_param_var.get()
        product_selector = self.product_selector_var.get()
        
        # Validate required fields
        if not all([client_id, client_name, base_url]):
            raise ValueError("Client ID, Client Name, and Base URL are required")
        
        # Get field mappings
        field_mappings_code = []
        output_columns = ["Part Number", "Status Code", "Exists"]
        
        for item in self.fields_tree.get_children():
            field_name, css_selector, transform = self.fields_tree.item(item, 'values')
            
            transform_func = f"TRANSFORM_FUNCTIONS['{transform}']" if transform != "none" else "None"
            
            field_code = f'''        "{field_name}": FieldMapping(
            css_selector="{css_selector}",
            transform_func={transform_func}
        ),'''
            field_mappings_code.append(field_code)
            output_columns.append(field_name)
        
        output_columns.append("Status")
        
        # Function name
        func_name = f"create_{client_id}_config"
        register_func_name = f"register_{client_id}"
        
        # Generate the code
        code = f'''"""
{client_name} Client Configuration
Generated by Generic Scraper Client Generator
"""

try:
    from ..client_config import ClientConfig, FieldMapping, registry, TRANSFORM_FUNCTIONS
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from client_config import ClientConfig, FieldMapping, registry, TRANSFORM_FUNCTIONS


def {func_name}() -> ClientConfig:
    """Create client configuration for {client_name}."""
    
    field_mappings = {{
        "Status Code": FieldMapping(default_value="200"),
        "Exists": FieldMapping(default_value="No"),
{chr(10).join(field_mappings_code)}
    }}
    
    output_columns = {output_columns}
    
    # Advanced configuration
    advanced_config = {{}}
    
    # Rate limiting and performance settings
    if hasattr(self, 'rate_limit_var') and self.rate_limit_var.get():
        try:
            rate_limit = float(self.rate_limit_var.get())
            if rate_limit != 1.0:
                advanced_config['rate_limit'] = rate_limit
        except ValueError:
            pass
    
    if hasattr(self, 'request_timeout_var') and self.request_timeout_var.get():
        try:
            timeout = int(self.request_timeout_var.get())
            if timeout != 30:
                advanced_config['request_timeout'] = timeout
        except ValueError:
            pass
    
    if hasattr(self, 'total_timeout_var') and self.total_timeout_var.get():
        try:
            total_timeout = int(self.total_timeout_var.get())
            if total_timeout != 300:
                advanced_config['total_timeout'] = total_timeout
        except ValueError:
            pass
    
    if hasattr(self, 'max_retries_var') and self.max_retries_var.get():
        try:
            max_retries = int(self.max_retries_var.get())
            if max_retries != 3:
                advanced_config['max_retries'] = max_retries
        except ValueError:
            pass
    
    # Proxy configuration
    if hasattr(self, 'use_proxy_var') and self.use_proxy_var.get():
        proxy_config = {{}}
        if self.proxy_url_var.get():
            proxy_config['url'] = self.proxy_url_var.get()
        if self.proxy_username_var.get():
            proxy_config['username'] = self.proxy_username_var.get()
        if self.proxy_password_var.get():
            proxy_config['password'] = self.proxy_password_var.get()
        
        if proxy_config:
            advanced_config['proxy'] = proxy_config
    
    # Headers configuration
    headers = {{}}
    if hasattr(self, 'user_agent_var') and self.user_agent_var.get():
        user_agent = self.user_agent_var.get()
        if user_agent != "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36":
            headers['User-Agent'] = user_agent
    
    if hasattr(self, 'custom_headers_text'):
        try:
            import json
            custom_headers = json.loads(self.custom_headers_text.get('1.0', 'end-1c'))
            headers.update(custom_headers)
        except (json.JSONDecodeError, AttributeError):
            pass
    
    if headers:
        advanced_config['headers'] = headers
    
    # Validation settings
    validation_config = {{}}
    if hasattr(self, 'strict_validation_var') and not self.strict_validation_var.get():
        validation_config['strict_validation'] = False
    if hasattr(self, 'save_html_var') and self.save_html_var.get():
        validation_config['save_html_responses'] = True
    if hasattr(self, 'log_requests_var') and self.log_requests_var.get():
        validation_config['log_http_requests'] = True
    
    if validation_config:
        advanced_config['validation'] = validation_config
    
    config_params = {{
        'client_id': "{client_id}",
        'client_name': "{client_name}",
        'description': "{description}",
        'base_url': "{base_url}",
        'search_endpoint': "{search_endpoint}",
        'search_param_name': "{search_param}",
        'product_link_selector': "{product_selector}",
        'field_mappings': field_mappings,
        'part_number_regex': r'^[\\w\\-/\\.]{{1,64}}$',
        'normalize_part_number': {str(self.normalize_parts_var.get())},
        'exact_match_required': {str(self.exact_match_var.get())},
        'output_columns': output_columns
    }}
    
    # Add advanced configuration if present
    if advanced_config:
        config_params['advanced_config'] = advanced_config
    
    return ClientConfig(**config_params)


def {register_func_name}():
    """Register {client_name} client."""
    config = {func_name}()
    registry.register(config)


# Auto-register when module is imported
{register_func_name}()
'''
        
        return code
    
    def generate_client(self):
        """Generate the client file."""
        try:
            client_id = self.client_id_var.get()
            if not client_id:
                messagebox.showerror("Error", "Please enter a Client ID")
                return
            
            # Generate code
            code = self.generate_client_code()
            
            # Write to file
            client_file = Path(f"clients/{client_id}.py")
            client_file.write_text(code, encoding='utf-8')
            
            # Update __init__.py
            self.update_init_file(client_id)
            
            messagebox.showinfo("Success", 
                              f"Client '{client_id}' has been generated successfully!\\n\\n"
                              f"File created: {client_file}\\n"
                              f"The client will appear in the scraper menu next time you run it.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error generating client: {str(e)}")
    
    def update_init_file(self, client_id: str):
        """Update clients/__init__.py to include the new client."""
        init_file = Path("clients/__init__.py")
        if not init_file.exists():
            return
        
        content = init_file.read_text()
        
        # Add import
        import_line = f"    from .{client_id} import register_{client_id}"
        if import_line not in content:
            # Find the imports section and add the new import
            lines = content.split('\\n')
            for i, line in enumerate(lines):
                if "# Add your new clients here:" in line:
                    lines.insert(i, import_line)
                    break
        
        # Add registration call
        register_line = f"    register_{client_id}()"
        if register_line not in content:
            lines = content.split('\\n')
            for i, line in enumerate(lines):
                if "# register_my_client()  # Uncomment when you add a new client" in line:
                    lines.insert(i, register_line)
                    break
        
        # Write back
        init_file.write_text('\\n'.join(lines))
    
    def save_template(self):
        """Save current configuration as a template."""
        template_data = {
            'client_id': self.client_id_var.get(),
            'client_name': self.client_name_var.get(),
            'description': self.description_var.get(),
            'base_url': self.base_url_var.get(),
            'search_endpoint': self.search_endpoint_var.get(),
            'search_param': self.search_param_var.get(),
            'product_selector': self.product_selector_var.get(),
            'normalize_parts': self.normalize_parts_var.get(),
            'exact_match': self.exact_match_var.get(),
            'fields': []
        }
        
        for item in self.fields_tree.get_children():
            field_name, css_selector, transform = self.fields_tree.item(item, 'values')
            template_data['fields'].append({
                'name': field_name,
                'selector': css_selector,
                'transform': transform
            })
        
        filename = filedialog.asksaveasfilename(
            defaultextension='.json',
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')],
            title='Save Client Template'
        )
        
        if filename:
            Path(filename).write_text(json.dumps(template_data, indent=2))
            messagebox.showinfo("Success", f"Template saved to {filename}")
    
    def load_template(self):
        """Load configuration from a template."""
        filename = filedialog.askopenfilename(
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')],
            title='Load Client Template'
        )
        
        if filename:
            try:
                template_data = json.loads(Path(filename).read_text())
                
                # Load basic info
                self.client_id_var.set(template_data.get('client_id', ''))
                self.client_name_var.set(template_data.get('client_name', ''))
                self.description_var.set(template_data.get('description', ''))
                
                # Load website config
                self.base_url_var.set(template_data.get('base_url', ''))
                self.search_endpoint_var.set(template_data.get('search_endpoint', '/search'))
                self.search_param_var.set(template_data.get('search_param', 'q'))
                self.product_selector_var.set(template_data.get('product_selector', 'a.product-link'))
                self.normalize_parts_var.set(template_data.get('normalize_parts', True))
                self.exact_match_var.set(template_data.get('exact_match', True))
                
                # Load fields
                self.fields_tree.delete(*self.fields_tree.get_children())
                for field in template_data.get('fields', []):
                    self.fields_tree.insert('', 'end', values=(
                        field['name'], field['selector'], field['transform']
                    ))
                
                messagebox.showinfo("Success", f"Template loaded from {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error loading template: {str(e)}")
    def on_client_selected(self, event=None):
        """Handle client selection from dropdown - populate configuration fields."""
        try:
            from client_config import registry
            
            # Extract client ID from selection (format: "Client Name (client_id)")
            client_selection = self.selected_client_var.get()
            if not client_selection or '(' not in client_selection:
                return
                
            client_id = client_selection.split('(')[-1].rstrip(')')
            client_config = registry.get_client(client_id)
            
            if client_config:
                # Populate basic information
                if hasattr(self, 'client_id_var'):
                    self.client_id_var.set(client_config.client_id)
                if hasattr(self, 'client_name_var'):
                    self.client_name_var.set(client_config.client_name)
                if hasattr(self, 'description_var'):
                    self.description_var.set(client_config.description or "")
                
                # Populate website configuration
                if hasattr(self, 'base_url_var'):
                    self.base_url_var.set(client_config.base_url)
                if hasattr(self, 'search_endpoint_var'):
                    self.search_endpoint_var.set(client_config.search_endpoint)
                if hasattr(self, 'search_param_var'):
                    self.search_param_var.set(client_config.search_param_name)
                if hasattr(self, 'product_selector_var'):
                    self.product_selector_var.set(client_config.product_link_selector)
                
                # Populate advanced settings  
                if hasattr(self, 'normalize_parts_var'):
                    self.normalize_parts_var.set(client_config.normalize_part_number)
                if hasattr(self, 'exact_match_var'):
                    self.exact_match_var.set(client_config.exact_match_required)
                
                # Clear and populate field mappings if available
                if hasattr(self, 'field_mappings'):
                    self.field_mappings.clear()
                    for field_name, field_mapping in client_config.field_mappings.items():
                        self.field_mappings.append({
                            'name': field_name,
                            'selector': field_mapping.css_selector or '',
                            'attribute': field_mapping.attribute or '',
                            'regex': field_mapping.regex_pattern or '',
                            'default': field_mapping.default_value or 'Not found'
                        })
                
                # Refresh field mappings display if we're on that tab
                self.refresh_field_mappings_display()
                
                # Update status to show client is loaded
                self.status_var.set(f"Client Loaded: {client_config.client_name}")
                
                # Show success message in log
                self.log_message(f"✅ Loaded configuration for: {client_config.client_name}", 'success')
                self.log_message(f"📋 {len(client_config.field_mappings)} field mappings loaded", 'info')
                self.log_message(f"🌐 Base URL: {client_config.base_url}", 'info')
                
        except Exception as e:
            self.log_message(f"❌ Error loading client configuration: {str(e)}", 'error')

    def refresh_field_mappings_display(self):
        """Refresh the field mappings display with loaded data."""
        try:
            # If we have a field mappings listbox, update it
            if hasattr(self, 'mappings_listbox'):
                self.mappings_listbox.delete(0, tk.END)
                for i, mapping in enumerate(self.field_mappings):
                    display_text = f"{mapping['name']} -> {mapping['selector'] or mapping['attribute'] or 'default'}"
                    self.mappings_listbox.insert(tk.END, display_text)
        except Exception as e:
            print(f"Warning: Could not refresh field mappings display: {e}")

    def browse_input_file(self):
        """Browse for input CSV file."""
        filename = filedialog.askopenfilename(
            title="Select Input CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.input_file_var.set(filename)
    
    def browse_output_file(self):
        """Browse for output CSV file."""
        filename = filedialog.asksaveasfilename(
            title="Select Output CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            defaultextension=".csv"
        )
        if filename:
            self.output_file_var.set(filename)
    
    def start_scraping(self):
        """Start the scraping process."""
        # Validate inputs
        if not self.input_file_var.get():
            messagebox.showerror("Error", "Please select an input CSV file.")
            return
        
        if not self.output_file_var.get():
            messagebox.showerror("Error", "Please select an output CSV file.")
            return
        
        if not self.selected_client_var.get():
            messagebox.showerror("Error", "Please select a client.")
            return
        
        # Extract client ID from selection
        client_selection = self.selected_client_var.get()
        client_id = client_selection.split('(')[-1].rstrip(')')
        
        # Update UI
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_var.set("Running...")
        self.progress_var.set(0)
        self.progress_text_var.set("Starting scraping process...")
        
        # Log start with styling
        self.log_message(f"🚀 Starting scraping with client: {client_id}", 'bright_green')
        self.log_message(f"📁 Input file: {self.input_file_var.get()}", 'info')
        self.log_message(f"💾 Output file: {self.output_file_var.get()}", 'info')
        self.log_message("─" * 68, 'dim')
        
        # Start scraping in background thread
        import threading
        self.scraping_thread = threading.Thread(target=self._run_scraping, args=(client_id,))
        self.scraping_thread.daemon = True
        self.scraping_thread.start()
    
    def _run_scraping(self, client_id):
        """Run the scraping process in background thread."""
        try:
            import subprocess
            import sys
            import os
            from pathlib import Path
            
            # Use virtual environment Python if available
            venv_python = Path(__file__).parent / "venv" / "bin" / "python"
            python_executable = str(venv_python) if venv_python.exists() else sys.executable
            
            # Build command
            cmd = [
                python_executable, "app.py",
                "--client", client_id,
                "--input-csv", self.input_file_var.get(),
                "--output-csv", self.output_file_var.get()
            ]
            
            self.log_message(f"Executing: {' '.join(cmd)}")
            
            # Set environment to preserve Rich colors and configure scraper settings
            env = os.environ.copy()
            env['FORCE_COLOR'] = '1'
            
            # Set concurrency and chunk size from GUI controls
            env['CONCURRENCY_LIMIT'] = str(self.concurrency_var.get())
            env['CHUNKSIZE'] = str(self.chunk_size_var.get())
            
            # Set email notification preference from GUI toggle
            env['EMAIL_NOTIFICATIONS_ENABLED'] = str(self.email_notify_var.get()).lower()
            env['TERM'] = 'xterm-256color'
            
            # Run the scraping process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env
            )
            
            # Read output line by line
            if process.stdout:
                for line in process.stdout:
                    if line.strip():  # Only process non-empty lines
                        # Process all output through log_rich_output which will filter appropriately
                        self.root.after(0, self.log_rich_output, line)
            
            # Wait for completion
            return_code = process.wait()
            
            if return_code == 0:
                self.root.after(0, self.scraping_complete, True)
            else:
                self.root.after(0, self.scraping_complete, False)
                
        except Exception as e:
            self.root.after(0, self.log_message, f"Error: {str(e)}")
            self.root.after(0, self.scraping_complete, False)
    
    def stop_scraping(self):
        """Stop the scraping process."""
        if hasattr(self, 'scraping_thread') and self.scraping_thread.is_alive():
            self.log_message("Stopping scraping process...")
            # Note: This is a simple implementation. In a real scenario, 
            # you'd want to properly terminate the subprocess
        self.scraping_complete(False)
    
    def scraping_complete(self, success):
        """Handle scraping completion."""
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        
        if success:
            self.status_var.set("Completed successfully")
            self.progress_var.set(100)
            self.progress_text_var.set("Scraping completed successfully!")
            self.log_message("─" * 68, 'dim')
            self.log_message("✅ SCRAPING COMPLETED SUCCESSFULLY! ✅", 'success')
            self.log_message(f"📊 Results saved to: {self.output_file_var.get()}", 'bright_green')
            self.log_message("─" * 68, 'dim')
            
            # Show completion message
            messagebox.showinfo("Success", 
                              f"Scraping completed successfully!\n\nResults saved to:\n{self.output_file_var.get()}")
        else:
            self.status_var.set("Failed")
            self.progress_text_var.set("Scraping failed or was stopped")
            self.log_message("─" * 68, 'dim')
            self.log_message("❌ SCRAPING FAILED OR STOPPED ❌", 'error')
            self.log_message("Check the logs above for error details", 'warning')
            self.log_message("─" * 68, 'dim')
    
    def update_progress_from_line(self, line):
        """Update progress bar from log line."""
        try:
            # Try to extract percentage from line
            import re
            match = re.search(r'(\d+)%', line)
            if match:
                percentage = int(match.group(1))
                self.progress_var.set(percentage)
                self.progress_text_var.set(f"Progress: {percentage}%")
        except:
            pass
    
    def setup_color_tags(self):
        """Set up color tags for terminal-like output."""
        # Rich color mapping for terminal display
        color_mapping = {
            'green': '#00FF00',
            'red': '#FF5555',
            'yellow': '#FFFF55',
            'blue': '#5555FF',
            'magenta': '#FF55FF',
            'cyan': '#55FFFF',
            'white': '#FFFFFF',
            'bright_green': '#55FF55',
            'bright_red': '#FF5555',
            'bright_yellow': '#FFFF55',
            'bright_blue': '#5555FF',
            'bright_magenta': '#FF55FF',
            'bright_cyan': '#55FFFF',
            'bright_white': '#FFFFFF',
            'dim': '#808080',
            'bold': '#FFFFFF',
        }
        
        # Configure tags for each color
        for tag, color in color_mapping.items():
            self.log_text.tag_configure(tag, foreground=color)
        
        # Special tags for formatting
        self.log_text.tag_configure('bold', font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure('underline', underline=True)
        self.log_text.tag_configure('progress_bar', background='#1a1a1a', foreground='#00FF41')
        self.log_text.tag_configure('success', foreground='#00FF41', font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure('error', foreground='#FF4444', font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure('warning', foreground='#FFAA00', font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure('info', foreground='#44AAFF')
        self.log_text.tag_configure('table_header', foreground='#00FFFF', font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure('table_row', foreground='#CCCCCC')
        self.log_text.tag_configure('black', foreground='#000000')

    def log_message(self, message, style=None):
        """Add message to log area with optional styling."""
        # Insert message with timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        start_pos = self.log_text.index(tk.END)
        self.log_text.insert(tk.END, formatted_message)
        
        # Apply styling if specified
        if style:
            end_pos = self.log_text.index(tk.END)
            self.log_text.tag_add(style, start_pos, end_pos)
        
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def strip_ansi_codes(self, text):
        """Remove all ANSI escape sequences from text."""
        import re
        # Remove all ANSI escape sequences including:
        # - Color codes: \033[...m
        # - Cursor movement: \033[...A, \033[...B, etc.
        # - Line clearing: \033[...K
        # - Show/hide cursor: \033[?25l, \033[?25h
        # - Any other escape sequences
        ansi_escape = re.compile(r'\033\[[0-9;?]*[mABCDEFGHJKSThlf]')
        # Also remove carriage returns and backspace sequences that mess up formatting
        text = re.sub(r'\r+', '', text)  # Remove carriage returns
        text = re.sub(r'\x08+', '', text)  # Remove backspaces
        # Remove the ANSI sequences
        clean_text = ansi_escape.sub('', text)
        return clean_text
    
    def should_display_line(self, text):
        """Determine if a line should be displayed based on content."""
        clean_text = self.strip_ansi_codes(text).strip()
        
        # Skip empty lines
        if not clean_text:
            return False
            
        # Skip lines that are just progress bar updates (repeated progress with same percentage)
        if clean_text.startswith('Overall ') and '━' in clean_text and '%' in clean_text:
            return False
        if clean_text.startswith('Chunk ') and '━' in clean_text and '%' in clean_text:
            return False
            
        # Skip cursor control lines
        if clean_text in ['', ' ']:
            return False
            
        return True

    def log_rich_output(self, text):
        """Parse and display Rich-formatted text with colors and formatting, matching CLI output."""
        # Clean the text first
        clean_text = self.strip_ansi_codes(text)
        
        # Skip lines that shouldn't be displayed
        if not self.should_display_line(text):
            return
            
        # Detect and style important content
        if any(indicator in clean_text for indicator in ["✅", "Success", "Processed:"]):
            self.insert_styled_text(clean_text, 'success')
        elif any(indicator in clean_text for indicator in ["❌", "Error", "Failed"]):
            self.insert_styled_text(clean_text, 'error')
        elif any(indicator in clean_text for indicator in ["⚠️", "Warning"]):
            self.insert_styled_text(clean_text, 'warning')
        elif "│" in clean_text or "┌" in clean_text or "├" in clean_text or "└" in clean_text:
            # Table content - cyan styling
            self.insert_styled_text(clean_text, 'cyan')
        elif "━━━" in clean_text:
            # Separators
            self.insert_styled_text(clean_text, 'dim')
        else:
            # Regular text
            self.insert_styled_text(clean_text, None)
            
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def parse_and_insert_ansi(self, text, ansi_codes):
        """Parse ANSI codes and insert formatted text."""
        import re
        
        # Split text by ANSI codes
        parts = re.split(r'(\033\[[0-9;]*m)', text)
        current_styles = []
        
        for part in parts:
            if part in ansi_codes:
                style = ansi_codes[part]
                if style is None:  # Reset
                    current_styles = []
                elif style not in current_styles:
                    current_styles.append(style)
            elif part:  # Non-empty text part
                self.insert_styled_text(part, current_styles)
    
    def insert_styled_text(self, text, styles):
        """Insert text with given styles."""
        start_pos = self.log_text.index(tk.END)
        self.log_text.insert(tk.END, text)
        
        if styles:
            end_pos = self.log_text.index(tk.END)
            if isinstance(styles, str):
                styles = [styles]
            for style in styles:
                self.log_text.tag_add(style, start_pos, end_pos)

    def add_terminal_welcome(self):
        """Add a terminal-like welcome message."""
        welcome_text = """╔══════════════════════════════════════════════════════════════════╗
║                    Generic Scraper Terminal                      ║
║                      Ready for Operations                        ║
╚══════════════════════════════════════════════════════════════════╝

Generic Scraper v2.0 - Terminal Interface
> Select input file, output location, and client to begin scraping
> All CLI output will be displayed here with full color support
> Progress bars, tables, and status updates will appear in real-time

"""
        self.insert_styled_text(welcome_text, 'bright_green')
        self.log_text.insert(tk.END, "─" * 68 + "\n\n")
        self.insert_styled_text("System: Ready to start scraping operations...\n", 'info')
    
    def clear_log(self):
        """Clear the log area and restore welcome message."""
        self.log_text.delete(1.0, tk.END)
        self.add_terminal_welcome()
    
    def open_results_folder(self):
        """Open the folder containing results."""
        if self.output_file_var.get():
            import platform
            import subprocess
            
            folder = str(Path(self.output_file_var.get()).parent)
            
            if platform.system() == "Windows":
                import os
                os.startfile(folder)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", folder])
            else:  # Linux
                subprocess.Popen(["xdg-open", folder])

    def run(self):
        """Run the GUI."""
        self.root.mainloop()


class FieldMappingDialog:
    def __init__(self, parent, initial_values=None):
        self.result = None
        
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
    
    def setup_dialog(self):
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
    
    def ok_clicked(self):
        """Handle OK button click."""
        field_name = self.field_name_var.get().strip()
        css_selector = self.css_selector_var.get().strip()
        transform = self.transform_var.get()
        
        if not field_name or not css_selector:
            messagebox.showerror("Error", "Field name and CSS selector are required.")
            return
        
        self.result = (field_name, css_selector, transform)
        self.dialog.destroy()
    
    def cancel_clicked(self):
        """Handle Cancel button click."""
        self.dialog.destroy()


def main():
    """Run the client generator GUI."""
    app = ClientGeneratorGUI()
    app.run()


if __name__ == "__main__":
    main()