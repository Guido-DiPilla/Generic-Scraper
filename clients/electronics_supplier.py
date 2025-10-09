"""
Electronics Supplier Client Configuration
Example client for a hypothetical electronics parts website.
"""

try:
    from ..client_config import ClientConfig, FieldMapping, registry, TRANSFORM_FUNCTIONS
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from client_config import ClientConfig, FieldMapping, registry, TRANSFORM_FUNCTIONS


def create_electronics_supplier_config() -> ClientConfig:
    """Create client config for Electronics Supplier website."""
    
    field_mappings = {
        "Status Code": FieldMapping(default_value="200"),
        "Exists": FieldMapping(default_value="No"),
        
        # Price extraction
        "Price": FieldMapping(
            css_selector=".product-price, .price, [data-price]",
            attribute="data-price",
            transform_func=TRANSFORM_FUNCTIONS['extract_numeric']
        ),
        
        # Stock availability
        "Stock Status": FieldMapping(
            css_selector=".stock-info, .availability",
            transform_func=TRANSFORM_FUNCTIONS['clean_text']
        ),
        
        # Manufacturer
        "Manufacturer": FieldMapping(
            css_selector=".brand, .manufacturer",
            transform_func=TRANSFORM_FUNCTIONS['clean_text']
        ),
        
        # Description
        "Description": FieldMapping(
            css_selector=".product-description, .description p",
            transform_func=TRANSFORM_FUNCTIONS['clean_text']
        ),
    }
    
    output_columns = [
        "Part Number",
        "Status Code",
        "Exists",
        "Price", 
        "Stock Status",
        "Manufacturer",
        "Description",
        "Status"
    ]
    
    return ClientConfig(
        client_id="electronics_supplier",
        client_name="Electronics Supplier",
        description="Electronic components supplier (electronics-supplier.com)",
        base_url="https://electronics-supplier.com",
        search_endpoint="/search",
        search_param_name="query",
        product_link_selector=".product-item a, .search-result-link",
        field_mappings=field_mappings,
        part_number_regex=r'^[A-Z0-9\-]{3,20}$',
        normalize_part_number=True,
        exact_match_required=True,
        output_columns=output_columns
    )


def register_electronics_supplier():
    """Register electronics supplier client."""
    config = create_electronics_supplier_config()
    registry.register(config)


# Auto-register (uncomment to activate)
register_electronics_supplier()