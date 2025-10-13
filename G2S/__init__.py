"""
G2S client configuration module.
Contains G2S-specific scraping configuration and registration.
"""

# Import and register G2S client
try:
    from .g2s_client import register_g2s_client
    register_g2s_client()
except ImportError:
    # Fallback for when running as script
    pass