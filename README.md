# Generic Multi-Client Web Scraper

A robust, async, and modular Python scraper framework that evolved from a single-purpose G2S scraper into a comprehensive multi-client platform. Built for enterprise reliability with beautiful UI and easy extensibility.

## 🚀 Features

### **Multi-Client Architecture**
- **Plugin-based clients**: Each website gets its own configuration module
- **GUI Client Generator**: Visual tool for creating new scrapers
- **CLI Client Generator**: Command-line tool for headless environments  
- **Auto-discovery**: New clients appear instantly in menus
- **5 Built-in Examples**: G2S, Demo, Electronics, Test, Auto Parts clients

### **Professional Scraping Engine**
- **Async/concurrent processing** with configurable limits
- **Proxy support** with authentication and rotation
- **Rate limiting** with exponential backoff and retry logic
- **Resume functionality** to continue interrupted sessions
- **Two-stage scraping**: Search → Product detail extraction
- **Exact match validation** with configurable normalization

### **Rich User Experience**
- **Beautiful terminal UI** with Rich progress bars and colors
- **GUI/CLI file selection** with automatic fallbacks
- **Real-time progress tracking** with detailed per-item output
- **Multiple output formats**: CSV, JSON, Excel
- **Email notifications** when jobs complete
- **Comprehensive error reporting** with masked secrets

### **Enterprise Features**
- **Streaming I/O**: Process large datasets without memory issues
- **Atomic operations**: No data corruption from interruptions
- **Schema validation**: Input/output format checking
- **Comprehensive logging**: JSON-structured with secret masking
- **Configuration management**: Environment-based secrets
- **Type safety**: Full type hints and validation throughout

## 📦 Installation & Setup

### **Prerequisites**
- Python 3.11+ (recommended)
- Virtual environment support

### **Quick Setup**
```bash
# Clone the repository
git clone <repository-url>
cd generic_scraper

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env configuration file
cp .env.example .env
# Edit .env with your proxy credentials and settings
```

### **Environment Configuration**
Create a `.env` file with your settings:
```env
# Proxy Configuration (Required)
PROXY_USERNAME=your_proxy_username
PROXY_PASSWORD=your_proxy_password
PROXY_HOST=proxy.example.com:1234

# Scraping Settings
CONCURRENCY_LIMIT=3
CHUNKSIZE=500
REQUEST_DELAY_MS=150
VERIFY_SSL=true

# Logging
LOG_FILE=scraper.log
LOG_LEVEL=INFO

# Email Notifications (Optional)
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
EMAIL_NOTIFY_TO=notifications@example.com
```

## 🎯 Quick Start

### **GUI Interface (Primary Method)**
```bash
# Launch the graphical interface
./venv/bin/python generate_client.py
# or
./venv/bin/python client_generator.py
```

The GUI provides:
- **File selection dialogs** for input/output CSV files
- **Client selection dropdown** with all available scrapers
- **Proxy configuration** with credential management
- **Real-time progress tracking** with colorized terminal output
- **Advanced settings** for concurrency, timeouts, and email notifications

### **Command Line (For Automation)**
```bash
# Direct execution with all parameters
./venv/bin/python app.py --client g2s --input-csv parts.csv --output-csv results.csv

# With all options
./venv/bin/python app.py \
  --client g2s \
  --input-csv input/parts.csv \
  --output-csv output/results.csv \
  --output-format excel \
  --resume \
  --log-level DEBUG
```

## 🛠️ Adding New Clients

The framework provides **three methods** for adding new scraping clients:

### **Method 1: GUI Client Generator (Recommended)**
```bash
./venv/bin/python generate_client.py
```

**Features:**
- 📱 Beautiful tabbed interface
- ✅ Real-time input validation  
- 🎨 CSS selector help and examples
- 📋 Interactive field mapping editor
- 👀 Live code preview
- 💾 Save/load templates
- 🚀 One-click client generation

### **Manual Method (Advanced Users)**
For advanced users who prefer manual configuration:
1. Copy `clients/example_client_template.py`
2. Modify the configuration for your website  
3. Add import/registration to `clients/__init__.py`

### **Method 3: Manual Configuration (Advanced)**
1. Copy `clients/example_client_template.py`
2. Modify for your website
3. Add import to `clients/__init__.py`

## 🏗️ Architecture Overview

### Core Components
- **`app.py`**: Main entry point with client selection, processing loop, progress tracking
- **`generic_scraper.py`**: Generic async scraping engine that works with any client config
- **`client_config.py`**: Client configuration system and field mapping definitions
- **`clients/`**: Directory containing individual client configurations
- **`config.py`**: Application config (proxy, concurrency, logging) from `.env`
- **`io_utils.py`**: CSV streaming, atomic writes, schema validation, summary reports
- **`ui.py`**: Rich CLI interface with file dialogs and progress bars
- **`log_utils.py`**: Structured logging with secret masking
- **`email_utils.py`**: Email notifications for completed scraping jobs
- **`exceptions.py`**: Custom exception classes for different error types

### Client Configuration System
Each client is defined by:
- **URLs**: Base URL, search endpoint, search parameter names
- **Selectors**: CSS selectors for finding product links and extracting data
- **Field mappings**: How to extract and transform each piece of data
- **Validation rules**: Part number format, exact match requirements
- **Output schema**: Column names and order for results

### Processing Flow
1. **Client Selection**: Choose which website to scrape
2. **Input Processing**: Read part numbers from CSV in chunks
3. **Two-Stage Scraping**: Search → Product Detail page extraction
4. **Data Extraction**: Use client-specific field mappings to extract data
5. **Validation**: Check for exact matches, validate extracted data
6. **Output**: Save results incrementally with resume capabilityed for G2S product/inventory scraping, now generalized to work with any e-commerce or product catalog website.

## Features
- **Multi-Client Support**: Configure scrapers for different websites using declarative client configs
- **Async scraping** with proxy support and rate limiting
- **Rich CLI/GUI interface** with beautiful progress bars and file selection
- **Streaming CSV I/O** for processing large datasets efficiently
- **Resume functionality** to continue interrupted scraping sessions
- **Multiple output formats**: CSV, JSON, Excel
- **Robust error handling** with retry logic and exponential backoff
- **Secure**: No secrets hardcoded or logged, all credentials from environment
- **Extensible**: Easy to add new websites/clients with minimal code
- **Type checking, linting, formatting** enforced for code quality

## Setup
1. **Python 3.11+ recommended**
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv myvenv
   source myvenv/bin/activate
   ```
3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your credentials.

## .env Configuration
All secrets and config are loaded from `.env` or environment variables. Example:
```
CONCURRENCY_LIMIT=3
CHUNKSIZE=500
PROXY_USERNAME=your_proxy_user
PROXY_PASSWORD=your_proxy_pass
PROXY_HOST=rp.proxyscrape.com:6060
LOG_FILE=modern_refactored.log
LOG_LEVEL=INFO
EMAIL_NOTIFY_TO=your@email.com
```

## Quick Start

### 1. Launch the GUI
```bash
# Start the graphical interface
python generate_client.py
```

### 2. Configure Scraping
In the GUI:
- **Select client** from the dropdown (G2S, Demo, etc.)
- **Choose input CSV** file containing part numbers
- **Set output location** for results
- **Configure proxy** settings if needed
- **Adjust advanced settings** like concurrency and email notifications

### 3. Run and Monitor
- Click "Start Scraping" to begin
- **Real-time progress** updates in the terminal display  
- **Colorized output** shows status, errors, and results
- **Email notification** when complete (if enabled)

## Adding New Clients

To add support for a new website, create a client configuration:

### 1. Create Client Config File
```python
# clients/my_new_client.py
from ..client_config import ClientConfig, FieldMapping, registry, TRANSFORM_FUNCTIONS

def create_my_client_config():
    field_mappings = {
        "Price": FieldMapping(
            css_selector=".price",
            transform_func=TRANSFORM_FUNCTIONS['extract_numeric']
        ),
        "Stock": FieldMapping(
            css_selector=".stock-level",
            transform_func=TRANSFORM_FUNCTIONS['clean_text']
        ),
    }
    
    return ClientConfig(
        client_id="my_client",
        client_name="My Website",
        description="Product scraper for my-website.com",
        base_url="https://my-website.com",
        search_endpoint="/search",
        search_param_name="q",
        product_link_selector=".product-link",
        field_mappings=field_mappings,
        output_columns=["Part Number", "Price", "Stock", "Status"]
    )

def register_my_client():
    registry.register(create_my_client_config())

register_my_client()  # Auto-register when imported
```

### 2. Import in clients/__init__.py
```python
from .my_new_client import register_my_client
register_my_client()
```

That's it! Your new client will appear in the selection menu.

### Example .env
```
CONCURRENCY_LIMIT=3
CHUNKSIZE=500
PROXY_USERNAME=your_proxy_user
PROXY_PASSWORD=your_proxy_pass
PROXY_HOST=rp.proxyscrape.com:6060
LOG_FILE=modern_refactored.log
LOG_LEVEL=INFO
EMAIL_NOTIFY_TO=your@email.com
```

## Troubleshooting

- **Import errors in VS Code:** Ensure you run from the Modern_Refactored folder, and use local imports (already set up).
- **Proxy errors:** Double-check your proxy credentials and network access. Use the built-in proxy test (runs at startup).
- **Email errors:** Make sure EMAIL_USER and EMAIL_PASS are set in your .env if using notifications.
- **Async test failures:** If pytest-asyncio is not installed, run `pip install pytest-asyncio`.
- **File dialog not appearing:** If tkinter is not available, the script will fall back to CLI input.
- **Typer errors:** The application requires Typer 0.19.2 or higher. If you encounter errors like "Secondary flag is not valid for non-boolean flag", upgrade Typer with `pip install -U typer`.

## Architecture Overview

- Quick “what does what” cheatsheet:
  - `app.py`: Main entry; wires config, logging, proxy test, processing loop, saving, summary, email.
  - `__main__.py`: Lets you run with `python -m modern_refactored`.
  - `config.py`: Loads and validates config from `.env` (concurrency, proxy, logging, email, etc.).
  - `scraper.py`: Async HTTP + HTML parsing for each part number; returns a result dict per item.
  - `io_utils.py`: CSV streaming read, atomic write, input/output schema validation, summary text.
  - `log_utils.py`: Logging setup + secret masking helpers.
  - `ui.py`: File pickers and progress bars using `rich` (CLI fallback if tkinter not available).
  - `email_utils.py`: Optional email notification via SMTP creds in env.
  - `exceptions.py`: Project-specific exception classes.

All modules are type-annotated and have docstrings for public functions/classes.

## Available Clients

### G2S Equipment (`g2s`)
- **Website**: g2stobeq.ca
- **Features**: Product search, inventory levels (Montreal/Mississauga/Edmonton), pricing
- **Fields**: Price, inventory by location, product flags (dropship, special order, etc.)
- **Status**: Production ready

### Demo Client (`demo`) 
- **Website**: demo-products.com (example)
- **Features**: Basic product search and pricing
- **Fields**: Price, title, stock status
- **Status**: Template/example only

## Extending & Customizing

### Adding New Fields to Existing Clients
Modify the `field_mappings` in the client configuration:
```python
field_mappings["New Field"] = FieldMapping(
    css_selector=".new-field-selector",
    transform_func=TRANSFORM_FUNCTIONS['clean_text']
)
```

### Custom Transform Functions
Add new data transformation functions:
```python
def extract_date(text: str) -> str:
    # Custom date extraction logic
    return formatted_date

TRANSFORM_FUNCTIONS['extract_date'] = extract_date
```

### Complex Custom Parsing
For sites requiring complex parsing logic, implement a custom parser:
```python
async def custom_parser(soup, part_number, config):
    # Custom parsing logic here
    return result_dict

# Set in client config
ClientConfig(..., custom_parser=custom_parser)
```

## Support

For issues, open an issue on GitHub or contact the maintainer.

## Testing & Code Quality
- Run all tests:
  ```bash
  pytest
  ```
- Type check:
  ```bash
  mypy .
  ```
- Lint:
  ```bash
  ruff .
  ```
- Format:
  ```bash
  black .
  ```

## Security & Extensibility
- No secrets are ever hardcoded or logged.
- All config is centralized in `config.py`.
- To add new scraping targets or fields, see TODOs in each module.

## Contributing
See `CONTRIBUTING.md` for guidelines.

---

*See each module for further documentation and extension points.*
