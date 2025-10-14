"""
Client generation functionality for Generic Scraper GUI.
Handles client code generation, template management, and file operations.
"""

import json
import os
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Callable, Dict, List, Optional


class ClientGenerator:
    """Handles client code generation and template management."""

    def __init__(self, main_app: Any) -> None:
        self.main_app = main_app

    def generate_client_code(self, config: Dict[str, Any]) -> str:
        """Generate the client code based on configuration."""
        client_id = config.get('client_id', 'new_client')
        client_name = config.get('client_name', 'New Client')
        description = config.get('description', 'Auto-generated client')
        base_url = config.get('base_url', '')
        search_url = config.get('search_url', '')
        product_url_template = config.get('product_url_template', '')
        fields = config.get('fields', [])

        # Generate function name
        func_name = f"get_{client_id}_config"
        register_func_name = f"register_{client_id}"

        # Build field mappings
        field_mappings = []
        for field in fields:
            field_name = field.get('name', '')
            css_selector = field.get('css_selector', '')
            attribute = field.get('attribute', 'text')
            required = field.get('required', False)

            field_mappings.append(f"""        FieldMapping(
            name="{field_name}",
            css_selector="{css_selector}",
            attribute="{attribute}",
            required={required}
        )""")

        field_mappings_str = ",\n".join(field_mappings)

        # Generate the complete client code
        code = f'''"""
{client_name} scraper client configuration.
{description}
"""

from client_config import ClientConfig, FieldMapping


def {func_name}() -> ClientConfig:
    """Get configuration for {client_name}."""
    return ClientConfig(
        client_id="{client_id}",
        name="{client_name}",
        description="{description}",
        base_url="{base_url}",
        search_url="{search_url}",
        product_url_template="{product_url_template}",
        part_number_field="{config.get('part_number_field', 'part_number')}",
        search_input_selector="{config.get('search_input_selector', '')}",
        search_button_selector="{config.get('search_button_selector', '')}",
        search_results_selector="{config.get('search_results_selector', '')}",
        product_link_selector="{config.get('product_link_selector', '')}",
        product_link_attribute="{config.get('product_link_attribute', 'href')}",
        headers={{{self._format_headers(config.get('headers', {}))}}},
        field_mappings=[
{field_mappings_str}
        ],
        delay_between_requests={config.get('delay_between_requests', 1.0)},
        max_retries={config.get('max_retries', 3)},
        timeout={config.get('timeout', 30)},
        use_proxy={str(config.get('use_proxy', False))},
        proxy_url="{config.get('proxy_url', '')}",
        proxy_username="{config.get('proxy_username', '')}",
        proxy_password="{config.get('proxy_password', '')}"
    )


def {register_func_name}():
    """Register the {client_name} client."""
    from client_config import register_client
    register_client({func_name}())


# Auto-register when imported
{register_func_name}()
'''
        return code

    def _format_headers(self, headers: Dict[str, str]) -> str:
        """Format headers dictionary for code generation."""
        if not headers:
            return ""

        header_items = []
        for key, value in headers.items():
            header_items.append(f'"{key}": "{value}"')

        return ", ".join(header_items)

    def generate_client(self, config: Dict[str, Any]) -> bool:
        """Generate and save the client file."""
        try:
            client_id = config.get('client_id', '').strip()
            if not client_id:
                messagebox.showerror("Error", "Client ID is required")
                return False

            # Validate client ID format
            if not re.match(r'^[a-z][a-z0-9_]*$', client_id):
                messagebox.showerror(
                    "Error",
                    "Client ID must start with a lowercase letter and contain only lowercase letters, numbers, and underscores"
                )
                return False

            # Generate the client code
            client_code = self.generate_client_code(config)

            # Create clients directory if it doesn't exist
            clients_dir = Path("clients")
            clients_dir.mkdir(exist_ok=True)

            # Save the client file
            client_file = clients_dir / f"{client_id}.py"
            with open(client_file, 'w', encoding='utf-8') as f:
                f.write(client_code)

            # Update __init__.py
            self.update_init_file(client_id)

            messagebox.showinfo("Success", f"Client '{client_id}' generated successfully!")
            return True

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate client: {str(e)}")
            return False

    def update_init_file(self, client_id: str) -> None:
        """Update the clients/__init__.py file to include the new client."""
        init_file = Path("clients") / "__init__.py"

        # Read existing content
        if init_file.exists():
            with open(init_file, encoding='utf-8') as f:
                content = f.read()
        else:
            content = '"""Clients package for Generic Scraper."""\n\n'

        # Check if import already exists
        import_line = f"from .{client_id} import *"
        if import_line not in content:
            # Add the import
            content += f"{import_line}\n"

            # Write back to file
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write(content)

    def save_template(self, config: Dict[str, Any]) -> bool:
        """Save current configuration as a template."""
        try:
            filename = filedialog.asksaveasfilename(
                title="Save Template",
                defaultextension='.json',
                filetypes=[('JSON files', '*.json'), ('All files', '*.*')]
            )

            if filename:
                # Prepare template data
                template_data = dict(config)

                # Save to file
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, indent=2, ensure_ascii=False)

                messagebox.showinfo("Success", f"Template saved to {filename}")
                return True

            return False

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save template: {str(e)}")
            return False

    def load_template(self, on_load_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> bool:
        """Load configuration from a template file."""
        try:
            filename = filedialog.askopenfilename(
                title="Load Template",
                defaultextension='.json',
                filetypes=[('JSON files', '*.json'), ('All files', '*.*')]
            )

            if filename:
                with open(filename, encoding='utf-8') as f:
                    template_data = json.load(f)

                # Call the callback to update the UI
                if on_load_callback:
                    on_load_callback(template_data)

                messagebox.showinfo("Success", f"Template loaded from {filename}")
                return True

            return False

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load template: {str(e)}")
            return False

    def get_existing_clients(self) -> List[str]:
        """Get list of existing client IDs."""
        clients = []
        clients_dir = Path("clients")

        if clients_dir.exists():
            for file_path in clients_dir.glob("*.py"):
                if file_path.name != "__init__.py":
                    client_id = file_path.stem
                    clients.append(client_id)

        return sorted(clients)

    def load_client_config(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Load configuration from an existing client file."""
        try:
            client_file = Path("clients") / f"{client_id}.py"
            if not client_file.exists():
                return None

            # This is a simplified parser - in reality you'd need more sophisticated parsing
            # For now, we'll return a basic structure
            return {
                'client_id': client_id,
                'client_name': client_id.replace('_', ' ').title(),
                'description': f'Configuration loaded from {client_id}.py',
                'base_url': '',
                'search_url': '',
                'fields': []
            }

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load client config: {str(e)}")
            return None


class FileManager:
    """Handles file browsing and management operations."""

    def __init__(self, main_app: Any) -> None:
        self.main_app = main_app

    def browse_input_file(self, file_var: tk.StringVar) -> str:
        """Browse for input CSV file."""
        filename = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            file_var.set(filename)
        return filename

    def browse_output_file(self, file_var: tk.StringVar) -> str:
        """Browse for output CSV file location."""
        filename = filedialog.asksaveasfilename(
            title="Save Results As",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            file_var.set(filename)
        return filename

    def validate_input_file(self, filename: str) -> bool:
        """Validate that the input file exists and is readable."""
        if not filename:
            return False

        try:
            path = Path(filename)
            return path.exists() and path.is_file() and path.suffix.lower() == '.csv'
        except Exception:
            return False

    def validate_output_path(self, filename: str) -> bool:
        """Validate that the output path is writable."""
        if not filename:
            return False

        try:
            path = Path(filename)
            # Check if directory exists and is writable
            parent_dir = path.parent
            return parent_dir.exists() and os.access(parent_dir, os.W_OK)
        except Exception:
            return False
