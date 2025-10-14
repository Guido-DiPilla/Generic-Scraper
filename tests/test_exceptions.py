"""
Unit tests for exceptions.py
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from exceptions import ScraperError, ConfigError, ProxyError, FetchError, ParseError, EmailError

def test_scraper_error():
    with pytest.raises(ScraperError):
        raise ScraperError("Base error")

def test_config_error():
    with pytest.raises(ConfigError):
        raise ConfigError("Config error")

def test_proxy_error():
    with pytest.raises(ProxyError):
        raise ProxyError("Proxy error")

def test_fetch_error():
    with pytest.raises(FetchError):
        raise FetchError("Fetch error")

def test_parse_error():
    with pytest.raises(ParseError):
        raise ParseError("Parse error")

def test_email_error():
    with pytest.raises(EmailError):
        raise EmailError("Email error")
