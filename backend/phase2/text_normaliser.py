"""
Text Normaliser — lowercases, strips HTML/markdown, removes special characters.

Prepares review text for LLM consumption.
"""

import re
from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)

# Strip HTML tags
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
# Strip markdown bold/italic/code
MARKDOWN_PATTERN = re.compile(r"[\*_`#]{1,3}([^*_`#]*)[\*_`#]{1,3}")
# Keep only letters, digits, and basic punctuation; collapse whitespace
SPECIAL_CHARS_PATTERN = re.compile(r"[^\w\s.,!?\'\"-]|\s+")


def normalise_text(text: str) -> str:
    """
    Normalise a single review text for LLM consumption.

    - Lowercase
    - Strip HTML tags
    - Strip markdown formatting (bold, italic, code)
    - Remove special characters (keep letters, digits, .,!?'"-)
    - Collapse multiple spaces into one and strip

    Args:
        text: Raw review text.

    Returns:
        Normalised text.
    """
    if not text or not isinstance(text, str):
        return ""
    t = text.lower().strip()
    t = HTML_TAG_PATTERN.sub(" ", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)  # markdown links -> link text
    t = re.sub(r"[*_`#]+", " ", t)  # remove markdown markers
    t = re.sub(r"[^\w\s.,!?\'\"-]", " ", t)  # replace other special chars with space
    t = re.sub(r"\s+", " ", t).strip()
    return t


def normalise(reviews: List[Dict[str, Any]], text_key: str = "text") -> List[Dict[str, Any]]:
    """
    Normalise text for a list of reviews (in place, then return).

    Expects each review to have a key `text_key` (default "text") with the review body.
    Updates that key with normalised text.

    Args:
        reviews: List of review dicts (e.g. CleanReview as dict with "text").
        text_key: Key holding the review text (default "text").

    Returns:
        Same list with text values normalised.
    """
    for review in reviews:
        if text_key in review and review[text_key]:
            review[text_key] = normalise_text(review[text_key])
    logger.info(f"Text normaliser: {len(reviews)} reviews normalised")
    return reviews
