
"""
Flexible and structured logging utilities for the G2S scraper.
Uses JSON logs by default (requires json-log-formatter).

Security:
- Never log secrets or credentials. Use mask_secrets() before logging any
    error that may contain sensitive info.

Extensibility:
- To add new log handlers (e.g., email, remote), extend setup_logging().
- TODO: Add support for masking additional secret patterns as needed.
"""

import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path


def mask_secrets(msg: str) -> str:
    """
    Mask common secrets in a string for safe logging.
    Extend this function as needed for new secret patterns.
    """
    import os
    # Add more secret patterns as needed
    secrets = [
        os.getenv('PROXY_USERNAME', ''),
        os.getenv('PROXY_PASSWORD', ''),
        os.getenv('EMAIL_USER', ''),
        os.getenv('EMAIL_PASS', ''),
        os.getenv('API_KEY', ''),
        os.getenv('API_TOKEN', ''),
    ]
    # Also mask common patterns
    patterns = [
        r'(?i)api[_-]?key[=: ]+([\w-]+)',
        r'(?i)token[=: ]+([\w-]+)',
        r'(?i)password[=: ]+([\w-]+)',
        r'(?i)pass[=: ]+([\w-]+)',
        r'(?i)secret[=: ]+([\w-]+)',
    ]
    for secret in secrets:
        if secret and secret in msg:
            msg = msg.replace(secret, '***')
    for pat in patterns:
        msg = re.sub(pat, lambda m: m.group(0).replace(m.group(1), '***'), msg)
    return msg

def setup_logging(log_file: Path, log_level: str = "INFO") -> None:
    """
    Set up logging with JSON logs (requires json-log-formatter), rotating file
    handler, and console output.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    handlers = [RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=3)]
    formatter = None
    try:
        import json_log_formatter

        formatter = json_log_formatter.JSONFormatter()
    except Exception:  # noqa: BLE001
        # Graceful fallback to plain text formatter if dependency is missing
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    for handler in handlers:
        handler.setFormatter(formatter)
    logging.basicConfig(level=level, handlers=handlers, force=True)

    # Also log to console at INFO level or above (plain text for human readability)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logging.getLogger().addHandler(console)

# TODO: Add support for remote log aggregation and alerting handlers.
