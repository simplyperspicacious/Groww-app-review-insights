"""
PII Scrubber — removes personally identifiable information from review data.

Strips:
- Email addresses from text
- Phone numbers from text
- URLs from text
- userName and reviewId fields (dropped entirely)
"""

import re
from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)

# Regex patterns for PII detection in review text
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_PATTERN = re.compile(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}')
URL_PATTERN = re.compile(r'https?://\S+|www\.\S+')

# Fields to strip entirely (PII)
PII_FIELDS = {"userName", "reviewId"}


def scrub_text(text: str) -> str:
    """
    Remove PII patterns (emails, phone numbers, URLs) from review text.

    Args:
        text: Raw review text.

    Returns:
        Text with PII patterns replaced by '[REDACTED]'.
    """
    text = EMAIL_PATTERN.sub("[REDACTED]", text)
    text = PHONE_PATTERN.sub("[REDACTED]", text)
    text = URL_PATTERN.sub("[REDACTED]", text)
    return text


def clean(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Scrub PII from a list of raw reviews.

    - Removes userName, reviewId fields entirely
    - Redacts emails, phone numbers, and URLs from text content

    Args:
        reviews: List of raw review dictionaries.

    Returns:
        List of reviews with PII removed.
    """
    cleaned = []
    redacted_count = 0

    for review in reviews:
        # Drop PII fields
        scrubbed = {k: v for k, v in review.items() if k not in PII_FIELDS}

        # Scrub text content
        if scrubbed.get("content"):
            original = scrubbed["content"]
            scrubbed["content"] = scrub_text(original)
            if scrubbed["content"] != original:
                redacted_count += 1

        cleaned.append(scrubbed)

    logger.info(f"PII scrubbed: {len(cleaned)} reviews processed, {redacted_count} had PII redacted")
    return cleaned
