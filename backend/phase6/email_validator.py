"""
Email Validator (Phase 6).

Basic regex validation to check if an email string is structurally sound
before attempting to build and send an email draft.
"""

import re

# Standard simple email regex
# (catches 99% of typos like "test@com", "test@.com", "user@site")
_EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

def is_valid_email(email: str) -> bool:
    """
    Return True if the email address string looks valid.
    
    Args:
        email: Email string to validate.
        
    Returns:
        bool: True if valid, False otherwise.
    """
    email = (email or "").strip()
    if not email:
        return False
        
    return bool(_EMAIL_REGEX.match(email))
