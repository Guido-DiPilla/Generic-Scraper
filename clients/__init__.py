"""
Clients package for the Generic Scraper.
Contains client-specific configurations for different websites.
"""

# Import and register all available clients
try:
    from .g2s_client import register_g2s_client
    from .demo_client import register_demo_client
    from .electronics_supplier import register_electronics_supplier
    from .test_supplier import register_test_supplier
    from .auto_parts_demo import register_auto_parts_demo
    # Add your new clients here:
    # from .my_new_client import register_my_client
    
    register_g2s_client()
    register_demo_client()
    register_electronics_supplier()
    register_test_supplier()
    register_auto_parts_demo()
    # register_my_client()  # Uncomment when you add a new client
except ImportError:
    # Fallback for when running as script
    pass