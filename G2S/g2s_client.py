"""
G2S Client Configuration
Defines the scraping configuration for G2S (g2stobeq.ca) website.
"""

try:
    from ..client_config import TRANSFORM_FUNCTIONS, ClientConfig, FieldMapping, registry
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from client_config import TRANSFORM_FUNCTIONS, ClientConfig, FieldMapping, registry


def create_g2s_config() -> ClientConfig:
    """Create and return G2S client configuration."""

    # Define field mappings for G2S-specific data extraction
    field_mappings = {
        # Basic product info
        "Status Code": FieldMapping(
            default_value="200"  # Will be populated by scraper logic
        ),
        "Exists": FieldMapping(
            default_value="No"  # Will be set to "Yes" if exact match found
        ),
        "Price": FieldMapping(
            css_selector="div.productView",
            attribute="data-product-price",
            transform_func=TRANSFORM_FUNCTIONS['extract_numeric']
        ),

        # Inventory levels
        "Montreal": FieldMapping(
            css_selector="dt:-soup-contains('stock-montreal:') + dd",
            transform_func=TRANSFORM_FUNCTIONS['extract_numeric']
        ),
        "Mississauga": FieldMapping(
            css_selector="dt:-soup-contains('stock-mississauga:') + dd",
            transform_func=TRANSFORM_FUNCTIONS['extract_numeric']
        ),
        "Edmonton": FieldMapping(
            css_selector="dt:-soup-contains('stock-edmonton:') + dd",
            transform_func=TRANSFORM_FUNCTIONS['extract_numeric']
        ),

        # Product flags
        "Dropship Item": FieldMapping(
            css_selector="dt:-soup-contains('Dropship Item:') + dd",
            transform_func=TRANSFORM_FUNCTIONS['clean_text']
        ),
        "LTL - Freight Extra": FieldMapping(
            css_selector="dt:-soup-contains('LTL - Freight Extra:') + dd",
            transform_func=TRANSFORM_FUNCTIONS['clean_text']
        ),
        "Special Order Items": FieldMapping(
            css_selector="dt:-soup-contains('Special Order Items:') + dd",
            transform_func=TRANSFORM_FUNCTIONS['clean_text']
        ),
        "While Quantities Last": FieldMapping(
            css_selector="dt:-soup-contains('While Quantities Last:') + dd",
            transform_func=TRANSFORM_FUNCTIONS['clean_text']
        ),
        "less-than-truckload": FieldMapping(
            css_selector="dt:-soup-contains('less-than-truckload:') + dd",
            transform_func=TRANSFORM_FUNCTIONS['clean_text']
        ),
    }

    # Define output columns in desired order
    output_columns = [
        "Part Number",
        "Status Code",
        "Exists",
        "Price",
        "Montreal",
        "Mississauga",
        "Edmonton",
        "Dropship Item",
        "LTL - Freight Extra",
        "Special Order Items",
        "While Quantities Last",
        "less-than-truckload",
        "In Stock",
        "Status",
    ]

    return ClientConfig(
        client_id="g2s",
        client_name="G2S Equipment",
        description="G2S Equipment product and inventory scraper (g2stobeq.ca)",
        base_url="https://g2stobeq.ca",
        search_endpoint="/search.php",
        search_param_name="search_query",
        product_link_selector='a[data-event-type="product-click"]',
        product_link_attribute="href",
        field_mappings=field_mappings,
        part_number_regex=r'^[\w\-/\.]{1,64}$',
        normalize_part_number=True,
        exact_match_required=True,
        output_columns=output_columns,
        custom_parser=None  # Will use generic parser with field mappings
    )


def register_g2s_client() -> None:
    """Register G2S client in the global registry."""
    config = create_g2s_config()
    registry.register(config)


# Auto-register when module is imported
register_g2s_client()
