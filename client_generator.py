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
import os
from typing import Dict, List, Optional, Any, Union
import json
from PIL import Image, ImageTk  # For image handling
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ToolTip:
    """
    Create a tooltip for a given widget
    """
    def __init__(self, widget: tk.Widget, text: str = 'widget info') -> None:
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.tooltip_window: Optional[tk.Toplevel] = None

    def enter(self, event: Optional[Any] = None) -> None:
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
        except:
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

    def leave(self, event: Optional[Any] = None) -> None:
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None


class ClientGeneratorGUI:
    def __init__(self) -> None:
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
        self.client_data: Dict[str, Any] = {}
        self.field_mappings: List[Dict[str, Any]] = []
        self.logo_image = None  # Store logo image reference
        
        self.setup_ui()
    
    def setup_ui(self) -> None:
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
    
    def setup_scraper_tab(self, parent: ttk.Frame) -> None:
        """Set up the main scraper execution tab."""
        # Title Section
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill='x', padx=20, pady=(15, 10))
        
        # Create a frame for the logo and title
        logo_title_frame = ttk.Frame(title_frame)
        logo_title_frame.pack(side='left')
        
        # Try to load custom logo image
        try:
            # Look for logo files in the current directory
            logo_paths = [
                'logo.png', 'logo.jpg', 'logo.jpeg', 'logo.gif', 'logo.bmp', 'logo.webp',
                'icon.png', 'icon.jpg', 'icon.jpeg', 'icon.gif', 'icon.bmp', 'icon.webp'
            ]
            
            logo_image = None
            for logo_path in logo_paths:
                if os.path.exists(logo_path):
                    # Load and process the image
                    pil_image = Image.open(logo_path)
                    
                    # Convert to RGBA to handle transparency
                    if pil_image.mode != 'RGBA':
                        pil_image = pil_image.convert('RGBA')
                    
                    # Optional: Remove white background (uncomment if needed)
                    # data = pil_image.getdata()
                    # new_data = []
                    # for item in data:
                    #     # Make white pixels transparent
                    #     if item[0] > 240 and item[1] > 240 and item[2] > 240:  # Almost white
                    #         new_data.append((255, 255, 255, 0))  # Transparent
                    #     else:
                    #         new_data.append(item)
                    # pil_image.putdata(new_data)
                    
                    # Resize to appropriate size (32x32 pixels)
                    pil_image = pil_image.resize((32, 32), Image.Resampling.LANCZOS)
                    logo_image = ImageTk.PhotoImage(pil_image)
                    break
            
            if logo_image:
                # Create label with image using tk.Label for better background control
                logo_label = tk.Label(logo_title_frame, image=logo_image, 
                                     bg=self.root.cget('bg'), bd=0, highlightthickness=0)
                self.logo_image = logo_image  # Keep a reference to prevent garbage collection
                logo_label.pack(side='left', padx=(0, 10))
                
                # Title without emoji
                ttk.Label(logo_title_frame, text="Multi-Client Web Scraper", 
                         font=('Arial', 18, 'bold')).pack(side='left')
            else:
                # Fallback to emoji if no image found
                ttk.Label(logo_title_frame, text="🚀  Multi-Client Web Scraper", 
                         font=('Arial', 18, 'bold')).pack(side='left')
                
        except ImportError:
            # Fallback if PIL is not available
            ttk.Label(logo_title_frame, text="🚀  Multi-Client Web Scraper", 
                     font=('Arial', 18, 'bold')).pack(side='left')
        except Exception as e:
            # Fallback for any other errors
            ttk.Label(logo_title_frame, text="🚀  Multi-Client Web Scraper", 
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
        
        # Add tooltip for client selection
        ToolTip(client_dropdown, "Select the website/client configuration to use for scraping.\nEach client contains specific settings for different websites.")
        
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
        input_browse_btn = ttk.Button(files_frame, text="Browse...", 
                  command=self.browse_input_file)
        input_browse_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Add tooltips for input file
        ToolTip(input_entry, "CSV file containing part numbers to scrape.\nShould have a 'Part Number' column with the items to search for.")
        ToolTip(input_browse_btn, "Click to browse and select your input CSV file")
        
        # Output file selection
        ttk.Label(files_frame, text="Output CSV file:").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        self.output_file_var = tk.StringVar()
        output_entry = ttk.Entry(files_frame, textvariable=self.output_file_var, width=50)
        output_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        output_browse_btn = ttk.Button(files_frame, text="Browse...", 
                  command=self.browse_output_file)
        output_browse_btn.grid(row=1, column=2, padx=5, pady=5)
        
        # Add tooltips for output file
        ToolTip(output_entry, "Where to save the scraping results.\nWill contain all found product information including prices, availability, etc.")
        ToolTip(output_browse_btn, "Click to choose where to save the results CSV file")
        
        # Options Section
        options_frame = ttk.LabelFrame(parent, text="Scraping Options")
        options_frame.pack(fill='x', padx=20, pady=10)
        
        # Concurrency
        ttk.Label(options_frame, text="Concurrency limit:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.concurrency_var = tk.StringVar(value="3")
        concurrency_entry = ttk.Entry(options_frame, textvariable=self.concurrency_var, width=10)
        concurrency_entry.grid(row=0, column=1, sticky='w', padx=5)
        
        # Chunk size
        ttk.Label(options_frame, text="Chunk size:").grid(row=0, column=2, sticky='w', pady=5, padx=(20, 5))
        self.chunk_size_var = tk.StringVar(value="500")
        chunk_entry = ttk.Entry(options_frame, textvariable=self.chunk_size_var, width=10)
        chunk_entry.grid(row=0, column=3, sticky='w', padx=5)
        
        # Email notification
        self.email_notify_var = tk.BooleanVar()
        email_checkbox = ttk.Checkbutton(options_frame, text="Send email notification when complete", 
                       variable=self.email_notify_var)
        email_checkbox.grid(row=1, column=0, columnspan=4, sticky='w', padx=5, pady=5)
        
        # Add tooltips for scraping options
        ToolTip(concurrency_entry, "Number of simultaneous web requests.\nHigher = faster but may overwhelm servers.\nRecommended: 2-5")
        ToolTip(chunk_entry, "Items to process before saving progress.\nLarger chunks = better performance but less frequent saves.\nRecommended: 100-1000")
        ToolTip(email_checkbox, "Send an email notification when scraping completes.\nRequires email configuration in settings.")
        
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
            fg='#FFFFFF',  # White text (default for unstyled text)
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
    
    def setup_basic_tab(self, parent: ttk.Frame) -> None:
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
        client_name_entry = ttk.Entry(form_frame, textvariable=self.client_name_var, width=40)
        client_name_entry.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=2, column=0, sticky='w', pady=5)
        self.description_var = tk.StringVar()
        description_entry = ttk.Entry(form_frame, textvariable=self.description_var, width=40)
        description_entry.grid(row=2, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Add tooltips for basic information
        ToolTip(self.client_id_entry, "Unique identifier for this client configuration.\nMust be lowercase, no spaces, only letters, numbers, and underscores.\nExample: 'digikey', 'mouser_electronics'")
        ToolTip(client_name_entry, "Human-readable name for this client.\nThis appears in the client selection dropdown.\nExample: 'DigiKey Electronics', 'Mouser Electronics'")
        ToolTip(description_entry, "Brief description of what this client does.\nHelps identify the purpose of this configuration.\nExample: 'Electronic components supplier'")
        
        # Validation label
        self.validation_label = ttk.Label(form_frame, text="", foreground='red')
        self.validation_label.grid(row=3, column=0, columnspan=2, pady=5)
    
    def setup_website_tab(self, parent: ttk.Frame) -> None:
        """Set up website configuration tab."""
        ttk.Label(parent, text="Website Configuration", font=('Arial', 14, 'bold')).pack(pady=(10, 20))
        
        form_frame = ttk.Frame(parent)
        form_frame.pack(fill='x', padx=20)
        
        # Base URL
        ttk.Label(form_frame, text="Base URL (e.g., https://example.com):").grid(row=0, column=0, sticky='w', pady=5)
        self.base_url_var = tk.StringVar()
        base_url_entry = ttk.Entry(form_frame, textvariable=self.base_url_var, width=50)
        base_url_entry.grid(row=0, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Search Endpoint
        ttk.Label(form_frame, text="Search Endpoint (e.g., /search):").grid(row=1, column=0, sticky='w', pady=5)
        self.search_endpoint_var = tk.StringVar(value="/search")
        search_endpoint_entry = ttk.Entry(form_frame, textvariable=self.search_endpoint_var, width=50)
        search_endpoint_entry.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Search Parameter
        ttk.Label(form_frame, text="Search Parameter Name (e.g., q, search, query):").grid(row=2, column=0, sticky='w', pady=5)
        self.search_param_var = tk.StringVar(value="q")
        search_param_entry = ttk.Entry(form_frame, textvariable=self.search_param_var, width=50)
        search_param_entry.grid(row=2, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Product Link Selector
        ttk.Label(form_frame, text="Product Link CSS Selector:").grid(row=3, column=0, sticky='w', pady=5)
        self.product_selector_var = tk.StringVar(value="a.product-link")
        product_selector_entry = ttk.Entry(form_frame, textvariable=self.product_selector_var, width=50)
        product_selector_entry.grid(row=3, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Part Number Regex
        ttk.Label(form_frame, text="Part Number Regex Pattern:").grid(row=4, column=0, sticky='w', pady=5)
        self.part_regex_var = tk.StringVar(value=r'^[\w\-/\.]{1,64}$')
        regex_entry = ttk.Entry(form_frame, textvariable=self.part_regex_var, width=50)
        regex_entry.grid(row=4, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Add tooltips for website configuration
        ToolTip(base_url_entry, "The main website URL.\nExample: 'https://www.digikey.com', 'https://www.mouser.com'\nDo not include search paths, just the domain.")
        ToolTip(search_endpoint_entry, "The search page path on the website.\nExample: '/products/en/search' for DigiKey, '/c/' for Mouser\nThis gets appended to the base URL.")
        ToolTip(search_param_entry, "The URL parameter name used for search queries.\nExample: 'keywords' for DigiKey, 'q' for many sites\nCheck the website's search URL to find this.")
        ToolTip(product_selector_entry, "CSS selector to find product links in search results.\nExample: 'a[href*=\"/product-detail/\"]' for DigiKey\nUse browser dev tools to inspect the search results page.")
        ToolTip(regex_entry, "Regular expression pattern to validate part numbers.\nDefault matches alphanumeric, dashes, slashes, dots, 1-64 chars.\nExample: '^[A-Z0-9-]{3,20}$' for uppercase alphanumeric with dashes.")
        
        # Add help label for regex
        help_label = ttk.Label(form_frame, text="(Pattern to validate part numbers - e.g., letters, numbers, dashes, dots, 1-64 chars)", 
                              font=('Arial', 8), foreground='gray')
        help_label.grid(row=5, column=1, sticky='w', padx=(10, 0), pady=(0, 5))
        
        # Options frame
        options_frame = ttk.LabelFrame(parent, text="Options")
        options_frame.pack(fill='x', padx=20, pady=20)
        
        # Checkboxes
        self.normalize_parts_var = tk.BooleanVar(value=True)
        normalize_checkbox = ttk.Checkbutton(options_frame, text="Normalize part numbers (remove dashes, lowercase)", 
                       variable=self.normalize_parts_var)
        normalize_checkbox.pack(anchor='w', padx=10, pady=5)
        
        self.exact_match_var = tk.BooleanVar(value=True)
        exact_match_checkbox = ttk.Checkbutton(options_frame, text="Require exact match between search and product", 
                       variable=self.exact_match_var)
        exact_match_checkbox.pack(anchor='w', padx=10, pady=5)
        
        # Add tooltips for website options
        ToolTip(normalize_checkbox, "Convert part numbers to standard format before comparing.\nRemoves dashes/spaces and converts to lowercase.\nHelps match 'ABC-123' with 'abc123'.")
        ToolTip(exact_match_checkbox, "Only accept products where the part number exactly matches the search.\nPrevents false positives from similar part numbers.\nRecommended: Keep enabled for accuracy.")
    
    def setup_fields_tab(self, parent: ttk.Frame) -> None:
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
        
        add_field_btn = ttk.Button(buttons_frame, text="Add Field", command=self.add_field)
        add_field_btn.pack(side='left', padx=5)
        edit_field_btn = ttk.Button(buttons_frame, text="Edit Field", command=self.edit_field)
        edit_field_btn.pack(side='left', padx=5)
        remove_field_btn = ttk.Button(buttons_frame, text="Remove Field", command=self.remove_field)
        remove_field_btn.pack(side='left', padx=5)
        common_fields_btn = ttk.Button(buttons_frame, text="Add Common Fields", command=self.add_common_fields)
        common_fields_btn.pack(side='left', padx=5)
        
        # Add tooltips for field mapping buttons
        ToolTip(add_field_btn, "Add a new field to extract from product pages.\nDefine CSS selectors to capture data like price, availability, etc.")
        ToolTip(edit_field_btn, "Modify the selected field mapping.\nSelect a field in the list above first.")
        ToolTip(remove_field_btn, "Delete the selected field mapping.\nSelect a field in the list above first.")
        ToolTip(common_fields_btn, "Add typical fields like Brand, Category, Model, Weight, Dimensions.\nUseful starting point for most e-commerce sites.")
        
        # Add some default fields
        self.add_default_fields()
    
    def setup_advanced_tab(self, parent: ttk.Frame) -> None:
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
        self.rate_limit_var = tk.StringVar(value="5")
        rate_limit_entry = ttk.Entry(rate_frame, textvariable=self.rate_limit_var, width=10)
        rate_limit_entry.grid(row=0, column=1, sticky='w', padx=5)
        
        # Timeout settings
        ttk.Label(rate_frame, text="Request timeout (seconds):").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        self.request_timeout_var = tk.StringVar(value="30")
        request_timeout_entry = ttk.Entry(rate_frame, textvariable=self.request_timeout_var, width=10)
        request_timeout_entry.grid(row=1, column=1, sticky='w', padx=5)
        
        ttk.Label(rate_frame, text="Total timeout (seconds):").grid(row=2, column=0, sticky='w', pady=5, padx=5)
        self.total_timeout_var = tk.StringVar(value="300")
        total_timeout_entry = ttk.Entry(rate_frame, textvariable=self.total_timeout_var, width=10)
        total_timeout_entry.grid(row=2, column=1, sticky='w', padx=5)
        
        # Retry settings
        ttk.Label(rate_frame, text="Max retries:").grid(row=3, column=0, sticky='w', pady=5, padx=5)
        self.max_retries_var = tk.StringVar(value="3")
        max_retries_entry = ttk.Entry(rate_frame, textvariable=self.max_retries_var, width=10)
        max_retries_entry.grid(row=3, column=1, sticky='w', padx=5)
        
        # Add tooltips for rate limiting
        ToolTip(rate_limit_entry, "Maximum requests per second to avoid overwhelming the server.\nLower values are more polite but slower.\nRecommended: 0.5-2.0")
        ToolTip(request_timeout_entry, "Seconds to wait for each HTTP request before timing out.\nIncrease for slow websites.\nRecommended: 15-60")
        ToolTip(total_timeout_entry, "Maximum seconds to wait for the entire scraping operation.\nPrevents infinite hangs.\nRecommended: 300-3600")
        ToolTip(max_retries_entry, "How many times to retry failed requests.\nHigher values improve reliability but slow down errors.\nRecommended: 2-5")
        
        # Proxy Configuration Section
        proxy_frame = ttk.LabelFrame(scrollable_frame, text="Proxy Configuration")
        proxy_frame.pack(fill='x', padx=20, pady=10)
        
        # Add instruction label
        instruction_label = ttk.Label(proxy_frame, text="Proxy is enabled by default with credentials from environment variables:", 
                                    font=('Arial', 9), foreground='gray')
        instruction_label.pack(anchor='w', padx=5, pady=(5, 0))
        
        # Default to proxy enabled with your credentials pre-filled
        self.use_proxy_var = tk.BooleanVar(value=True)
        proxy_checkbox = ttk.Checkbutton(proxy_frame, text="Use proxy", variable=self.use_proxy_var,
                       command=self.toggle_proxy_fields)
        proxy_checkbox.pack(anchor='w', padx=5, pady=5)
        
        # Proxy fields frame
        self.proxy_fields_frame = ttk.Frame(proxy_frame)
        self.proxy_fields_frame.pack(fill='x', padx=20, pady=5)
        
        ttk.Label(self.proxy_fields_frame, text="Proxy URL:").grid(row=0, column=0, sticky='w', pady=5)
        self.proxy_url_var = tk.StringVar(value=os.getenv("PROXY_HOST", "rp.proxyscrape.com:6060"))
        proxy_url_entry = ttk.Entry(self.proxy_fields_frame, textvariable=self.proxy_url_var, width=40)
        proxy_url_entry.grid(row=0, column=1, sticky='w', padx=5)
        
        ttk.Label(self.proxy_fields_frame, text="Username:").grid(row=1, column=0, sticky='w', pady=5)
        self.proxy_username_var = tk.StringVar(value=os.getenv("PROXY_USERNAME", ""))
        proxy_username_entry = ttk.Entry(self.proxy_fields_frame, textvariable=self.proxy_username_var, width=40)
        proxy_username_entry.grid(row=1, column=1, sticky='w', padx=5)
        
        ttk.Label(self.proxy_fields_frame, text="Password:").grid(row=2, column=0, sticky='w', pady=5)
        self.proxy_password_var = tk.StringVar(value=os.getenv("PROXY_PASSWORD", ""))
        proxy_password_entry = ttk.Entry(self.proxy_fields_frame, textvariable=self.proxy_password_var, width=40, show='*')
        proxy_password_entry.grid(row=2, column=1, sticky='w', padx=5)
        
        # Add tooltips for proxy configuration
        ToolTip(proxy_checkbox, "Route requests through a proxy server.\nHelps avoid IP blocking and provides anonymity.\nRecommended for heavy scraping.")
        ToolTip(proxy_url_entry, "Proxy server address and port.\nFormat: hostname:port or ip:port\nExample: 'proxy.example.com:8080'")
        ToolTip(proxy_username_entry, "Username for proxy authentication.\nLeave blank if proxy doesn't require authentication.")
        ToolTip(proxy_password_entry, "Password for proxy authentication.\nLeave blank if proxy doesn't require authentication.")
        
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
    
    def toggle_proxy_fields(self) -> None:
        """Enable/disable proxy fields based on checkbox."""
        state = 'normal' if self.use_proxy_var.get() else 'disabled'
        for widget in self.proxy_fields_frame.winfo_children():
            if isinstance(widget, ttk.Entry):
                widget.configure(state=state)
    
    def setup_preview_tab(self, parent: ttk.Frame) -> None:
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
        
        update_preview_btn = ttk.Button(button_frame, text="Update Preview", command=self.update_preview)
        update_preview_btn.pack(side='left', padx=5)
        generate_client_btn = ttk.Button(button_frame, text="Generate Client File", command=self.generate_client)
        generate_client_btn.pack(side='left', padx=5)
        save_template_btn = ttk.Button(button_frame, text="Save Template", command=self.save_template)
        save_template_btn.pack(side='left', padx=5)
        load_template_btn = ttk.Button(button_frame, text="Load Template", command=self.load_template)
        load_template_btn.pack(side='left', padx=5)
        
        # Add tooltips for preview and generation buttons
        ToolTip(update_preview_btn, "Generate and display the Python code that will be created.\nUse this to review the configuration before generating the file.")
        ToolTip(generate_client_btn, "Create the actual client Python file in the clients/ directory.\nThe client will be immediately available for use.")
        ToolTip(save_template_btn, "Save current configuration as a reusable template.\nUseful for creating similar clients or backing up configurations.")
        ToolTip(load_template_btn, "Load a previously saved template.\nAutomatically fills in all the form fields with saved values.")
    
    def validate_client_id(self, *args: Any) -> None:
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
    
    def add_default_fields(self) -> None:
        """Add default field mappings."""
        default_fields = [
            ("Price", ".price, .product-price", "extract_numeric"),
            ("In Stock", ".stock-status, .availability", "clean_text"),
            ("Description", ".description, .product-description", "clean_text"),
        ]
        
        for field_name, selector, transform in default_fields:
            self.fields_tree.insert('', 'end', values=(field_name, selector, transform))
    
    def add_field(self) -> None:
        """Add a new field mapping."""
        dialog = FieldMappingDialog(self.root)
        if dialog.result:
            field_name, css_selector, transform = dialog.result
            self.fields_tree.insert('', 'end', values=(field_name, css_selector, transform))
    
    def edit_field(self) -> None:
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
    
    def remove_field(self) -> None:
        """Remove selected field mapping."""
        selection = self.fields_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a field to remove.")
            return
        
        for item in selection:
            self.fields_tree.delete(item)
    
    def add_common_fields(self) -> None:
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
    
    def update_preview(self) -> None:
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
        part_regex = self.part_regex_var.get()
        
        # Validate required fields
        if not all([client_id, client_name, base_url]):
            raise ValueError("Client ID, Client Name, and Base URL are required")
        
        # Get field mappings
        field_mappings_code = []
        output_columns = ["Part Number", "Status Code", "Exists"]
        
        for item in self.fields_tree.get_children():
            values = self.fields_tree.item(item, 'values')
            if not values or len(values) < 3:
                continue
            field_name, css_selector, transform = values
            
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
        'part_number_regex': r'{part_regex}',
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
    
    def generate_client(self) -> None:
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
    
    def update_init_file(self, client_id: str) -> None:
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
    
    def save_template(self) -> None:
        """Save current configuration as a template."""
        template_data = {
            'client_id': self.client_id_var.get(),
            'client_name': self.client_name_var.get(),
            'description': self.description_var.get(),
            'base_url': self.base_url_var.get(),
            'search_endpoint': self.search_endpoint_var.get(),
            'search_param': self.search_param_var.get(),
            'product_selector': self.product_selector_var.get(),
            'part_regex': self.part_regex_var.get(),
            'normalize_parts': self.normalize_parts_var.get(),
            'exact_match': self.exact_match_var.get(),
            'fields': []
        }
        
        for item in self.fields_tree.get_children():
            values = self.fields_tree.item(item, 'values')
            if not values or len(values) < 3:
                continue
            field_name, css_selector, transform = values
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
    
    def load_template(self) -> None:
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
                self.part_regex_var.set(template_data.get('part_regex', r'^[\w\-/\.]{1,64}$'))
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
    def on_client_selected(self, event: Optional[Any] = None) -> None:
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
                if hasattr(self, 'part_regex_var'):
                    self.part_regex_var.set(client_config.part_number_regex or r'^[\w\-/\.]{1,64}$')
                
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

    def refresh_field_mappings_display(self) -> None:
        """Refresh the field mappings display with loaded data."""
        try:
            # If we have a field mappings treeview, update it
            if hasattr(self, 'fields_tree'):
                # Clear existing items
                for item in self.fields_tree.get_children():
                    self.fields_tree.delete(item)
                
                # Add field mappings from loaded configuration
                for mapping in getattr(self, 'field_mappings', []):
                    field_name = mapping.get('name', '')
                    selector = mapping.get('selector', '')
                    transform = 'clean_text'  # Default transform
                    self.fields_tree.insert('', 'end', values=(field_name, selector, transform))
        except Exception as e:
            print(f"Warning: Could not refresh field mappings display: {e}")

    def browse_input_file(self) -> None:
        """Browse for input CSV file."""
        filename = filedialog.askopenfilename(
            title="Select Input CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.input_file_var.set(filename)
    
    def browse_output_file(self) -> None:
        """Browse for output CSV file."""
        filename = filedialog.asksaveasfilename(
            title="Select Output CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            defaultextension=".csv"
        )
        if filename:
            self.output_file_var.set(filename)
    
    def start_scraping(self) -> None:
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
    
    def _run_scraping(self, client_id: str) -> None:
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
            
            # Pass proxy configuration from GUI to subprocess
            if hasattr(self, 'use_proxy_var') and self.use_proxy_var.get():
                proxy_host = self.proxy_url_var.get() if hasattr(self, 'proxy_url_var') else ''
                proxy_user = self.proxy_username_var.get() if hasattr(self, 'proxy_username_var') else ''
                proxy_pass = self.proxy_password_var.get() if hasattr(self, 'proxy_password_var') else ''
                
                # Always set the environment variables, even if empty
                env['PROXY_HOST'] = proxy_host
                env['PROXY_USERNAME'] = proxy_user  
                env['PROXY_PASSWORD'] = proxy_pass
                    
                self.log_message(f"🔗 GUI Proxy Config - Host: '{proxy_host}', User: '{proxy_user}', Pass: {'*' * len(proxy_pass) if proxy_pass else '(empty)'}", 'info')
            else:
                # Explicitly disable proxy if unchecked in GUI
                env['PROXY_USERNAME'] = ''
                env['PROXY_PASSWORD'] = ''
                env['PROXY_HOST'] = ''
                self.log_message("🚫 Proxy disabled in GUI - clearing all proxy environment variables", 'warning')
            
            # Debug: Show what environment variables are actually being set
            proxy_env_vars = {k: v for k, v in env.items() if 'PROXY' in k}
            self.log_message(f"🔍 Environment variables being passed: {proxy_env_vars}", 'dim')
            
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
                        # Also update progress bar in real-time
                        self.root.after(0, self.update_progress_from_line, line)
            
            # Wait for completion
            return_code = process.wait()
            
            if return_code == 0:
                self.root.after(0, self.scraping_complete, True)
            else:
                self.root.after(0, self.scraping_complete, False)
                
        except Exception as e:
            self.root.after(0, self.log_message, f"Error: {str(e)}")
            self.root.after(0, self.scraping_complete, False)
    
    def stop_scraping(self) -> None:
        """Stop the scraping process."""
        if hasattr(self, 'scraping_thread') and self.scraping_thread.is_alive():
            self.log_message("Stopping scraping process...")
            # Note: This is a simple implementation. In a real scenario, 
            # you'd want to properly terminate the subprocess
        self.scraping_complete(False)
    
    def scraping_complete(self, success: bool) -> None:
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
    
    def update_progress_from_line(self, line: str) -> None:
        """Update progress bar from log line."""
        try:
            import re
            
            # Extract percentage from progress indicators
            match = re.search(r'(\d+)%', line)
            if match:
                percentage = int(match.group(1))
                self.progress_var.set(percentage)
                self.progress_text_var.set(f"Progress: {percentage}%")
                return
            
            # Look for item count indicators like "[1/100]" or "Processed: 25/100"
            count_match = re.search(r'\[(\d+)/(\d+)\]', line)
            if count_match:
                current = int(count_match.group(1))
                total = int(count_match.group(2))
                if total > 0:
                    percentage = min(100, (current / total) * 100)
                    self.progress_var.set(percentage)
                    self.progress_text_var.set(f"Processing item {current} of {total} ({percentage:.1f}%)")
                return
            
            # Look for "Processed: n items" style updates
            processed_match = re.search(r'Processed (\d+) items', line)
            if processed_match:
                count = int(processed_match.group(1))
                self.progress_text_var.set(f"Processed {count} items so far...")
                return
                
        except Exception:
            pass
    
    def setup_color_tags(self) -> None:
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
            if tag == 'bold':
                # Configure bold with both color and font
                self.log_text.tag_configure(tag, foreground=color, font=('Consolas', 9, 'bold'))
            else:
                self.log_text.tag_configure(tag, foreground=color)
        
        # Special tags for formatting
        self.log_text.tag_configure('underline', underline=True)
        self.log_text.tag_configure('progress_bar', background='#1a1a1a', foreground='#00FF41')
        self.log_text.tag_configure('success', foreground='#00FF41', font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure('error', foreground='#FF4444', font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure('warning', foreground='#FFAA00', font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure('info', foreground='#44AAFF')
        
        # Bold color combinations for Rich markup
        self.log_text.tag_configure('bold_green', foreground='#00FF00', font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure('bold_blue', foreground='#5555FF', font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure('bold_red', foreground='#FF5555', font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure('bold_yellow', foreground='#FFFF55', font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure('table_header', foreground='#00FFFF', font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure('table_row', foreground='#CCCCCC')
        self.log_text.tag_configure('black', foreground='#000000')

    def log_message(self, message: str, style: Optional[str] = None) -> None:
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

    def parse_ansi_codes(self, text: str) -> List[tuple[str, str]]:
        """Parse ANSI escape sequences and return segments with styling."""
        import re
        
        # ANSI color code mappings
        ansi_color_map = {
            '30': 'black', '31': 'red', '32': 'green', '33': 'yellow',
            '34': 'blue', '35': 'magenta', '36': 'cyan', '37': 'white',
            '90': 'bright_black', '91': 'bright_red', '92': 'bright_green', '93': 'bright_yellow',
            '94': 'bright_blue', '95': 'bright_magenta', '96': 'bright_cyan', '97': 'bright_white'
        }
        
        segments = []
        current_text = text
        current_styles = []
        
        # Pattern to match all ANSI escape sequences
        ansi_pattern = re.compile(r'\033\[([0-9;?]*)([mABCDEFGHJKSThlf])')
        
        while current_text:
            match = ansi_pattern.search(current_text)
            if match:
                # Add text before the ANSI code
                if match.start() > 0:
                    text_segment = current_text[:match.start()]
                    if text_segment:
                        segments.append((text_segment, current_styles.copy()))
                
                # Only process color codes (ending with 'm')
                if match.group(2) == 'm':
                    codes = match.group(1).split(';') if match.group(1) else ['0']
                    i = 0
                    while i < len(codes):
                        code = codes[i]
                        if code == '0' or code == '':  # Reset
                            current_styles = []
                        elif code == '1':  # Bold
                            if 'bold' not in current_styles:
                                current_styles.append('bold')
                        elif code == '38' and i + 2 < len(codes) and codes[i + 1] == '2':
                            # 24-bit RGB color: 38;2;r;g;b
                            if i + 4 < len(codes):
                                r, g, b = int(codes[i + 2]), int(codes[i + 3]), int(codes[i + 4])
                                # Map common Rich colors to our color scheme
                                if (r, g, b) == (249, 38, 114):  # Rich pink/magenta for progress bars
                                    current_styles = [s for s in current_styles if not s.endswith('_bar')]
                                    current_styles.append('magenta')
                                elif r > 200 and g < 100 and b < 100:  # Reddish
                                    current_styles = [s for s in current_styles if s not in ansi_color_map.values()]
                                    current_styles.append('red')
                                elif r < 100 and g > 200 and b < 100:  # Greenish
                                    current_styles = [s for s in current_styles if s not in ansi_color_map.values()]
                                    current_styles.append('green')
                                elif r < 100 and g < 100 and b > 200:  # Blueish
                                    current_styles = [s for s in current_styles if s not in ansi_color_map.values()]
                                    current_styles.append('blue')
                                elif r > 200 and g > 200 and b < 100:  # Yellowish
                                    current_styles = [s for s in current_styles if s not in ansi_color_map.values()]
                                    current_styles.append('yellow')
                                elif r < 150 and g > 200 and b > 200:  # Cyanish
                                    current_styles = [s for s in current_styles if s not in ansi_color_map.values()]
                                    current_styles.append('cyan')
                                i += 4  # Skip the RGB values
                            else:
                                i += 2
                        elif code in ansi_color_map:  # Standard color
                            # Remove other colors first
                            current_styles = [s for s in current_styles if s not in ansi_color_map.values()]
                            current_styles.append(ansi_color_map[code])
                        i += 1
                
                current_text = current_text[match.end():]
            else:
                # No more ANSI codes, add remaining text
                if current_text:
                    segments.append((current_text, current_styles.copy()))
                break
        
        return segments

    def strip_ansi_codes(self, text: str) -> str:
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
    
    def should_display_line(self, text: str) -> bool:
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

    def parse_rich_markup(self, text: str) -> List[tuple[str, Optional[str]]]:
        """Parse Rich-style markup and return segments with styling."""
        import re
        
        # Rich markup patterns
        patterns = {
            r'\[green\](.*?)\[/green\]': ('green', r'\1'),
            r'\[red\](.*?)\[/red\]': ('red', r'\1'),
            r'\[yellow\](.*?)\[/yellow\]': ('yellow', r'\1'),
            r'\[cyan\](.*?)\[/cyan\]': ('cyan', r'\1'),
            r'\[blue\](.*?)\[/blue\]': ('blue', r'\1'),
            r'\[magenta\](.*?)\[/magenta\]': ('magenta', r'\1'),
            r'\[bold\](.*?)\[/bold\]': ('bold', r'\1'),
            r'\[dim\](.*?)\[/dim\]': ('dim', r'\1'),
            r'\[bold blue\](.*?)\[/bold blue\]': ('bold_blue', r'\1'),
            r'\[bold green\](.*?)\[/bold green\]': ('bold_green', r'\1'),
            r'\[bright_green\](.*?)\[/bright_green\]': ('bright_green', r'\1'),
            r'\[bright_red\](.*?)\[/bright_red\]': ('bright_red', r'\1'),
            r'\[bright_yellow\](.*?)\[/bright_yellow\]': ('bright_yellow', r'\1'),
        }
        
        segments = []
        current_text = text
        
        while current_text:
            earliest_match = None
            earliest_pos = len(current_text)
            
            # Find the earliest pattern match
            for pattern, (style, replacement) in patterns.items():
                match = re.search(pattern, current_text)
                if match and match.start() < earliest_pos:
                    earliest_match = (match, style, replacement)
                    earliest_pos = match.start()
            
            if earliest_match:
                match, style, replacement = earliest_match
                
                # Add text before the match
                if match.start() > 0:
                    segments.append((current_text[:match.start()], None))
                
                # Add the styled text
                styled_text = re.sub(match.re.pattern, replacement, match.group(0))
                segments.append((styled_text, style))
                
                # Continue with the rest
                current_text = current_text[match.end():]
            else:
                # No more patterns, add remaining text
                if current_text:
                    segments.append((current_text, None))
                break
        
        return segments

    def log_rich_output(self, text: str) -> None:
        """Parse and display Rich-formatted text with colors and formatting."""
        # Skip lines that shouldn't be displayed
        if not self.should_display_line(text):
            return
        
        # First try to parse ANSI codes (which is what Rich actually outputs)
        ansi_segments = self.parse_ansi_codes(text)
        
        if ansi_segments and any(styles for _, styles in ansi_segments if styles):
            # We found ANSI codes, use them
            for segment_text, styles in ansi_segments:
                if not segment_text:
                    continue
                
                # Convert ANSI styles to GUI styles
                gui_styles = []
                has_bold = 'bold' in styles if styles else False
                
                for style in (styles or []):
                    if style in ['green', 'red', 'yellow', 'cyan', 'blue', 'magenta', 'bright_green', 'bright_red', 'bright_yellow', 'bright_cyan', 'bright_blue', 'bright_magenta']:
                        if has_bold:
                            # Check if we have a bold variant
                            bold_style = f'bold_{style}'
                            if bold_style in ['bold_green', 'bold_blue', 'bold_red', 'bold_yellow']:
                                gui_styles.append(bold_style)
                            else:
                                gui_styles.extend([style, 'bold'])
                        else:
                            gui_styles.append(style)
                    elif style == 'bold' and not any(c in styles for c in ['green', 'red', 'yellow', 'cyan', 'blue', 'magenta']):
                        gui_styles.append('bold')
                
                # If no specific styles, apply context-based styling
                final_style = gui_styles if gui_styles else None
                if not final_style:
                    context_style = self.detect_content_style(segment_text)
                    if context_style:
                        final_style = [context_style]
                
                # Apply the style - convert single item list to single item
                if isinstance(final_style, list) and len(final_style) == 1:
                    final_style = final_style[0]
                elif isinstance(final_style, list) and len(final_style) == 0:
                    final_style = None
                    
                self.insert_styled_text(segment_text, final_style)
        else:
            # Fallback to Rich markup parsing or smart styling
            clean_text = self.strip_ansi_codes(text)
            
            # Parse Rich markup and apply styling
            segments = self.parse_rich_markup(clean_text)
            
            # If no segments were parsed, handle as plain text with smart styling
            if not segments or (len(segments) == 1 and segments[0][1] is None):
                self.handle_plain_text_with_smart_styling(clean_text)
            else:
                # Handle Rich markup segments
                for segment_text, style in segments:
                    if not segment_text:
                        continue
                        
                    # Apply context-based styling if no specific style
                    if style is None:
                        style = self.detect_content_style(segment_text)
                    
                    self.insert_styled_text(segment_text, style)
        
        # Add newline
        self.insert_styled_text('\n', None)
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def detect_content_style(self, text: str) -> Optional[str]:
        """Detect appropriate style based on text content."""
        if any(indicator in text for indicator in ["✅", "Success"]):
            return 'success'
        elif any(indicator in text for indicator in ["❌", "Error", "Failed"]):
            return 'error'
        elif any(indicator in text for indicator in ["⚠️", "Warning"]):
            return 'warning'
        elif "│" in text or "┌" in text or "├" in text or "└" in text:
            return 'cyan'
        elif "━━━" in text:
            return 'dim'
        elif text.startswith('  🌐') or text.startswith('  📍') or text.startswith('  🏢'):
            return 'info'
        elif text.startswith('Proxy test') or text.startswith('✅ Proxy test'):
            return 'success'
        elif 'External IP:' in text:
            return 'bold_blue'
        elif 'Location:' in text:
            return 'yellow'
        elif 'ISP:' in text:
            return 'magenta'
        elif 'Country Code:' in text:
            return 'green'
        elif 'Timezone:' in text:
            return 'cyan'
        return None

    def handle_plain_text_with_smart_styling(self, text: str) -> None:
        """Handle plain text with smart content-based styling."""
        # Look for patterns in the text to apply appropriate styling
        import re
        
        # Check if this is proxy test output and apply formatting
        if 'External IP:' in text:
            # Split and style different parts
            parts = text.split('External IP:', 1)
            if len(parts) == 2:
                self.insert_styled_text(parts[0] + 'External IP: ', 'info')
                ip_part = parts[1].strip()
                self.insert_styled_text(ip_part, 'bold_blue')
                return
        elif 'Location:' in text:
            parts = text.split('Location:', 1)
            if len(parts) == 2:
                self.insert_styled_text(parts[0] + 'Location: ', 'info')
                location_part = parts[1].strip()
                self.insert_styled_text(location_part, 'yellow')
                return
        elif 'ISP:' in text:
            parts = text.split('ISP:', 1)
            if len(parts) == 2:
                self.insert_styled_text(parts[0] + 'ISP: ', 'info')
                isp_part = parts[1].strip()
                self.insert_styled_text(isp_part, 'magenta')
                return
        elif 'Country Code:' in text:
            parts = text.split('Country Code:', 1)
            if len(parts) == 2:
                self.insert_styled_text(parts[0] + 'Country Code: ', 'info')
                country_part = parts[1].strip()
                self.insert_styled_text(country_part, 'green')
                return
        elif 'Timezone:' in text:
            parts = text.split('Timezone:', 1)
            if len(parts) == 2:
                self.insert_styled_text(parts[0] + 'Timezone: ', 'info')
                timezone_part = parts[1].strip()
                self.insert_styled_text(timezone_part, 'cyan')
                return
        
        # Apply general content-based styling
        style = self.detect_content_style(text)
        self.insert_styled_text(text, style)

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
    
    def insert_styled_text(self, text: str, styles: Union[str, List[str], None]) -> None:
        """Insert text with given styles."""
        if not text:  # Don't process empty text
            return
        
        if styles:
            if isinstance(styles, str):
                styles = [styles]
            # Insert text with immediate style application
            self.log_text.insert(tk.END, text, tuple(styles))
        else:
            # Insert text without styles
            self.log_text.insert(tk.END, text)

    def add_terminal_welcome(self) -> None:
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
        self.insert_styled_text(welcome_text, None)  # Use default white
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
                subprocess.Popen(["explorer", folder])
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


def main() -> None:
    """Run the client generator GUI."""
    app = ClientGeneratorGUI()
    app.run()


if __name__ == "__main__":
    main()