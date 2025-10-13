
"""
Async scraping logic for G2S product/inventory, using robust error handling and
custom exceptions.

Security:
- No secrets are hardcoded or logged.
- All credentials must be loaded from environment/config.
- Logging utility masks secrets if present in error messages.

Extensibility:
- To add new scraping targets, implement a new async function and register it in
    the main workflow.
- To add new fields, update the result dict and parsing logic.

Maintainability:
- All functions have type hints and docstrings.
- All exceptions are handled with clear error messages.
- TODOs are marked for future extension points.
"""

import asyncio
import logging
import random
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup, Tag

# Import shim: allow running as a module or as a script without package context
try:  # Prefer package-relative imports
    from .exceptions import FetchError
    from .log_utils import mask_secrets
except ImportError:  # Fallback for direct script execution
    from exceptions import FetchError
    from log_utils import mask_secrets

USER_AGENT = "Mozilla/5.0"

async def fetch(
    session: aiohttp.ClientSession,
    url: str,
    params: Optional[dict[str, str]] = None,
    max_retries: int = 3,
    proxy_url: Optional[str] = None,
    proxy_auth: Optional[aiohttp.BasicAuth] = None,
    request_delay_s: float = 0.0,
) -> tuple[Optional[str], Optional[int]]:
    """
    Asynchronously fetch a URL with retries and exponential backoff.

    Args:
        session: aiohttp ClientSession.
        url: URL to fetch.
        params: Optional query parameters.
        max_retries: Number of retry attempts on failure.

    Returns:
        Tuple of (response text or None, HTTP status or None).

    Raises:
        FetchError: If all retries fail.

    Example:
        async with aiohttp.ClientSession() as session:
            text, status = await fetch(session, 'https://example.com')
    """
    headers = {'User-Agent': USER_AGENT}
    for attempt in range(max_retries):
        try:
            async with session.get(
                url,
                params=params,
                headers=headers,
                proxy=proxy_url,
                proxy_auth=proxy_auth,
            ) as resp:
                text = await resp.text()
                if resp.status == 429:
                    # Honor Retry-After if provided; else exponential backoff with jitter
                    retry_after_hdr = resp.headers.get('Retry-After')
                    if retry_after_hdr and retry_after_hdr.isdigit():
                        sleep_s = max(0, int(retry_after_hdr))
                    else:
                        base = 2 ** attempt
                        jitter = random.uniform(0, 0.5)
                        sleep_s = base + jitter
                    await asyncio.sleep(sleep_s)
                    continue
                # Optional polite delay after successful request (not after retries)
                if request_delay_s > 0:
                    await asyncio.sleep(request_delay_s)
                return text, resp.status
        except aiohttp.ClientError as e:
            safe_msg = mask_secrets(str(e))
            logging.warning(f"HTTP error: {safe_msg}")
            # Exponential backoff with jitter on transport errors
            base = 2 ** attempt
            jitter = random.uniform(0, 0.5)
            await asyncio.sleep(base + jitter)
    raise FetchError(f"Failed to fetch {url} after {max_retries} attempts.")

async def process_part_number(
    session: aiohttp.ClientSession,
    part_number: str,
    semaphore: asyncio.Semaphore,
    proxy_url: Optional[str] = None,
    proxy_auth: Optional[aiohttp.BasicAuth] = None,
    request_delay_s: float = 0.0,
) -> dict[str, str]:
    """
    Scrape and process a single part number from G2S, extracting product info.

    Args:
        session: aiohttp ClientSession.
        part_number: The part number to search for.
        semaphore: Asyncio semaphore for concurrency limiting.

    Returns:
        Dictionary of product info and status fields.

    Raises:
        FetchError: On network errors.
        ParseError: On HTML/data extraction errors.

    Example:
        async with aiohttp.ClientSession() as session:
            result = await process_part_number(session, 'ABC123', semaphore)
    """
    base_url: str = 'https://g2stobeq.ca/search.php'
    result: dict[str, str] = {'Part Number': part_number}
    async with semaphore:
        try:
            text: Optional[str]
            status: Optional[int]
            text, status = await fetch(
                session,
                base_url,
                params={"search_query": part_number},
                proxy_url=proxy_url,
                proxy_auth=proxy_auth,
                request_delay_s=request_delay_s,
            )
            if status != 200 or not text:
                result["Status"] = "Failed"
                return result
            soup = BeautifulSoup(text, "html.parser")
            product_link = soup.find("a", {"data-event-type": "product-click"})
            if not (product_link and isinstance(product_link, Tag)):
                result["Status"] = "Not Found"
                return result
            product_url = product_link.get("href") if product_link.has_attr("href") else None
            if not isinstance(product_url, str):
                result["Status"] = "Product URL not found or invalid"
                return result
            text, status = await fetch(
                session,
                product_url,
                proxy_url=proxy_url,
                proxy_auth=proxy_auth,
                request_delay_s=request_delay_s,
            )
            if status != 200 or not text:
                result["Status"] = "Failed"
                return result
            soup = BeautifulSoup(text, "html.parser")
            result["Status Code"] = str(status)
            product_heading = soup.find("h1", {"class": "productView-title"})
            sku_div = soup.find("div", {"class": "productView-sku"})
            normalized_part: str = part_number.replace("-", "").rstrip("/").lower()
            normalized_heading: str = (
                product_heading.text.replace("-", "").rstrip("/").lower()
                if product_heading and hasattr(product_heading, "text")
                else ""
            )
            sku_span = None
            if sku_div and isinstance(sku_div, Tag):
                found_span = sku_div.find("span")
                if found_span and isinstance(found_span, Tag) and hasattr(found_span, "text"):
                    sku_span = found_span
            normalized_sku: str = (
                sku_span.text.replace("-", "").rstrip("/").lower()
                if sku_span and hasattr(sku_span, "text")
                else ""
            )
            if normalized_part != normalized_sku and normalized_part != normalized_heading:
                result["Status"] = "No Exact Match"
                result["Exists"] = "No"
                return result
            result["Exists"] = "Yes"
            info = soup.find_all(
                ["dt", "dd"], class_=["productView-info-name", "productView-info-value"]
            )
            if info:
                info_dict = dict(
                    zip(
                        [dt.text.strip() if hasattr(dt, "text") else "" for dt in info[::2]],
                        [dd.text.strip() if hasattr(dd, "text") else "" for dd in info[1::2]],
                    )
                )
                montreal: str = info_dict.get("stock-montreal:", "Not found")
                mississauga: str = info_dict.get("stock-mississauga:", "Not found")
                edmonton: str = info_dict.get("stock-edmonton:", "Not found")
                in_stock: list[str] = []
                for loc, qty in [
                    ("Montreal", montreal),
                    ("Mississauga", mississauga),
                    ("Edmonton", edmonton),
                ]:
                    try:
                        if qty != "Not found" and float(qty) > 0:
                            in_stock.append(loc)
                    except Exception:  # noqa: BLE001
                        pass
                result.update(
                    {
                        "Montreal": montreal,
                        "Mississauga": mississauga,
                        "Edmonton": edmonton,
                        "Dropship Item": info_dict.get("Dropship Item:", "Not found"),
                        "LTL - Freight Extra": info_dict.get(
                            "LTL - Freight Extra:", "Not found"
                        ),
                        "Special Order Items": info_dict.get(
                            "Special Order Items:", "Not found"
                        ),
                        "While Quantities Last": info_dict.get(
                            "While Quantities Last:", "Not found"
                        ),
                        "less-than-truckload": info_dict.get(
                            "less-than-truckload:", "Not found"
                        ),
                        "In Stock": ", ".join(in_stock) if in_stock else "Not found",
                        "Price": "Not found",
                    }
                )
            div_tag = soup.find("div", {"class": "productView"})
            price: str = ""
            if div_tag and isinstance(div_tag, Tag):
                price_val = div_tag.get("data-product-price", "")
                if isinstance(price_val, str):
                    price = price_val.strip()
            if price:
                result["Price"] = price
                result["Status"] = "Success"
            else:
                result["Price"] = "Not found"
                result["Status"] = "Failed"
        except FetchError as fe:
            result["Status"] = "FetchError"
            result["Error"] = mask_secrets(str(fe))
        except Exception as e:  # noqa: BLE001
            result["Status"] = "Error"
            result["Error"] = mask_secrets(str(e))
    return result

# TODO: Add support for scraping additional sites by implementing new async functions.
# TODO: Add more granular error types in exceptions.py for better error reporting.

if __name__ == "__main__":
    print("This module contains scraping functions and is not meant to be run directly.")
    print("To run the scraper, use:")
    print("  python generic_scrape.py")
    print("Or run as a module:")
    print("  python -m modern_refactored.refactored")
