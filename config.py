"""
Configuration and environment loading for G2S scraper.
Centralizes all config, loads from .env, and validates required fields.

Security:
- All secrets (e.g., proxy credentials) are loaded from environment variables or .env only.
- No secrets are ever logged or hardcoded.

Extensibility:
- To add new config fields, extend the ScraperConfig dataclass and update get_config().
- TODO: Support for additional environment-based config (e.g., API tokens, new endpoints).

Maintainability:
- All config is type-annotated and validated.
- Clear error messages for missing/invalid config.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class ScraperConfig:
    concurrency_limit: int
    chunksize: int
    proxy_username: str
    proxy_password: str
    proxy_host: str
    proxy_url: str
    default_columns: list[str]
    log_file: Path
    log_level: str
    email_notify_to: str
    email_notifications_enabled: bool
    request_delay_s: float
    verify_ssl: bool

def get_config() -> ScraperConfig:
    """
    Loads configuration from .env and environment variables, validates required fields.
    Returns a ScraperConfig dataclass instance.
    """
    load_dotenv()
    concurrency_limit: int = int(os.getenv("CONCURRENCY_LIMIT", 3))
    chunksize: int = int(os.getenv("CHUNKSIZE", 500))
    proxy_username: str = os.getenv("PROXY_USERNAME", "")
    proxy_password: str = os.getenv("PROXY_PASSWORD", "")
    proxy_host: str = os.getenv("PROXY_HOST", "rp.proxyscrape.com:6060")
    proxy_url: str = f"http://{proxy_username}:{proxy_password}@{proxy_host}"
    # Default column names - will be overridden by client-specific configurations
    default_columns: list[str] = [
        "Part Number",
        "Status Code", 
        "Exists",
        "Price",
        "In Stock",
        "Status",
    ]
    log_file: Path = Path(os.getenv("LOG_FILE", "modern_refactored.log"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    email_notify_to: str = os.getenv("EMAIL_NOTIFY_TO", proxy_username)
    email_notifications_enabled: bool = os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "true").lower() in ["true", "1", "yes", "on"]
    # Polite per-request delay in milliseconds (default 150ms) - required to avoid bot detection
    try:
        request_delay_ms_env = os.getenv("REQUEST_DELAY_MS", "150")
        request_delay_ms = int(request_delay_ms_env)
    except Exception:
        request_delay_ms = 150
    request_delay_s: float = max(0.0, request_delay_ms / 1000.0)

    # SSL verification toggle (default true)
    verify_ssl_env = os.getenv("VERIFY_SSL", "true").strip().lower()
    verify_ssl: bool = verify_ssl_env in {"1", "true", "yes", "on"}

    # Proxy validation - use proxy by default when credentials are available
    # If proxy credentials are missing, disable proxy usage with warning
    if not proxy_username or not proxy_password:
        proxy_url = ""  # Empty proxy URL disables proxy usage
        print("Warning: Running without proxy (PROXY_USERNAME/PROXY_PASSWORD not set)")
    else:
        # Proxy credentials found - enable proxy by default
        print(f"Proxy enabled: {proxy_host}")
    
    # For mandatory proxy mode (uncomment if needed):
    # missing = []
    # if not proxy_username:
    #     missing.append("PROXY_USERNAME")
    # if not proxy_password:
    #     missing.append("PROXY_PASSWORD")
    # if missing:
    #     raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return ScraperConfig(
        concurrency_limit=concurrency_limit,
        chunksize=chunksize,
        proxy_username=proxy_username,
        proxy_password=proxy_password,
        proxy_host=proxy_host,
        proxy_url=proxy_url,
        default_columns=default_columns,
        log_file=log_file,
        log_level=log_level,
        email_notify_to=email_notify_to,
        email_notifications_enabled=email_notifications_enabled,
        request_delay_s=request_delay_s,
        verify_ssl=verify_ssl,
    )

# TODO: Add support for loading additional secrets (e.g., API tokens) securely from env only.
