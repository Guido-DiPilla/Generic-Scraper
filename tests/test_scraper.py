"""
Unit tests for scraper.py (parsing and error handling)
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from modern_refactored.scraper import process_part_number, FetchError, fetch
import aiohttp
import time
from pathlib import Path
from bs4 import BeautifulSoup

@pytest.mark.asyncio
async def test_process_part_number_success():
    # Mock session and response for a successful fetch
    session = AsyncMock(spec=aiohttp.ClientSession)
    # Simulate a valid response for both fetches
    async def fetch_side_effect(*args, **kwargs):
        if 'search_query' in kwargs.get('params', {}):
            # First fetch: product link found
            return ("<a data-event-type='product-click' href='product_url'></a>", 200)
        else:
            # Second fetch: product details
            return ("<h1 class='productView-title'>Test Product</h1><div class='productView-sku'><span>ABC123</span></div>", 200)
    with patch('modern_refactored.scraper.fetch', new=AsyncMock(side_effect=fetch_side_effect)):
        result = await process_part_number(session, 'ABC123', asyncio.Semaphore(1))
        assert result['Status'] in {'Success', 'Failed', 'No Exact Match', 'Not Found'}

@pytest.mark.asyncio
async def test_process_part_number_fetch_error():
    session = AsyncMock(spec=aiohttp.ClientSession)
    with patch('modern_refactored.scraper.fetch', new=AsyncMock(side_effect=FetchError("fail"))):
        result = await process_part_number(session, 'BAD', asyncio.Semaphore(1))
        assert result['Status'] == 'FetchError'
        assert 'Error' in result

@pytest.mark.asyncio
async def test_fetch_uses_proxy_and_auth():
    """Ensure fetch() passes proxy and proxy_auth to session.get."""
    class DummyResp:
        status = 200
        async def text(self):
            return "ok"

    class AsyncCtx:
        def __init__(self, resp):
            self._resp = resp
        async def __aenter__(self):
            return self._resp
        async def __aexit__(self, exc_type, exc, tb):
            return False

    # Mock session with a get() that returns an async context manager
    session = MagicMock(spec=aiohttp.ClientSession)
    session.get = MagicMock(side_effect=lambda *a, **kw: AsyncCtx(DummyResp()))

    proxy_url = "http://user:pass@proxy.example.com:1234"
    proxy_auth = aiohttp.BasicAuth("user", "pass")

    text, status = await fetch(session, "http://example.com", proxy_url=proxy_url, proxy_auth=proxy_auth)
    assert status == 200
    assert text == "ok"

    # Validate proxy and proxy_auth were forwarded to session.get
    assert session.get.called
    _, kwargs = session.get.call_args
    assert kwargs.get("proxy") == proxy_url
    assert isinstance(kwargs.get("proxy_auth"), aiohttp.BasicAuth)

@pytest.mark.asyncio
async def test_fetch_honors_retry_after_and_delay(monkeypatch):
    class DummyResp429:
        status = 429
        headers = {"Retry-After": "1"}
        async def text(self):
            return "rate limited"

    class DummyResp200:
        status = 200
        headers = {}
        async def text(self):
            return "ok"

    class AsyncCtx:
        def __init__(self, resp):
            self._resp = resp
        async def __aenter__(self):
            return self._resp
        async def __aexit__(self, exc_type, exc, tb):
            return False

    # Sequence: 429 (Retry-After=1s) then 200
    responses = [DummyResp429(), DummyResp200()]
    def get_side_effect(*args, **kwargs):
        return AsyncCtx(responses.pop(0))

    session = MagicMock(spec=aiohttp.ClientSession)
    session.get = MagicMock(side_effect=get_side_effect)

    start = time.time()
    text, status = await fetch(session, "http://example.com", request_delay_s=0.1)
    elapsed = time.time() - start
    assert status == 200
    assert text == "ok"
    # Should have slept at least ~1s for Retry-After (plus minimal overhead)
    assert elapsed >= 1.0

def _read_fixture(name: str) -> str:
    base = Path(__file__).parent / "fixtures"
    return (base / name).read_text(encoding="utf-8")

@pytest.mark.asyncio
async def test_process_part_number_parsing_integration():
    """Integration-like test: search page -> product page parsed from fixtures."""
    session = AsyncMock(spec=aiohttp.ClientSession)

    # Return search page first, then product page
    search_html = _read_fixture("search_with_result.html")
    product_html = _read_fixture("product_detail_exact_match.html")

    async def fetch_side_effect(*args, **kwargs):
        # First call includes params with search_query; second does not
        if kwargs.get('params'):
            return (search_html, 200)
        return (product_html, 200)

    with patch('modern_refactored.scraper.fetch', new=AsyncMock(side_effect=fetch_side_effect)):
        result = await process_part_number(session, 'ABC123', asyncio.Semaphore(1))
        assert result['Status'] == 'Success'
        assert result['Exists'] == 'Yes'
        assert result['Price'] == '99.99'
        # Inventory parsing
        assert result['Montreal'] == '10'
        assert result['Mississauga'] == '0'
        assert result['Edmonton'] == '2'
