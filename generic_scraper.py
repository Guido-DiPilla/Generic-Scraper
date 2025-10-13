"""
Generic scraper engine that works with client configurations.
Supports pluggable scrapers for different websites while maintaining
the async, robust architecture of the original G2S scraper.

Security:
- No secrets are hardcoded or logged
- All credentials must be loaded from environment/config
- Logging utility masks secrets if present in error messages

Extensibility:
- Client configurations define parsing rules and field mappings
- Custom parser functions can be provided for complex sites
- Easy to add new clients without modifying core scraper logic

Maintainability:
- All functions have type hints and docstrings
- All exceptions are handled with clear error messages
- Generic architecture separates concerns cleanly
"""

import asyncio
import logging
import random
from typing import Optional, Dict, Any
import re

import aiohttp
from bs4 import BeautifulSoup, Tag

# Import shim: allow running as a module or as a script without package context
try:  # Prefer package-relative imports
    from .exceptions import FetchError
    from .log_utils import mask_secrets
    from .client_config import ClientConfig, FieldMapping, normalize_part_number
except ImportError:  # Fallback for direct script execution
    from exceptions import FetchError
    from log_utils import mask_secrets
    from client_config import ClientConfig, FieldMapping, normalize_part_number

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
    This is the same robust fetch function from the original scraper.
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


def extract_field_value(soup: BeautifulSoup, field_mapping: FieldMapping) -> str:
    """
    Extract a field value from HTML using the field mapping configuration.
    
    Args:
        soup: BeautifulSoup parsed HTML
        field_mapping: Configuration for how to extract this field
        
    Returns:
        Extracted and transformed field value or default_value
    """
    try:
        value = field_mapping.default_value
        
        # Extract raw value using CSS selector
        if field_mapping.css_selector:
            elements = soup.select(field_mapping.css_selector)
            if elements:
                element = elements[0]
                if field_mapping.attribute:
                    # Extract from attribute
                    value = element.get(field_mapping.attribute, field_mapping.default_value)
                else:
                    # Extract text content
                    value = element.get_text(strip=True) if hasattr(element, 'get_text') else str(element)
        
        # Apply regex pattern if specified
        if field_mapping.regex_pattern and value != field_mapping.default_value:
            match = re.search(field_mapping.regex_pattern, str(value))
            value = match.group(1) if match and match.groups() else field_mapping.default_value
        
        # Apply transform function if specified
        if field_mapping.transform_func and value != field_mapping.default_value:
            value = field_mapping.transform_func(str(value))
            
        return str(value) if value is not None else field_mapping.default_value
        
    except Exception as e:
        logging.warning(f"Error extracting field: {mask_secrets(str(e))}")
        return field_mapping.default_value


def validate_part_number(part_number: str, config: ClientConfig) -> bool:
    """Validate part number against client-specific regex pattern."""
    if not config.part_number_regex:
        return True
    return bool(re.match(config.part_number_regex, str(part_number).strip()))


def check_exact_match(part_number: str, soup: BeautifulSoup, config: ClientConfig) -> bool:
    """
    Check if the product page represents an exact match for the part number.
    This is a generic version of the G2S exact match logic.
    """
    if not config.exact_match_required:
        return True
        
    # Normalize the input part number
    normalized_input = normalize_part_number(part_number) if config.normalize_part_number else part_number.lower()
    
    # Check product title
    title_element = soup.find("h1", class_="productView-title")
    if title_element and hasattr(title_element, "text"):
        normalized_title = normalize_part_number(title_element.text) if config.normalize_part_number else title_element.text.lower()
        if normalized_input == normalized_title:
            return True
    
    # Check SKU in product view
    sku_div = soup.find("div", class_="productView-sku")
    if sku_div and isinstance(sku_div, Tag):
        sku_span = sku_div.find("span")
        if sku_span and hasattr(sku_span, "text"):
            normalized_sku = normalize_part_number(sku_span.text) if config.normalize_part_number else sku_span.text.lower()
            if normalized_input == normalized_sku:
                return True
    
    return False


async def process_part_number_generic(
    session: aiohttp.ClientSession,
    part_number: str,
    client_config: ClientConfig,
    semaphore: asyncio.Semaphore,
    proxy_url: Optional[str] = None,
    proxy_auth: Optional[aiohttp.BasicAuth] = None,
    request_delay_s: float = 0.0,
) -> Dict[str, str]:
    """
    Generic scraper that processes a part number using client configuration.
    
    Args:
        session: aiohttp ClientSession
        part_number: The part number to search for
        client_config: Client-specific configuration
        semaphore: Asyncio semaphore for concurrency limiting
        proxy_url: Optional proxy URL
        proxy_auth: Optional proxy authentication
        request_delay_s: Delay between requests
        
    Returns:
        Dictionary of extracted data and status fields
    """
    
    # Initialize result with part number and default status
    result: Dict[str, str] = {"Part Number": part_number, "Status": "Failed"}
    
    async with semaphore:
        try:
            # Validate part number format
            if not validate_part_number(part_number, client_config):
                result["Status"] = "Invalid Part Number"
                return result
            
            # Stage 1: Search for the part number
            search_url = f"{client_config.base_url}{client_config.search_endpoint}"
            search_params = {client_config.search_param_name: part_number}
            
            text, status = await fetch(
                session,
                search_url,
                params=search_params,
                proxy_url=proxy_url,
                proxy_auth=proxy_auth,
                request_delay_s=request_delay_s,
            )
            
            if status != 200 or not text:
                result["Status"] = "Search Failed"
                result["Status Code"] = str(status) if status else "Unknown"
                return result
            
            # Parse search results and find product link
            soup = BeautifulSoup(text, "html.parser")
            product_link_element = soup.select_one(client_config.product_link_selector)
            
            if not product_link_element:
                result["Status"] = "Not Found"
                result["Status Code"] = str(status)
                return result
            
            # Extract product URL
            product_url = product_link_element.get(client_config.product_link_attribute)
            if not product_url:
                result["Status"] = "Product URL Not Found"
                result["Status Code"] = str(status)
                return result
            
            # Handle relative URLs
            if product_url.startswith('/'):
                product_url = f"{client_config.base_url}{product_url}"
            elif not product_url.startswith('http'):
                product_url = f"{client_config.base_url}/{product_url}"
            
            # Stage 2: Fetch product details
            text, status = await fetch(
                session,
                product_url,
                proxy_url=proxy_url,
                proxy_auth=proxy_auth,
                request_delay_s=request_delay_s,
            )
            
            if status != 200 or not text:
                result["Status"] = "Product Fetch Failed"
                result["Status Code"] = str(status) if status else "Unknown"
                return result
            
            # Parse product page
            soup = BeautifulSoup(text, "html.parser")
            result["Status Code"] = str(status)
            
            # Check for exact match if required
            if client_config.exact_match_required:
                if not check_exact_match(part_number, soup, client_config):
                    result["Status"] = "No Exact Match"
                    result["Exists"] = "No"
                    return result
            
            result["Exists"] = "Yes"
            
            # Extract all configured fields
            for field_name, field_mapping in client_config.field_mappings.items():
                if field_name not in result:  # Don't override Status Code, etc.
                    result[field_name] = extract_field_value(soup, field_mapping)
            
            # Calculate derived fields (like "In Stock" from inventory levels)
            calculate_derived_fields(result, client_config)
            
            # Determine final status based on extracted data
            if result.get("Price", "Not found") != "Not found":
                result["Status"] = "Success"
            else:
                result["Status"] = "Price Not Found"
                
        except FetchError as fe:
            result["Status"] = "FetchError"
            result["Error"] = mask_secrets(str(fe))
        except Exception as e:
            result["Status"] = "Error"
            result["Error"] = mask_secrets(str(e))
    
    return result


def calculate_derived_fields(result: Dict[str, str], config: ClientConfig) -> None:
    """
    Calculate derived fields like 'In Stock' from inventory data.
    This can be customized per client as needed.
    """
    # Generic "In Stock" calculation from inventory fields
    inventory_fields = ["Montreal", "Mississauga", "Edmonton"]  # Common inventory locations
    in_stock_locations = []
    
    for location in inventory_fields:
        if location in result:
            qty_str = result[location]
            try:
                if qty_str != "Not found" and float(qty_str) > 0:
                    in_stock_locations.append(location)
            except (ValueError, TypeError):
                pass  # Invalid quantity format
    
    result["In Stock"] = ", ".join(in_stock_locations) if in_stock_locations else "Not found"


# Backward compatibility: alias the generic function to match existing code
async def process_part_number(
    session: aiohttp.ClientSession,
    part_number: str,
    semaphore: asyncio.Semaphore,
    proxy_url: Optional[str] = None,
    proxy_auth: Optional[aiohttp.BasicAuth] = None,
    request_delay_s: float = 0.0,
    client_config: Optional[ClientConfig] = None,
) -> Dict[str, str]:
    """
    Backward-compatible wrapper for the generic scraper.
    If no client_config is provided, will use G2S config as default.
    """
    if client_config is None:
        # Import and use G2S config as default for backward compatibility
        try:
            from .G2S.g2s_client import create_g2s_config
            client_config = create_g2s_config()
        except ImportError:
            from G2S.g2s_client import create_g2s_config
            client_config = create_g2s_config()
    
    return await process_part_number_generic(
        session=session,
        part_number=part_number,
        client_config=client_config,
        semaphore=semaphore,
        proxy_url=proxy_url,
        proxy_auth=proxy_auth,
        request_delay_s=request_delay_s,
    )


if __name__ == "__main__":
    print("This module contains generic scraping functions and is not meant to be run directly.")
    print("To run the scraper, use:")
    print("  python app.py")
    print("Or run as a module:")
    print("  python -m generic_scraper")