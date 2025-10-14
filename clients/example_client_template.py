"""
Example Client Configuration Template
Copy this file and modify it to add support for new websites.

This example shows how to create a client configuration for a hypothetical
"Example Corp" website that sells electronic components.
"""

try:
    from ..client_config import TRANSFORM_FUNCTIONS, ClientConfig, FieldMapping, registry
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from client_config import TRANSFORM_FUNCTIONS, ClientConfig, FieldMapping, registry


def create_example_config() -> ClientConfig:
    """
    Create client configuration for Example Corp website.

    This is a template showing how to configure a client for a typical
    e-commerce site with search functionality and product detail pages.
    """

    # Define field mappings for data extraction
    field_mappings = {
        # Basic product info
        "Status Code": FieldMapping(
            default_value="200"  # Will be populated by scraper logic
        ),
        "Exists": FieldMapping(
            default_value="No"  # Will be set to "Yes" if exact match found
        ),

        # Price extraction - look for price in common locations
        "Price": FieldMapping(
            css_selector=".price, .product-price, [data-price]",
            attribute="data-price",  # Try data attribute first
            regex_pattern=r'[\d,]+\.?\d*',  # Extract numeric price
            transform_func=TRANSFORM_FUNCTIONS['extract_numeric'],
            default_value="Not found"
        ),

        # Availability/Stock status
        "In Stock": FieldMapping(
            css_selector=".stock-status, .availability",
            transform_func=TRANSFORM_FUNCTIONS['clean_text'],
            default_value="Not found"
        ),

        # Product description
        "Description": FieldMapping(
            css_selector=".product-description, .description",
            transform_func=TRANSFORM_FUNCTIONS['clean_text'],
            default_value="Not found"
        ),

        # Manufacturer/Brand
        "Brand": FieldMapping(
            css_selector=".brand, .manufacturer",
            transform_func=TRANSFORM_FUNCTIONS['clean_text'],
            default_value="Not found"
        ),

        # Product category
        "Category": FieldMapping(
            css_selector=".breadcrumb li:last-child, .category",
            transform_func=TRANSFORM_FUNCTIONS['clean_text'],
            default_value="Not found"
        ),
    }

    # Define output columns in desired order
    output_columns = [
        "Part Number",
        "Status Code",
        "Exists",
        "Price",
        "In Stock",
        "Description",
        "Brand",
        "Category",
        "Status",
    ]

    return ClientConfig(
        client_id="example_corp",
        client_name="Example Corp",
        description="Example Corp electronic components (example.com)",

        # Website URLs and search configuration
        base_url="https://example.com",
        search_endpoint="/search",
        search_param_name="q",  # URL parameter for search query

        # How to find product links in search results
        product_link_selector="a.product-link, .product-title a",
        product_link_attribute="href",

        # Field extraction configuration
        field_mappings=field_mappings,

        # Part number validation
        part_number_regex=r'^[\w\-/\.]{1,50}$',  # Alphanumeric, dashes, slashes, dots
        normalize_part_number=True,  # Remove dashes, lowercase for comparison
        exact_match_required=True,   # Require exact match between search and product

        # Output configuration
        output_columns=output_columns,

        # Custom parser (None = use generic parser)
        custom_parser=None
    )


def register_example_client() -> None:
    """Register the example client in the global registry."""
    config = create_example_config()
    registry.register(config)


# Uncomment the line below to auto-register when module is imported
# register_example_client()


if __name__ == "__main__":
    # Test the configuration
    config = create_example_config()
    print(f"Client: {config.client_name}")
    print(f"Search URL: {config.base_url}{config.search_endpoint}")
    print(f"Fields to extract: {list(config.field_mappings.keys())}")
    print(f"Output columns: {config.output_columns}")
