#!/usr/bin/env python3
"""
Environment Variable Validator for Generic-Scraper

This script validates that all required environment variables are set
and provides warnings for missing optional variables.

Usage:
    python validate_env.py

If using email notifications, make sure EMAIL_USER, EMAIL_PASS, and
EMAIL_NOTIFY_TO are properly set in your .env file.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Set
from dotenv import load_dotenv

# Define required and optional variables
REQUIRED_VARS: Dict[str, str] = {
    # Core settings
    "CONCURRENCY_LIMIT": "Number of simultaneous requests",
    "CHUNKSIZE": "Number of items to process before saving progress",
    
    # Proxy is optional but if username is provided, then password is required
    # Will check this logic separately
}

# Email notification variables - only required if email notifications are enabled
EMAIL_VARS: Dict[str, str] = {
    "EMAIL_USER": "Email address used to send notifications",
    "EMAIL_PASS": "Password or app-specific password for the email account",
    "EMAIL_NOTIFY_TO": "Email address to receive notifications"
}

# Optional variables with their descriptions and default values
OPTIONAL_VARS: Dict[str, tuple] = {
    "PROXY_USERNAME": ("Username for proxy authentication", ""),
    "PROXY_PASSWORD": ("Password for proxy authentication", ""),
    "PROXY_HOST": ("Proxy host and port", "rp.proxyscrape.com:6060"),
    "LOG_FILE": ("Log file path", "modern_refactored.log"),
    "LOG_LEVEL": ("Logging level", "INFO"),
    "EMAIL_NOTIFICATIONS_ENABLED": ("Enable/disable email notifications", "true"),
    "REQUEST_DELAY_MS": ("Delay between requests in milliseconds", "50"),
    "PART_TIMEOUT": ("Timeout for part processing in seconds", "90"),
    "SOCKET_CONNECT_TIMEOUT": ("Timeout for socket connections in seconds", "15"),
    "SOCKET_READ_TIMEOUT": ("Timeout for socket reads in seconds", "45")
}


def check_env_variables() -> bool:
    """Check if all required environment variables are set."""
    load_dotenv()
    
    missing_required: List[str] = []
    missing_optional: List[str] = []
    proxy_issues: List[str] = []
    email_issues: List[str] = []
    
    # Check required variables
    for var, description in REQUIRED_VARS.items():
        if not os.getenv(var):
            missing_required.append(f"{var}: {description}")
    
    # Check optional variables
    for var, (description, default) in OPTIONAL_VARS.items():
        if not os.getenv(var):
            missing_optional.append(f"{var}: {description} (default: {default})")
    
    # Special check for proxy variables
    proxy_username = os.getenv("PROXY_USERNAME")
    proxy_password = os.getenv("PROXY_PASSWORD")
    if proxy_username and not proxy_password:
        proxy_issues.append("PROXY_PASSWORD is required when PROXY_USERNAME is set")
    elif proxy_password and not proxy_username:
        proxy_issues.append("PROXY_USERNAME is required when PROXY_PASSWORD is set")
    
    # Special check for email notifications
    email_enabled = os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "").lower() in ("true", "yes", "1", "on")
    if email_enabled:
        for var, description in EMAIL_VARS.items():
            if not os.getenv(var):
                email_issues.append(f"{var}: {description}")
    
    # Print results
    if missing_required:
        print("❌ Missing required environment variables:")
        for var in missing_required:
            print(f"  - {var}")
    
    if proxy_issues:
        print("\n⚠️ Proxy configuration issues:")
        for issue in proxy_issues:
            print(f"  - {issue}")
    
    if email_issues:
        print("\n⚠️ Email notification issues (only required if email notifications are enabled):")
        for issue in email_issues:
            print(f"  - {issue}")
    
    if missing_optional:
        print("\n⚠️ Missing optional environment variables (will use defaults):")
        for var in missing_optional:
            print(f"  - {var}")
    
    if not missing_required and not proxy_issues and not email_issues:
        print("✅ All required environment variables are set correctly!")
        if not missing_optional:
            print("✅ All optional environment variables are set as well!")
        return True
    
    return not (missing_required or email_issues)


def compare_with_example() -> None:
    """Compare current .env with .env.example to find missing keys."""
    env_path = Path(".env")
    example_path = Path(".env.example")
    
    if not env_path.exists():
        print(f"❌ .env file not found at {env_path.absolute()}")
        return
    
    if not example_path.exists():
        print(f"❌ .env.example file not found at {example_path.absolute()}")
        return
    
    # Extract keys from files (ignore comments and empty lines)
    env_content = env_path.read_text().splitlines()
    example_content = example_path.read_text().splitlines()
    
    env_keys = set()
    for line in env_content:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            env_keys.add(line.split('=', 1)[0])
    
    example_keys = set()
    for line in example_content:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            # Remove leading # if it's a commented out key
            key = line.lstrip('# ').split('=', 1)[0]
            example_keys.add(key)
    
    # Find missing keys
    missing_in_env = example_keys - env_keys
    missing_in_example = env_keys - example_keys
    
    if missing_in_env:
        print("\n⚠️ Keys from .env.example that are missing in your .env file:")
        for key in sorted(missing_in_env):
            print(f"  - {key}")
    
    if missing_in_example:
        print("\n⚠️ Keys in your .env that are not documented in .env.example:")
        for key in sorted(missing_in_example):
            print(f"  - {key}")
    
    if not missing_in_env and not missing_in_example:
        print("\n✅ Your .env file has all the same keys as .env.example!")


if __name__ == "__main__":
    print("🔍 Validating environment variables for Generic-Scraper\n")
    env_valid = check_env_variables()
    print("\n🔄 Comparing .env with .env.example")
    compare_with_example()
    
    if env_valid:
        print("\n✅ Your environment appears to be properly configured.")
        print("📝 Tip: Keep a backup of your .env file in a secure location outside of git.")
        sys.exit(0)
    else:
        print("\n⚠️ Please fix the issues above to ensure proper application functionality.")
        print("📖 Refer to the README.md or .env.example for more information.")
        sys.exit(1)