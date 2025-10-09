"""
Custom exception classes for the G2S scraper project.
Provides clear, consistent error handling across all modules.

Security:
- Never include secrets or credentials in exception messages.

Extensibility:
- To add new error types, subclass ScraperError below.
- TODO: Add more granular error types for new modules as needed.

Maintainability:
- All exceptions should be type-annotated and documented.
"""

class ScraperError(Exception):
    """Base exception for all scraper-related errors."""
    pass

class ConfigError(ScraperError):
    """Raised for configuration or environment errors."""
    pass

class ProxyError(ScraperError):
    """Raised for proxy connection or authentication errors."""
    pass

class FetchError(ScraperError):
    """Raised for HTTP/network errors during scraping."""
    pass

class ParseError(ScraperError):
    """Raised for HTML parsing or data extraction errors."""
    pass

class EmailError(ScraperError):
    """Raised for email notification failures."""
    pass
