"""
Email notification utilities for G2S scraper.

Security:
- Never log or hardcode email credentials. Always load from environment/config.

Extensibility:
- To add new notification channels (e.g., Slack, SMS), add new functions here.
- TODO: Add support for secure OAuth or app-specific passwords if needed.

Maintainability:
- All notification logic should be type-annotated and have clear error handling.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(subject: str, body: str, to: str) -> None:
    """
    Send an email notification using SMTP credentials from environment variables.
    Supports Gmail and other SMTP servers.
    """
    email_user = os.getenv('EMAIL_USER')
    email_pass = os.getenv('EMAIL_PASS')
    if not (email_user and email_pass):
        raise RuntimeError("EMAIL_USER and EMAIL_PASS must be set in .env for email notifications.")
    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email_user, email_pass)
            server.sendmail(email_user, to, msg.as_string())
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Failed to send email: {e}") from e
