#!/usr/bin/env python3
"""
Test script for email functionality with proper error handling.
This is a standalone script, not a pytest test file.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))
# Skip pytest collection of this file
__test__ = False

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get email settings
email_user = os.getenv('EMAIL_USER', '')
email_pass = os.getenv('EMAIL_PASS', '')
email_notify_to = os.getenv('EMAIL_NOTIFY_TO', '')

print("Email Configuration:")
print(f"- EMAIL_USER: {'set' if email_user else 'not set'} ({email_user})")
mask = '*' * (len(email_pass) if email_pass else 0)
print(f"- EMAIL_PASS: {'set' if email_pass else 'not set'} {mask}")
print(f"- EMAIL_NOTIFY_TO: {'set' if email_notify_to else 'not set'} ({email_notify_to})")

# Try to import and use send_email
try:
    from email_utils import send_email

    # Don't actually send if using placeholder credentials
    if email_user == 'your_email@gmail.com' or email_pass == 'your_app_password':
        print("\nSkipping actual email send with placeholder credentials.")
        print("Update the .env file with real credentials to test sending.")
    else:
        print("\nAttempting to send test email...")
        send_email(
            subject="Test Email from Generic Scraper",
            body="This is a test email from the Generic Scraper application.",
            to=email_notify_to or email_user
        )
        print("Test email sent successfully!")
except ImportError as e:
    print(f"\nError importing email_utils: {e}")
except RuntimeError as e:
    print(f"\nRuntime error: {e}")
except Exception as e:
    print(f"\nUnexpected error: {e}")
