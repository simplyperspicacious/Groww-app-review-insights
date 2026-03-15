"""
Email Sender (Phase 6).

Sends the HTML/Text email payload using an SMTP server (default Gmail).
Requires SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD in config.
"""

import smtplib
import json
import urllib.request
import urllib.error
from email.message import EmailMessage

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def send_via_brevo(to_email: str, subject: str, text_body: str, html_body: str) -> dict:
    brevo_key = getattr(settings, "BREVO_API_KEY", "")
    sender_name = getattr(settings, "SENDER_NAME", "Groww App Insights")
    sender_email = getattr(settings, "SMTP_USER", "")
    
    if not sender_email:
        sender_email = "insights@growwanalyser.com" # Fallback if user didn't set SMTP_USER
        
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": brevo_key,
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_body,
        "textContent": text_body
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = response.read()
            logger.info(f"Successfully sent email via Brevo API to {to_email}")
            return {"status": "success", "message": f"Email sent via Brevo to {to_email}"}
    except urllib.error.URLError as e:
        error_msg = str(e)
        if hasattr(e, 'read'):
            error_msg += f" - {e.read().decode('utf-8', errors='ignore')}"
        logger.error(f"Brevo API failed: {error_msg}")
        raise RuntimeError(f"Brevo API failure: {error_msg}")


def send_email(to_email: str, subject: str, text_body: str, html_body: str) -> dict:
    """
    Send an email via SMTP.
    
    Args:
        to_email: The recipient's email address.
        subject: Email subject.
        text_body: Plain text fallback body.
        html_body: Primary HTML body.
        
    Returns:
        A dict with status and message (e.g., {"status": "success", "message": "..."}).
        
    Raises:
        ValueError: If SMTP credentials are not configured.
        smtplib.SMTPException: If the email fails to send.
    """
    # 1. Try Brevo HTTP Bypass First
    brevo_key = getattr(settings, "BREVO_API_KEY", "")
    if brevo_key:
        logger.info("BREVO_API_KEY found. Attempting HTTP dispatch to bypass SMTP blocks...")
        try:
            return send_via_brevo(to_email, subject, text_body, html_body)
        except Exception as e:
            logger.warning(f"Brevo dispatch failed, trying SMTP fallback: {e}")

    # 2. SMTP Fallback
    smtp_host = getattr(settings, "SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(getattr(settings, "SMTP_PORT", 587))
    smtp_user = getattr(settings, "SMTP_USER", "")
    smtp_pass = getattr(settings, "SMTP_PASSWORD", "")
    sender_name = getattr(settings, "SENDER_NAME", "Groww App Insights")

    if not smtp_user or not smtp_pass:
        raise ValueError(
            "SMTP_USER or SMTP_PASSWORD not found in environment. "
            "Please configure your .env file with valid SMTP credentials "
            "(e.g. Gmail App Password) or provide a BREVO_API_KEY."
        )

    # Build the message envelope
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{smtp_user}>"
    msg["To"] = to_email

    # Add the text and HTML alternate parts
    # email.message requires setting the content as text, then adding html alternative
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    logger.info(f"Connecting to {smtp_host}:{smtp_port} as {smtp_user}...")
    
    try:
        # Connect and authenticate (timeout prevents indefinite hanging on blocked ports)
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            
        logger.info(f"Successfully sent email to {to_email}")
        return {"status": "success", "message": f"Email sent to {to_email}"}

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        raise RuntimeError(f"Failed to send email: {e}")
