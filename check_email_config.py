#!/usr/bin/env python3
"""
Test script to verify email configurations.
"""

import os

# Add the project root to Python path
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get email settings
email_user = os.getenv('EMAIL_USER', '')
email_pass = os.getenv('EMAIL_PASS', '')
email_notify_to = os.getenv('EMAIL_NOTIFY_TO', '')
email_enabled = os.getenv('EMAIL_NOTIFICATIONS_ENABLED', '').lower() in ('true', '1', 'yes', 'on')

# Print configuration
print("Email Configuration:")
print(f"- EMAIL_USER: {'set' if email_user else 'not set'} ({email_user})")
print(f"- EMAIL_PASS: {'set' if email_pass else 'not set'} {'*' * (len(email_pass) if email_pass else 0)}")
print(f"- EMAIL_NOTIFY_TO: {'set' if email_notify_to else 'not set'} ({email_notify_to})")
print(f"- EMAIL_NOTIFICATIONS_ENABLED: {email_enabled}")
