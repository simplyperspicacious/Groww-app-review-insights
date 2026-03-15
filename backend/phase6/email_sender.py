"""
Email Sender (Phase 6).

Sends the HTML/Text email payload using an SMTP server (default Gmail).
Requires SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD in config.
"""

import smtplib
from email.message import EmailMessage

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


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
    smtp_host = getattr(settings, "SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(getattr(settings, "SMTP_PORT", 587))
    smtp_user = getattr(settings, "SMTP_USER", "")
    smtp_pass = getattr(settings, "SMTP_PASSWORD", "")
    sender_name = getattr(settings, "SENDER_NAME", "Groww App Insights")

    if not smtp_user or not smtp_pass:
        raise ValueError(
            "SMTP_USER or SMTP_PASSWORD not found in environment. "
            "Please configure your .env file with valid SMTP credentials "
            "(e.g. Gmail App Password)."
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
        # Connect and authenticate
        # Use simple SMTP with STARTTLS (standard for SMTP port 587)
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_pass)
            
            # Send
            server.send_message(msg)
            
        logger.info(f"Successfully sent email to {to_email}")
        return {"status": "success", "message": f"Email sent to {to_email}"}

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        raise RuntimeError(f"Failed to send email: {e}")
