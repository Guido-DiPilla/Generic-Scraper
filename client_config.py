"""
Client configuration system for the Generic Scraper.
Defines scraping targets, field mappings, and parsing rules for different websites/clients.

Each client configuration specifies:
- Base URLs and search patterns
- Field mappings and parsing selectors
- Validation rules and normalization logic
- Custom processing functions

Security:
- No secrets are hardcoded here - all credentials come from .env
- Client configs are declarative and safe to version control

Extensibility:
- To add a new client, create a new ClientConfig instance
- Custom parsing logic can be added via parser functions
- Field mappings are flexible and can be extended per client
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FieldMapping:
    """Configuration for extracting a specific field from HTML."""
    css_selector: str | None = None
    xpath: str | None = None
    attribute: str | None = None  # e.g., 'href', 'data-price'
    regex_pattern: str | None = None
    default_value: str = "Not found"
    transform_func: Callable[[str], str] | None = None


@dataclass(frozen=True)
class ClientConfig:
    """Configuration for a specific scraping client/website."""

    # Client identification
    client_id: str
    client_name: str
    description: str

    # URLs and search configuration
    base_url: str
    search_endpoint: str
    search_param_name: str  # e.g., 'search_query', 'q', 'term'

    # Two-stage scraping (search -> product detail)
    product_link_selector: str  # CSS selector to find product links
    product_link_attribute: str = "href"  # attribute containing product URL

    # Field mappings for data extraction
    field_mappings: dict[str, FieldMapping] = field(default_factory=dict)

    # Validation and normalization
    part_number_regex: str = r'^[\w\-/\.]{1,64}$'
    normalize_part_number: bool = True  # Remove dashes, convert to lowercase
    exact_match_required: bool = True

    # Optional custom parser function
    custom_parser: Callable[..., Any] | None = None

    # Output column names (in desired order)
    output_columns: list[str] = field(default_factory=list)


class ClientRegistry:
    """Registry of available scraping clients."""

    def __init__(self) -> None:
        self._clients: dict[str, ClientConfig] = {}

    def register(self, config: ClientConfig) -> None:
        """Register a new client configuration."""
        self._clients[config.client_id] = config

    def get_client(self, client_id: str) -> ClientConfig | None:
        """Get client configuration by ID."""
        return self._clients.get(client_id)

    def list_clients(self) -> list[ClientConfig]:
        """Get all registered clients."""
        return list(self._clients.values())

    def get_client_ids(self) -> list[str]:
        """Get list of all client IDs."""
        return list(self._clients.keys())


# Global registry instance
registry = ClientRegistry()


def normalize_part_number(part_number: str) -> str:
    """Standard part number normalization: remove dashes, strip slashes, lowercase."""
    return part_number.replace("-", "").rstrip("/").lower().strip()


def extract_numeric_value(text: str) -> str:
    """Extract numeric value from text (useful for prices, quantities)."""
    if not text or text == "Not found":
        return "Not found"

    # Look for numeric patterns (including decimals)
    match = re.search(r'[\d,]+\.?\d*', text.replace(',', ''))
    return match.group(0) if match else "Not found"


def clean_text(text: str) -> str:
    """Clean extracted text by removing extra whitespace and normalizing."""
    if not text or text == "Not found":
        return "Not found"
    return ' '.join(text.strip().split())


# Built-in transform functions
TRANSFORM_FUNCTIONS = {
    'extract_numeric': extract_numeric_value,
    'clean_text': clean_text,
    'normalize_part': normalize_part_number,
}
