"""
Phase 6 Pipeline — Email Draft Assembly & Delivery.

Reads weekly_pulse.md, validates recipient, converts Markdown to HTML,
and sends the final email payload via SMTP.
"""

from pathlib import Path

from utils.logger import get_logger
from phase6 import email_validator, email_builder, email_sender

logger = get_logger("phase6.pipeline")

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_DATA_PROCESSED = _BACKEND_ROOT / "data" / "processed"

PULSE_FILE = _DATA_PROCESSED / "weekly_pulse.md"


def run_pipeline(user_email: str, pulse_path: Path = None) -> dict:
    """
    Execute the Phase 6 pipeline.
    
    Args:
        user_email: The target email address to send the pulse to.
        pulse_path: Path to the generated weekly_pulse.md.
        
    Returns:
        Result dictionary with status.
    """
    pulse_path = pulse_path or PULSE_FILE

    logger.info("=" * 60)
    logger.info(f"PHASE 6 PIPELINE — Email Delivery to {user_email}")
    logger.info("=" * 60)

    # Step 1: Validate input email
    logger.info("[Step 1/3] Validating recipient email address...")
    if not email_validator.is_valid_email(user_email):
        logger.error(f"Invalid email address provided: {user_email}")
        raise ValueError(f"Invalid email address: {user_email}")
        
    if not pulse_path.exists():
        logger.error(f"Pulse file not found at {pulse_path}")
        raise FileNotFoundError(f"Pulse not found: {pulse_path}. Run Phase 5 first.")

    # Load the markdown content
    markdown_text = pulse_path.read_text(encoding="utf-8")
    
    # Step 2: Build email content
    logger.info("[Step 2/3] Converting Markdown pulse to HTML template...")
    html_body, text_body = email_builder.build_email_content(markdown_text)
    
    # Step 3: Send email
    logger.info("[Step 3/3] Sending email via SMTP...")
    # Extract week label from markdown header if possible, else generic
    subject = "📊 Groww Weekly App Review Pulse"
    first_line = markdown_text.strip().split("\n")[0]
    if "Week of" in first_line or "Pulse" in first_line:
        # Strip markdown hashes
        subject = first_line.replace("#", "").strip()

    result = email_sender.send_email(
        to_email=user_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body
    )

    logger.info("=" * 60)
    logger.info("PHASE 6 COMPLETE")
    logger.info("=" * 60)
    
    return result
