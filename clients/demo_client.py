"""
Demo Client Configuration - Simple Example
A minimal working example for demonstration purposes.

This client demonstrates scraping a simple product catalog site
with basic search and product detail pages.
"""

try:
    from ..client_config import TRANSFORM_FUNCTIONS, ClientConfig, FieldMapping, registry
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from client_config import TRANSFORM_FUNCTIONS, ClientConfig, FieldMapping, registry


def create_demo_config() -> ClientConfig:
    """Create a demo client configuration for testing purposes."""

    field_mappings = {
        "Status Code": FieldMapping(default_value="200"),
        "Exists": FieldMapping(default_value="No"),
        "Price": FieldMapping(
            css_selector=".price",
            transform_func=TRANSFORM_FUNCTIONS['extract_numeric']
        ),
        "Title": FieldMapping(
            css_selector="h1, .title",
            transform_func=TRANSFORM_FUNCTIONS['clean_text']
        ),
        "Stock": FieldMapping(
            css_selector=".stock",
            transform_func=TRANSFORM_FUNCTIONS['clean_text']
        ),
    }

    output_columns = [
        "Part Number",
        "Status Code",
        "Exists",
        "Price",
        "Title",
        "Stock",
        "Status"
    ]

    return ClientConfig(
        client_id="demo",
        client_name="Demo Client",
        description="Simple demo client for testing the generic scraper framework",
        base_url="https://demo-products.com",
        search_endpoint="/search",
        search_param_name="search",
        product_link_selector=".product-link",
        product_link_attribute="href",
        field_mappings=field_mappings,
        part_number_regex=r'^[\w\-]{1,32}$',
        normalize_part_number=True,
        exact_match_required=False,  # More lenient matching for demo
        output_columns=output_columns,
    )


def register_demo_client() -> None:
    """Register Demo client in the global registry."""
    config = create_demo_config()
    registry.register(config)


# Auto-register when module is imported (uncomment for real use)
register_demo_client()
